"""
GAIM Lab v8.0 — PathRegistry (경로 중앙 관리)

에러 #1 방지: 분석 파이프라인의 모든 경로를 단일 객체로 관리
파일을 생성하는 함수와 읽는 함수가 동일한 경로 객체를 참조
"""

from pathlib import Path
from typing import Optional


class PathRegistry:
    """분석 파이프라인 파일 경로 중앙 관리

    모든 에이전트와 오케스트레이터는 이 객체를 통해 경로를 참조합니다.
    직접 경로 문자열을 구성하지 않습니다.
    
    사용 예:
        paths = PathRegistry("/tmp/analysis_abc123")
        paths.ensure_dirs()
        # Extractor가 프레임 저장
        frame_path = paths.frames_dir / "frame_001.jpg"
        # Vision Agent가 프레임 읽기
        frames = paths.list_frames()
    """

    def __init__(self, base_dir: str | Path):
        self.base = Path(base_dir)
        self.frames_dir = self.base / "frames"
        self.audio_file = self.base / "audio.wav"
        self.result_json = self.base / "result.json"
        self.transcript_file = self.base / "transcript.json"
        self.vibe_file = self.base / "vibe_analysis.json"
        self.discourse_file = self.base / "discourse.json"
        self.report_html = self.base / "report.html"
        self.report_pdf = self.base / "report.pdf"

    def ensure_dirs(self):
        """필요한 디렉토리 생성"""
        self.base.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)

    def list_frames(self, extensions: tuple = (".jpg", ".jpeg", ".png")) -> list[Path]:
        """프레임 이미지 파일 목록 (정렬됨)
        
        v7.2 에러 원인: frames/ 하위와 base/ 직접 모두 검색하던 분산 로직
        v8.0: 무조건 frames_dir에서만 검색 (단일 경로)
        """
        if not self.frames_dir.exists():
            return []
        frames = [
            f for f in sorted(self.frames_dir.iterdir())
            if f.suffix.lower() in extensions
        ]
        return frames

    def has_audio(self) -> bool:
        """오디오 파일 존재 여부"""
        return self.audio_file.exists() and self.audio_file.stat().st_size > 0

    def has_frames(self) -> bool:
        """프레임 파일 존재 여부"""
        return len(self.list_frames()) > 0

    @property
    def frame_count(self) -> int:
        """추출된 프레임 수"""
        return len(self.list_frames())

    def frame_path(self, index: int) -> Path:
        """특정 인덱스의 프레임 경로 (저장용)"""
        return self.frames_dir / f"frame_{index:04d}.jpg"

    def __repr__(self) -> str:
        return f"PathRegistry(base='{self.base}', frames={self.frame_count})"
