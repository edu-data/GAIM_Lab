"""
📚 Pedagogy Agent - 교육학 이론 기반 평가 전문 에이전트
RAG 지식 기반과 연동하여 7차원 교육학 평가를 수행합니다.

v4.1 개선: 점수 차별화 강화
- 에이전트 데이터 없을 때 합리적 기본값 부여
- STT 데이터(word_count, speaking_rate, filler_ratio) 기반 차별화 강화
- 한국어 발화 속도 기준 보정 (WPM, 자모수 아닌 어절 기준)
"""

from typing import Dict, List
from dataclasses import dataclass, field

DIMENSION_FRAMEWORK = {
    "수업 전문성": {"weight": 20, "theory": "구성주의 학습이론 - 학습 목표의 명확한 제시는 학생의 인지적 스캐폴딩을 제공합니다."},
    "교수학습 방법": {"weight": 20, "theory": "다중지능이론(Gardner) - 다양한 교수법은 학생의 서로 다른 지능 유형에 호소합니다."},
    "판서 및 언어": {"weight": 15, "theory": "이중부호화이론(Paivio) - 시각적, 언어적 정보의 병행 제시가 학습 효과를 높입니다."},
    "수업 태도": {"weight": 15, "theory": "사회학습이론(Bandura) - 교사의 열정적 태도는 학생의 학습 동기에 모델링 효과를 줍니다."},
    "학생 참여": {"weight": 15, "theory": "ZPD(Vygotsky) - 적절한 발문은 학생의 근접발달영역에서의 학습을 촉진합니다."},
    "시간 배분": {"weight": 10, "theory": "ARCS 모델(Keller) - 적절한 시간 배분은 학습자의 주의를 효과적으로 유지합니다."},
    "창의성": {"weight": 5, "theory": "창의적 문제해결(Torrance) - 독창적 수업 설계는 학생의 확산적 사고를 자극합니다."},
}


@dataclass
class DimensionScore:
    name: str; score: float; max_score: float; percentage: float; grade: str
    feedback: str; theory_reference: str; improvement_tips: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict:
        return {"name": self.name, "score": round(self.score, 1), "max_score": self.max_score,
                "percentage": round(self.percentage, 1), "grade": self.grade, "feedback": self.feedback,
                "theory_reference": self.theory_reference, "improvement_tips": self.improvement_tips}


def _safe(d: Dict, key: str, default=None):
    """에이전트 데이터에서 안전하게 값 추출 (error 딕셔너리 처리)"""
    if not d or not isinstance(d, dict) or 'error' in d:
        return default
    return d.get(key, default)


