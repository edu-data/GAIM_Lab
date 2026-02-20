"""
🎨 Content Agent - 슬라이드/화면 품질 분석 (v7.1)
로컬 OCR(pytesseract)과 OpenCV를 활용한 화면 분석 (API 키 불필요)

v7.1 Optimizations:
  - SSIM 기반 유사 프레임 스킵 (동일 슬라이드 구간 고속 처리)
  - ThreadPoolExecutor 병렬 OCR (4 workers)
  - OCR 영역 축소 + 리사이즈 (처리 속도 향상)
"""

import cv2
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# pytesseract는 선택적 import
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# ─── v7.1: SSIM threshold for frame deduplication ───
_SSIM_THRESHOLD = 0.95   # frames with SSIM > this reuse previous result
_OCR_MAX_WIDTH = 800      # resize to this width before OCR
_PARALLEL_WORKERS = 4     # parallel OCR workers


def _compute_ssim_fast(img1_gray: np.ndarray, img2_gray: np.ndarray) -> float:
    """
    Fast structural similarity (simplified SSIM) between two grayscale images.
    Uses mean/variance/covariance without the full Wang et al. formula
    for speed — sufficient for frame deduplication.
    """
    if img1_gray.shape != img2_gray.shape:
        # resize to match
        img2_gray = cv2.resize(img2_gray, (img1_gray.shape[1], img1_gray.shape[0]))

    C1 = 6.5025    # (0.01 * 255)^2
    C2 = 58.5225   # (0.03 * 255)^2

    # Downscale for speed
    h, w = img1_gray.shape
    if w > 256:
        scale = 256 / w
        img1_gray = cv2.resize(img1_gray, (256, int(h * scale)))
        img2_gray = cv2.resize(img2_gray, (256, int(h * scale)))

    i1 = img1_gray.astype(np.float64)
    i2 = img2_gray.astype(np.float64)

    mu1 = cv2.GaussianBlur(i1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(i2, (11, 11), 1.5)

    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(i1 * i1, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(i2 * i2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(i1 * i2, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

    return float(np.mean(ssim_map))


@dataclass
class ContentMetrics:
    """화면/슬라이드 분석 결과"""
    timestamp: float
    text_density: int = 0              # 감지된 텍스트 글자 수
    text_density_score: int = 5        # 텍스트 밀도 점수 (1-10, 10=매우 많음)
    readability: str = "unknown"       # good, bad, unknown
    slide_detected: bool = False       # 슬라이드 영역 감지 여부
    speaker_visible: bool = False      # 강사 영상 감지 여부
    speaker_overlap: bool = False      # 강사가 슬라이드를 가리는지
    color_contrast: float = 0.0        # 색상 대비 (0-1)
    brightness: float = 0.0            # 평균 밝기 (0-255)
    complexity_score: float = 0.0      # 화면 복잡도 (0-100)
    is_duplicate: bool = False         # v7.1: 이전 프레임과 동일 (재사용)


class ContentAgent:
    """
    🎨 Content Agent (v7.1)
    PPT/화면 구성, 텍스트 밀도, 가독성 분석
    (Gemini API 없이 로컬 분석)

    v7.1: SSIM dedup + parallel OCR + region-resize optimization
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {
            "text_density_threshold": 150,
            "min_font_detection": 12,
            "ocr_language": "kor+eng",
        }

        self.results: List[ContentMetrics] = []
        self._prev_gray: Optional[np.ndarray] = None  # v7.1: for SSIM comparison
        self._prev_metrics: Optional[ContentMetrics] = None

        # v7.1: performance stats
        self._stats = {
            "total_frames": 0,
            "unique_frames": 0,
            "skipped_frames": 0,
            "ocr_time": 0.0,
        }

        if not TESSERACT_AVAILABLE:
            print("[!] pytesseract not installed. Text analysis will be limited.")

    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> ContentMetrics:
        """
        단일 프레임의 화면 구성 분석

        Args:
            frame: BGR 이미지 (OpenCV 형식)
            timestamp: 프레임 타임스탬프 (초)

        Returns:
            ContentMetrics 객체
        """
        self._stats["total_frames"] += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # v7.1: SSIM deduplication — skip if very similar to previous frame
        if self._prev_gray is not None and self._prev_metrics is not None:
            ssim = _compute_ssim_fast(gray, self._prev_gray)
            if ssim > _SSIM_THRESHOLD:
                # Reuse previous metrics with updated timestamp
                dup = ContentMetrics(
                    timestamp=timestamp,
                    text_density=self._prev_metrics.text_density,
                    text_density_score=self._prev_metrics.text_density_score,
                    readability=self._prev_metrics.readability,
                    slide_detected=self._prev_metrics.slide_detected,
                    speaker_visible=self._prev_metrics.speaker_visible,
                    speaker_overlap=self._prev_metrics.speaker_overlap,
                    color_contrast=self._prev_metrics.color_contrast,
                    brightness=self._prev_metrics.brightness,
                    complexity_score=self._prev_metrics.complexity_score,
                    is_duplicate=True,
                )
                self.results.append(dup)
                self._stats["skipped_frames"] += 1
                return dup

        # Full analysis for unique frames
        metrics = self._analyze_single_frame(frame, gray, timestamp)
        self._prev_gray = gray
        self._prev_metrics = metrics
        self._stats["unique_frames"] += 1
        self.results.append(metrics)
        return metrics

    def analyze_frames_batch(self, frames_with_ts: List[Tuple[np.ndarray, float]]) -> List[ContentMetrics]:
        """
        v7.1: 여러 프레임을 SSIM dedup + 병렬 OCR로 분석

        1단계: SSIM으로 고유 프레임 필터링
        2단계: 고유 프레임을 병렬로 분석
        3단계: 중복 프레임에 결과 복사

        Args:
            frames_with_ts: [(frame_bgr, timestamp), ...]

        Returns:
            분석 결과 리스트
        """
        if not frames_with_ts:
            return []

        t_start = time.time()

        # Step 1: Identify unique frames via SSIM
        unique_indices = []  # indices of unique frames
        dup_map = {}         # dup_index -> reference_unique_index

        prev_gray = None
        prev_unique_idx = None

        for i, (frame, ts) in enumerate(frames_with_ts):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                ssim = _compute_ssim_fast(gray, prev_gray)
                if ssim > _SSIM_THRESHOLD:
                    dup_map[i] = prev_unique_idx
                    self._stats["skipped_frames"] += 1
                    continue

            unique_indices.append(i)
            prev_gray = gray
            prev_unique_idx = i
            self._stats["unique_frames"] += 1

        self._stats["total_frames"] = len(frames_with_ts)

        print(f"  [ContentAgent] 프레임 중복 제거: {len(frames_with_ts)} → {len(unique_indices)} 고유 프레임 "
              f"({len(frames_with_ts) - len(unique_indices)} 스킵)")

        # Step 2: Parallel analysis of unique frames
        unique_results = {}  # index -> ContentMetrics

        def _analyze_one(idx):
            frame, ts = frames_with_ts[idx]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return idx, self._analyze_single_frame(frame, gray, ts)

        with ThreadPoolExecutor(max_workers=_PARALLEL_WORKERS) as pool:
            futures = {pool.submit(_analyze_one, idx): idx for idx in unique_indices}
            for future in as_completed(futures):
                try:
                    idx, metrics = future.result()
                    unique_results[idx] = metrics
                except Exception as e:
                    idx = futures[future]
                    frame, ts = frames_with_ts[idx]
                    unique_results[idx] = ContentMetrics(timestamp=ts)

        # Step 3: Build full results list (fill duplicates)
        all_results = []
        for i in range(len(frames_with_ts)):
            if i in unique_results:
                all_results.append(unique_results[i])
            elif i in dup_map:
                ref_idx = dup_map[i]
                ref = unique_results[ref_idx]
                _, ts = frames_with_ts[i]
                dup = ContentMetrics(
                    timestamp=ts,
                    text_density=ref.text_density,
                    text_density_score=ref.text_density_score,
                    readability=ref.readability,
                    slide_detected=ref.slide_detected,
                    speaker_visible=ref.speaker_visible,
                    speaker_overlap=ref.speaker_overlap,
                    color_contrast=ref.color_contrast,
                    brightness=ref.brightness,
                    complexity_score=ref.complexity_score,
                    is_duplicate=True,
                )
                all_results.append(dup)

        self.results = all_results
        elapsed = time.time() - t_start
        self._stats["ocr_time"] = elapsed
        print(f"  [ContentAgent] 분석 완료: {elapsed:.1f}s "
              f"(고유 {len(unique_indices)} / 전체 {len(frames_with_ts)})")

        return all_results

    def _analyze_single_frame(self, frame: np.ndarray, gray: np.ndarray,
                              timestamp: float) -> ContentMetrics:
        """단일 고유 프레임 전체 분석 (스레드 안전)"""
        metrics = ContentMetrics(timestamp=timestamp)

        # 1. 기본 이미지 속성 분석
        self._analyze_basic_properties(frame, gray, metrics)

        # 2. 화면 영역 분석 (슬라이드 vs 강사)
        self._analyze_regions(frame, gray, metrics)

        # 3. 텍스트 분석 (OCR)
        if TESSERACT_AVAILABLE:
            self._analyze_text(frame, gray, metrics)
        else:
            self._estimate_text_density(frame, gray, metrics)

        # 4. 화면 복잡도 분석
        self._analyze_complexity(gray, metrics)

        return metrics

    def _analyze_basic_properties(self, frame: np.ndarray, gray: np.ndarray,
                                  metrics: ContentMetrics):
        """기본 이미지 속성 분석"""
        # 밝기 계산
        metrics.brightness = float(np.mean(gray))

        # 색상 대비 계산
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        metrics.color_contrast = float(np.std(l_channel) / 128)

    def _analyze_regions(self, frame: np.ndarray, gray: np.ndarray,
                         metrics: ContentMetrics):
        """화면 영역 분석 (슬라이드, 강사 영역 감지)"""
        height, width = frame.shape[:2]

        # 얼굴 감지로 강사 영역 확인
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            metrics.speaker_visible = True

            # 얼굴이 중앙에 있으면 슬라이드를 가릴 가능성
            for (x, y, w, h) in faces:
                face_center_x = x + w // 2
                if width // 3 < face_center_x < 2 * width // 3:
                    metrics.speaker_overlap = True
                    break

        # 슬라이드 감지 (텍스트/도형이 있는 균일한 배경 영역)
        center_region = gray[height//4:3*height//4, width//4:3*width//4]

        # 엣지 감지로 콘텐츠 존재 확인
        edges = cv2.Canny(center_region, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # 일정 수준의 엣지 밀도가 있으면 슬라이드로 판단
        if 0.01 < edge_density < 0.3:
            metrics.slide_detected = True

    def _analyze_text(self, frame: np.ndarray, gray: np.ndarray,
                      metrics: ContentMetrics):
        """OCR을 통한 텍스트 분석 (v7.1: region + resize optimization)"""
        try:
            h, w = gray.shape

            # v7.1: Resize for faster OCR
            if w > _OCR_MAX_WIDTH:
                scale = _OCR_MAX_WIDTH / w
                gray_resized = cv2.resize(gray, (_OCR_MAX_WIDTH, int(h * scale)))
            else:
                gray_resized = gray

            # 적응형 이진화
            binary = cv2.adaptiveThreshold(
                gray_resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # OCR 수행
            text = pytesseract.image_to_string(
                binary,
                lang=self.config["ocr_language"]
            )

            # 텍스트 밀도 계산
            clean_text = ''.join(c for c in text if c.isalnum())
            metrics.text_density = len(clean_text)

            # 텍스트 밀도 점수 (1-10)
            threshold = self.config["text_density_threshold"]
            density_ratio = metrics.text_density / threshold
            metrics.text_density_score = min(10, max(1, int(density_ratio * 5) + 1))

            # 가독성 판단
            if metrics.text_density > threshold * 1.5:
                metrics.readability = "bad"  # 텍스트 과다
            elif metrics.text_density < 10:
                metrics.readability = "good"
            else:
                metrics.readability = "good"

        except Exception as e:
            self._estimate_text_density(frame, gray, metrics)

    def _estimate_text_density(self, frame: np.ndarray, gray: np.ndarray,
                               metrics: ContentMetrics):
        """OCR 없이 텍스트 밀도 추정 (엣지 기반)"""
        # 텍스트 영역 감지 (MSER 알고리즘)
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)

        # 텍스트로 추정되는 영역 수로 밀도 추정
        estimated_chars = len(regions) // 3
        metrics.text_density = estimated_chars

        # 점수 계산
        density_ratio = estimated_chars / self.config["text_density_threshold"]
        metrics.text_density_score = min(10, max(1, int(density_ratio * 5) + 1))

        if estimated_chars > self.config["text_density_threshold"]:
            metrics.readability = "bad"
        else:
            metrics.readability = "unknown"

    def _analyze_complexity(self, gray: np.ndarray, metrics: ContentMetrics):
        """화면 복잡도 분석"""
        # Laplacian variance로 복잡도 측정
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # 정규화 (0-100)
        metrics.complexity_score = min(100, variance / 50)

    def get_summary(self) -> Dict:
        """분석 결과 요약"""
        if not self.results:
            return {"error": "분석 결과가 없습니다"}

        total = len(self.results)

        summary = {
            "total_frames_analyzed": total,
            "avg_text_density": np.mean([r.text_density for r in self.results]),
            "avg_text_density_score": np.mean([r.text_density_score for r in self.results]),
            "high_density_ratio": sum(1 for r in self.results if r.text_density_score >= 7) / total,
            "slide_detection_ratio": sum(1 for r in self.results if r.slide_detected) / total,
            "speaker_visible_ratio": sum(1 for r in self.results if r.speaker_visible) / total,
            "speaker_overlap_ratio": sum(1 for r in self.results if r.speaker_overlap) / total,
            "avg_brightness": np.mean([r.brightness for r in self.results]),
            "avg_complexity": np.mean([r.complexity_score for r in self.results]),
            "warnings": self._get_warnings()
        }

        # v7.1: Add optimization stats
        if self._stats["total_frames"] > 0:
            summary["optimization"] = {
                "total_frames": self._stats["total_frames"],
                "unique_frames": self._stats["unique_frames"],
                "skipped_frames": self._stats["skipped_frames"],
                "dedup_ratio": round(self._stats["skipped_frames"] / max(1, self._stats["total_frames"]), 3),
                "ocr_time": round(self._stats["ocr_time"], 2),
            }

        return summary

    def _get_warnings(self) -> List[str]:
        """경고 메시지 생성"""
        if not self.results:
            return []

        warnings = []
        total = len(self.results)

        # Calculate values directly to avoid recursion
        high_density_ratio = sum(1 for r in self.results if r.text_density_score >= 7) / total
        speaker_overlap_ratio = sum(1 for r in self.results if r.speaker_overlap) / total
        avg_brightness = np.mean([r.brightness for r in self.results])

        if high_density_ratio > 0.3:
            warnings.append("[!] High text density detected in over 30% of frames")

        if speaker_overlap_ratio > 0.2:
            warnings.append("[!] Speaker frequently overlaps slide content")

        if avg_brightness < 80:
            warnings.append("[!] Screen is generally too dark")
        elif avg_brightness > 220:
            warnings.append("[!] Screen is generally too bright")

        return warnings

    def get_timeline(self) -> List[Dict]:
        """시간별 분석 결과"""
        return [
            {
                "timestamp": r.timestamp,
                "text_density_score": r.text_density_score,
                "readability": r.readability,
                "slide_detected": r.slide_detected,
                "speaker_overlap": r.speaker_overlap
            }
            for r in self.results
        ]

    def find_high_density_frames(self) -> List[float]:
        """텍스트 밀도가 높은 프레임 타임스탬프"""
        return [
            r.timestamp
            for r in self.results
            if r.text_density_score >= 7
        ]

    def reset(self):
        """분석 결과 초기화"""
        self.results = []
        self._prev_gray = None
        self._prev_metrics = None
        self._stats = {
            "total_frames": 0,
            "unique_frames": 0,
            "skipped_frames": 0,
            "ocr_time": 0.0,
        }
