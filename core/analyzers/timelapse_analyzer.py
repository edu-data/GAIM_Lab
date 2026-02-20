"""
⚡ Time-Lapse Analyzer v3 - 초고속 타임랩스 분석 모듈
FFmpeg + Multiprocessing으로 15분 영상을 60초 내에 분석

핵심 전략:
1. FFmpeg C 레벨 디코딩으로 I/O 병목 제거
2. MediaPipe Lite (model_complexity=0) 사용
3. Vision + Audio 완전 병렬 처리
4. Perceptual Hash 기반 중복 프레임 건너뛰기 (유니크 프레임만 분석)
5. 최적화된 CPU 병렬 청크 + 메모리 관리
"""

import os
import glob
import shutil
import subprocess
import multiprocessing
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import cv2
import numpy as np

# MediaPipe 조건부 임포트
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[!] MediaPipe not available, using OpenCV fallback")

# Librosa 조건부 임포트
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[!] Librosa not available, audio analysis disabled")

# pytesseract OCR 설정
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("[!] pytesseract not available, text extraction disabled")


@dataclass
class TurboAnalysisResult:
    """터보 분석 결과 컨테이너"""
    timeline: List[Dict]
    audio_metrics: Dict
    audio_timeline: List[Dict]  # 세그먼트별 오디오 타임라인
    elapsed_seconds: float
    frame_count: int
    unique_frame_count: int = 0  # 유니크 프레임 수
    skipped_frames: int = 0     # 건너뛴 중복 프레임 수