class PedagogyAgent:
    """📚 교육학 이론 기반 7차원 평가 에이전트 (v4.1 — 점수 차별화 강화)"""

    def __init__(self, use_rag: bool = True):
        self.use_rag = use_rag
        self._rag_kb = None

    def evaluate(self, vision_summary: Dict, content_summary: Dict,
                 vibe_summary: Dict, stt_result: Dict = None) -> Dict:
        stt = stt_result or {}
        # 에이전트 데이터 유효성 확인
        vis_ok = bool(vision_summary and 'error' not in vision_summary)
        con_ok = bool(content_summary and 'error' not in content_summary)
        vib_ok = bool(vibe_summary and len(vibe_summary) > 0)
        stt_ok = bool(stt and 'word_count' in stt)

        dimensions = [
            self._eval_expertise(content_summary, stt, vis_ok, con_ok, stt_ok),
            self._eval_methods(content_summary, vision_summary, stt, vis_ok, con_ok, stt_ok),
            self._eval_language(content_summary, stt, vibe_summary, stt_ok, vib_ok),
            self._eval_attitude(vision_summary, vibe_summary, vis_ok, vib_ok, stt_ok, stt),
            self._eval_participation(stt, vibe_summary, stt_ok, vib_ok),
            self._eval_time(vibe_summary, stt, vib_ok, stt_ok),
            self._eval_creativity(content_summary, vision_summary, stt, vibe_summary, vis_ok, con_ok, stt_ok, vib_ok),
        ]
        total = sum(d.score for d in dimensions)
        return {"total_score": round(total, 1), "grade": self._grade(total),
                "dimensions": [d.to_dict() for d in dimensions],
                "dimension_scores": {d.name: d.score for d in dimensions},
                "theory_references": [d.theory_reference for d in dimensions]}

    def _make_score(self, name, base, feedback_fn, tips=None):
        w = DIMENSION_FRAMEWORK[name]["weight"]
        score = max(0, min(w, round(base, 1)))
        pct = (score / w) * 100
        g = "우수" if pct >= 85 else ("양호" if pct >= 70 else ("보통" if pct >= 55 else "노력 필요"))
        return DimensionScore(name=name, score=score, max_score=w, percentage=pct, grade=g,
                              feedback=feedback_fn(pct),
                              theory_reference=DIMENSION_FRAMEWORK[name]["theory"],
                              improvement_tips=tips or [])

    # ================================================================
    # 1. 수업 전문성 (20점)
    #    기본 14.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_expertise(self, content, stt, vis_ok, con_ok, stt_ok):
        base = 14.0

        if stt_ok:
            # 발화량 — 내용 충실성의 핵심 지표
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0  # 분당 어절수

            if wc > 1200:
                base += 3.0  # 매우 풍부한 설명
            elif wc > 800:
                base += 1.5
            elif wc > 500:
                base += 0.0  # 보통
            elif wc > 300:
                base -= 1.5
            else:
                base -= 3.0  # 설명이 매우 부족

            # 발화 속도 적절성 (한국어 기준 분당 70~100 어절 적절)
            if 70 <= wpm <= 100:
                base += 1.5  # 최적 구간
            elif 55 <= wpm <= 120:
                base += 0.5
            elif wpm > 140:
                base -= 1.5  # 너무 빠름
            elif wpm < 40:
                base -= 1.5  # 너무 느림

        if con_ok:
            slide_r = _safe(content, 'slide_detected_ratio', 0)
            if slide_r > 0.5:
                base += 1.5
            elif slide_r > 0.3:
                base += 0.5
            elif slide_r < 0.1:
                base -= 0.5

        tips = []
        if stt_ok and stt.get('word_count', 0) < 500:
            tips.append("충분한 설명을 통해 학습 내용을 풍부하게 전달하세요.")
        if not con_ok:
            tips.append("시각적 자료를 활용하여 핵심 개념을 구조화하세요.")

        return self._make_score("수업 전문성", base,
            lambda p: "학습 목표가 명확하고 내용 구조화가 매우 체계적입니다." if p >= 85 else
                      ("학습 목표와 내용 구성이 전반적으로 양호합니다." if p >= 70 else
                       ("내용 전달이 보통 수준입니다. 구조화가 필요합니다." if p >= 55 else
                        "학습 목표를 명확히 하고 내용을 체계적으로 구성하세요.")), tips)

    # ================================================================
    # 2. 교수학습 방법 (20점)
    #    기본 14.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_methods(self, content, vision, stt, vis_ok, con_ok, stt_ok):
        base = 14.0

        if con_ok:
            slide_r = _safe(content, 'slide_detected_ratio', 0)
            if slide_r > 0.6:
                base += 2.0
            elif slide_r > 0.3:
                base += 1.0
            elif slide_r < 0.1:
                base -= 1.0

            contrast = _safe(content, 'avg_color_contrast', 0)
            if contrast > 60:
                base += 1.0
            elif contrast < 20:
                base -= 0.5

        if vis_ok:
            g = _safe(vision, 'gesture_active_ratio', 0)
            if g > 0.5:
                base += 2.0
            elif g > 0.3:
                base += 1.0
            elif g < 0.1:
                base -= 1.0

            motion = _safe(vision, 'avg_motion_score', 0)
            if motion > 25:
                base += 1.0
            elif motion < 5:
                base -= 0.5

        # STT 기반 교수법 차별화 (Vision/Content 데이터 없을 때 특히 중요)
        if stt_ok:
            # 발화량 — 다양한 설명 방법의 지표
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0
            if wpm > 90:
                base += 2.0  # 매우 적극적 교수법
            elif wpm > 70:
                base += 1.0
            elif wpm < 45:
                base -= 1.5  # 소극적 교수법
            elif wpm < 55:
                base -= 0.5

            # 세그먼트 다양성 — 교수법 역동성
            sc = stt.get('segment_count', 0)
            if sc > 100:
                base += 1.0  # 매우 역동적
            elif sc > 60:
                base += 0.5
            elif sc < 30:
                base -= 0.5

        tips = []
        if not vis_ok and not con_ok:
            tips.append("다양한 교수학습 매체를 활용하세요.")

        return self._make_score("교수학습 방법", base,
            lambda p: "다양한 교수학습 방법을 매우 효과적으로 활용합니다." if p >= 85 else
                      ("교수법이 양호하며 시각자료 활용도 적절합니다." if p >= 70 else
                       ("교수법이 보통 수준입니다. 다양한 전략을 시도하세요." if p >= 55 else
                        "다양한 교수학습 전략과 매체 활용이 필요합니다.")), tips)

    # ================================================================
    # 3. 판서 및 언어 (15점)
    #    기본 10.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_language(self, content, stt, vibe, stt_ok, vib_ok):
        base = 10.0

        if stt_ok:
            # 습관어 비율 — 핵심 차별화 지표
            fr = stt.get('filler_ratio', 0.03)
            if fr < 0.015:
                base += 2.5
            elif fr < 0.025:
                base += 1.5
            elif fr < 0.035:
                base += 0.5
            elif fr > 0.07:
                base -= 2.5  # 습관어 매우 많음
            elif fr > 0.05:
                base -= 1.5
            elif fr > 0.04:
                base -= 0.5

            # 발화 패턴
            pat = stt.get('speaking_pattern', '')
            if '빠름' in pat or 'Fast' in pat:
                base -= 0.5
            elif '느림' in pat or 'Slow' in pat:
                base -= 0.5  # 약간의 감점 (너무 느려도 좋지 않음)

        if vib_ok:
            mono = _safe(vibe, 'monotone_ratio', 0.5)
            if mono < 0.2:
                base += 1.5
            elif mono < 0.3:
                base += 0.5
            elif mono > 0.6:
                base -= 1.5
            elif mono > 0.4:
                base -= 0.5

        tips = []
        if stt_ok and stt.get('filler_ratio', 0) > 0.04:
            tips.append(f"습관어를 줄이세요 (현재: {stt.get('filler_ratio', 0):.1%}).")
        if not vib_ok:
            tips.append("목소리 톤에 변화를 주어 핵심 내용을 강조하세요.")

        return self._make_score("판서 및 언어", base,
            lambda p: "언어 표현이 명확하고 발화가 매우 깨끗합니다." if p >= 85 else
                      ("언어 사용이 양호하나 미세한 개선 여지가 있습니다." if p >= 70 else
                       ("습관어나 단조로운 어조 개선이 필요합니다." if p >= 55 else
                        "발화 습관을 개선하고 핵심 용어를 정확히 사용하세요.")), tips)

    # ================================================================
    # 4. 수업 태도 (15점)
    #    기본 10.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_attitude(self, vision, vibe, vis_ok, vib_ok, stt_ok, stt):
        base = 10.0

        if vis_ok:
            ec = _safe(vision, 'eye_contact_ratio', 0)
            if ec > 0.7:
                base += 2.5
            elif ec > 0.5:
                base += 1.5
            elif ec > 0.3:
                base += 0.5
            elif ec < 0.15:
                base -= 1.5

            expr = _safe(vision, 'avg_expression_score', 50)
            if expr > 70:
                base += 1.5
            elif expr > 55:
                base += 0.5
            elif expr < 30:
                base -= 1.0

        if vib_ok:
            ed = _safe(vibe, 'energy_distribution', {})
            if ed:
                high_e = ed.get('high', 0)
                low_e = ed.get('low', 0)
                if high_e > 0.4:
                    base += 1.5
                elif high_e > 0.25:
                    base += 0.5
                if low_e > 0.5:
                    base -= 1.0

        if stt_ok:
            # 발화량이 많을수록 열정적
            wc = stt.get('word_count', 0)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0
            if wpm > 90:
                base += 1.0  # 적극적 발화
            elif wpm < 40:
                base -= 1.0  # 소극적

        tips = []
        if not vis_ok:
            tips.append("학생들과 시선을 고르게 맞추며 소통하세요.")
        if not vib_ok:
            tips.append("에너지 수준을 높여 활기찬 수업 분위기를 만드세요.")

        return self._make_score("수업 태도", base,
            lambda p: "열정적인 태도와 시선 접촉이 매우 우수합니다." if p >= 85 else
                      ("전반적으로 양호한 태도이나 소통 강화가 필요합니다." if p >= 70 else
                       ("태도 전반에 개선이 필요합니다." if p >= 55 else
                        "시선 접촉과 표정 관리를 통해 열정을 전달하세요.")), tips)

    # ================================================================
    # 5. 학생 참여 (15점)
    #    기본 10.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_participation(self, stt, vibe, stt_ok, vib_ok):
        base = 10.0

        if stt_ok:
            # 발화 패턴 — 핵심 차별화 지표
            pat = stt.get('speaking_pattern', '')
            if 'Conversational' in pat or '대화' in pat:
                base += 3.0
            elif 'Interactive' in pat or '상호' in pat:
                base += 2.0
            elif '보통' in pat or 'Normal' in pat or 'Moderate' in pat:
                base += 0.5
            elif '느림' in pat or 'Slow' in pat:
                base -= 0.5  # 느린 진행은 소극적 참여 의미
            elif '빠름' in pat or 'Fast' in pat:
                base += 0.0  # 빠른 진행은 강의식

            # 습관어 비율이 낮으면 더 유창한 상호작용
            fr = stt.get('filler_ratio', 0.03)
            if fr < 0.02:
                base += 1.5
            elif fr < 0.03:
                base += 0.5
            elif fr > 0.06:
                base -= 1.0

            # 발화량 대비 세그먼트수 — 발화 리듬 (짧은 발화가 많을수록 대화적)
            sc = stt.get('segment_count', 0)
            wc = stt.get('word_count', 1)
            if sc > 0 and wc > 0:
                words_per_seg = wc / sc
                if words_per_seg < 8:
                    base += 1.0  # 짧은 발화 = 대화형
                elif words_per_seg > 20:
                    base -= 0.5  # 긴 발화 = 강의형

        if vib_ok:
            sr = _safe(vibe, 'avg_silence_ratio', 0.3)
            if 0.15 <= sr <= 0.30:
                base += 1.0
            elif sr < 0.05:
                base -= 0.5
            elif sr > 0.45:
                base -= 1.0

        tips = []
        if stt_ok and ('느림' in stt.get('speaking_pattern', '') or 'Slow' in stt.get('speaking_pattern', '')):
            tips.append("개방형 질문으로 학생 사고를 자극하세요.")
        if not vib_ok:
            tips.append("적절한 발문으로 학생 참여를 유도하세요.")

        return self._make_score("학생 참여", base,
            lambda p: "학생 참여를 효과적으로 이끌어내며 상호작용이 활발합니다." if p >= 85 else
                      ("참여 유도가 양호하나 상호작용을 더 늘리세요." if p >= 70 else
                       ("학생 참여 유도가 부족합니다." if p >= 55 else
                        "발문과 피드백 전략을 적극적으로 활용하세요.")), tips)

    # ================================================================
    # 6. 시간 배분 (10점)
    #    기본 7.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_time(self, vibe, stt, vib_ok, stt_ok):
        base = 7.0

        if vib_ok:
            ed = _safe(vibe, 'energy_distribution', {})
            if ed:
                lvs = [ed.get('low', 0), ed.get('normal', 0), ed.get('high', 0)]
                if sum(lvs) > 0:
                    spread = max(lvs) - min(lvs)
                    if spread < 0.25:
                        base += 2.0
                    elif spread < 0.4:
                        base += 1.0
                    elif spread > 0.65:
                        base -= 1.0

            mono = _safe(vibe, 'monotone_ratio', 0.5)
            if mono < 0.2:
                base += 1.0
            elif mono > 0.5:
                base -= 0.5

        if stt_ok:
            # 적절한 수업 길이 (10~15분 = 600~900초)
            dur = stt.get('duration_seconds', 600)
            if 500 <= dur <= 900:
                base += 0.5  # 적절한 길이
            elif dur > 1200:
                base -= 0.5  # 너무 길 수 있음
            elif dur < 300:
                base -= 0.5  # 너무 짧음

        tips = []
        if base < 7:
            tips.append("도입(10%)-전개(70%)-정리(20%) 비율로 시간을 배분하세요.")
        if not vib_ok:
            tips.append("수업 에너지를 전체 시간에 걸쳐 고르게 배분하세요.")

        return self._make_score("시간 배분", base,
            lambda p: "시간 배분이 매우 적절하며 수업 흐름이 자연스럽습니다." if p >= 85 else
                      ("시간 배분이 양호하나 정리 단계를 확보하세요." if p >= 70 else
                       ("시간 배분에 개선이 필요합니다." if p >= 55 else
                        "시간 배분을 사전에 계획하고 각 단계에 충실하세요.")), tips)

    # ================================================================
    # 7. 창의성 (5점)
    #    기본 3.0 (데이터 가용시 조정)
    # ================================================================
    def _eval_creativity(self, content, vision, stt, vibe, vis_ok, con_ok, stt_ok, vib_ok):
        base = 3.0

        if con_ok:
            slide_r = _safe(content, 'slide_detected_ratio', 0)
            if slide_r > 0.5:
                base += 0.8
            elif slide_r > 0.3:
                base += 0.3

            contrast = _safe(content, 'avg_color_contrast', 0)
            if contrast > 60:
                base += 0.5
            elif contrast < 20:
                base -= 0.3

        if vis_ok:
            motion = _safe(vision, 'avg_motion_score', 0)
            if motion > 25:
                base += 0.5
            openness = _safe(vision, 'avg_body_openness', 0.5)
            if openness > 0.7:
                base += 0.3

        if stt_ok:
            # 발화 다양성 — 세그먼트 수 대비 어절수
            wc = stt.get('word_count', 0)
            sc = stt.get('segment_count', 1)
            dur = stt.get('duration_seconds', 600)
            wpm = (wc / dur * 60) if dur > 0 else 0

            if sc > 100 and wc > 800:
                base += 0.8  # 매우 풍부한 발화
            elif sc > 60 and wc > 500:
                base += 0.4
            elif wc < 300:
                base -= 0.4  # 발화 부족

            # 발화 속도 다양성 — 창의적 전달
            if wpm > 80:
                base += 0.3
            elif wpm < 40:
                base -= 0.3

        tips = []
        if base < 3.5:
            tips.append("ICT 도구를 활용한 창의적 수업 설계를 시도하세요.")

        return self._make_score("창의성", base,
            lambda p: "창의적인 수업 설계와 전달이 돋보입니다." if p >= 85 else
                      ("창의성이 양호한 수준입니다." if p >= 70 else
                       ("창의적 요소를 더 추가하세요." if p >= 55 else
                        "독창적인 활동과 시각적 매체를 적극 활용하세요.")), tips)

    def _grade(self, total):
        if total >= 90: return "A+"
        elif total >= 85: return "A"
        elif total >= 80: return "A-"
        elif total >= 75: return "B+"
        elif total >= 70: return "B"
        elif total >= 65: return "B-"
        elif total >= 60: return "C+"
        elif total >= 55: return "C"
        elif total >= 50: return "C-"
        else: return "D"
