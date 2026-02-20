"""
GAIM Lab - 분석 API 엔드포인트
영상 업로드, 분석 실행, 결과 조회
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import uuid
import shutil
import json

from app.core.analyzer import GAIMAnalysisPipeline
from app.core.evaluator import GAIMLectureEvaluator

router = APIRouter()

# 인메모리 분석 상태 저장소 (프로덕션에서는 Redis/DB 사용)
analysis_store: Dict[str, Dict] = {}

# 디렉토리 설정
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = _PROJECT_ROOT / "uploads"
OUTPUT_DIR = _PROJECT_ROOT / "output"


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    use_turbo: bool = True
    use_text: bool = True


class AnalysisStatus(BaseModel):
    """분석 상태 응답 모델"""
    id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    created_at: str
    completed_at: Optional[str] = None
    result_url: Optional[str] = None


class EvaluationResponse(BaseModel):
    """평가 결과 응답 모델"""
    id: str
    video_name: str
    total_score: float
    grade: str
    dimensions: List[Dict]
    strengths: List[str]
    improvements: List[str]
    overall_feedback: str


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    use_turbo: bool = True,
    use_text: bool = True
):
    """
    영상 업로드 및 분석 실행 (동기 — 결과를 즉시 반환)
    
    - **file**: 분석할 영상 파일 (MP4, AVI, MOV)
    - **use_turbo**: Turbo 모드 사용 여부 (기본: True)
    - **use_text**: 텍스트 분석 사용 여부 (기본: True)
    """
    # 파일 확장자 검증
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 파일 형식입니다. 허용: {allowed_extensions}"
        )
    
    # 분석 ID 생성
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 파일 저장
    save_path = UPLOAD_DIR / f"{analysis_id}_{timestamp}{file_ext}"
    
    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")
    
    # 분석 상태 초기화
    analysis_store[analysis_id] = {
        "id": analysis_id,
        "status": "processing",
        "progress": 10,
        "message": "분석 시작",
        "video_path": str(save_path),
        "video_name": file.filename,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "use_turbo": use_turbo,
        "use_text": use_text,
        "result": None
    }
    
    try:
        # 동기 실행 — 분석 완료까지 대기
        pipeline = GAIMAnalysisPipeline(
            use_turbo=use_turbo,
            use_text=use_text
        )
        
        analysis_store[analysis_id]["progress"] = 30
        analysis_store[analysis_id]["message"] = "AI 분석 진행 중..."
        
        video_path = Path(save_path)
        output_dir = OUTPUT_DIR / analysis_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        raw_result = await pipeline.analyze_video(video_path, output_dir)
        
        # gaim_evaluation 안의 데이터를 플랫하게 추출
        evaluation = raw_result.get("gaim_evaluation", raw_result)
        
        # 결과 JSON 저장
        result_path = output_dir / "result.json"
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(raw_result, f, ensure_ascii=False, indent=2)
        
        # 상태 업데이트
        analysis_store[analysis_id].update({
            "status": "completed",
            "progress": 100,
            "message": "분석 완료",
            "completed_at": datetime.now().isoformat(),
            "result": raw_result,
            "result_url": f"/output/{analysis_id}/result.json"
        })
        
        # 프론트엔드 기대 형식으로 반환 (플랫 구조)
        return {
            "id": analysis_id,
            "status": "completed",
            "progress": 100,
            "message": "분석 완료",
            "created_at": analysis_store[analysis_id]["created_at"],
            **evaluation
        }
        
    except Exception as e:
        analysis_store[analysis_id].update({
            "status": "failed",
            "message": f"분석 실패: {str(e)}",
            "progress": 0
        })
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)[:300]}")


def _flatten_evaluation(raw_result: dict) -> dict:
    """gaim_evaluation 구조를 플랫 구조로 변환 (프론트엔드 호환)"""
    evaluation = raw_result.get("gaim_evaluation", raw_result)
    return evaluation


@router.get("/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """분석 상태 조회"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")
    
    store = analysis_store[analysis_id]
    
    return AnalysisStatus(
        id=store["id"],
        status=store["status"],
        progress=store["progress"],
        message=store["message"],
        created_at=store["created_at"],
        completed_at=store.get("completed_at"),
        result_url=store.get("result_url")
    )


