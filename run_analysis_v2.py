"""
GAIM Lab - RAG 연동 영상 분석 스크립트 V2
EnhancedGeminiEvaluator (RAG) + GAIMReportGeneratorV2 통합 실행
"""

import sys
import io
import json
import os
import importlib.util
from pathlib import Path
from datetime import datetime

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(GAIM_ROOT / ".env")
print(f"✅ 환경 변수 로드: GOOGLE_API_KEY={'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")

def load_module_from_path(module_name: str, file_path: Path):
    """특정 경로에서 모듈 로드"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 모듈 직접 로드
timelapse_module = load_module_from_path(
    "timelapse_analyzer", 
    GAIM_ROOT / "core" / "analyzers" / "timelapse_analyzer.py"
)
TimeLapseAnalyzer = timelapse_module.TimeLapseAnalyzer

# backend/app 경로를 sys.path에 추가
sys.path.insert(0, str(GAIM_ROOT / "backend" / "app"))

# ====================================================================
# V2: Enhanced Evaluator (RAG 포함) + Report Generator V2
# ====================================================================
from core.enhanced_gemini_evaluator import EnhancedGeminiEvaluator
from services.report_generator_v2 import GAIMReportGeneratorV2


def run_analysis_v2(video_path: str, output_dir: str = None):
    """
    RAG 연동 영상 분석 실행 (V2)
    
    Args:
        video_path: 분석할 영상 파일 경로
        output_dir: 출력 디렉토리 (None이면 자동 생성)
        
    Returns:
        (evaluation_result, report_path) 튜플
    """
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ 영상 파일을 찾을 수 없습니다: {video_path}")
        return None, None
        
    video_name = video_path.stem
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path("D:/AI/GAIM_Lab/output") / f"analysis_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"🧪 GAIM Lab RAG 연동 분석 V2")
    print(f"📁 영상: {video_path.name}")
    print(f"📂 출력: {output_dir}")
    print("=" * 60)
    
    # =================================================================
    # Phase 1: TimeLapse 분석 (비전 + 오디오)
    # =================================================================
    print("\n🔍 [Phase 1/3] 영상 분석 중...")
    
    analyzer = TimeLapseAnalyzer(temp_dir=str(output_dir / "cache"))
    vision_results, content_results = analyzer.analyze_video(video_path)
    
    audio_metrics = analyzer.get_audio_metrics()
    audio_timeline = analyzer.get_audio_timeline()
    elapsed_time = analyzer.get_elapsed_time()
    
    print(f"   - 처리 시간: {elapsed_time:.1f}초")
    print(f"   - 비전 프레임: {len(vision_results)}개")
    print(f"   - 오디오 세그먼트: {len(audio_timeline)}개")
    
    # =================================================================
    # Phase 1.5: 음성 → 텍스트 변환 (Whisper STT)
    # =================================================================
    transcript = ""
    audio_path = output_dir / "audio.wav"
    
    print(f"\n🎤 [Phase 1.5/3] 음성 인식 (Whisper STT) 중...")
    try:
        import subprocess
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-ar', '16000', '-ac', '1',
            str(audio_path),
            '-y', '-loglevel', 'quiet'
        ]
        subprocess.run(cmd, check=True)
        print(f"   ✅ 오디오 추출 완료: {audio_path.name}")
        
        # Whisper로 음성 인식
        import whisper
        print(f"📝 [STT] Whisper 모델 로딩... (small)")
        model = whisper.load_model("small")
        print(f"   언어: ko")
        print(f"   🎙️ 음성 인식 중...")
        result = model.transcribe(str(audio_path), language="ko")
        
        # 세그먼트 추출
        segments = result.get("segments", [])
        transcript = result.get("text", "")
        
        print(f"   ✅ STT 완료: {len(segments)}개 세그먼트, {len(transcript)}자")
        print(f"   ✅ 텍스트 변환 완료: {len(transcript)}자")
        
    except Exception as e:
        print(f"   ⚠️ STT 오류: {e}")
    
    # =================================================================
    # Phase 2: Enhanced Gemini 평가 (RAG 포함!)
    # =================================================================
    print("\n📊 [Phase 2/3] RAG 연동 7차원 평가 수행 중...")
    
    # Enhanced Evaluator 초기화 (RAG 자동 활성화)
    evaluator = EnhancedGeminiEvaluator()
    
    # RAG 상태 확인
    if evaluator.knowledge_base and evaluator.knowledge_base.is_initialized:
        print(f"   ✅ RAG 활성화됨: {evaluator.knowledge_base.chunk_count}개 청크")
    else:
        print("   ⚠️ RAG 비활성화 (지식 기반 없음)")
    
    # 프레임 디렉토리 경로
    frames_dir = output_dir / "cache" / "frames"
    
    # 통합 데이터 준비
    analysis_data = {
        "video_info": {
            "name": video_name,
            "path": str(video_path),
            "duration": elapsed_time
        },
        "vision_analysis": vision_results,
        "audio_analysis": {
            "metrics": audio_metrics,
            "timeline": audio_timeline
        },
        "transcript": transcript,
        "segments": segments if 'segments' in dir() else []
    }
    
    # RAG 강화 평가 실행 - evaluate_with_frames 사용
    raw_result = evaluator.evaluate_with_frames(
        transcript=transcript,
        frames_dir=frames_dir if frames_dir.exists() else None
    )
    
    # 표준 형식으로 변환
    evaluation_result = evaluator.get_dimension_scores(raw_result) if raw_result else {
        "total_score": 0, "grade": "F", "dimensions": {}
    }
    
    print(f"   - 총점: {evaluation_result.get('total_score', 0):.1f} / 100")
    print(f"   - 등급: {evaluation_result.get('grade', 'N/A')}")
    
    # RAG 이론 참조 정보 출력
    has_theory = False
    for dim, data in evaluation_result.get("dimensions", {}).items():
        if data.get("theory_references"):
            has_theory = True
            break
    
    if has_theory:
        print(f"   📖 교육학 이론 참조 포함됨!")
    
    # 결과 저장
    result_path = output_dir / "evaluation_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
    print(f"   - 결과 저장: {result_path.name}")
    
    # =================================================================
    # Phase 3: Report Generator V2 (이론 참조 표시)
    # =================================================================
    print("\n📋 [Phase 3/3] HTML/PDF 리포트 생성 중 (V2)...")
    
    generator = GAIMReportGeneratorV2()
    
    # HTML 리포트 생성
    html_path = output_dir / f"gaim_report_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generator.generate_html_report(evaluation_result, str(html_path))
    print(f"   - HTML 리포트: {html_path.name}")
    
    # PDF 리포트 생성 시도
    try:
        pdf_path = html_path.with_suffix('.pdf')
        generator.generate_pdf_report(evaluation_result, str(pdf_path))
        print(f"   - PDF 리포트: {pdf_path.name}")
    except Exception as e:
        print(f"   - PDF 생성 스킵: {e}")
    
    # =================================================================
    # 결과 출력
    # =================================================================
    print("\n" + "=" * 60)
    print("✅ RAG 연동 분석 완료!")
    print("=" * 60)
    
    print(f"\n📊 7차원 평가 결과:")
    print(f"   총점: {evaluation_result['total_score']:.1f} / 100점")
    print(f"   등급: {evaluation_result['grade']}")
    
    print(f"\n📈 차원별 점수:")
    dimension_names = {
        "teaching_expertise": "수업 전문성",
        "teaching_method": "교수학습 방법",
        "communication": "판서 및 언어",
        "teaching_attitude": "수업 태도",
        "student_engagement": "학생 참여",
        "time_management": "시간 배분",
        "creativity": "창의성"
    }
    
    for dim_key, dim_name in dimension_names.items():
        dim_data = evaluation_result.get("dimensions", {}).get(dim_key, {})
        score = dim_data.get("score", 0)
        max_score = dim_data.get("max_score", 20)
        pct = (score / max_score * 100) if max_score > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        theory_mark = " 📖" if dim_data.get("theory_references") else ""
        print(f"   {dim_name}: {score:.1f}/{max_score} [{bar}] {pct:.0f}%{theory_mark}")
    
    print(f"\n📂 출력 디렉토리: {output_dir}")
    
    return evaluation_result, str(html_path)


if __name__ == "__main__":
    # 기본 테스트 영상
    default_video = GAIM_ROOT / "video" / "youtube_demo.mp4"
    
    if len(sys.argv) > 1:
        video = Path(sys.argv[1])
        if not video.is_absolute():
            video = GAIM_ROOT / video
    else:
        video = default_video
    
    if not video.exists():
        print(f"❌ 영상을 찾을 수 없습니다: {video}")
        sys.exit(1)
    
    run_analysis_v2(str(video))
