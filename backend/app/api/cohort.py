"""
GAIM Lab v7.1 — Cohort Comparison API (코호트 비교 분석)

학급/대학/연도별 집단 간 비교 통계 및 시각화 데이터 제공.
- 두 그룹의 분석 결과를 DB에서 가져와 비교
- 차원별 평균, 독립표본 t-검정, Cohen's d 효과 크기
"""

import sys
import math
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

router = APIRouter()

DIM_NAMES = ["수업 전문성", "교수학습 방법", "판서 및 언어", "수업 태도",
             "학생 참여", "시간 배분", "창의성"]


# ── 통계 함수 ──────────────────────────────────────────────
def _mean(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0

def _std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))

def _t_test_independent(a: List[float], b: List[float]) -> Dict:
    """독립표본 t-검정 (Welch's t-test 근사)"""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return {"t": 0.0, "p": 1.0, "significant": False}

    ma, mb = _mean(a), _mean(b)
    sa, sb = _std(a), _std(b)
    se = math.sqrt((sa ** 2 / na) + (sb ** 2 / nb)) if (sa + sb) > 0 else 1e-9
    t_stat = (ma - mb) / se

    # Welch-Satterthwaite 자유도 근사
    num = ((sa ** 2 / na) + (sb ** 2 / nb)) ** 2
    denom = ((sa ** 2 / na) ** 2 / (na - 1)) + ((sb ** 2 / nb) ** 2 / (nb - 1))
    df = num / denom if denom > 0 else 1

    # p-value 근사 (정규분포 근사, scipy 미사용)
    z = abs(t_stat)
    p_approx = 2 * math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi) if z < 10 else 0.0
    p_approx = min(max(p_approx, 0.0), 1.0)

    return {"t": round(t_stat, 4), "p": round(p_approx, 4), "df": round(df, 1),
            "significant": p_approx < 0.05}

def _cohens_d(a: List[float], b: List[float]) -> float:
    """Cohen's d 효과 크기"""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    sa, sb = _std(a), _std(b)
    pooled = math.sqrt(((na - 1) * sa ** 2 + (nb - 1) * sb ** 2) / (na + nb - 2))
    return round((ma - mb) / pooled, 4) if pooled > 0 else 0.0


# ── 요청/응답 모델 ────────────────────────────────────────
class GroupDef(BaseModel):
    prefix: str
    label: str = ""

class CohortCompareRequest(BaseModel):
    group_a: GroupDef
    group_b: GroupDef


# ── API ────────────────────────────────────────────────────
@router.post("/compare")
async def compare_cohorts(req: CohortCompareRequest):
    """두 코호트 그룹의 분석 결과를 비교합니다."""
    try:
        from core.database import AnalysisRepository
        repo = AnalysisRepository()
        data_a = repo.get_growth_data(req.group_a.prefix) or []
        data_b = repo.get_growth_data(req.group_b.prefix) or []
    except Exception:
        data_a, data_b = [], []

    # DB 데이터가 없으면 데모 데이터로 폴백
    if not data_a:
        data_a = _demo_group(req.group_a.prefix)
    if not data_b:
        data_b = _demo_group(req.group_b.prefix)

    # 차원별 점수 추출
    def _extract_dim_scores(data: List[Dict]) -> Dict[str, List[float]]:
        result = {d: [] for d in DIM_NAMES}
        result["total"] = []
        for entry in data:
            result["total"].append(entry.get("total_score", 0))
            for dim in entry.get("dimensions", []):
                name = dim.get("name", "")
                if name in result:
                    result[name].append(dim.get("percentage", 0))
        return result

    scores_a = _extract_dim_scores(data_a)
    scores_b = _extract_dim_scores(data_b)

    # 비교 결과
    comparisons = []
    for dim in ["total"] + DIM_NAMES:
        a_vals = scores_a.get(dim, [])
        b_vals = scores_b.get(dim, [])
        t_result = _t_test_independent(a_vals, b_vals)
        d = _cohens_d(a_vals, b_vals)

        effect_label = "large" if abs(d) >= 0.8 else "medium" if abs(d) >= 0.5 else "small"

        comparisons.append({
            "dimension": dim,
            "group_a": {
                "mean": round(_mean(a_vals), 2),
                "std": round(_std(a_vals), 2),
                "n": len(a_vals),
            },
            "group_b": {
                "mean": round(_mean(b_vals), 2),
                "std": round(_std(b_vals), 2),
                "n": len(b_vals),
            },
            "t_test": t_result,
            "cohens_d": d,
            "effect_size": effect_label,
        })

    return {
        "group_a": {
            "prefix": req.group_a.prefix,
            "label": req.group_a.label or req.group_a.prefix,
            "n_analyses": len(data_a),
        },
        "group_b": {
            "prefix": req.group_b.prefix,
            "label": req.group_b.label or req.group_b.prefix,
            "n_analyses": len(data_b),
        },
        "comparisons": comparisons,
    }


def _demo_group(prefix: str) -> List[Dict]:
    """데모용 가상 분석 결과"""
    import random
    random.seed(hash(prefix) % 10000)
    results = []
    for i in range(random.randint(5, 15)):
        dims = []
        for name in DIM_NAMES:
            score = random.gauss(70, 12)
            score = max(0, min(100, score))
            dims.append({"name": name, "percentage": round(score, 1), "score": round(score * 0.15, 1), "max": 15})
        total = round(sum(d["percentage"] for d in dims) / len(dims), 1)
        results.append({"total_score": total, "dimensions": dims})
    return results
