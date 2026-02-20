"""
🤖 에이전트 모니터링 API 엔드포인트
멀티 에이전트 파이프라인 상태 조회, 분석 실행, 이벤트 히스토리
"""

import sys
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

router = APIRouter()

# 파이프라인 저장소 (인메모리)
pipeline_store: Dict[str, Dict] = {}

# 비디오 디렉토리
VIDEO_DIR = Path(PROJECT_ROOT) / "video"


class AgentAnalysisRequest(BaseModel):
    """에이전트 분석 요청"""
    video_path: Optional[str] = None
    video_name: Optional[str] = None


class AgentPipelineStatus(BaseModel):
    """파이프라인 상태 응답"""
    pipeline_id: str
    status: str
    progress: int
    agents: Dict
    elapsed: float


# =============================================================================
# 에이전트 상태 API
# =============================================================================

@router.get("/status")
async def get_agent_registry():
    """전체 에이전트 레지스트리 및 상태 조회"""
    from core.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()
    agents_info = {}
    for name, state in orch.agents.items():
        agents_info[name] = {
            "name": state.name,
            "role": state.role,
            "icon": state.icon,
            "dependencies": state.dependencies,
            "status": "idle",
        }

    return {
        "total_agents": len(agents_info),
        "agents": agents_info,
        "pipeline_phases": [
            {"phase": "extract", "agents": ["extractor"], "parallel": False},
            {"phase": "analyze", "agents": ["vision", "content", "stt", "vibe"], "parallel": True},
            {"phase": "evaluate", "agents": ["pedagogy"], "parallel": False},
            {"phase": "feedback", "agents": ["feedback"], "parallel": False},
            {"phase": "synthesize", "agents": ["master"], "parallel": False},
        ],
    }


@router.post("/analyze")
async def start_agent_analysis(
    background_tasks: BackgroundTasks,
    request: AgentAnalysisRequest = None,
):
    """
    멀티 에이전트 분석 시작

    - video_path: 직접 경로 지정
    - video_name: video/ 디렉토리 내 파일명
    """
    req = request or AgentAnalysisRequest()

    # 비디오 경로 결정
    if req.video_path and Path(req.video_path).exists():
        video_path = req.video_path
    elif req.video_name:
        video_path = str(VIDEO_DIR / req.video_name)
        if not Path(video_path).exists():
            raise HTTPException(404, f"비디오 파일을 찾을 수 없습니다: {req.video_name}")
    else:
        # 데모 모드: 첫 번째 비디오 사용
        videos = sorted(VIDEO_DIR.glob("*.mp4")) if VIDEO_DIR.exists() else []
        if not videos:
            raise HTTPException(404, "분석할 비디오 파일이 없습니다.")
        video_path = str(videos[0])

    # 파이프라인 ID 생성
    import uuid
    pipeline_id = str(uuid.uuid4())[:8]

    pipeline_store[pipeline_id] = {
        "id": pipeline_id,
        "status": "queued",
        "progress": 0,
        "video_path": video_path,
        "created_at": datetime.now().isoformat(),
        "agents": {},
        "result": None,
    }

    background_tasks.add_task(run_agent_pipeline, pipeline_id, video_path)

    return {
        "pipeline_id": pipeline_id,
        "status": "queued",
        "video": Path(video_path).name,
        "message": "멀티 에이전트 분석이 시작되었습니다.",
    }


def run_agent_pipeline(pipeline_id: str, video_path: str):
    """백그라운드 에이전트 파이프라인 실행"""
    from core.agents.orchestrator import AgentOrchestrator
    from backend.app.core.agent_message_bus import get_message_bus

    bus = get_message_bus()
    orch = AgentOrchestrator()

    # 메시지 버스 연결
    def on_event(event):
        bus.publish(
            agent_name=event["agent"],
            event_type=event["type"],
            data=event.get("data", {}),
            pipeline_id=pipeline_id,
        )
        # 파이프라인 상태 업데이트
        if pipeline_id in pipeline_store:
            status = orch.get_pipeline_status()
            pipeline_store[pipeline_id]["status"] = status["status"]
            pipeline_store[pipeline_id]["progress"] = status["progress"]
            pipeline_store[pipeline_id]["agents"] = status["agents"]

    orch.on_event(on_event)

    try:
        pipeline_store[pipeline_id]["status"] = "running"
        result = orch.run_pipeline(video_path)
        pipeline_store[pipeline_id]["status"] = "completed"
        pipeline_store[pipeline_id]["progress"] = 100
        pipeline_store[pipeline_id]["result"] = result
        pipeline_store[pipeline_id]["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        pipeline_store[pipeline_id]["status"] = "failed"
        pipeline_store[pipeline_id]["error"] = str(e)


@router.get("/pipeline/{pipeline_id}")
async def get_pipeline_detail(pipeline_id: str):
    """특정 파이프라인 상세 조회"""
    if pipeline_id not in pipeline_store:
        raise HTTPException(404, f"파이프라인을 찾을 수 없습니다: {pipeline_id}")
    return pipeline_store[pipeline_id]


@router.get("/pipeline/{pipeline_id}/events")
async def get_pipeline_events(pipeline_id: str):
    """파이프라인 이벤트 로그 조회"""
    from backend.app.core.agent_message_bus import get_message_bus
    bus = get_message_bus()
    return {"pipeline_id": pipeline_id, "events": bus.get_pipeline_events(pipeline_id)}


@router.get("/pipelines")
async def list_pipelines(limit: int = 10):
    """파이프라인 목록 조회"""
    pipelines = sorted(
        pipeline_store.values(),
        key=lambda p: p.get("created_at", ""),
        reverse=True,
    )[:limit]
    return {
        "total": len(pipeline_store),
        "pipelines": [
            {
                "id": p["id"],
                "status": p["status"],
                "progress": p["progress"],
                "video": Path(p.get("video_path", "")).name,
                "created_at": p.get("created_at"),
                "completed_at": p.get("completed_at"),
            }
            for p in pipelines
        ],
    }


@router.get("/history")
async def get_event_history(limit: int = 50, agent: str = None):
    """에이전트 이벤트 히스토리 조회"""
    from backend.app.core.agent_message_bus import get_message_bus
    bus = get_message_bus()
    return {"events": bus.get_history(limit=limit, agent_name=agent)}
