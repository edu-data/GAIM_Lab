"""
Agent Orchestrator - Multi-Agent Pipeline Orchestrator
Google ADK style agent execution management system

v7.0: Pydantic-based SharedContext, confidence metadata propagation
Pipeline flow:
EXTRACT -> [VISION | CONTENT | STT | VIBE] (parallel) -> PEDAGOGY -> FEEDBACK -> SYNTHESIZE
"""

import time
import traceback
import threading
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

# 프로젝트 구조 기반 경로 설정
_AGENTS_DIR = Path(__file__).resolve().parent
_CORE_DIR = _AGENTS_DIR.parent
_PROJECT_ROOT = _CORE_DIR.parent


def _load_module(module_name: str, file_path: Path):
    """파일 경로 기반 모듈 동적 로드"""
    import sys
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None:
        raise ImportError(f"Cannot load module from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class AgentStatus(Enum):
    """에이전트 실행 상태"""
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class PipelinePhase(Enum):
    """파이프라인 단계"""
    EXTRACT = "extract"
    VISION = "vision"
    CONTENT = "content"
    STT = "stt"
    VIBE = "vibe"
    PEDAGOGY = "pedagogy"
    FEEDBACK = "feedback"
    SYNTHESIZE = "synthesize"


@dataclass
class AgentState:
    """개별 에이전트 상태"""
    name: str
    role: str
    icon: str
    status: AgentStatus = AgentStatus.IDLE
    progress: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    @property
    def elapsed_seconds(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "role": self.role,
            "icon": self.icon,
            "status": self.status.value,
            "progress": self.progress,
            "elapsed_seconds": self.elapsed_seconds,
            "error": self.error,
            "has_result": self.result is not None,
            "dependencies": self.dependencies,
        }


# v7.0: Pydantic-based SharedContext (with dataclass fallback)
try:
    from pydantic import BaseModel, Field as PydField
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

if HAS_PYDANTIC:
    class SharedContext(BaseModel):
        """v7.0: Pydantic-validated agent shared context"""
        model_config = {"arbitrary_types_allowed": True}

        video_path: str = ""
        temp_dir: str = ""
        extracted_frames: List[str] = PydField(default_factory=list)
        audio_path: str = ""
        vision_summary: Dict = PydField(default_factory=dict)
        vision_timeline: List[Dict] = PydField(default_factory=list)
        content_summary: Dict = PydField(default_factory=dict)
        content_timeline: List[Dict] = PydField(default_factory=list)
        stt_result: Dict = PydField(default_factory=dict)
        vibe_summary: Dict = PydField(default_factory=dict)
        vibe_timeline: List[Dict] = PydField(default_factory=list)
        audio_metrics: Dict = PydField(default_factory=dict)
        discourse_result: Dict = PydField(default_factory=dict)
        pedagogy_result: Dict = PydField(default_factory=dict)
        feedback_result: Dict = PydField(default_factory=dict)
        master_report: Dict = PydField(default_factory=dict)
        duration: float = 0.0
        metadata: Dict = PydField(default_factory=dict)
else:
    @dataclass
    class SharedContext:
        """Agent shared context (dataclass fallback)"""
        video_path: str = ""
        temp_dir: str = ""
        extracted_frames: List[str] = field(default_factory=list)
        audio_path: str = ""
        vision_summary: Dict = field(default_factory=dict)
        vision_timeline: List[Dict] = field(default_factory=list)
        content_summary: Dict = field(default_factory=dict)
        content_timeline: List[Dict] = field(default_factory=list)
        stt_result: Dict = field(default_factory=dict)
        vibe_summary: Dict = field(default_factory=dict)
        vibe_timeline: List[Dict] = field(default_factory=list)
        audio_metrics: Dict = field(default_factory=dict)
        discourse_result: Dict = field(default_factory=dict)
        pedagogy_result: Dict = field(default_factory=dict)
        feedback_result: Dict = field(default_factory=dict)
        master_report: Dict = field(default_factory=dict)
        duration: float = 0.0
        metadata: Dict = field(default_factory=dict)


class AgentOrchestrator:
    """
    Multi-Agent Pipeline Orchestrator (v7.0)

    Manages 6 specialist agents + Master Agent with
    Pydantic-validated context sharing, confidence metadata,
    and thread-safe state monitoring.

    Pipeline:
        EXTRACT -> [VISION | CONTENT | STT | VIBE] (parallel) -> PEDAGOGY -> FEEDBACK -> SYNTHESIZE
    """

    def __init__(self):
        self.agents: Dict[str, AgentState] = {}
        self.context = SharedContext()
        self.pipeline_id: Optional[str] = None
        self.pipeline_start: Optional[float] = None
        self.pipeline_end: Optional[float] = None
        self.event_log: List[Dict] = []
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()  # v5.0: 스레드 안전

        self._register_agents()

    def _register_agents(self):
        """에이전트 레지스트리 초기화"""
        agent_defs = [
            ("extractor", "리소스 추출기", "📦", []),
            ("vision", "비전 분석 에이전트", "👁️", ["extractor"]),
            ("content", "콘텐츠 분석 에이전트", "🎨", ["extractor"]),
            ("stt", "음성→텍스트 에이전트", "🗣️", ["extractor"]),
            ("vibe", "음성 프로소디 에이전트", "🔊", ["extractor"]),
            ("pedagogy", "교육학 평가 에이전트", "📚", ["vision", "content", "stt", "vibe"]),
            ("feedback", "피드백 생성 에이전트", "💡", ["pedagogy"]),
            ("master", "종합 분석 마스터", "🧠", ["vision", "content", "vibe", "pedagogy", "feedback"]),
        ]

        for name, role, icon, deps in agent_defs:
            self.agents[name] = AgentState(
                name=name, role=role, icon=icon, dependencies=deps
            )

    def on_event(self, callback: Callable):
        """이벤트 콜백 등록"""
        self._callbacks.append(callback)

    def _emit(self, event_type: str, agent_name: str, data: Dict = None):
        """이벤트 발행 (스레드 안전)"""
        event = {
            "type": event_type,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }
        with self._lock:
            self.event_log.append(event)
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass

    def _run_agent(self, name: str, fn: Callable, *args, **kwargs) -> Any:
        """단일 에이전트 실행 및 상태 관리"""
        agent = self.agents[name]
        agent.status = AgentStatus.RUNNING
        agent.start_time = time.time()
        agent.progress = 0
        self._emit("agent_start", name)

        try:
            result = fn(*args, **kwargs)
            agent.status = AgentStatus.DONE
            agent.progress = 100
            agent.result = result if isinstance(result, dict) else {"data": result}
            agent.end_time = time.time()
            self._emit("agent_done", name, {"elapsed": agent.elapsed_seconds})
            return result
        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error = str(e)
            agent.end_time = time.time()
            self._emit("agent_error", name, {"error": str(e), "traceback": traceback.format_exc()})
            return None

    def run_pipeline(self, video_path: str, temp_dir: str = None) -> Dict:
        """
        전체 멀티 에이전트 파이프라인 실행

        Args:
            video_path: 분석할 비디오 파일 경로
            temp_dir: 임시 캐시 디렉토리

        Returns:
            종합 분석 리포트 딕셔너리
        """
        import uuid
        self.pipeline_id = str(uuid.uuid4())[:8]
        self.pipeline_start = time.time()
        self.context = SharedContext(video_path=video_path, temp_dir=temp_dir or "")

        self._emit("pipeline_start", "orchestrator", {"video": video_path})

        # Phase 1: 리소스 추출 (순차)
        self._run_agent("extractor", self._phase_extract, video_path, temp_dir)

        # Phase 2: 진짜 병렬 실행 (v5.0) — Vision + Content + STT + Vibe
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent") as pool:
            futures = {
                pool.submit(self._run_agent, "vision", self._phase_vision): "vision",
                pool.submit(self._run_agent, "content", self._phase_content): "content",
                pool.submit(self._run_agent, "stt", self._phase_stt): "stt",
                pool.submit(self._run_agent, "vibe", self._phase_vibe): "vibe",
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self._emit("agent_error", name, {"error": str(e)})

        # Phase 3: 교육학 평가
        self._run_agent("pedagogy", self._phase_pedagogy)

        # Phase 4: 피드백 생성
        self._run_agent("feedback", self._phase_feedback)

        # Phase 5: 종합 분석
        result = self._run_agent("master", self._phase_synthesize)

        self.pipeline_end = time.time()
        total_elapsed = round(self.pipeline_end - self.pipeline_start, 2)
        self._emit("pipeline_done", "orchestrator", {"total_elapsed": total_elapsed})

        # v7.0: Extract confidence & profile from pedagogy result
        pedagogy = self.context.pedagogy_result or {}
        confidence = pedagogy.get("confidence", {})
        profile = pedagogy.get("profile_summary", {})

        # v7.0: Auto-save to DB if available
        self._try_save_to_db(video_path, result, total_elapsed)

        return {
            "pipeline_id": self.pipeline_id,
            "version": "7.0",
            "total_elapsed": total_elapsed,
            "agents": {name: s.to_dict() for name, s in self.agents.items()},
            "report": result or {},
            "confidence": confidence,
            "profile_summary": profile,
            "event_count": len(self.event_log),
        }

    # =================================================================
    # 파이프라인 단계별 실행 함수
    # =================================================================

    def _phase_extract(self, video_path: str, temp_dir: str = None) -> Dict:
        """Phase 1: FFmpeg 기반 리소스 추출"""
        tl_mod = _load_module("timelapse_analyzer", _CORE_DIR / "analyzers" / "timelapse_analyzer.py")
        flash_extract_resources = tl_mod.flash_extract_resources
        import tempfile

        if not temp_dir:
            temp_dir = tempfile.mkdtemp(prefix="gaim_agent_")

        self.context.temp_dir = temp_dir
        resources = flash_extract_resources(video_path, temp_dir)

        # 추출된 프레임 목록 (flash_extract_resources는 temp_dir 루트에 저장)
        temp_path = Path(temp_dir)
        frames = sorted(temp_path.glob("*.jpg"))
        if not frames:
            # fallback: frames/ 서브디렉토리 확인
            frames_dir = temp_path / "frames"
            if frames_dir.exists():
                frames = sorted(frames_dir.glob("*.jpg"))
        self.context.extracted_frames = [str(f) for f in frames]

        # 오디오 파일 경로
        audio_file = Path(temp_dir) / "audio.wav"
        if audio_file.exists():
            self.context.audio_path = str(audio_file)

        return {
            "frames_count": len(self.context.extracted_frames),
            "audio_extracted": bool(self.context.audio_path),
            "temp_dir": temp_dir,
        }

    def _phase_vision(self) -> Dict:
        """Phase 2a: 비전 분석"""
        va_mod = _load_module("vision_agent", _AGENTS_DIR / "vision_agent.py")
        VisionAgent = va_mod.VisionAgent
        import cv2

        agent = VisionAgent()
        for frame_path in self.context.extracted_frames:
            frame = cv2.imread(frame_path)
            if frame is not None:
                timestamp = self._path_to_timestamp(frame_path)
                agent.analyze_frame(frame, timestamp)

        self.context.vision_summary = agent.get_summary()
        self.context.vision_timeline = agent.get_timeline()
        return self.context.vision_summary

    def _phase_content(self) -> Dict:
        """Phase 2b: 콘텐츠 분석"""
        ca_mod = _load_module("content_agent", _AGENTS_DIR / "content_agent.py")
        ContentAgent = ca_mod.ContentAgent
        import cv2

        agent = ContentAgent()
        for frame_path in self.context.extracted_frames:
            frame = cv2.imread(frame_path)
            if frame is not None:
                timestamp = self._path_to_timestamp(frame_path)
                agent.analyze_frame(frame, timestamp)

        self.context.content_summary = agent.get_summary()
        self.context.content_timeline = agent.get_timeline()
        return self.context.content_summary

    def _phase_stt(self) -> Dict:
        """Phase 2c: 음성→텍스트 변환"""
        stt_mod = _load_module("stt_agent", _AGENTS_DIR / "stt_agent.py")
        STTAgent = stt_mod.STTAgent

        agent = STTAgent()
        if self.context.audio_path:
            result = agent.analyze(self.context.audio_path)
        else:
            result = agent.analyze_from_video(self.context.video_path)
        self.context.stt_result = result
        return result

    def _phase_vibe(self) -> Dict:
        """Phase 2d: 음성 프로소디 분석"""
        vb_mod = _load_module("vibe_agent", _AGENTS_DIR / "vibe_agent.py")
        VibeAgent = vb_mod.VibeAgent

        agent = VibeAgent()
        if self.context.audio_path:
            agent.analyze_full(Path(self.context.audio_path))
            self.context.vibe_summary = agent.get_summary()
            self.context.vibe_timeline = agent.get_timeline()
        return self.context.vibe_summary

    def _phase_pedagogy(self) -> Dict:
        """Phase 3: 교육학 이론 기반 평가"""
        # v5.0: 발화 분석 먼저 실행
        self._run_discourse_analysis()

        pg_mod = _load_module("pedagogy_agent", _AGENTS_DIR / "pedagogy_agent.py")
        PedagogyAgent = pg_mod.PedagogyAgent

        agent = PedagogyAgent()
        result = agent.evaluate(
            vision_summary=self.context.vision_summary,
            content_summary=self.context.content_summary,
            vibe_summary=self.context.vibe_summary,
            stt_result=self.context.stt_result,
            discourse_result=self.context.discourse_result,  # v5.0
        )
        self.context.pedagogy_result = result
        return result

    def _run_discourse_analysis(self):
        """v5.0: 발화 내용 교육학적 분석 (교육학 평가 전 실행)"""
        try:
            da_mod = _load_module("discourse_analyzer", _AGENTS_DIR / "discourse_analyzer.py")
            DiscourseAnalyzer = da_mod.DiscourseAnalyzer

            analyzer = DiscourseAnalyzer()
            stt = self.context.stt_result or {}
            transcript = stt.get("transcript", "")
            segments = stt.get("segments", [])
            speaker_segments = stt.get("speaker_segments", [])

            if transcript and len(transcript) > 20:
                self.context.discourse_result = analyzer.analyze(
                    transcript, segments, speaker_segments
                )
                self._emit("agent_done", "discourse", {"method": self.context.discourse_result.get("analysis_method", "none")})
        except Exception as e:
            self._emit("agent_error", "discourse", {"error": str(e)})
            self.context.discourse_result = {}

    def _phase_feedback(self) -> Dict:
        """Phase 4: 맞춤형 피드백 생성"""
        fb_mod = _load_module("feedback_agent", _AGENTS_DIR / "feedback_agent.py")
        FeedbackAgent = fb_mod.FeedbackAgent

        agent = FeedbackAgent()
        result = agent.generate(
            pedagogy_result=self.context.pedagogy_result,
            vision_summary=self.context.vision_summary,
            content_summary=self.context.content_summary,
            vibe_summary=self.context.vibe_summary,
            stt_result=self.context.stt_result,
            discourse_result=self.context.discourse_result,  # v5.0
        )
        self.context.feedback_result = result
        return result

    def _phase_synthesize(self) -> Dict:
        """Phase 5: MasterAgent를 통한 종합 분석"""
        ma_mod = _load_module("master_agent", _AGENTS_DIR / "master_agent.py")
        MasterAgent = ma_mod.MasterAgent

        master = MasterAgent()
        report = master.synthesize(
            vision_summary=self.context.vision_summary,
            content_summary=self.context.content_summary,
            vibe_summary=self.context.vibe_summary,
            vision_timeline=self.context.vision_timeline,
            content_timeline=self.context.content_timeline,
            vibe_timeline=self.context.vibe_timeline,
            duration=self.context.duration or 900.0,
        )

        # 교육학 및 피드백 결과 통합
        if hasattr(report, '__dict__'):
            report_dict = report.__dict__
        elif isinstance(report, dict):
            report_dict = report
        else:
            report_dict = {"report": str(report)}

        report_dict["pedagogy"] = self.context.pedagogy_result
        report_dict["feedback"] = self.context.feedback_result
        report_dict["stt"] = self.context.stt_result
        report_dict["discourse"] = self.context.discourse_result  # v5.0
        report_dict["vision_summary"] = self.context.vision_summary
        report_dict["content_summary"] = self.context.content_summary
        report_dict["vibe_summary"] = self.context.vibe_summary

        self.context.master_report = report_dict
        return report_dict

    # =================================================================
    # 유틸리티
    # =================================================================

    def _path_to_timestamp(self, path: str) -> float:
        """프레임 파일명에서 타임스탬프 추출"""
        import re
        name = Path(path).stem
        match = re.search(r'(\d+)', name)
        return float(match.group(1)) if match else 0.0

    def get_pipeline_status(self) -> Dict:
        """현재 파이프라인 상태 조회"""
        total = len(self.agents)
        done = sum(1 for a in self.agents.values() if a.status == AgentStatus.DONE)
        errors = sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR)
        running = sum(1 for a in self.agents.values() if a.status == AgentStatus.RUNNING)

        if self.pipeline_end:
            status = "completed"
        elif errors > 0 and running == 0:
            status = "failed"
        elif running > 0:
            status = "running"
        else:
            status = "idle"

        return {
            "pipeline_id": self.pipeline_id,
            "status": status,
            "progress": int((done / total) * 100) if total > 0 else 0,
            "agents": {name: s.to_dict() for name, s in self.agents.items()},
            "summary": {
                "total": total,
                "done": done,
                "running": running,
                "errors": errors,
            },
            "elapsed": round(
                (self.pipeline_end or time.time()) - (self.pipeline_start or time.time()), 2
            ),
        }

    def get_event_log(self) -> List[Dict]:
        """이벤트 로그 반환"""
        return self.event_log

    def reset(self):
        """Reset orchestrator state"""
        for agent in self.agents.values():
            agent.status = AgentStatus.IDLE
            agent.progress = 0
            agent.start_time = None
            agent.end_time = None
            agent.result = None
            agent.error = None
        self.context = SharedContext()
        self.event_log = []
        self.pipeline_id = None
        self.pipeline_start = None
        self.pipeline_end = None

    def _try_save_to_db(self, video_path: str, result: Dict, elapsed: float):
        """v7.0: Auto-save analysis result to SQLite DB"""
        try:
            # Use absolute path to avoid sys.path issues in batch context
            db_mod = _load_module("database", _CORE_DIR / "database.py")
            repo = db_mod.AnalysisRepository()
            repo.save_result(
                video_path=video_path,
                pipeline_id=self.pipeline_id,
                result=result or {},
                pedagogy=self.context.pedagogy_result,
                elapsed_seconds=elapsed,
            )
        except Exception:
            pass  # DB save is optional, don't break pipeline
