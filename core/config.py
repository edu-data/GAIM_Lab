"""
멀티모달 렉처 코치 - 설정 파일
Multimodal Lecture Coach Configuration
"""

from pathlib import Path

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
TEMPLATES_DIR = REPORTS_DIR / "templates"

# 테스트 영상 경로 (환경변수 또는 기본 경로)
import os
SAMPLE_VIDEO = Path(os.getenv("GAIM_SAMPLE_VIDEO", str(BASE_DIR.parent / "video")))

# ============================================================
# Vision Agent 설정
# ============================================================
VISION_CONFIG = {
    "frame_sample_rate": 1.0,        # 초당 샘플링할 프레임 수
    "gesture_threshold": 0.6,         # 손 위치 활성화 임계값 (y좌표)
    "face_confidence": 0.5,           # 얼굴 인식 최소 신뢰도
}

# ============================================================
# Vibe Agent 설정 (Audio Analysis)
# ============================================================
VIBE_CONFIG = {
    "whisper_model": "base",          # tiny, base, small, medium, large
    "sample_rate": 22050,             # librosa 샘플링 레이트
    "segment_duration": 10.0,         # 분석 세그먼트 길이 (초)
    "monotone_threshold": 15,         # pitch_std < 이 값이면 단조로움
    "silence_db": 20,                 # 침묵 감지 데시벨 임계값
    "ideal_silence_ratio": (0.1, 0.3) # 이상적인 침묵 비율 범위
}

# ============================================================
# Content Agent 설정 (Slide Analysis - Local)
# ============================================================
CONTENT_CONFIG = {
    "text_density_threshold": 150,    # 글자 수 초과 시 경고
    "min_font_detection": 12,         # 최소 감지 폰트 크기
    "ocr_language": "kor+eng",        # Tesseract 언어
}

# ============================================================
# Master Agent 설정
# ============================================================
MASTER_CONFIG = {
    "segment_duration": 10.0,             # 분석 세그먼트 길이 (초)
    "death_valley_duration": 30,          # 연속 지루함 구간 최소 초
    "incongruence_threshold": 0.5,        # 불일치 감지 임계값
}

# ============================================================
# 참고: 평가 프레임워크
# ============================================================
# 실제 7차원 100점 만점 평가 체계는 config/rubric_config.yaml에 정의되어 있으며
# core/agents/pedagogy_agent.py의 PedagogyAgent가 로드합니다.
# 레거시 135점 4차원 체계(v1.0)는 v7.0에서 완전히 제거되었습니다.