@router.get("/{analysis_id}/result")
async def get_analysis_result(analysis_id: str):
    """분석 결과 조회 (플랫 구조 반환)"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")
    
    store = analysis_store[analysis_id]
    
    if store["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다")
    
    raw_result = store["result"]
    evaluation = _flatten_evaluation(raw_result)
    
    return {
        "id": analysis_id,
        "video_name": store["video_name"],
        **evaluation
    }


@router.get("/{analysis_id}/report")
async def download_report(analysis_id: str, format: str = "json"):
    """
    분석 리포트 다운로드
    
    - **format**: 리포트 형식 (json, pdf)
    """
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")
    
    store = analysis_store[analysis_id]
    
    if store["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다")
    
    output_dir = OUTPUT_DIR / analysis_id
    
    if format == "json":
        result_path = output_dir / "result.json"
        if result_path.exists():
            return FileResponse(
                path=str(result_path),
                filename=f"gaim_result_{analysis_id}.json",
                media_type="application/json"
            )
    elif format == "pdf":
        # PDF 리포트 생성 로직 (추후 구현)
        raise HTTPException(status_code=501, detail="PDF 리포트는 준비 중입니다")
    
    raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")


@router.get("/")
async def list_analyses(limit: int = 10, offset: int = 0):
    """최근 분석 목록 조회"""
    analyses = list(analysis_store.values())
    analyses.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(analyses),
        "limit": limit,
        "offset": offset,
        "items": analyses[offset:offset + limit]
    }


@router.post("/demo")
async def run_demo_analysis():
    """
    데모 분석 실행 (더미 데이터)
    MLC 없이도 7차원 평가 결과를 확인 가능
    """
    from app.core.analyzer import GAIMAnalysisPipeline
    
    analysis_id = f"demo_{uuid.uuid4().hex[:8]}"
    
    pipeline = GAIMAnalysisPipeline()
    dummy_data = pipeline._get_dummy_analysis()
    evaluation = pipeline.evaluator.evaluate(dummy_data)
    eval_dict = pipeline.evaluator.to_dict(evaluation)
    
    # 프론트엔드와 호환되는 플랫 구조로 반환
    # 내부 저장도 동시에 수행
    analysis_store[analysis_id] = {
        "id": analysis_id,
        "status": "completed",
        "progress": 100,
        "message": "데모 분석 완료",
        "video_name": "demo_lecture.mp4",
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "result": {"gaim_evaluation": eval_dict},
        "use_turbo": True,
        "use_text": True,
        "video_path": ""
    }
    
    return {
        "id": analysis_id,
        "status": "completed",
        "progress": 100,
        "message": "데모 분석 완료",
        "video_name": "demo_lecture.mp4",
        "created_at": analysis_store[analysis_id]["created_at"],
        **eval_dict
    }


# =============================================================================
# 일괄 분석 API (Batch Analysis)
# =============================================================================

# 배치 작업 저장소
batch_store: Dict[str, Dict] = {}

VIDEO_DIR = _PROJECT_ROOT / "video"


class BatchRequest(BaseModel):
    """배치 분석 요청 모델"""
    limit: Optional[int] = None
    video_names: Optional[List[str]] = None


class BatchStatus(BaseModel):
    """배치 분석 상태 모델"""
    id: str
    status: str  # pending, processing, completed, failed
    total_videos: int
    completed_videos: int
    current_video: Optional[str] = None
    progress: int
    created_at: str
    completed_at: Optional[str] = None


@router.get("/batch/videos")
async def list_batch_videos():
    """분석 가능한 영상 목록 조회"""
    videos = sorted(VIDEO_DIR.glob("*.mp4"))
    
    return {
        "total": len(videos),
        "videos": [
            {
                "name": v.name,
                "size_mb": round(v.stat().st_size / (1024 * 1024), 1),
                "path": str(v)
            }
            for v in videos
        ]
    }


@router.post("/batch/start", response_model=BatchStatus)
async def start_batch_analysis(
    background_tasks: BackgroundTasks,
    request: BatchRequest = None
):
    """
    일괄 분석 시작
    
    - **limit**: 분석할 영상 수 제한 (기본: 전체)
    - **video_names**: 특정 영상만 분석 (선택)
    """
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    # 영상 목록 결정
    if request and request.video_names:
        videos = [VIDEO_DIR / name for name in request.video_names if (VIDEO_DIR / name).exists()]
    else:
        videos = sorted(VIDEO_DIR.glob("*.mp4"))
        if request and request.limit:
            videos = videos[:request.limit]
    
    if not videos:
        raise HTTPException(status_code=400, detail="분석할 영상이 없습니다")
    
    # 배치 상태 초기화
    batch_store[batch_id] = {
        "id": batch_id,
        "status": "pending",
        "total_videos": len(videos),
        "completed_videos": 0,
        "current_video": None,
        "progress": 0,
        "videos": [str(v) for v in videos],
        "results": [],
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    # 백그라운드 배치 실행
    background_tasks.add_task(run_batch_analysis, batch_id)
    
    return BatchStatus(
        id=batch_id,
        status="pending",
        total_videos=len(videos),
        completed_videos=0,
        current_video=None,
        progress=0,
        created_at=batch_store[batch_id]["created_at"]
    )


async def run_batch_analysis(batch_id: str):
    """배치 분석 백그라운드 실행"""
    import subprocess
    
    if batch_id not in batch_store:
        return
    
    store = batch_store[batch_id]
    store["status"] = "processing"
    
    videos = [Path(v) for v in store["videos"]]
    total = len(videos)
    
    for idx, video in enumerate(videos):
        store["current_video"] = video.name
        store["progress"] = int((idx / total) * 100)
        
        try:
            # run_sample_analysis 실행
            result = subprocess.run(
                ["python", "run_sample_analysis.py", str(video)],
                capture_output=True,
                text=True,
                cwd=str(_PROJECT_ROOT),
                timeout=1800  # 30분 타임아웃
            )
            
            if result.returncode == 0:
                store["results"].append({
                    "video_name": video.name,
                    "status": "success"
                })
            else:
                store["results"].append({
                    "video_name": video.name,
                    "status": "failed",
                    "error": result.stderr[:500] if result.stderr else "Unknown error"
                })
                
        except subprocess.TimeoutExpired:
            store["results"].append({
                "video_name": video.name,
                "status": "timeout"
            })
        except Exception as e:
            store["results"].append({
                "video_name": video.name,
                "status": "failed",
                "error": str(e)
            })
        
        store["completed_videos"] = idx + 1
    
    store["status"] = "completed"
    store["progress"] = 100
    store["current_video"] = None
    store["completed_at"] = datetime.now().isoformat()


@router.get("/batch/{batch_id}", response_model=BatchStatus)
async def get_batch_status(batch_id: str):
    """배치 분석 상태 조회"""
    if batch_id not in batch_store:
        raise HTTPException(status_code=404, detail="배치 작업을 찾을 수 없습니다")
    
    store = batch_store[batch_id]
    
    return BatchStatus(
        id=store["id"],
        status=store["status"],
        total_videos=store["total_videos"],
        completed_videos=store["completed_videos"],
        current_video=store.get("current_video"),
        progress=store["progress"],
        created_at=store["created_at"],
        completed_at=store.get("completed_at")
    )


@router.get("/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    """배치 분석 결과 조회"""
    if batch_id not in batch_store:
        raise HTTPException(status_code=404, detail="배치 작업을 찾을 수 없습니다")
    
    store = batch_store[batch_id]
    
    return {
        "id": batch_id,
        "status": store["status"],
        "total_videos": store["total_videos"],
        "success_count": sum(1 for r in store["results"] if r.get("status") == "success"),
        "failed_count": sum(1 for r in store["results"] if r.get("status") != "success"),
        "results": store["results"]
    }


@router.get("/batch")
async def list_batch_jobs():
    """배치 작업 목록 조회"""
    jobs = list(batch_store.values())
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(jobs),
        "items": [
            {
                "id": j["id"],
                "status": j["status"],
                "total_videos": j["total_videos"],
                "completed_videos": j["completed_videos"],
                "progress": j["progress"],
                "created_at": j["created_at"],
                "completed_at": j.get("completed_at")
            }
            for j in jobs
        ]
    }

