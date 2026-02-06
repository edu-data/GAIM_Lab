"""
GAIM Lab - 샘플 영상 분석 스크립트
TimeLapseAnalyzer + GAIMLectureEvaluator + GAIMReportGenerator 통합 실행
"""

import sys
import io
import json
import importlib.util
from pathlib import Path
from datetime import datetime

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")

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
from core.evaluator import GAIMLectureEvaluator
from services.report_generator import GAIMReportGenerator


def run_sample_analysis(video_path: str, output_dir: str = None):
    """
    샘플 영상 분석 실행
    
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
        output_dir = Path("D:/AI/GAIM_Lab/output") / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"🎬 GAIM Lab 영상 분석 시작")
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
    
    # FFmpeg으로 오디오 직접 추출
    print(f"\n🎤 [Phase 1.5/3] 음성 인식 (Whisper STT) 중...")
    try:
        import subprocess
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-ar', '16000', '-ac', '1',
            str(audio_path),
            '-loglevel', 'error', '-y'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ 오디오 추출 완료: {audio_path.name}")
        
        # Whisper STT 실행
        text_analyzer_module = load_module_from_path(
            "text_analyzer", 
            GAIM_ROOT / "core" / "analyzers" / "text_analyzer.py"
        )
        transcribe_audio = text_analyzer_module.transcribe_audio
        transcript, segments = transcribe_audio(str(audio_path), model_size="small")
        if transcript:
            print(f"   ✅ 텍스트 변환 완료: {len(transcript)}자")
            # 텍스트 저장
            transcript_path = output_dir / "transcript.txt"
            with transcript_path.open("w", encoding="utf-8") as f:
                f.write(transcript)
    except ImportError as ie:
        print(f"   [!] openai-whisper 미설치 - STT 건너뜀: {ie}")
    except Exception as e:
        import traceback
        print(f"   [!] STT 오류: {e}")
        traceback.print_exc()
    
    # =================================================================
    # Phase 2: 7차원 평가 (GAIMLectureEvaluator + Gemini)
    # =================================================================
    print("\n📊 [Phase 2/3] 7차원 평가 수행 중...")
    
    # 분석 데이터 구성 (transcript 포함)
    analysis_data = {
        "vision_metrics": _extract_vision_metrics(vision_results),
        "vibe_metrics": audio_metrics,
        "content_metrics": _extract_content_metrics(content_results),
        "text_metrics": {},
        "transcript": transcript  # Gemini 평가용
    }
    
    evaluator = GAIMLectureEvaluator()
    evaluation_result = evaluator.evaluate(analysis_data)
    evaluation_dict = evaluator.to_dict(evaluation_result)
    
    print(f"   - 총점: {evaluation_result.total_score:.1f} / 100")
    print(f"   - 등급: {evaluation_result.grade}")
    
    # 결과 저장
    result_path = output_dir / "evaluation_result.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(evaluation_dict, f, ensure_ascii=False, indent=2)
    print(f"   - 결과 저장: {result_path.name}")
    
    # =================================================================
    # Phase 3: 리포트 생성
    # =================================================================
    print("\n📋 [Phase 3/3] HTML/PDF 리포트 생성 중...")
    
    report_generator = GAIMReportGenerator(output_dir=output_dir)
    html_path_str = report_generator.generate_html_report(evaluation_dict, video_name)
    html_path = Path(html_path_str)
    
    print(f"   - HTML 리포트: {html_path.name}")
    
    # PDF 생성 시도 (Playwright 필요)
    try:
        pdf_path_str = report_generator.generate_pdf_report(evaluation_dict, video_name)
        pdf_path = Path(pdf_path_str)
        print(f"   - PDF 리포트: {pdf_path.name}")
    except Exception as e:
        print(f"   - PDF 생성 스킵 (Playwright 미설치): {e}")
        pdf_path = None
    
    # =================================================================
    # 최종 결과 출력
    # =================================================================
    print("\n" + "=" * 60)
    print("✅ 분석 완료!")
    print("=" * 60)
    print(f"\n📊 7차원 평가 결과:")
    print(f"   총점: {evaluation_result.total_score:.1f} / 100점")
    print(f"   등급: {evaluation_result.grade}")
    print(f"\n📈 차원별 점수:")
    for dim in evaluation_result.dimensions:
        bar = "█" * int(dim.percentage / 10) + "░" * (10 - int(dim.percentage / 10))
        print(f"   {dim.dimension}: {dim.score:.1f}/{dim.max_score} [{bar}] {dim.percentage:.0f}%")
    
    print(f"\n✅ 강점:")
    for s in evaluation_result.strengths[:3]:
        print(f"   - {s}")
        
    print(f"\n🔧 개선점:")
    for i in evaluation_result.improvements[:3]:
        print(f"   - {i}")
    
    print(f"\n💬 종합 피드백:")
    print(f"   {evaluation_result.overall_feedback}")
    
    print(f"\n📂 출력 디렉토리: {output_dir}")
    
    return evaluation_dict, html_path


def _extract_vision_metrics(vision_results):
    """비전 분석 결과에서 메트릭 추출"""
    if not vision_results:
        return {}
        
    total = len(vision_results)
    eye_contact_count = sum(1 for r in vision_results if r.get("face_visible", False))
    gesture_count = sum(1 for r in vision_results if r.get("gesture_active", False))
    
    return {
        "eye_contact_ratio": eye_contact_count / total if total > 0 else 0,
        "gesture_ratio": gesture_count / total if total > 0 else 0,
        "frame_count": total
    }


def _extract_content_metrics(content_results):
    """콘텐츠 분석 결과에서 메트릭 추출"""
    if not content_results:
        return {}
        
    # 슬라이드 변화 수, 텍스트 밀도 평균 등
    text_densities = [r.get("text_density", 0) for r in content_results if r.get("text_density")]
    
    return {
        "slide_changes": len(content_results),
        "avg_text_density": sum(text_densities) / len(text_densities) if text_densities else 0
    }


if __name__ == "__main__":
    # 가장 작은 영상 파일 선택
    video = Path(r"D:\AI\GAIM_Lab\video\20251209_142648.mp4")
    
    if len(sys.argv) > 1:
        video = Path(sys.argv[1])
    
    run_sample_analysis(str(video))