# ---------------------------------------------------------
# 0. [Dedup] Perceptual Hash 기반 중복 프레임 제거
# ---------------------------------------------------------
def compute_phash(image_path: str, hash_size: int = 8) -> str:
    """
    Average Hash (aHash) 기반 Perceptual Hash 계산
    
    Args:
        image_path: 이미지 파일 경로
        hash_size: 해시 크기 (8 = 64bit hash)
        
    Returns:
        해시 문자열
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return ""
    # 해시 크기로 리사이즈 → 평균 기준 이진화
    resized = cv2.resize(img, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    mean_val = resized.mean()
    bits = (resized > mean_val).flatten()
    return ''.join(['1' if b else '0' for b in bits])


def hamming_distance(h1: str, h2: str) -> int:
    """두 해시 간 Hamming Distance"""
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def deduplicate_frames(image_paths: List[str], threshold: int = 4) -> Tuple[List[str], List[int]]:
    """
    유사한 프레임을 건너뛰고 유니크한 프레임만 반환
    
    Args:
        image_paths: 정렬된 이미지 경로 리스트
        threshold: Hamming Distance 임계값 (낮을수록 엄격)
                   4 = 93.75% 유사도 이상이면 중복으로 판정
        
    Returns:
        (유니크 이미지 경로 리스트, 스킵된 프레임 인덱스 리스트)
    """
    if not image_paths:
        return [], []
    
    unique = [image_paths[0]]
    skipped_indices = []
    prev_hash = compute_phash(image_paths[0])
    
    for i, path in enumerate(image_paths[1:], start=1):
        curr_hash = compute_phash(path)
        if not curr_hash:
            skipped_indices.append(i)
            continue
        
        dist = hamming_distance(prev_hash, curr_hash)
        if dist > threshold:
            # 유니크 프레임
            unique.append(path)
            prev_hash = curr_hash
        else:
            skipped_indices.append(i)
    
    return unique, skipped_indices


# ---------------------------------------------------------
# 1. [I/O Phase] FFmpeg를 이용한 초고속 리소스 추출
# ---------------------------------------------------------
def flash_extract_resources(video_path: str, output_dir: str, use_gpu: bool = True) -> Tuple[List[str], str]:
    """
    영상에서 '분석에 필요한 최소한의 데이터'만 물리적으로 추출합니다.
    
    Args:
        video_path: 입력 비디오 경로
        output_dir: 출력 디렉토리 (임시 캐시)
        use_gpu: GPU 가속 사용 여부 (NVIDIA CUDA)
        
    Returns:
        (이미지 경로 리스트, 오디오 파일 경로)
        
    Notes:
        - Video: 1초에 1장(1fps), 360p 해상도로 이미지 저장
        - Audio: 16kHz 모노 WAV 파일로 분리
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # GPU 가속 감지
    gpu_available = False
    if use_gpu:
        try:
            result = subprocess.run(
                ['ffmpeg', '-hwaccels'],
                capture_output=True, text=True, timeout=5
            )
            gpu_available = 'cuda' in result.stdout.lower()
        except Exception:
            pass
    
    accel_mode = "GPU (CUDA)" if gpu_available else "CPU"
    print(f"⚡ [Phase 1] FFmpeg 리소스 추출 시작... [{accel_mode}]")
    
    # 비디오 추출 명령 (GPU 가속 적용)
    if gpu_available:
        # NVIDIA GPU: scale_cuda로 GPU에서 스케일링까지 처리
        cmd_vid = [
            'ffmpeg',
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda',
            '-i', video_path,
            '-vf', 'scale_cuda=640:360,hwdownload,format=nv12,fps=1',
            '-q:v', '2',
            f'{output_dir}/frame_%04d.jpg',
            '-loglevel', 'error', '-y'
        ]
    else:
        cmd_vid = [
            'ffmpeg', '-i', video_path,
            '-vf', 'fps=1,scale=640:360',
            '-q:v', '2',
            f'{output_dir}/frame_%04d.jpg',
            '-loglevel', 'error', '-y'
        ]
    
    # 오디오 추출 명령
    audio_path = os.path.join(output_dir, "audio.wav")
    cmd_aud = [
        'ffmpeg', '-i', video_path,
        '-ar', '16000', '-ac', '1',
        audio_path,
        '-loglevel', 'error', '-y'
    ]
    
    # 두 작업을 동시에 던져놓고 기다림 (Parallel I/O)
    p1 = subprocess.Popen(cmd_vid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p2 = subprocess.Popen(cmd_aud, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # GPU 명령 실패 시 CPU fallback
    exit_code = p1.wait()
    if exit_code != 0 and gpu_available:
        print("   [!] GPU 추출 실패, CPU fallback...")
        cmd_vid_cpu = [
            'ffmpeg', '-i', video_path,
            '-vf', 'fps=1,scale=640:360',
            '-q:v', '2',
            f'{output_dir}/frame_%04d.jpg',
            '-loglevel', 'error', '-y'
        ]
        subprocess.run(cmd_vid_cpu, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    p2.wait()
    
    images = sorted(glob.glob(f'{output_dir}/*.jpg'))
    print(f"   ✅ 추출 완료: 이미지 {len(images)}장, 오디오 1개")
    
    return images, audio_path


# ---------------------------------------------------------
# 2. [Vision Worker] 이미지 배치 분석
# ---------------------------------------------------------
def analyze_vision_batch(image_paths: List[str]) -> List[Dict]:
    """
    할당받은 이미지 묶음(Chunk)을 연속 처리
    
    핵심: 프로세스당 모델을 단 한 번만 로드(Load Once)
    
    Args:
        image_paths: 분석할 이미지 파일 경로 리스트
        
    Returns:
        분석 결과 딕셔너리 리스트
    """
    results = []
    
    # MediaPipe 사용 가능 시 Pose 모델 초기화
    mp_pose = None
    if MEDIAPIPE_AVAILABLE:
        try:
            mp_pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=0,  # Lite 모델 (최고 속도)
                min_detection_confidence=0.5
            )
        except Exception:
            mp_pose = None
    
    # OpenCV Haar Cascade (fallback)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    for img_path in image_paths:
        try:
            # 프레임 인덱스 추출 (frame_0001.jpg -> 1)
            frame_idx = int(os.path.basename(img_path).split('_')[1].split('.')[0])
            
            frame = cv2.imread(img_path)
            if frame is None:
                continue
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = frame.shape[:2]
            
            # A. 제스처 역동성 분석
            gesture_active = False
            face_detected = False
            eye_contact = False
            
            if mp_pose is not None:
                pose_res = mp_pose.process(frame_rgb)
                if pose_res.pose_landmarks:
                    # 손목(15,16)이 가슴(0.7) 높이보다 위인지 확인
                    lw_y = pose_res.pose_landmarks.landmark[15].y
                    rw_y = pose_res.pose_landmarks.landmark[16].y
                    if lw_y < 0.7 or rw_y < 0.7:
                        gesture_active = True
                    # 코(0) 위치로 얼굴 중앙 체크
                    nose_x = pose_res.pose_landmarks.landmark[0].x
                    if 0.3 < nose_x < 0.7:
                        eye_contact = True
                    face_detected = True
            else:
                # Haar Cascade fallback
                faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                if len(faces) > 0:
                    face_detected = True
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    face_center_x = (x + w // 2) / width
                    eye_contact = 0.3 < face_center_x < 0.7
            
            # B. 슬라이드 복잡도 (Canny Edge 밀도)
            edges = cv2.Canny(gray, 100, 200)
            complexity = float(np.sum(edges)) / edges.size
            
            # C. 텍스트 밀도 추정 (MSER)
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            text_density = len(regions) // 3
            
            results.append({
                "sec": frame_idx,
                "timestamp": float(frame_idx),
                "gesture_active": gesture_active,
                "face_detected": face_detected,
                "eye_contact": eye_contact,
                "slide_complexity": complexity,
                "text_density": text_density,
                "gesture_score": 1.0 if gesture_active else 0.0,
                "expression_score": 50.0 if face_detected else 0.0
            })
            
        except Exception as e:
            # 오류 시 해당 프레임 스킵
            continue
    
    # MediaPipe 리소스 정리
    if mp_pose is not None:
        mp_pose.close()
    
    return results


def analyze_audio_track(audio_path: str, segment_duration: float = 10.0) -> Tuple[Dict, List[Dict]]:
    """
    오디오 트랙 분석 (침묵 비율, 피치 다양성) + 세그먼트별 타임라인
    
    Args:
        audio_path: WAV 파일 경로
        segment_duration: 세그먼트 길이 (초)
        
    Returns:
        (전체 오디오 메트릭, 세그먼트별 타임라인 리스트)
    """
    empty_metrics = {
        "silence_ratio": 0.0,
        "pitch_std": 0.0,
        "energy_mean": 0.0,
        "is_monotone": False
    }
    
    if not LIBROSA_AVAILABLE:
        return empty_metrics, []
    
    try:
        # WAV 파일 직접 로딩
        y, sr = librosa.load(audio_path, sr=16000)
        total_duration = len(y) / sr
        
        # === 전체 메트릭 계산 ===
        non_silent = librosa.effects.split(y, top_db=20)
        if len(y) > 0:
            speech_samples = sum(end - start for start, end in non_silent)
            silence_ratio = 1 - (speech_samples / len(y))
        else:
            silence_ratio = 1.0
        
        energy = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(energy))
        
        # 피치 다양성 (앞부분 60초 샘플링)
        sample_length = min(60 * sr, len(y))
        f0 = librosa.yin(y[:sample_length], fmin=50, fmax=300)
        pitch_std = float(np.std(f0[f0 > 0])) if np.any(f0 > 0) else 0.0
        is_monotone = pitch_std < 20.0
        
        overall_metrics = {
            "silence_ratio": silence_ratio,
            "pitch_std": pitch_std,
            "energy_mean": energy_mean,
            "is_monotone": is_monotone
        }
        
        # === 세그먼트별 타임라인 생성 (병렬화 - ThreadPool) ===
        segment_samples = int(segment_duration * sr)
        segment_data = []
        
        # 세그먼트 데이터 준비
        for seg_idx in range(0, len(y), segment_samples):
            seg_start = seg_idx
            seg_end = min(seg_idx + segment_samples, len(y))
            segment = y[seg_start:seg_end]
            
            if len(segment) < sr:  # 1초 미만 세그먼트 스킵
                continue
            
            segment_data.append((segment, seg_idx / sr, sr))
        
        # ThreadPoolExecutor 사용 (daemonic process 문제 회피)
        from concurrent.futures import ThreadPoolExecutor
        num_workers = max(2, multiprocessing.cpu_count() // 2)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            segment_timeline = list(executor.map(_analyze_audio_segment, segment_data))
        
        return overall_metrics, segment_timeline
        
    except Exception as e:
        print(f"   [!] 오디오 분석 오류: {e}")
        return empty_metrics, []


def _analyze_audio_segment(args: Tuple) -> Dict:
    """
    단일 오디오 세그먼트 분석 (병렬 워커)
    
    Args:
        args: (segment_array, timestamp, sample_rate) 튜플
    """
    segment, timestamp, sr = args
    
    try:
        # 세그먼트 에너지
        seg_energy = librosa.feature.rms(y=segment)[0]
        seg_energy_mean = float(np.mean(seg_energy))
        
        # 세그먼트 침묵 감지
        seg_non_silent = librosa.effects.split(segment, top_db=25)
        seg_speech = sum(end - start for start, end in seg_non_silent)
        seg_is_silent = seg_speech < len(segment) * 0.3
        
        # 세그먼트 피치
        seg_f0 = librosa.yin(segment, fmin=50, fmax=300)
        seg_pitch_std = float(np.std(seg_f0[seg_f0 > 0])) if np.any(seg_f0 > 0) else 0.0
        seg_pitch_mean = float(np.mean(seg_f0[seg_f0 > 0])) if np.any(seg_f0 > 0) else 0.0
        
        return {
            "timestamp": timestamp,
            "energy": seg_energy_mean,
            "pitch": seg_pitch_mean,
            "pitch_std": seg_pitch_std,
            "is_silent": seg_is_silent,
            "is_monotone": seg_pitch_std < 15.0
        }
    except Exception:
        return {
            "timestamp": timestamp,
            "energy": 0.0,
            "pitch": 0.0,
            "pitch_std": 0.0,
            "is_silent": True,
            "is_monotone": True
        }


def run_turbo_analysis(video_path: str, temp_dir: str = None, use_gpu: bool = True) -> TurboAnalysisResult:
    """
    초고속 타임랩스 분석 메인 오케스트레이터 v3
    
    v3 개선:
    - Perceptual Hash 기반 중복 프레임 제거 (유니크 프레임만 분석)
    - CPU 병렬 처리 최적화 (코어 수 × 2 청크로 부하 분산)
    - 메모리 관리 강화
    
    Args:
        video_path: 분석할 비디오 파일 경로
        temp_dir: 임시 캐시 디렉토리 (None이면 자동 생성)
        use_gpu: GPU 가속 사용 여부
        
    Returns:
        TurboAnalysisResult 객체
    """
    start_time = time.time()
    
    video_path = str(Path(video_path).resolve())
    if temp_dir is None:
        temp_dir = os.path.join(os.path.dirname(video_path), ".turbo_cache")
    
    print("=" * 60)
    print("  ⚡ TURBO MODE v3: 초고속 타임랩스 분석")
    print("  GPU가속 + 중복프레임 제거 + CPU 병렬 최적화")
    print("=" * 60)
    print(f"📁 입력: {os.path.basename(video_path)}")
    
    # [Step 1] 리소스 추출 (GPU 가속 시도)
    images, audio_path = flash_extract_resources(video_path, temp_dir, use_gpu=use_gpu)
    extract_time = time.time() - start_time
    print(f"   ⏱️ 추출 시간: {extract_time:.1f}초")
    
    if not images:
        raise ValueError("프레임 추출 실패: 이미지가 생성되지 않았습니다.")
    
    total_images = len(images)
    
    # [Step 1.5] 중복 프레임 제거 (Perceptual Hash)
    print(f"\n🔍 [Phase 1.5] 중복 프레임 제거 중...")
    dedup_start = time.time()
    unique_images, skipped = deduplicate_frames(images, threshold=4)
    dedup_time = time.time() - dedup_start
    skipped_count = len(skipped)
    print(f"   📊 전체 {total_images}장 → 유니크 {len(unique_images)}장 (중복 {skipped_count}장 건너뜀)")
    print(f"   💾 분석 절감: {skipped_count / max(total_images, 1) * 100:.1f}%")
    print(f"   ⏱️ 중복 제거 시간: {dedup_time:.1f}초")
    
    # [Step 2] 최적 청크 크기 계산 (CPU 코어 수 기반)
    num_cores = max(2, multiprocessing.cpu_count())
    unique_count = len(unique_images)
    
    # 최적 청크 크기: 코어당 30-80장 (모델 로딩 오버헤드 vs 메모리 균형)
    # 코어 × 2 청크로 부하 분산 극대화
    target_chunks = num_cores * 2
    optimal_chunk_size = max(20, min(80, unique_count // target_chunks + 1))
    
    image_chunks = [unique_images[i:i + optimal_chunk_size] for i in range(0, unique_count, optimal_chunk_size)]
    
    print(f"\n⚡ [Phase 2] CPU 병렬 분석 시작...")
    print(f"   코어: {num_cores}개, 청크: {len(image_chunks)}개 (청크당 ~{optimal_chunk_size}장)")
    
    # [Step 3] 병렬 실행 (Vision과 Audio가 동시에 돌아감)
    analysis_start = time.time()
    
    # maxtasksperchild로 메모리 누수 방지
    with multiprocessing.Pool(processes=num_cores, maxtasksperchild=4) as pool:
        # A. 오디오 분석을 비동기(Async)로 던짐 (세그먼트 타임라인 포함)
        audio_job = pool.apply_async(analyze_audio_track, (audio_path, 10.0))
        
        # B. 비전 분석을 병렬(Map)로 수행 (유니크 프레임만)
        vision_results_list = pool.map(analyze_vision_batch, image_chunks)
        
        # C. 오디오 결과 회수 (metrics, timeline)
        audio_result = audio_job.get(timeout=600)  # 10분 타임아웃
        audio_metrics, audio_timeline = audio_result
    
    analysis_time = time.time() - analysis_start
    print(f"   ⏱️ 분석 시간: {analysis_time:.1f}초")

    # [Step 4] 결과 병합 및 정리
    final_timeline = [item for sublist in vision_results_list for item in sublist]
    final_timeline.sort(key=lambda x: x['sec'])
    
    # 캐시 삭제
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass
    
    elapsed = time.time() - start_time
    
    print(f"\n✨ 전체 분석 완료!")
    print(f"   📊 Vision 프레임: {len(final_timeline)}개 (전체 {total_images}장 중 유니크 {len(unique_images)}장 분석)")
    print(f"   🔊 Audio 세그먼트: {len(audio_timeline)}개")
    print(f"   ⏱️ 총 소요: {elapsed:.2f}초")
    print("=" * 60)
    
    return TurboAnalysisResult(
        timeline=final_timeline,
        audio_metrics=audio_metrics,
        audio_timeline=audio_timeline,
        elapsed_seconds=elapsed,
        frame_count=len(final_timeline),
        unique_frame_count=len(unique_images),
        skipped_frames=skipped_count
    )


class TimeLapseAnalyzer:
    """
    ⚡ 타임랩스 분석기 클래스
    
    기존 ParallelFrameAnalyzer와 호환되는 인터페이스 제공
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Args:
            temp_dir: 임시 캐시 디렉토리
        """
        self.temp_dir = temp_dir
        self.last_result: Optional[TurboAnalysisResult] = None
    
    def analyze_video(self, video_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """
        비디오 분석 (ParallelFrameAnalyzer 호환 인터페이스)
        
        Args:
            video_path: 비디오 파일 경로
            
        Returns:
            (vision_results, content_results) 튜플
        """
        result = run_turbo_analysis(str(video_path), self.temp_dir)
        self.last_result = result
        
        # 기존 형식으로 변환
        vision_results = []
        content_results = []
        
        for item in result.timeline:
            vision_results.append({
                "timestamp": item["timestamp"],
                "face_detected": item.get("face_detected", False),
                "eye_contact": item.get("eye_contact", False),
                "gesture_score": item.get("gesture_score", 0.0),
                "expression_score": item.get("expression_score", 50.0),
                "motion_score": 0.0
            })
            content_results.append({
                "timestamp": item["timestamp"],
                "text_density": item.get("text_density", 0),
                "text_density_score": min(10, item.get("text_density", 0) // 15 + 1),
                "complexity_score": item.get("slide_complexity", 0) * 100,
                "slide_detected": item.get("slide_complexity", 0) > 0.05,
                "brightness": 128.0,
                "speaker_visible": item.get("face_detected", False),
                "speaker_overlap": False
            })
        
        return vision_results, content_results
    
    def get_audio_metrics(self) -> Dict:
        """마지막 분석의 오디오 메트릭 반환"""
        if self.last_result:
            return self.last_result.audio_metrics
        return {}
    
    def get_elapsed_time(self) -> float:
        """마지막 분석 소요 시간 반환"""
        if self.last_result:
            return self.last_result.elapsed_seconds
        return 0.0
    
    def get_audio_timeline(self) -> List[Dict]:
        """마지막 분석의 오디오 세그먼트 타임라인 반환"""
        if self.last_result:
            return self.last_result.audio_timeline
        return []


# ---------------------------------------------------------
# CLI 테스트
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video = sys.argv[1]
    else:
        # 기본 테스트 경로
        video = r"D:\data science\02.21\녹화_2025_02_21_08_37_50_910.mp4"
    
    if os.path.exists(video):
        result = run_turbo_analysis(video)
        print(f"\n📊 타임라인 항목: {len(result.timeline)}개")
        print(f"🔊 오디오 메트릭: {result.audio_metrics}")
        print(f"⏱️ 목표 60초 대비: {result.elapsed_seconds/60*100:.1f}%")
    else:
        print(f"파일을 찾을 수 없습니다: {video}")
