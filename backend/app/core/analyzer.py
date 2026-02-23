"""
GAIM Lab - 분석 파이프라인
MLC 분석 결과를 GAIM 평가 프레임워크로 통합
"""

import sys
from pathlib import Path
from typing import Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# MLC 핵심 모듈 경로 추가
CORE_PATH = Path(__file__).parent.parent.parent.parent / "core"
sys.path.insert(0, str(CORE_PATH))

from .evaluator import GAIMLectureEvaluator, EvaluationResult


class GAIMAnalysisPipeline:
    """
    GAIM Lab 분석 파이프라인
    
    영상 입력 → MLC 분석 → 7차원 평가 → 피드백 리포트
    """
    
    def __init__(self, use_turbo: bool = True, use_text: bool = True):
        self.use_turbo = use_turbo
        self.use_text = use_text
        self.evaluator = GAIMLectureEvaluator()
        self._mlc_coach = None
    
    def _get_mlc_coach(self):
        """MLC LectureCoach 인스턴스 lazy 로딩"""
        if self._mlc_coach is None:
            try:
                # MLC 원본 모듈 import
                mlc_path = Path(r"d:/data science/lecture_coach")
                sys.path.insert(0, str(mlc_path))
                from main import LectureCoach
                self._mlc_coach = LectureCoach()
            except ImportError as e:
                print(f"Warning: MLC module not found: {e}")
                self._mlc_coach = None
        return self._mlc_coach
    
    async def analyze_video(
        self, 
        video_path: Path, 
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        영상 분석 수행 (비동기)
        
        Args:
            video_path: 분석할 영상 경로
            output_dir: 결과 저장 디렉토리
            
        Returns:
            분석 결과 딕셔너리 (7차원 평가 포함)
        """
        output_dir = output_dir or Path(__file__).resolve().parent.parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. MLC 분석 수행
        mlc_result = await self._run_mlc_analysis(video_path, output_dir)
        
        # 2. 7차원 평가 수행
        evaluation = self.evaluator.evaluate(mlc_result)
        
        # 3. 결과 통합
        result = {
            "video_path": str(video_path),
            "mlc_analysis": mlc_result,
            "gaim_evaluation": self.evaluator.to_dict(evaluation),
            "status": "completed"
        }
        
        return result
    
    async def _run_mlc_analysis(self, video_path: Path, output_dir: Path) -> Dict:
        """MLC 분석 실행 (ProcessPool에서 실행)"""
        coach = self._get_mlc_coach()
        
        if coach is None:
            # MLC 없이 더미 데이터 반환 (개발/테스트용)
            return self._get_dummy_analysis()
        
        # 동기 분석을 비동기로 래핑
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self._sync_analyze,
                coach, video_path, output_dir
            )
        
        return result
    
    def _sync_analyze(self, coach, video_path: Path, output_dir: Path) -> Dict:
        """동기 MLC 분석"""
        result = coach.analyze(
            video_path=video_path,
            output_dir=output_dir,
            use_turbo=self.use_turbo,
            use_text=self.use_text
        )
        
        # MLC 결과를 GAIM 형식으로 변환
        return self._convert_mlc_result(result)
    
    def _convert_mlc_result(self, mlc_result: Dict) -> Dict:
        """MLC 결과를 GAIM 형식으로 변환"""
        return {
            "vision_metrics": {
                "gesture_active_ratio": mlc_result.get("gesture_active_ratio", 0.3),
                "eye_contact_ratio": mlc_result.get("eye_contact_ratio", 0.7),
                "expression_score": mlc_result.get("expression_score", 0.6)
            },
            "vibe_metrics": {
                "pitch_std": mlc_result.get("pitch_std", 20),
                "energy_mean": mlc_result.get("energy_mean", 0.05),
                "silence_ratio": mlc_result.get("silence_ratio", 0.15),
                "is_monotone": mlc_result.get("is_monotone", False)
            },
            "text_metrics": {
                "pedagogy_score": mlc_result.get("pedagogy_score", 50),
                "interaction_score": mlc_result.get("interaction_score", 40),
                "structure_score": mlc_result.get("structure_score", 45),
                "example_count": mlc_result.get("example_count", 3),
                "transition_count": mlc_result.get("transition_count", 4),
                "engagement_phrases": mlc_result.get("engagement_phrases", 5),
                "summary_count": mlc_result.get("summary_count", 2)
            },
            "content_metrics": {
                "text_density": mlc_result.get("text_density", 80),
                "readability": mlc_result.get("readability", 0.7)
            }
        }
    
    def _get_dummy_analysis(self) -> Dict:
        """개발/테스트용 더미 분석 데이터"""
        return {
            "vision_metrics": {
                "gesture_active_ratio": 0.35,
                "eye_contact_ratio": 0.72,
                "expression_score": 0.65
            },
            "vibe_metrics": {
                "pitch_std": 22.5,
                "energy_mean": 0.055,
                "silence_ratio": 0.18,
                "is_monotone": False
            },
            "text_metrics": {
                "pedagogy_score": 55,
                "interaction_score": 48,
                "structure_score": 52,
                "example_count": 4,
                "transition_count": 5,
                "engagement_phrases": 6,
                "summary_count": 2
            },
            "content_metrics": {
                "text_density": 95,
                "readability": 0.75
            }
        }


# 직접 실행 테스트
if __name__ == "__main__":
    import asyncio
    
    pipeline = GAIMAnalysisPipeline()
    
    # 더미 데이터로 평가 테스트
    dummy_data = pipeline._get_dummy_analysis()
    evaluation = pipeline.evaluator.evaluate(dummy_data)
    
    print("=" * 60)
    print("🎓 GAIM Lab 7차원 수업 평가 결과")
    print("=" * 60)
    print(f"\n📊 총점: {evaluation.total_score}/100 ({evaluation.grade})")
    print("\n📈 차원별 점수:")
    for dim in evaluation.dimensions:
        bar = "█" * int(dim.percentage / 10) + "░" * (10 - int(dim.percentage / 10))
        print(f"  {dim.dimension:12s}: {bar} {dim.score}/{dim.max_score} ({dim.percentage}%)")
    
    print("\n✅ 강점:")
    for s in evaluation.strengths:
        print(f"  {s}")
    
    print("\n🔧 개선점:")
    for i in evaluation.improvements:
        print(f"  {i}")
    
    print(f"\n💬 종합 피드백: {evaluation.overall_feedback}")
