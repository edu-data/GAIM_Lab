"""
GAIM Lab v7.1 — A/B 루브릭 실험 API

2개 루브릭을 동시 적용하여 채점 기준 비교 연구 지원.
- 동일 영상에 루브릭 A/B를 각각 적용
- 7차원 점수 비교 + 차이 분석
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter()


# ── 내장 루브릭 정의 ──────────────────────────────────────
_BUILTIN_RUBRICS = {
    "standard_v7": {
        "name": "표준 루브릭 v7 (임용시험 기준)",
        "weights": {
            "수업 전문성": 15, "교수학습 방법": 15, "판서 및 언어": 15,
            "수업 태도": 15, "학생 참여": 15, "시간 배분": 10, "창의성": 15,
        },
        "criteria": "교원임용시험 2차 수업실연 평가 기준 기반",
    },
    "student_centered": {
        "name": "학생중심 루브릭",
        "weights": {
            "수업 전문성": 10, "교수학습 방법": 20, "판서 및 언어": 10,
            "수업 태도": 10, "학생 참여": 25, "시간 배분": 10, "창의성": 15,
        },
        "criteria": "학생 참여 및 상호작용 중심 평가",
    },
    "creativity_focus": {
        "name": "창의성 강조 루브릭",
        "weights": {
            "수업 전문성": 10, "교수학습 방법": 15, "판서 및 언어": 10,
            "수업 태도": 10, "학생 참여": 15, "시간 배분": 10, "창의성": 30,
        },
        "criteria": "창의적 교수법 및 매체 활용 중심 평가",
    },
    "balanced": {
        "name": "균등 배점 루브릭",
        "weights": {
            "수업 전문성": 14.3, "교수학습 방법": 14.3, "판서 및 언어": 14.3,
            "수업 태도": 14.3, "학생 참여": 14.3, "시간 배분": 14.3, "창의성": 14.2,
        },
        "criteria": "7차원 동일 가중치",
    },
}


# ── 모델 ──────────────────────────────────────────────────
class ABExperimentRequest(BaseModel):
    analysis_id: Optional[int] = None
    video_prefix: Optional[str] = None
    rubric_a: str = "standard_v7"
    rubric_b: str = "student_centered"


# ── API ──────────────────────────────────────────────────
@router.get("/rubrics")
async def list_rubrics():
    """사용 가능한 루브릭 목록"""
    return {
        name: {"name": r["name"], "criteria": r["criteria"], "weights": r["weights"]}
        for name, r in _BUILTIN_RUBRICS.items()
    }


@router.post("/ab")
async def run_ab_experiment(req: ABExperimentRequest):
    """A/B 루브릭 실험 실행"""
    rubric_a = _BUILTIN_RUBRICS.get(req.rubric_a)
    rubric_b = _BUILTIN_RUBRICS.get(req.rubric_b)

    if not rubric_a:
        raise HTTPException(status_code=400, detail=f"루브릭 A '{req.rubric_a}' 없음")
    if not rubric_b:
        raise HTTPException(status_code=400, detail=f"루브릭 B '{req.rubric_b}' 없음")

    # DB에서 원시 점수 가져오기 또는 데모 사용
    raw_scores = _get_raw_scores(req.analysis_id, req.video_prefix)

    # 각 루브릭으로 가중 점수 계산
    result_a = _apply_rubric(raw_scores, rubric_a)
    result_b = _apply_rubric(raw_scores, rubric_b)

    # 차이 분석
    diffs = []
    for dim in raw_scores.keys():
        sa = result_a["dimensions"].get(dim, {}).get("weighted_score", 0)
        sb = result_b["dimensions"].get(dim, {}).get("weighted_score", 0)
        diffs.append({
            "dimension": dim,
            "rubric_a_score": sa,
            "rubric_b_score": sb,
            "diff": round(sb - sa, 2),
            "pct_diff": round((sb - sa) / max(sa, 1) * 100, 1),
        })

    return {
        "rubric_a": {"id": req.rubric_a, "name": rubric_a["name"], **result_a},
        "rubric_b": {"id": req.rubric_b, "name": rubric_b["name"], **result_b},
        "dimension_diffs": diffs,
        "total_diff": round(result_b["total"] - result_a["total"], 2),
        "summary": _generate_summary(result_a, result_b, diffs),
    }


def _get_raw_scores(analysis_id: Optional[int], prefix: Optional[str]) -> Dict[str, float]:
    """DB에서 원시 점수를 가져오거나 데모 데이터 반환"""
    try:
        if analysis_id:
            from core.database import AnalysisRepository
            repo = AnalysisRepository()
            data = repo.get_by_id(analysis_id)
            if data:
                return {d["name"]: d.get("percentage", 70) for d in data.get("dimensions", [])}
    except Exception:
        pass

    # 데모 데이터
    import random
    random.seed(42)
    dims = ["수업 전문성", "교수학습 방법", "판서 및 언어",
            "수업 태도", "학생 참여", "시간 배분", "창의성"]
    return {d: round(random.uniform(55, 90), 1) for d in dims}


def _apply_rubric(raw_scores: Dict[str, float], rubric: Dict) -> Dict:
    """루브릭 가중치를 적용하여 점수 계산"""
    weights = rubric["weights"]
    total_weight = sum(weights.values())
    dimensions = {}
    total = 0

    for dim, raw in raw_scores.items():
        w = weights.get(dim, 0)
        weighted = round(raw * w / 100, 2)
        dimensions[dim] = {
            "raw_score": raw,
            "weight": w,
            "weighted_score": weighted,
        }
        total += weighted

    return {"total": round(total, 2), "dimensions": dimensions}


def _generate_summary(result_a: Dict, result_b: Dict, diffs: List[Dict]) -> str:
    """비교 요약문 생성"""
    diff_total = result_b["total"] - result_a["total"]
    most_diff = max(diffs, key=lambda x: abs(x["diff"]))

    if abs(diff_total) < 1:
        overall = "두 루브릭의 총점 차이는 미미합니다."
    elif diff_total > 0:
        overall = f"루브릭 B가 {abs(diff_total):.1f}점 높습니다."
    else:
        overall = f"루브릭 A가 {abs(diff_total):.1f}점 높습니다."

    return (
        f"{overall} "
        f"가장 큰 차이를 보이는 차원은 '{most_diff['dimension']}' "
        f"(차이: {most_diff['diff']:+.2f}점)입니다."
    )
