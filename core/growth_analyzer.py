"""
GAIM Lab v7.0 — Growth Path Analyzer

시계열 분석을 통한 교사 성장 경로 리포트 생성.
DB에 저장된 과거 분석 결과를 기반으로 차원별 성장 추세, 강점/약점 프로필,
자동 개선 피드백을 생성합니다.
"""

from typing import Dict, List, Optional


# ============================================================
# 개선 피드백 규칙 (RAG 없이 규칙 기반)
# ============================================================
_IMPROVEMENT_TIPS = {
    "수업 전문성": [
        "핵심 개념 간 연결고리를 명시적으로 설명해 보세요",
        "학생 수준에 맞는 사례와 비유를 추가하세요",
        "최신 교육과정 성취기준과의 연계를 강화하세요",
    ],
    "교수학습 방법": [
        "다양한 교수 전략(토론, 모둠, 실험)을 번갈아 활용하세요",
        "발문 유형을 다양화하세요 (개방형, 비계 설정형)",
        "학생 활동 시간을 늘리고, 교사 중심 설명을 줄이세요",
    ],
    "판서 및 언어": [
        "필러 사용(음, 어)을 줄이는 연습을 하세요",
        "핵심 용어를 반복적으로 강조하여 학습을 지원하세요",
        "학생 발화를 재구성(revoicing)하여 참여를 유도하세요",
    ],
    "수업 태도": [
        "학생과의 시선 접촉 빈도를 높이세요",
        "제스처를 활용하여 설명을 보강하세요",
        "교실 전체를 이동하며 가까이 다가가세요",
    ],
    "학생 참여": [
        "모든 학생이 참여할 수 있는 구조화된 활동을 설계하세요",
        "대기 시간을 충분히 확보하세요 (3초 이상)",
        "소그룹 토론 후 전체 공유 구조를 활용하세요",
    ],
    "시간 배분": [
        "단계별 시간 배분을 사전에 계획하세요",
        "전환(transition) 시간을 최소화하는 루틴을 만드세요",
        "도입-전개-정리 비율을 1:6:3으로 목표해 보세요",
    ],
    "창의성": [
        "다양한 매체(영상, 실물, ICT)를 활용하세요",
        "학생의 창의적 사고를 유발하는 발문을 추가하세요",
        "교과 간 융합 요소를 시도해 보세요",
    ],
}


def _linear_trend(values: List[float]) -> Dict:
    """Simple linear regression: y = slope * x + intercept"""
    n = len(values)
    if n < 2:
        return {"slope": 0.0, "direction": "stable", "r_squared": 0.0}

    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n

    ss_xy = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    ss_xx = sum((i - x_mean) ** 2 for i in range(n))
    ss_yy = sum((v - y_mean) ** 2 for v in values)

    slope = ss_xy / ss_xx if ss_xx else 0.0
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if (ss_xx and ss_yy) else 0.0

    if slope > 0.5:
        direction = "improving"
    elif slope < -0.5:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "slope": round(slope, 3),
        "direction": direction,
        "r_squared": round(r_squared, 3),
    }


