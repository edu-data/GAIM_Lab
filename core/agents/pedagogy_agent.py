"""
📚 Pedagogy Agent - 교육학 이론 기반 평가 전문 에이전트
v7.0: 신뢰도 강화 리팩토링

v7.0 개선:
- 입력 구간화(Binning): 연속 메트릭을 이산 구간으로 변환 → 결정론적 채점
- adjust_range 확대: 점수 범위 25pt+ 확보
- confidence 메타데이터: 에이전트 데이터 유효성 기반 신뢰도 추적
- 차원별 독립 프로필: 총점은 보조 지표로 격하
- 가감점 폭 강화: 양호/미흡 간 격차 확대
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# YAML 로드
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# 기본 프레임워크 (YAML 로드 실패 시 폴백)
DEFAULT_DIMENSIONS = {
    "수업 전문성": {"weight": 20, "theory": "구성주의 학습이론 - 학습 목표의 명확한 제시는 학생의 인지적 스캐폴딩을 제공합니다."},
    "교수학습 방법": {"weight": 20, "theory": "다중지능이론(Gardner) - 다양한 교수법은 학생의 다양한 학습 양식에 대응합니다."},
    "판서 및 언어": {"weight": 15, "theory": "Vygotsky의 근접발달영역(ZPD) - 명확한 언어 사용은 효과적인 비계설정의 핵심입니다."},
    "수업 태도": {"weight": 15, "theory": "Bandura의 사회학습이론 - 교사의 열정과 태도는 학생의 학습 동기에 직접적으로 영향을 미칩니다."},
    "학생 참여": {"weight": 15, "theory": "구성주의적 참여이론(Engagement Theory) - 학생의 능동적 참여는 심층 학습의 핵심 요소입니다."},
    "시간 배분": {"weight": 10, "theory": "Keller의 ARCS 모델 - 체계적 시간 배분은 학습자의 주의와 만족에 기여합니다."},
    "창의성": {"weight": 5, "theory": "창의적 문제해결(Torrance) - 독창적 수업 설계는 학생의 확산적 사고를 자극합니다."},
}

DEFAULT_PRESETS = {
    "default": {
        "수업 전문성": {"base": 14.0, "adjust_range": 7.0},
        "교수학습 방법": {"base": 14.0, "adjust_range": 7.0},
        "판서 및 언어": {"base": 10.0, "adjust_range": 6.0},
        "수업 태도": {"base": 10.0, "adjust_range": 6.0},
        "학생 참여": {"base": 10.0, "adjust_range": 6.0},
        "시간 배분": {"base": 7.0, "adjust_range": 4.0},
        "창의성": {"base": 3.0, "adjust_range": 2.5},
    }
}

DEFAULT_GRADING = {
    "A+": 90, "A": 85, "A-": 80, "B+": 75, "B": 70,
    "B-": 65, "C+": 60, "C": 55, "C-": 50, "D": 0,
}

# v7.0 기본 구간화 설정
DEFAULT_BINNING = {
    "gesture_active_ratio": {
        "INACTIVE": [0.0, 0.15], "LOW": [0.15, 0.35],
        "MODERATE": [0.35, 0.55], "ACTIVE": [0.55, 1.0],
    },
    "eye_contact_ratio": {
        "POOR": [0.0, 0.2], "LOW": [0.2, 0.4],
        "MODERATE": [0.4, 0.6], "GOOD": [0.6, 0.8], "EXCELLENT": [0.8, 1.0],
    },
    "filler_ratio": {
        "CLEAN": [0.0, 0.02], "GOOD": [0.02, 0.035],
        "MODERATE": [0.035, 0.05], "HIGH": [0.05, 0.07], "EXCESSIVE": [0.07, 1.0],
    },
    "monotone_ratio": {
        "EXPRESSIVE": [0.0, 0.2], "VARIED": [0.2, 0.35],
        "MODERATE": [0.35, 0.5], "MONOTONE": [0.5, 0.7], "FLAT": [0.7, 1.0],
    },
    "teacher_ratio": {
        "STUDENT_LED": [0.0, 0.5], "BALANCED": [0.5, 0.65],
        "TEACHER_MODERATE": [0.65, 0.8], "TEACHER_DOMINANT": [0.8, 0.92],
        "LECTURE_ONLY": [0.92, 1.0],
    },
    "speaking_wpm": {
        "VERY_SLOW": [0, 40], "SLOW": [40, 60], "MODERATE": [60, 80],
        "GOOD": [80, 110], "FAST": [110, 145], "VERY_FAST": [145, 999],
    },
}

DEFAULT_CONFIDENCE_WEIGHTS = {
    "vision": 0.20, "stt": 0.30, "vibe": 0.15,
    "content": 0.15, "discourse": 0.20,
}


@dataclass
class DimensionScore:
    name: str
    score: float
    max_score: float
    percentage: float
    grade: str
    feedback: str
    theory_reference: str
    confidence: float = 1.0  # v7.0: 이 차원의 채점 신뢰도
    improvement_tips: List[str] = field(default_factory=list)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


def _safe(d: Dict, key: str, default=None):
    """에이전트 데이터에서 안전하게 값 추출 (error 딕셔너리 처리)"""
    if not d or not isinstance(d, dict) or 'error' in d:
        return default
    return d.get(key, default)


def _bin(value: float, bins: Dict) -> str:
    """v7.0: 연속값을 구간 레이블로 변환 (결정론적 채점 보장)"""
    for label, (low, high) in bins.items():
        if low <= value < high:
            return label
    # 최대값 포함 (마지막 구간)
    last_label = list(bins.keys())[-1]
    return last_label


class PedagogyAgent:
    """📚 교육학 이론 기반 7차원 평가 에이전트 (v7.0 — 신뢰도 강화)"""

    def __init__(self, use_rag: bool = True, preset: str = "default"):
        self.use_rag = use_rag
        self.preset = preset
        self._rag_kb = None

        # YAML 설정 로드
        self.dimensions, self.presets, self.grading, self.binning, self.confidence_weights = self._load_config()
        self.current_preset = self.presets.get(preset, self.presets.get("default", {}))

    def _load_config(self):
        """rubric_config.yaml 로드 (실패 시 기본값)"""
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "rubric_config.yaml"

        if HAS_YAML and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)

                dims = {}
                for name, d in cfg.get("dimensions", {}).items():
                    # YAML의 underscore 이름을 space로 변환
                    display_name = name.replace("_", " ")
                    dims[display_name] = {"weight": d["weight"], "theory": d["theory"]}

                presets = {}
                for pname, pvals in cfg.get("presets", {}).items():
                    preset_data = {}
                    for dname, dvals in pvals.items():
                        display_name = dname.replace("_", " ")
                        preset_data[display_name] = dvals
                    presets[pname] = preset_data

                grading = cfg.get("grading", DEFAULT_GRADING)
                binning = cfg.get("binning", DEFAULT_BINNING)
                conf_weights = cfg.get("confidence_weights", DEFAULT_CONFIDENCE_WEIGHTS)
                return dims, presets, grading, binning, conf_weights
            except Exception as e:
                print(f"[PedagogyAgent] YAML 설정 로드 실패: {e}")

        return DEFAULT_DIMENSIONS, DEFAULT_PRESETS, DEFAULT_GRADING, DEFAULT_BINNING, DEFAULT_CONFIDENCE_WEIGHTS

    def _bin_metric(self, metric_name: str, value: float) -> str:
        """v7.0: 메트릭을 구간 레이블로 변환"""
        bins = self.binning.get(metric_name)
        if not bins:
            return "UNKNOWN"
        return _bin(value, bins)

    def _compute_confidence(self, vis_ok, con_ok, stt_ok, vib_ok, disc_ok) -> Dict:
        """v7.0: 입력 데이터 품질에 따른 신뢰도 계산"""
        cw = self.confidence_weights
        available = 0.0
        if vis_ok:
            available += cw.get("vision", 0.2)
        if stt_ok:
            available += cw.get("stt", 0.3)
        if vib_ok:
            available += cw.get("vibe", 0.15)
        if con_ok:
            available += cw.get("content", 0.15)
        if disc_ok:
            available += cw.get("discourse", 0.2)

        total_possible = sum(cw.values())
        overall = available / total_possible if total_possible > 0 else 0.0

        return {
            "overall": round(overall, 3),
            "vision_available": vis_ok,
            "content_available": con_ok,
            "stt_available": stt_ok,
            "vibe_available": vib_ok,
            "discourse_available": disc_ok,
            "data_completeness": round(available, 3),
        }

    def evaluate(self, vision_summary: Dict, content_summary: Dict,
                 vibe_summary: Dict, stt_result: Dict = None,
                 discourse_result: Dict = None) -> Dict:
        """
        7차원 종합 평가 (v7.0)

        Args:
            vision_summary: VisionAgent 분석 결과
            content_summary: ContentAgent 분석 결과
            vibe_summary: VibeAgent 분석 결과
            stt_result: STTAgent 분석 결과
            discourse_result: DiscourseAnalyzer 분석 결과 (v5.0+)
        """
        stt = stt_result or {}
        discourse = discourse_result or {}

        # 에이전트 데이터 유효성 확인
        vis_ok = bool(vision_summary and 'error' not in vision_summary)
        con_ok = bool(content_summary and 'error' not in content_summary)
        vib_ok = bool(vibe_summary and len(vibe_summary) > 0)
        stt_ok = bool(stt and 'word_count' in stt)
        disc_ok = bool(discourse and 'question_types' in discourse)

        # v7.0: confidence 계산
        confidence = self._compute_confidence(vis_ok, con_ok, stt_ok, vib_ok, disc_ok)

        dimensions = [
            self._eval_expertise(content_summary, stt, vis_ok, con_ok, stt_ok, discourse, disc_ok),
            self._eval_methods(content_summary, vision_summary, stt, vis_ok, con_ok, stt_ok, discourse, disc_ok),
            self._eval_language(content_summary, stt, vibe_summary, stt_ok, vib_ok),
            self._eval_attitude(vision_summary, vibe_summary, vis_ok, vib_ok, stt_ok, stt, discourse, disc_ok),
            self._eval_participation(stt, vibe_summary, stt_ok, vib_ok, discourse, disc_ok),
            self._eval_time(vibe_summary, stt, vib_ok, stt_ok),
            self._eval_creativity(content_summary, vision_summary, stt, vibe_summary, vis_ok, con_ok, stt_ok, vib_ok, discourse, disc_ok),
        ]
        total = sum(d.score for d in dimensions)

        # v7.0: 차원별 독립 프로필 요약
        strengths = [d.name for d in dimensions if d.percentage >= 80]
        improvements = [d.name for d in dimensions if d.percentage < 60]

        return {
            "total_score": round(total, 1),
            "grade": self._grade(total),
            "is_supplementary": True,  # v7.0: 총점은 보조 지표
            "dimensions": [d.to_dict() for d in dimensions],
            "dimension_scores": {d.name: d.score for d in dimensions},
            "theory_references": [d.theory_reference for d in dimensions],
            "preset_used": self.preset,
            "confidence": confidence,  # v7.0
            "profile_summary": {  # v7.0: 차원별 독립 프로필
                "strengths": strengths,
                "improvements": improvements,
                "top_dimension": max(dimensions, key=lambda d: d.percentage).name if dimensions else "",
                "weakest_dimension": min(dimensions, key=lambda d: d.percentage).name if dimensions else "",
            },
            "version": "7.0",
        }

    def _get_base(self, dim_name: str) -> float:
        """프리셋에서 기본점 가져오기"""
        p = self.current_preset.get(dim_name, {})
        return p.get("base", 10.0)

    def _get_adjust_range(self, dim_name: str) -> float:
        """프리셋에서 조정 범위 가져오기"""
        p = self.current_preset.get(dim_name, {})
        return p.get("adjust_range", 5.0)

    def _make_score(self, name, base, feedback_fn, tips=None, confidence=1.0):
        w = self.dimensions.get(name, DEFAULT_DIMENSIONS.get(name, {})).get("weight", 10)
        # v7.0: adjust_range 클램핑 — base ± range 내에서만 허용
        preset_base = self._get_base(name)
        adj_range = self._get_adjust_range(name)
        # v7.0: 유효 최대값을 weight * 0.95로 제한 (천장 효과 방지)
        effective_max = min(preset_base + adj_range, w * 0.95)
        effective_min = max(preset_base - adj_range, 0)
        clamped = max(effective_min, min(effective_max, base))
        score = max(0, min(w, round(clamped, 1)))
        pct = (score / w) * 100
        g = "우수" if pct >= 85 else ("양호" if pct >= 70 else ("보통" if pct >= 55 else "노력 필요"))
        theory = self.dimensions.get(name, DEFAULT_DIMENSIONS.get(name, {})).get("theory", "")
        return DimensionScore(name=name, score=score, max_score=w, percentage=pct, grade=g,
                              feedback=feedback_fn(pct),
                              theory_reference=theory,
                              confidence=confidence,
                              improvement_tips=tips or [])

    # ================================================================
    # 1. 수업 전문성 (20점) — v7.0: 구간화 + 강화된 가감점
    # ================================================================
    def _eval_expertise(self, content, stt, vis_ok, con_ok, stt_ok, discourse, disc_ok):
        base = self._get_base("수업 전문성")
        conf = 0.5  # 기본 신뢰도

        if stt_ok:
            conf += 0.25
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0

            # v7.0: 구간화된 WPM 평가
            wpm_bin = self._bin_metric("speaking_wpm", wpm)
            if wpm_bin == "GOOD":
                base += 3.0
            elif wpm_bin == "MODERATE":
                base += 1.5
            elif wpm_bin == "SLOW":
                base += 0.0
            elif wpm_bin == "FAST":
                base -= 1.5
            elif wpm_bin == "VERY_FAST":
                base -= 3.0
            elif wpm_bin == "VERY_SLOW":
                base -= 3.0

            # 발화량
            if wc > 1200:
                base += 3.0
            elif wc > 800:
                base += 2.0
            elif wc > 500:
                base += 0.5
            elif wc > 300:
                base -= 2.5
            else:
                base -= 5.0

        if con_ok:
            conf += 0.1
            speaker_vis = _safe(content, 'speaker_visible_ratio', 0)
            if speaker_vis > 0.8:
                base += 1.0
            elif speaker_vis < 0.3:
                base -= 1.0

        # Bloom 인지수준
        if disc_ok:
            conf += 0.15
            bloom = discourse.get('bloom_levels', {})
            higher_order = bloom.get('analyze', 0) + bloom.get('evaluate', 0) + bloom.get('create', 0)
            if higher_order > 0.3:
                base += 3.5
            elif higher_order > 0.15:
                base += 2.0
            elif higher_order > 0.05:
                base += 0.5
            else:
                base -= 2.5  # 암기 중심 수업

        tips = []
        if stt_ok and stt.get('word_count', 0) < 500:
            tips.append("충분한 설명을 통해 학습 내용을 풍부하게 전달하세요.")
        if disc_ok and discourse.get('bloom_levels', {}).get('analyze', 0) < 0.1:
            tips.append("분석·평가·창작 수준의 사고를 유도하는 질문을 늘리세요.")

        return self._make_score("수업 전문성", base,
            lambda p: "학습 목표가 명확하고 내용 구조화가 매우 체계적입니다." if p >= 85 else
                      ("학습 목표와 내용 구성이 전반적으로 양호합니다." if p >= 70 else
                       ("내용 전달이 보통 수준입니다. 구조화가 필요합니다." if p >= 55 else
                        "학습 목표를 명확히 하고 내용을 체계적으로 구성하세요.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 2. 교수학습 방법 (20점) — v7.0: 구간화 + 강화
    # ================================================================
    def _eval_methods(self, content, vision, stt, vis_ok, con_ok, stt_ok, discourse, disc_ok):
        base = self._get_base("교수학습 방법")
        conf = 0.5

        if con_ok:
            conf += 0.15
            slide_r = _safe(content, 'slide_detected_ratio', 0)
            if slide_r > 0.6:
                base += 3.0
            elif slide_r > 0.3:
                base += 1.5
            elif slide_r < 0.1:
                base -= 2.0

            contrast = _safe(content, 'avg_color_contrast', 0)
            if contrast > 60:
                base += 1.5
            elif contrast < 20:
                base -= 1.0

        if vis_ok:
            conf += 0.15
            g_ratio = _safe(vision, 'gesture_active_ratio', 0)
            g_bin = self._bin_metric("gesture_active_ratio", g_ratio)
            if g_bin == "ACTIVE":
                base += 3.5
            elif g_bin == "MODERATE":
                base += 1.5
            elif g_bin == "LOW":
                base -= 0.5
            elif g_bin == "INACTIVE":
                base -= 2.0

            motion = _safe(vision, 'avg_motion_score', 0)
            if motion > 25:
                base += 1.5
            elif motion < 5:
                base -= 1.0

        if stt_ok:
            conf += 0.1
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0
            wpm_bin = self._bin_metric("speaking_wpm", wpm)
            if wpm_bin in ("GOOD", "MODERATE"):
                base += 2.0
            elif wpm_bin == "VERY_SLOW":
                base -= 2.5

        # 질문 유형 분석
        if disc_ok:
            conf += 0.1
            qt = discourse.get('question_types', {})
            total_q = sum(qt.values()) or 1
            open_ratio = qt.get('open_ended', 0) / total_q
            scaffolding = qt.get('scaffolding', 0)

            if open_ratio > 0.4:
                base += 2.5
            elif open_ratio > 0.2:
                base += 1.0
            elif open_ratio < 0.05:
                base -= 1.5

            if scaffolding >= 3:
                base += 2.0
            elif scaffolding >= 1:
                base += 0.5

        tips = []
        if disc_ok:
            qt = discourse.get('question_types', {})
            if qt.get('open_ended', 0) < 3:
                tips.append("'왜?', '어떻게?' 등 개방형 질문을 더 활용하세요.")
            if qt.get('scaffolding', 0) < 1:
                tips.append("스캐폴딩 질문으로 학생의 사고를 단계적으로 유도하세요.")

        return self._make_score("교수학습 방법", base,
            lambda p: "다양한 교수학습 방법을 매우 효과적으로 활용합니다." if p >= 85 else
                      ("교수법이 양호하며 시각자료 활용도 적절합니다." if p >= 70 else
                       ("교수법이 보통 수준입니다. 다양한 전략을 시도하세요." if p >= 55 else
                        "다양한 교수학습 전략과 매체 활용이 필요합니다.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 3. 판서 및 언어 (15점) — v7.0: 구간화
    # ================================================================
    def _eval_language(self, content, stt, vibe, stt_ok, vib_ok):
        base = self._get_base("판서 및 언어")
        conf = 0.5

        if stt_ok:
            conf += 0.25
            fr = stt.get('filler_ratio', 0.03)
            fr_bin = self._bin_metric("filler_ratio", fr)
            if fr_bin == "CLEAN":
                base += 4.0
            elif fr_bin == "GOOD":
                base += 2.0
            elif fr_bin == "MODERATE":
                base += 0.5
            elif fr_bin == "HIGH":
                base -= 2.0
            elif fr_bin == "EXCESSIVE":
                base -= 4.0

            pat = stt.get('speaking_pattern', '')
            if '빠름' in pat or 'Fast' in pat:
                base -= 1.5
            elif '느림' in pat or 'Slow' in pat:
                base -= 0.5

        if vib_ok:
            conf += 0.25
            mono = _safe(vibe, 'monotone_ratio', 0.5)
            mono_bin = self._bin_metric("monotone_ratio", mono)
            if mono_bin == "EXPRESSIVE":
                base += 3.0
            elif mono_bin == "VARIED":
                base += 1.5
            elif mono_bin == "MODERATE":
                base += 0.0
            elif mono_bin == "MONOTONE":
                base -= 2.0
            elif mono_bin == "FLAT":
                base -= 3.5

        tips = []
        if stt_ok and stt.get('filler_ratio', 0) > 0.04:
            tips.append(f"습관어를 줄이세요 (현재: {stt.get('filler_ratio', 0):.1%}).")
        if not vib_ok:
            tips.append("목소리 톤에 변화를 주어 핵심 내용을 강조하세요.")

        return self._make_score("판서 및 언어", base,
            lambda p: "언어 표현이 명확하고 발화가 매우 깨끗합니다." if p >= 85 else
                      ("언어 사용이 양호하나 미세한 개선 여지가 있습니다." if p >= 70 else
                       ("습관어나 단조로운 어조 개선이 필요합니다." if p >= 55 else
                        "발화 습관을 개선하고 핵심 용어를 정확히 사용하세요.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 4. 수업 태도 (15점) — v7.0: 구간화 + 강화
    # ================================================================
    def _eval_attitude(self, vision, vibe, vis_ok, vib_ok, stt_ok, stt, discourse, disc_ok):
        base = self._get_base("수업 태도")
        conf = 0.5

        if vis_ok:
            conf += 0.2
            ec = _safe(vision, 'eye_contact_ratio', 0)
            ec_bin = self._bin_metric("eye_contact_ratio", ec)
            if ec_bin == "EXCELLENT":
                base += 4.0
            elif ec_bin == "GOOD":
                base += 3.0
            elif ec_bin == "MODERATE":
                base += 1.0
            elif ec_bin == "LOW":
                base -= 1.0
            elif ec_bin == "POOR":
                base -= 3.0

            expr = _safe(vision, 'avg_expression_score', 50)
            if expr > 70:
                base += 2.5
            elif expr > 55:
                base += 0.5
            elif expr < 30:
                base -= 2.0

        if vib_ok:
            conf += 0.1
            ed = _safe(vibe, 'energy_distribution', {})
            if ed:
                high_e = ed.get('high', 0)
                low_e = ed.get('low', 0)
                if high_e > 0.4:
                    base += 2.5
                elif high_e > 0.25:
                    base += 1.0
                if low_e > 0.5:
                    base -= 2.0

        if stt_ok:
            conf += 0.1
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0
            wpm_bin = self._bin_metric("speaking_wpm", wpm)
            if wpm_bin in ("GOOD", "MODERATE"):
                base += 2.0
            elif wpm_bin == "VERY_SLOW":
                base -= 2.0

        # 피드백 품질 반영
        if disc_ok:
            conf += 0.1
            fb = discourse.get('feedback_quality', {})
            specific_praise = fb.get('specific_praise', 0)
            corrective = fb.get('corrective', 0)
            if specific_praise >= 5:
                base += 2.5
            elif specific_praise >= 2:
                base += 1.0
            if corrective >= 3:
                base += 1.5

        tips = []
        if vis_ok and _safe(vision, 'eye_contact_ratio', 0) < 0.3:
            tips.append("학생들과 시선을 고르게 맞추며 소통하세요.")
        if disc_ok and discourse.get('feedback_quality', {}).get('specific_praise', 0) < 2:
            tips.append("'잘했어요' 대신 '○○을 정확히 파악했네!'와 같은 구체적 칭찬을 하세요.")

        return self._make_score("수업 태도", base,
            lambda p: "열정적인 태도와 학생과의 라포 형성이 매우 우수합니다." if p >= 85 else
                      ("전반적으로 양호한 태도이나 소통 강화가 필요합니다." if p >= 70 else
                       ("태도 전반에 개선이 필요합니다." if p >= 55 else
                        "시선 접촉과 구체적 피드백을 통해 열정을 전달하세요.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 5. 학생 참여 (15점) — v7.0: 구간화 + 점수 범위 확대
    # ================================================================
    def _eval_participation(self, stt, vibe, stt_ok, vib_ok, discourse, disc_ok):
        base = self._get_base("학생 참여")
        conf = 0.5

        if stt_ok:
            conf += 0.25
            student_turns = stt.get('student_turns', 0)
            interaction_count = stt.get('interaction_count', 0)
            teacher_ratio = stt.get('teacher_ratio', 0.75)

            # 학생 발화
            if student_turns > 20:
                base += 2.5
            elif student_turns > 10:
                base += 1.5
            elif student_turns > 5:
                base += 0.5
            elif student_turns > 0:
                base += 0.0
            else:
                base -= 4.0  # v7.0: 학생 발화 없음 → 강한 감점

            # 상호작용 교대
            if interaction_count > 20:
                base += 1.5
            elif interaction_count > 10:
                base += 0.5
            elif interaction_count < 3:
                base -= 1.5

            # v7.0: 교사 발화 비율 — 구간화
            tr_bin = self._bin_metric("teacher_ratio", teacher_ratio)
            if tr_bin == "STUDENT_LED":
                base += 2.0
            elif tr_bin == "BALANCED":
                base += 1.5
            elif tr_bin == "TEACHER_MODERATE":
                base += 0.5
            elif tr_bin == "TEACHER_DOMINANT":
                base -= 1.5
            elif tr_bin == "LECTURE_ONLY":
                base -= 4.0  # v7.0: 독강 대폭 감점

            # 질문 횟수
            question_count = stt.get('question_count', 0)
            if question_count > 10:
                base += 1.0
            elif question_count == 0:
                base -= 1.0

        if vib_ok:
            conf += 0.1
            sr = _safe(vibe, 'avg_silence_ratio', 0.3)
            if 0.15 <= sr <= 0.30:
                base += 0.5
            elif sr > 0.45:
                base -= 1.0

        # 상호작용 점수 반영
        if disc_ok:
            conf += 0.15
            interaction_score = discourse.get('interaction_score', 50)
            if interaction_score > 80:
                base += 1.5
            elif interaction_score > 65:
                base += 0.5
            elif interaction_score < 30:
                base -= 1.5

        tips = []
        if stt_ok and stt.get('student_turns', 0) < 3:
            tips.append("개방형 질문으로 학생 발언 기회를 늘리세요.")
        if stt_ok and stt.get('teacher_ratio', 0.75) > 0.85:
            tips.append("교사 발화 비율이 높습니다. 학생에게 더 많은 발언 기회를 주세요.")

        return self._make_score("학생 참여", base,
            lambda p: "학생 참여를 효과적으로 이끌어내며 상호작용이 활발합니다." if p >= 85 else
                      ("참여 유도가 양호하나 상호작용을 더 늘리세요." if p >= 70 else
                       ("학생 참여 유도가 부족합니다." if p >= 55 else
                        "발문과 피드백 전략을 적극적으로 활용하세요.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 6. 시간 배분 (10점) — v7.0: 강화된 가감점
    # ================================================================
    def _eval_time(self, vibe, stt, vib_ok, stt_ok):
        base = self._get_base("시간 배분")
        conf = 0.5

        if vib_ok:
            conf += 0.25
            ed = _safe(vibe, 'energy_distribution', {})
            if ed:
                lvs = [ed.get('low', 0), ed.get('normal', 0), ed.get('high', 0)]
                if sum(lvs) > 0:
                    spread = max(lvs) - min(lvs)
                    if spread < 0.25:
                        base += 3.5
                    elif spread < 0.4:
                        base += 1.5
                    elif spread > 0.65:
                        base -= 2.5

            mono = _safe(vibe, 'monotone_ratio', 0.5)
            mono_bin = self._bin_metric("monotone_ratio", mono)
            if mono_bin in ("EXPRESSIVE", "VARIED"):
                base += 1.5
            elif mono_bin in ("MONOTONE", "FLAT"):
                base -= 1.5

        if stt_ok:
            conf += 0.25
            dur = stt.get('duration_seconds', 600)
            if 500 <= dur <= 900:
                base += 1.0
            elif dur > 1200:
                base -= 2.0
            elif dur < 300:
                base -= 2.0

        tips = []
        if base < 7:
            tips.append("도입(10%)-전개(70%)-정리(20%) 비율로 시간을 배분하세요.")

        return self._make_score("시간 배분", base,
            lambda p: "시간 배분이 매우 적절하며 수업 흐름이 자연스럽습니다." if p >= 85 else
                      ("시간 배분이 양호하나 정리 단계를 확보하세요." if p >= 70 else
                       ("시간 배분에 개선이 필요합니다." if p >= 55 else
                        "시간 배분을 사전에 계획하고 각 단계에 충실하세요.")),
            tips, confidence=min(1.0, conf))

    # ================================================================
    # 7. 창의성 (5점) — v7.0: 구간화 + 범위 확대
    # ================================================================
    def _eval_creativity(self, content, vision, stt, vibe, vis_ok, con_ok, stt_ok, vib_ok, discourse, disc_ok):
        base = self._get_base("창의성")
        conf = 0.5

        if con_ok:
            conf += 0.1
            contrast = _safe(content, 'avg_color_contrast', 0)
            complexity = _safe(content, 'avg_complexity', 0)
            if contrast > 60:
                base += 0.5
            elif contrast < 15:
                base -= 0.4
            if complexity > 10:
                base += 0.4
            elif complexity < 3:
                base -= 0.4

        if vis_ok:
            conf += 0.15
            motion = _safe(vision, 'avg_motion_score', 0)
            if motion > 30:
                base += 0.8
            elif motion > 15:
                base += 0.4
            elif motion < 3:
                base -= 0.6

            openness = _safe(vision, 'avg_body_openness', 0.5)
            if openness > 0.75:
                base += 0.6
            elif openness < 0.3:
                base -= 0.4

            g_ratio = _safe(vision, 'gesture_active_ratio', 0)
            g_bin = self._bin_metric("gesture_active_ratio", g_ratio)
            if g_bin == "ACTIVE":
                base += 0.7
            elif g_bin == "MODERATE":
                base += 0.3
            elif g_bin == "INACTIVE":
                base -= 0.6

        if stt_ok:
            conf += 0.1
            wc = stt.get('word_count', 0)
            sc = stt.get('segment_count', 1)

            if sc > 100 and wc > 800:
                base += 0.5
            elif sc > 60 and wc > 500:
                base += 0.2
            elif wc < 300:
                base -= 0.5

        # 고차원 인지 + 스캐폴딩
        if disc_ok:
            conf += 0.15
            bloom = discourse.get('bloom_levels', {})
            create_level = bloom.get('create', 0)
            analyze_level = bloom.get('analyze', 0)
            if create_level > 0.1:
                base += 0.8
            elif create_level > 0.03:
                base += 0.4
            if analyze_level > 0.15:
                base += 0.4
            scaffolding = discourse.get('question_types', {}).get('scaffolding', 0)
            if scaffolding >= 3:
                base += 0.5
            elif scaffolding >= 1:
                base += 0.2
            # 암기 위주 감점
            remember = bloom.get('remember', 0)
            if remember > 0.7:
                base -= 0.7

        tips = []
        if base < 3.5:
            tips.append("ICT 도구를 활용한 창의적 수업 설계를 시도하세요.")
        if vis_ok and _safe(vision, 'gesture_active_ratio', 0) < 0.2:
            tips.append("몸짓과 제스처를 적극 활용하여 수업을 역동적으로 만드세요.")

        return self._make_score("창의성", base,
            lambda p: "창의적인 수업 설계와 전달이 돋보입니다." if p >= 85 else
                      ("창의성이 양호한 수준입니다." if p >= 70 else
                       ("창의적 요소를 더 추가하세요." if p >= 55 else
                        "독창적인 활동과 시각적 매체를 적극 활용하세요.")),
            tips, confidence=min(1.0, conf))

    def _grade(self, total):
        for g, threshold in sorted(self.grading.items(), key=lambda x: x[1], reverse=True):
            if total >= threshold:
                return g
        return "D"
