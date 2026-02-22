"""
GAIM Lab - 100점 7차원 평가 프레임워크
초등 임용 2차 수업 시연 평가 기준 기반
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import sys
from pathlib import Path

# Gemini LLM 평가기 임포트 (옵션)
GEMINI_AVAILABLE = False
GeminiLectureEvaluator = None

try:
    # 상대 경로 import 시도
    from .gemini_evaluator import GeminiLectureEvaluator
    GEMINI_AVAILABLE = True
except ImportError:
    # 절대 경로 import 시도
    try:
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        from gemini_evaluator import GeminiLectureEvaluator
        GEMINI_AVAILABLE = True
    except ImportError:
        pass


# ============================================================
# 7차원 평가 프레임워크 정의 (초등 임용 2차 수업 시연 기준)
# 총 100점, 7차원, 17개 세부 평가 기준
# ============================================================
EVALUATION_FRAMEWORK_100 = {
    "수업_전문성": {
        "max_score": 20,
        "weight": 0.20,
        "description": "학습 목표 및 내용의 전문적 구성",
        "criteria": {
            "학습목표_명료성": {"max": 10, "description": "학습 목표가 명확하고 구체적으로 제시되었는가"},
            "학습내용_충실성": {"max": 10, "description": "교육과정에 맞는 적절한 학습 내용을 다루는가"}
        }
    },
    "교수학습_방법": {
        "max_score": 20,
        "weight": 0.20,
        "description": "다양하고 효과적인 교수법 활용",
        "criteria": {
            "교수법_다양성": {"max": 10, "description": "다양한 교수 매체와 기법을 활용하는가"},
            "학습활동_효과성": {"max": 10, "description": "학습 활동이 목표 달성에 효과적인가"}
        }
    },
    "판서_및_언어": {
        "max_score": 15,
        "weight": 0.15,
        "description": "판서와 언어적 표현의 명확성",
        "criteria": {
            "판서_가독성": {"max": 5, "description": "판서가 체계적이고 가독성이 좋은가"},
            "언어_명료성": {"max": 5, "description": "발화가 정확하고 명료한가"},
            "발화속도_적절성": {"max": 5, "description": "학습자 수준에 맞는 속도로 진행하는가"}
        }
    },
    "수업_태도": {
        "max_score": 15,
        "weight": 0.15,
        "description": "교사로서의 태도와 열정",
        "criteria": {
            "교사_열정": {"max": 5, "description": "수업에 대한 열정과 에너지가 있는가"},
            "학생_소통": {"max": 5, "description": "학생과의 비언어적 소통(시선, 제스처)이 자연스러운가"},
            "자신감": {"max": 5, "description": "당당하고 자신감 있는 태도인가"}
        }
    },
    "학생_참여": {
        "max_score": 15,
        "weight": 0.15,
        "description": "학생 참여 유도 및 피드백",
        "criteria": {
            "질문_기법": {"max": 7.5, "description": "사고를 자극하는 발문을 활용하는가"},
            "피드백_제공": {"max": 7.5, "description": "학생 반응에 적절한 피드백을 제공하는가"}
        }
    },
    "시간_배분": {
        "max_score": 10,
        "weight": 0.10,
        "description": "수업 시간의 효율적 활용",
        "criteria": {
            "시간_균형": {"max": 10, "description": "도입-전개-정리가 균형 있게 배분되었는가"}
        }
    },
    "창의성": {
        "max_score": 5,
        "weight": 0.05,
        "description": "수업의 독창성과 차별화",
        "criteria": {
            "수업_창의성": {"max": 5, "description": "독창적인 아이디어와 교수 기법을 사용하는가"}
        }
    }
}



@dataclass
class DimensionScore:
    """개별 차원 점수"""
    dimension: str
    score: float
    max_score: float
    percentage: float
    criteria_scores: Dict[str, float]
    feedback: List[str]


@dataclass
class EvaluationResult:
    """전체 평가 결과"""
    total_score: float
    max_score: float = 100.0
    grade: str = ""
    dimensions: List[DimensionScore] = None
    strengths: List[str] = None
    improvements: List[str] = None
    overall_feedback: str = ""


class GAIMLectureEvaluator:
    """
    GAIM Lab 100점 7차원 강의 평가기
    
    MLC 분석 결과를 입력받아 7차원 평가 점수로 변환
    """
    
    def __init__(self, use_gemini: bool = True):
        self.framework = EVALUATION_FRAMEWORK_100
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        self.gemini_evaluator = None
        
        if self.use_gemini:
            try:
                self.gemini_evaluator = GeminiLectureEvaluator()
                if not self.gemini_evaluator.model:
                    self.use_gemini = False
            except Exception as e:
                print(f"[!] Gemini 초기화 실패: {e}")
                self.use_gemini = False
    
    def evaluate(self, analysis_data: Dict) -> EvaluationResult:
        """
        분석 데이터를 기반으로 7차원 평가 수행 (초등 임용 2차 기준)
        
        Args:
            analysis_data: MLC 분석 결과 딕셔너리
                - vision_metrics: 비전 분석 결과
                - vibe_metrics: 오디오 분석 결과
                - text_metrics: 텍스트 분석 결과
                - content_metrics: 콘텐츠 분석 결과
        """
        dimensions = []
        total_score = 0.0
        
        # Gemini 평가 (transcript가 있는 경우)
        gemini_scores = None
        if self.use_gemini and "transcript" in analysis_data:
            transcript = analysis_data["transcript"]
            if transcript and len(transcript) > 50:
                print("\n🤖 Gemini LLM 평가 수행 중...")
                gemini_result = self.gemini_evaluator.evaluate_transcript(transcript)
                if gemini_result:
                    gemini_scores = self.gemini_evaluator.get_dimension_scores(gemini_result)
                    analysis_data["gemini_metrics"] = gemini_scores
                    print(f"   ✅ Gemini 평가 완료: {gemini_scores.get('total_score', 0)}점")
        
        # Gemini 점수가 있으면 해당 점수 사용, 없으면 규칙 기반 평가
        use_gemini_score = gemini_scores is not None
        
        # 1. 수업 전문성 평가 (20점)
        dim1 = self._evaluate_professionalism(analysis_data)
        dimensions.append(dim1)
        total_score += dim1.score
        
        # 2. 교수학습 방법 평가 (20점)
        dim2 = self._evaluate_teaching_method(analysis_data)
        dimensions.append(dim2)
        total_score += dim2.score
        
        # 3. 판서 및 언어 평가 (15점)
        dim3 = self._evaluate_language(analysis_data)
        dimensions.append(dim3)
        total_score += dim3.score
        
        # 4. 수업 태도 평가 (15점)
        dim4 = self._evaluate_attitude(analysis_data)
        dimensions.append(dim4)
        total_score += dim4.score
        
        # 5. 학생 참여 평가 (15점)
        dim5 = self._evaluate_participation(analysis_data)
        dimensions.append(dim5)
        total_score += dim5.score
        
        # 6. 시간 배분 평가 (10점)
        dim6 = self._evaluate_time_management(analysis_data)
        dimensions.append(dim6)
        total_score += dim6.score
        
        # 7. 창의성 평가 (5점)
        dim7 = self._evaluate_creativity(analysis_data)
        dimensions.append(dim7)
        total_score += dim7.score
        
        # 등급 산출
        grade = self._calculate_grade(total_score)
        
        # 강점/개선점 도출
        strengths, improvements = self._extract_feedback(dimensions)
        
        return EvaluationResult(
            total_score=round(total_score, 1),
            grade=grade,
            dimensions=dimensions,
            strengths=strengths,
            improvements=improvements,
            overall_feedback=self._generate_overall_feedback(total_score, grade, dimensions)
        )
    
    def _evaluate_professionalism(self, data: Dict) -> DimensionScore:
        """수업 전문성 평가 (20점)"""
        gemini = data.get("gemini_metrics", {}).get("professionalism", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="수업 전문성",
                score=score,
                max_score=20,
                percentage=round(score / 20 * 100, 1),
                criteria_scores={
                    "학습목표_명료성": criteria.get("학습목표_명료성", 0),
                    "학습내용_충실성": criteria.get("학습내용_충실성", 0)
                },
                feedback=feedback if feedback else self._get_professionalism_feedback(score)
            )
        
        # 기존 규칙 기반 평가
        text = data.get("text_metrics", {})
        
        # 학습목표 명료성 (10점): 도입부 구조화 표현 + 목표 관련 키워드
        structure_score = text.get("structure_score", 0) / 100 * 10
        
        # 학습내용 충실성 (10점): 핵심 개념 설명 빈도
        pedagogy_score = text.get("pedagogy_score", 0) / 100 * 10
        
        total = round(structure_score + pedagogy_score, 1)
        
        return DimensionScore(
            dimension="수업 전문성",
            score=total,
            max_score=20,
            percentage=round(total / 20 * 100, 1),
            criteria_scores={
                "학습목표_명료성": round(structure_score, 1),
                "학습내용_충실성": round(pedagogy_score, 1)
            },
            feedback=self._get_professionalism_feedback(total)
        )
    
    def _evaluate_teaching_method(self, data: Dict) -> DimensionScore:
        """교수학습 방법 평가 (20점)"""
        gemini = data.get("gemini_metrics", {}).get("teaching_method", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="교수학습 방법",
                score=score,
                max_score=20,
                percentage=round(score / 20 * 100, 1),
                criteria_scores={
                    "교수법_다양성": criteria.get("교수법_다양성", 0),
                    "학습활동_효과성": criteria.get("학습활동_효과성", 0)
                },
                feedback=feedback if feedback else self._get_teaching_method_feedback(score)
            )
        
        # 기존 규칙 기반 평가
        text = data.get("text_metrics", {})
        vision = data.get("vision_metrics", {})
        
        # 교수법 다양성 (10점): 예시, 제스처, 매체 활용
        example_count = text.get("example_count", 0)
        gesture_ratio = vision.get("gesture_active_ratio", 0)
        diversity_score = min((example_count / 3 * 5) + (gesture_ratio * 10), 10)
        
        # 학습활동 효과성 (10점): 상호작용, 구조화
        interaction_score = text.get("interaction_score", 0) / 100 * 5
        structure_score = text.get("structure_score", 0) / 100 * 5
        effectiveness_score = interaction_score + structure_score
        
        total = round(diversity_score + effectiveness_score, 1)
        
        return DimensionScore(
            dimension="교수학습 방법",
            score=total,
            max_score=20,
            percentage=round(total / 20 * 100, 1),
            criteria_scores={
                "교수법_다양성": round(diversity_score, 1),
                "학습활동_효과성": round(effectiveness_score, 1)
            },
            feedback=self._get_teaching_method_feedback(total)
        )
    
    def _evaluate_language(self, data: Dict) -> DimensionScore:
        """판서 및 언어 평가 (15점)"""
        gemini = data.get("gemini_metrics", {}).get("language", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="판서 및 언어",
                score=score,
                max_score=15,
                percentage=round(score / 15 * 100, 1),
                criteria_scores={
                    "판서_가독성": criteria.get("판서_가독성", 0),
                    "언어_명료성": criteria.get("언어_명료성", 0),
                    "발화속도_적절성": criteria.get("발화속도_적절성", 0)
                },
                feedback=feedback if feedback else self._get_language_feedback(score, 100)
            )
        
        # 기존 규칙 기반 평가 (fallback)
        content = data.get("content_metrics", {})
        vibe = data.get("vibe_metrics", {})
        
        # 판서 가독성 (5점)
        readability = content.get("readability", 0.5)
        board_score = readability * 5
        
        # 언어 명료성 (5점)
        text_density = content.get("text_density", 100)
        clarity_score = 5 if text_density < 150 else (3 if text_density < 200 else 1)
        
        # 발화속도 적절성 (5점): 침묵 비율 기반
        silence_ratio = vibe.get("silence_ratio", 0)
        if 0.1 <= silence_ratio <= 0.3:
            speed_score = 5
        elif 0.05 <= silence_ratio <= 0.4:
            speed_score = 3
        else:
            speed_score = 1
        
        total = round(board_score + clarity_score + speed_score, 1)
        
        return DimensionScore(
            dimension="판서 및 언어",
            score=total,
            max_score=15,
            percentage=round(total / 15 * 100, 1),
            criteria_scores={
                "판서_가독성": round(board_score, 1),
                "언어_명료성": round(clarity_score, 1),
                "발화속도_적절성": round(speed_score, 1)
            },
            feedback=self._get_language_feedback(total, text_density)
        )
    
    def _evaluate_attitude(self, data: Dict) -> DimensionScore:
        """수업 태도 평가 (15점)"""
        gemini = data.get("gemini_metrics", {}).get("attitude", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="수업 태도",
                score=score,
                max_score=15,
                percentage=round(score / 15 * 100, 1),
                criteria_scores={
                    "교사_열정": criteria.get("교사_열정", 0),
                    "학생_소통": criteria.get("학생_소통", 0),
                    "자신감": criteria.get("자신감", 0)
                },
                feedback=feedback if feedback else self._get_attitude_feedback(score, 0, 0)
            )
        
        # 기존 규칙 기반 평가 (fallback)
        vision = data.get("vision_metrics", {})
        vibe = data.get("vibe_metrics", {})
        
        # 교사 열정 (5점): 에너지 레벨
        energy = vibe.get("energy_mean", 0)
        passion_score = min(energy / 0.1 * 5, 5) if energy > 0 else 2.5
        
        # 학생 소통 (5점): 시선 처리
        eye_contact = vision.get("eye_contact_ratio", 0)
        communication_score = eye_contact * 5
        
        # 자신감 (5점): 제스처 + 표정
        gesture_ratio = vision.get("gesture_active_ratio", 0)
        expression = vision.get("expression_score", 0.5)
        confidence_score = min((gesture_ratio * 5) + (expression * 2.5), 5)
        
        total = round(passion_score + communication_score + confidence_score, 1)
        
        return DimensionScore(
            dimension="수업 태도",
            score=total,
            max_score=15,
            percentage=round(total / 15 * 100, 1),
            criteria_scores={
                "교사_열정": round(passion_score, 1),
                "학생_소통": round(communication_score, 1),
                "자신감": round(confidence_score, 1)
            },
            feedback=self._get_attitude_feedback(total, eye_contact, gesture_ratio)
        )
    
    def _evaluate_participation(self, data: Dict) -> DimensionScore:
        """학생 참여 평가 (15점)"""
        gemini = data.get("gemini_metrics", {}).get("participation", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="학생 참여",
                score=score,
                max_score=15,
                percentage=round(score / 15 * 100, 1),
                criteria_scores={
                    "질문_기법": criteria.get("질문_기법", 0),
                    "피드백_제공": criteria.get("피드백_제공", 0)
                },
                feedback=feedback if feedback else self._get_participation_feedback(score)
            )
        
        # 기존 규칙 기반 평가
        text = data.get("text_metrics", {})
        
        # 질문 기법 (7.5점): 발문 빈도
        interaction_score = text.get("interaction_score", 0) / 100 * 7.5
        
        # 피드백 제공 (7.5점): 참여 유도 표현
        engagement_phrases = text.get("engagement_phrases", 0)
        feedback_score = min(engagement_phrases / 5 * 7.5, 7.5)
        
        total = round(interaction_score + feedback_score, 1)
        
        return DimensionScore(
            dimension="학생 참여",
            score=total,
            max_score=15,
            percentage=round(total / 15 * 100, 1),
            criteria_scores={
                "질문_기법": round(interaction_score, 1),
                "피드백_제공": round(feedback_score, 1)
            },
            feedback=self._get_participation_feedback(total)
        )
    
    def _evaluate_time_management(self, data: Dict) -> DimensionScore:
        """시간 배분 평가 (10점)"""
        gemini = data.get("gemini_metrics", {}).get("time_management", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="시간 배분",
                score=score,
                max_score=10,
                percentage=round(score / 10 * 100, 1),
                criteria_scores={
                    "시간_균형": criteria.get("시간_균형", 0)
                },
                feedback=feedback if feedback else self._get_time_feedback(score)
            )
        
        # 기존 규칙 기반 평가 (fallback)
        text = data.get("text_metrics", {})
        vibe = data.get("vibe_metrics", {})
        
        # 시간 균형 (10점): 구조화 점수 + 침묵 비율
        structure_score = text.get("structure_score", 0) / 100 * 5
        
        silence_ratio = vibe.get("silence_ratio", 0)
        balance_score = 5 if 0.1 <= silence_ratio <= 0.3 else (3 if 0.05 <= silence_ratio <= 0.4 else 1)
        
        total = round(structure_score + balance_score, 1)
        
        return DimensionScore(
            dimension="시간 배분",
            score=total,
            max_score=10,
            percentage=round(total / 10 * 100, 1),
            criteria_scores={
                "시간_균형": round(total, 1)
            },
            feedback=self._get_time_feedback(total)
        )
    
    def _evaluate_creativity(self, data: Dict) -> DimensionScore:
        """창의성 평가 (5점)"""
        gemini = data.get("gemini_metrics", {}).get("creativity", {})
        
        # Gemini 점수가 있으면 사용
        if gemini and gemini.get("score", 0) > 0:
            score = gemini.get("score", 0)
            criteria = gemini.get("criteria", {})
            feedback = [gemini.get("feedback", "")] if gemini.get("feedback") else []
            return DimensionScore(
                dimension="창의성",
                score=score,
                max_score=5,
                percentage=round(score / 5 * 100, 1),
                criteria_scores={
                    "수업_창의성": criteria.get("수업_창의성", 0)
                },
                feedback=feedback if feedback else self._get_creativity_feedback(score)
            )
        
        # 기존 규칙 기반 평가
        text = data.get("text_metrics", {})
        vision = data.get("vision_metrics", {})
        
        # 수업 창의성 (5점): 다양한 표현 기법의 총합
        example_count = text.get("example_count", 0)
        gesture_ratio = vision.get("gesture_active_ratio", 0)
        pedagogy_score = text.get("pedagogy_score", 0) / 100
        
        creativity_score = min((example_count / 3) + (gesture_ratio * 2) + (pedagogy_score * 2), 5)
        
        total = round(creativity_score, 1)
        
        return DimensionScore(
            dimension="창의성",
            score=total,
            max_score=5,
            percentage=round(total / 5 * 100, 1),
            criteria_scores={
                "수업_창의성": round(total, 1)
            },
            feedback=self._get_creativity_feedback(total)
        )
    
    def _calculate_grade(self, score: float) -> str:
        """점수 기반 등급 산출"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 65:
            return "D+"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _extract_feedback(self, dimensions: List[DimensionScore]):
        """강점과 개선점 추출"""
        sorted_dims = sorted(dimensions, key=lambda d: d.percentage, reverse=True)
        
        strengths = []
        improvements = []
        
        for dim in sorted_dims[:2]:
            if dim.percentage >= 70:
                strengths.append(f"✅ {dim.dimension}: {dim.percentage}%")
        
        for dim in sorted_dims[-2:]:
            if dim.percentage < 60:
                improvements.append(f"🔧 {dim.dimension}: 추가 연습 필요")
        
        return strengths, improvements
    
    def _generate_overall_feedback(self, score: float, grade: str, dimensions: List[DimensionScore]) -> str:
        """종합 피드백 생성"""
        if score >= 85:
            return f"우수한 수업 시연입니다! 전체 {score}점({grade})으로 대부분의 영역에서 안정적인 역량을 보여주고 있습니다."
        elif score >= 70:
            return f"양호한 수업 시연입니다. {score}점({grade})으로 기본적인 교수 역량을 갖추고 있으며, 일부 영역에서 보완이 필요합니다."
        else:
            return f"추가적인 연습이 필요합니다. {score}점({grade})으로 여러 영역에서 개선의 여지가 있습니다. 피드백을 참고하여 반복 연습해 주세요."
    
    # 개별 차원 피드백 생성 메서드들 (초등 임용 2차 기준)
    def _get_professionalism_feedback(self, score: float) -> List[str]:
        if score >= 16:
            return ["학습 목표가 명확하고 구체적으로 제시됨", "교육과정에 맞는 충실한 학습 내용"]
        elif score >= 10:
            return ["기본적인 전문성 확보", "학습 목표를 더 구체적으로 제시하면 좋겠음"]
        else:
            return ["수업 도입부에서 학습 목표를 명시적으로 제시할 것", "핵심 개념 설명을 보강할 것"]
    
    def _get_teaching_method_feedback(self, score: float) -> List[str]:
        if score >= 16:
            return ["다양한 교수 매체와 기법 활용", "학습 활동이 목표 달성에 효과적"]
        elif score >= 10:
            return ["기본적인 교수법 활용", "더 다양한 교수 매체를 활용하면 좋겠음"]
        else:
            return ["예시와 비유를 더 많이 활용할 것", "학습 활동의 효과성을 높일 것"]
    
    def _get_language_feedback(self, score: float, text_density: float) -> List[str]:
        feedback = []
        if text_density > 150:
            feedback.append("판서 텍스트 양을 줄이고 핵심만 제시할 것")
        if score >= 12:
            feedback.append("언어 사용이 명료하고 적절함")
        elif score >= 8:
            feedback.append("기본적인 언어 전달력 보유")
        else:
            feedback.append("발화 속도와 명료성을 개선할 것")
        return feedback if feedback else ["판서와 언어 사용이 자연스러움"]
    
    def _get_attitude_feedback(self, score: float, eye_contact: float, gesture: float) -> List[str]:
        feedback = []
        if eye_contact < 0.6:
            feedback.append("학생과의 눈맞춤을 더 자주 할 것")
        if gesture < 0.3:
            feedback.append("제스처를 더 적극적으로 활용할 것")
        if score >= 12:
            if not feedback:
                feedback.append("열정적이고 자신감 있는 수업 태도")
        elif score >= 8:
            feedback.append("기본적인 수업 태도 양호")
        else:
            feedback.append("수업에 대한 열정과 자신감을 높일 것")
        return feedback
    
    def _get_participation_feedback(self, score: float) -> List[str]:
        if score >= 12:
            return ["효과적인 발문 기법 활용", "학생 참여를 잘 유도함"]
        elif score >= 8:
            return ["기본적인 상호작용 있음", "질문을 더 자주 활용하면 좋겠음"]
        else:
            return ["'여러분', '생각해보세요' 등 참여 유도 표현 사용", "개방형 질문을 더 활용할 것"]
    
    def _get_time_feedback(self, score: float) -> List[str]:
        if score >= 8:
            return ["도입-전개-정리가 균형 있게 배분됨"]
        elif score >= 5:
            return ["기본적인 시간 배분은 양호", "페이스 조절에 신경 쓸 것"]
        else:
            return ["수업 시간 배분을 더 균형 있게 조절할 것", "도입과 정리 시간을 확보할 것"]
    
    def _get_creativity_feedback(self, score: float) -> List[str]:
        if score >= 4:
            return ["독창적인 교수 기법과 아이디어 활용"]
        elif score >= 2:
            return ["기본적인 수업 진행", "더 창의적인 교수 기법을 시도해 볼 것"]
        else:
            return ["다양한 교수 기법과 아이디어를 개발할 것"]
    
    def to_dict(self, result: EvaluationResult) -> Dict:
        """평가 결과를 딕셔너리로 변환"""
        return {
            "total_score": result.total_score,
            "max_score": result.max_score,
            "grade": result.grade,
            "dimensions": [
                {
                    "name": d.dimension,
                    "score": d.score,
                    "max_score": d.max_score,
                    "percentage": d.percentage,
                    "criteria": d.criteria_scores,
                    "feedback": d.feedback
                }
                for d in result.dimensions
            ],
            "strengths": result.strengths,
            "improvements": result.improvements,
            "overall_feedback": result.overall_feedback
        }
    
    def to_json(self, result: EvaluationResult) -> str:
        """평가 결과를 JSON 문자열로 변환"""
        return json.dumps(self.to_dict(result), ensure_ascii=False, indent=2)