class GrowthAnalyzer:
    """
    교사 성장 경로 분석기 (v7.0)

    DB에 저장된 시계열 데이터를 기반으로:
    - 차원별 성장 추세 (선형 회귀)
    - 강점/약점 프로필
    - 자동 개선 피드백
    """

    def analyze_from_db(self, video_name_prefix: str) -> Optional[Dict]:
        """DB에서 성장 데이터를 가져와 분석"""
        try:
            from core.database import AnalysisRepository
            repo = AnalysisRepository()
            data = repo.get_growth_data(video_name_prefix)
            if not data:
                return None
            return self.analyze(data)
        except Exception:
            return None

    def analyze(self, history: List[Dict]) -> Dict:
        """
        시계열 분석 결과 생성

        Args:
            history: 시간순 분석 결과 리스트 (각각 dimensions 포함)

        Returns:
            성장 리포트 딕셔너리
        """
        if not history:
            return {"error": "No historical data available"}

        n_sessions = len(history)
        total_scores = [h.get("total_score", 0) for h in history]

        # 차원별 시계열 추출
        dim_series = {}
        for h in history:
            for d in h.get("dimensions", []):
                name = d.get("name", "")
                if name not in dim_series:
                    dim_series[name] = []
                dim_series[name].append(d.get("percentage", 0))

        # 차원별 추세 분석
        dim_trends = {}
        for name, values in dim_series.items():
            trend = _linear_trend(values)
            trend["latest"] = values[-1] if values else 0
            trend["first"] = values[0] if values else 0
            trend["change"] = round(trend["latest"] - trend["first"], 1)
            dim_trends[name] = trend

        # 총점 추세
        total_trend = _linear_trend(total_scores)

        # 강점/약점 (최신 세션 기준)
        latest_dims = history[-1].get("dimensions", [])
        strengths = [d["name"] for d in latest_dims if d.get("percentage", 0) >= 80]
        weaknesses = [d["name"] for d in latest_dims if d.get("percentage", 0) < 60]

        # 가장 성장한 / 하락한 차원
        most_improved = max(dim_trends.items(), key=lambda x: x[1]["change"], default=("", {"change": 0}))
        most_declined = min(dim_trends.items(), key=lambda x: x[1]["change"], default=("", {"change": 0}))

        # 자동 개선 피드백
        feedback = []
        for name in weaknesses[:3]:  # 상위 3개 약점
            tips = _IMPROVEMENT_TIPS.get(name, [])
            if tips:
                feedback.append({
                    "dimension": name,
                    "tips": tips[:2],  # 각 차원 2개씩
                })

        # v7.1: 3/6/12주 개선 로드맵 생성
        profile = {
            "strengths": strengths,
            "weaknesses": weaknesses,
        }
        roadmap = self.generate_roadmap(profile, dim_trends, latest_dims)

        return {
            "sessions": n_sessions,
            "period": {
                "first": history[0].get("analyzed_at", ""),
                "last": history[-1].get("analyzed_at", ""),
            },
            "total_trend": {
                "scores": total_scores,
                **total_trend,
            },
            "dimension_trends": dim_trends,
            "profile": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "most_improved": most_improved[0] if most_improved[1].get("change", 0) > 0 else "",
                "most_declined": most_declined[0] if most_declined[1].get("change", 0) < 0 else "",
            },
            "improvement_feedback": feedback,
            "roadmap": roadmap,
            "version": "7.1",
        }

    def generate_roadmap(self, profile: Dict, dim_trends: Dict,
                         latest_dims: List[Dict]) -> Dict:
        """
        v7.1: 3주/6주/12주 개인별 개선 로드맵 자동 생성

        약점 차원을 우선순위로, 각 기간별 구체적 목표와 실천 과제를 생성합니다.
        """
        weaknesses = profile.get("weaknesses", [])
        if not weaknesses:
            weaknesses = [d["name"] for d in sorted(
                latest_dims, key=lambda x: x.get("percentage", 0)
            )[:3]]

        # 현재 점수 매핑
        current_scores = {d.get("name", ""): d.get("percentage", 0)
                          for d in latest_dims}

        # 주차별 템플릿 — 단계적 난이도
        _PHASE_TEMPLATES = {
            "3주": {"label": "기초 역량 강화", "target_boost": 5, "focus": "인식 및 습관화"},
            "6주": {"label": "심화 적용", "target_boost": 12, "focus": "전략적 실천"},
            "12주": {"label": "전문성 내면화", "target_boost": 20, "focus": "자기 모니터링 & 코칭"},
        }

        # 주차별 활동 유형
        _WEEKLY_ACTIVITIES = [
            "자기 수업 영상 분석 (10분)",
            "동료 수업 참관 및 피드백 작성",
            "교수법 논문/자료 1편 읽기",
            "마이크로티칭 실습 (5분 모의수업)",
            "수업 일지 작성 및 성찰",
            "학생 반응 분석 체크리스트 작성",
            "수업 설계안 작성 및 동료 검토",
            "교수학습 전략 워크숍 참석",
            "자기 점검표(rubric) 기반 자가평가",
            "멘토 교사 피드백 세션",
            "수업 동영상 비교 분석 (이전 vs 현재)",
            "최종 수업 시연 및 종합 평가",
        ]

        roadmap = {}
        for period, meta in _PHASE_TEMPLATES.items():
            weeks_count = int(period.replace("주", ""))
            plan_weeks = []

            for week_idx in range(weeks_count):
                # 이번 주에 집중할 차원 (순환)
                focus_dim = weaknesses[week_idx % len(weaknesses)]
                tips = _IMPROVEMENT_TIPS.get(focus_dim, ["일반 교수법 개선 연습"])
                current = current_scores.get(focus_dim, 50)

                # 주차별 목표 점수 (점진적 상승)
                progress_ratio = (week_idx + 1) / weeks_count
                target = min(100, round(current + meta["target_boost"] * progress_ratio, 1))

                plan_weeks.append({
                    "week": week_idx + 1,
                    "focus_dimension": focus_dim,
                    "goal": tips[week_idx % len(tips)],
                    "activity": _WEEKLY_ACTIVITIES[week_idx % len(_WEEKLY_ACTIVITIES)],
                    "target_score": target,
                    "current_score": current,
                })

            roadmap[period] = {
                "label": meta["label"],
                "focus": meta["focus"],
                "target_dimensions": weaknesses[:3],
                "weeks": plan_weeks,
                "expected_improvement": meta["target_boost"],
            }

        return roadmap
