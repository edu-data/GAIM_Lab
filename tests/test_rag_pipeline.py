"""
GAIM Lab - RAG 통합 테스트 스크립트
enhanced_gemini_evaluator + rag_knowledge_base + report_generator_v2 파이프라인 검증
"""

import sys
import os
import io
import json
from pathlib import Path

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 환경 변수 로드
env_path = Path("D:/AI/GAIM_Lab/.env")
if env_path.exists():
    with env_path.open() as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# 경로 설정
sys.path.insert(0, str(Path("D:/AI/GAIM_Lab/backend/app")))

from core.enhanced_gemini_evaluator import EnhancedGeminiEvaluator
from services.report_generator_v2 import GAIMReportGeneratorV2


def test_rag_pipeline():
    """RAG 파이프라인 통합 테스트"""
    
    print("=" * 60)
    print("🧪 GAIM Lab RAG 통합 테스트")
    print("=" * 60)
    
    # 1. 평가기 초기화 (RAG 포함)
    print("\n[1/3] Enhanced Evaluator 초기화 (RAG 포함)...")
    evaluator = EnhancedGeminiEvaluator(enable_rag=True)
    
    if not evaluator.model:
        print("❌ Gemini 모델 초기화 실패. GOOGLE_API_KEY 확인 필요.")
        return False
    
    rag_status = "✅ 활성화" if evaluator.knowledge_base and evaluator.knowledge_base.is_initialized else "❌ 비활성화"
    print(f"   RAG 상태: {rag_status}")
    
    # 2. 샘플 수업 텍스트로 평가
    print("\n[2/3] 샘플 수업 평가 중...")
    
    sample_transcript = """
    여러분, 오늘 수업의 주제는 지구촌 문제입니다.
    먼저 이 사진을 보세요. 어떤 문제가 보이나요?
    네, 맞아요. 기아 문제입니다.
    그럼 우리가 할 수 있는 일은 무엇일까요?
    모둠별로 토의해보세요.
    지금부터 5분간 모둠 토의를 시작하겠습니다.
    토의가 끝나면 각 모둠별로 발표해주세요.
    네, 1모둠 먼저 발표해볼까요?
    좋은 의견이에요. 기부와 봉사가 중요하다고 했네요.
    다른 모둠 의견도 들어볼까요?
    """
    
    result = evaluator.evaluate_with_frames(sample_transcript)
    
    if not result:
        print("❌ 평가 실패")
        return False
    
    # 3. 차원별 점수 변환 (RAG 강화 포함)
    print("\n[3/3] 결과 변환 및 RAG 강화...")
    scores = evaluator.get_dimension_scores(result)
    
    print(f"\n📊 평가 결과:")
    print(f"   총점: {scores.get('total_score', 0)}/100")
    print(f"   등급: {scores.get('grade', 'N/A')}")
    
    # RAG 강화 확인
    rag_enhanced = False
    for dim in scores.get("dimensions", []):
        theory_refs = dim.get("theory_references", [])
        tips = dim.get("improvement_tips", [])
        
        if theory_refs or tips:
            rag_enhanced = True
            print(f"\n   📚 {dim['name']}: {dim['percentage']}%")
            if theory_refs:
                print(f"      📖 이론: {theory_refs[0][:50]}...")
            if tips:
                print(f"      💡 팁: {tips[0] if tips else 'N/A'}")
    
    if rag_enhanced:
        print("\n✅ RAG 기반 피드백 강화 성공!")
    else:
        print("\n⚠️ RAG 피드백 없음 (knowledge base 확인 필요)")
    
    # 4. V2 리포트 생성
    print("\n[4/4] V2 리포트 생성...")
    output_dir = Path("D:/AI/GAIM_Lab/output/rag_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = GAIMReportGeneratorV2(output_dir=output_dir)
    report_path = generator.generate_html_report(scores, "RAG_테스트_수업")
    
    print(f"   📄 리포트: {report_path}")
    
    print("\n" + "=" * 60)
    print("✅ RAG 통합 테스트 완료!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_rag_pipeline()
