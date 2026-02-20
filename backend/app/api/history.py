"""
GAIM Lab v7.0 — History & Growth API Router

분석 이력 조회 및 성장 경로 분석 엔드포인트
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

# Add project root to path for core module imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter()


@router.get("/history")
async def get_analysis_history(limit: int = Query(50, ge=1, le=200)):
    """분석 이력 조회 (최신 순)"""
    try:
        from core.database import AnalysisRepository
        repo = AnalysisRepository()
        history = repo.get_history(limit=limit)
        return {"history": history, "total": repo.count()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")


@router.get("/history/{analysis_id}")
async def get_analysis_detail(analysis_id: int):
    """분석 상세 조회"""
    try:
        from core.database import AnalysisRepository
        repo = AnalysisRepository()
        result = repo.get_by_id(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")


@router.get("/growth/{video_prefix}")
async def get_growth_analysis(video_prefix: str):
    """교사 성장 경로 분석"""
    try:
        from core.growth_analyzer import GrowthAnalyzer
        analyzer = GrowthAnalyzer()
        result = analyzer.analyze_from_db(video_prefix)
        if not result:
            raise HTTPException(status_code=404, detail="No growth data found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: int):
    """분석 결과 삭제"""
    try:
        from core.database import AnalysisRepository
        repo = AnalysisRepository()
        if repo.delete_by_id(analysis_id):
            return {"deleted": True}
        raise HTTPException(status_code=404, detail="Analysis not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
