"""
GAIM Lab - 용량 최대 영상 재분석 (검사-재검사 신뢰도용)
20251209_110545.mp4 2차 분석
"""

import sys
import io
import os
import json
import importlib.util
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent

env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")

print(f"✅ GOOGLE_API_KEY: {'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")


def load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


timelapse_module = load_module_from_path(
    "timelapse_analyzer",
    PROJECT_ROOT / "core" / "analyzers" / "timelapse_analyzer.py"
)
TimeLapseAnalyzer = timelapse_module.TimeLapseAnalyzer

sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))
from core.evaluator import GAIMLectureEvaluator
from services.report_generator import GAIMReportGenerator


def analyze_single(video_path: Path, output_dir: Path):
    """단일 영상 분석"""
    video_name = video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()

    # Phase 1: TimeLapse 분석
    print(f"\n🔍 [Phase 1/3] 영상 분석 중...")
    analyzer = TimeLapseAnalyzer(temp_dir=str(output_dir / "cache"))
    vision_results, content_results = analyzer.analyze_video(video_path)
    audio_metrics = analyzer.get_audio_metrics()
    elapsed = analyzer.get_elapsed_time()
    print(f"   ✅ 비전 {len(vision_results)}프레임, 처리시간 {elapsed:.1f}s")

    # Phase 1.5: Whisper STT
    transcript = ""
    audio_path = output_dir / "audio.wav"
    try:
        import subprocess
        cmd = ['ffmpeg', '-i', str(video_path), '-ar', '16000', '-ac', '1', str(audio_path), '-loglevel', 'error', '-y']
        subprocess.run(cmd, check=True, capture_output=True)

        text_module = load_module_from_path("text_analyzer", PROJECT_ROOT / "core" / "analyzers" / "text_analyzer.py")
        transcript, segments = text_module.transcribe_audio(str(audio_path), model_size="small")
        if transcript:
            print(f"   🎤 STT 완료: {len(transcript)}자")
            (output_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    except Exception as e:
        print(f"   ⚠️ STT 스킵: {e}")

    # Phase 2: 7차원 평가
    print(f"\n📊 [Phase 2/3] 7차원 평가 중...")
    total_frames = len(vision_results) if vision_results else 0
    eye_ratio = sum(1 for r in vision_results if r.get("face_visible", False)) / total_frames if total_frames > 0 else 0
    gesture_ratio = sum(1 for r in vision_results if r.get("gesture_active", False)) / total_frames if total_frames > 0 else 0
    text_densities = [r.get("text_density", 0) for r in (content_results or []) if r.get("text_density")]

    analysis_data = {
        "vision_metrics": {"eye_contact_ratio": eye_ratio, "gesture_ratio": gesture_ratio, "frame_count": total_frames},
        "vibe_metrics": audio_metrics,
        "content_metrics": {"slide_changes": len(content_results or []), "avg_text_density": sum(text_densities) / len(text_densities) if text_densities else 0},
        "text_metrics": {},
        "transcript": transcript,
    }

    evaluator = GAIMLectureEvaluator()
    evaluation_result = evaluator.evaluate(analysis_data)
    evaluation_dict = evaluator.to_dict(evaluation_result)

    result_path = output_dir / "evaluation_result.json"
    result_path.write_text(json.dumps(evaluation_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✅ 평가 완료: {evaluation_dict.get('total_score', 0)}점 ({evaluation_dict.get('grade', 'N/A')})")

    # Phase 3: 리포트 생성
    print(f"\n📋 [Phase 3/3] HTML 리포트 생성 중...")
    try:
        gen = GAIMReportGenerator(output_dir=output_dir)
        gen.generate_html_report(evaluation_dict, video_name)
        print(f"   ✅ HTML 리포트 생성 완료")
    except Exception as e:
        print(f"   ⚠️ 리포트 생성 스킵: {e}")

    total_elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("✅ 2차 분석 완료!")
    print("=" * 60)
    print(f"📁 영상: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"⏱️ 총 소요: {total_elapsed:.1f}초")
    print(f"📊 총점: {evaluation_dict.get('total_score', 0)} / 100점")
    print(f"📊 등급: {evaluation_dict.get('grade', 'N/A')}")

    print(f"\n📈 차원별 점수:")
    for dim in evaluation_dict.get("dimensions", []):
        name = dim.get("name", "")
        score = dim.get("score", 0)
        max_score = dim.get("max_score", 20)
        pct = dim.get("percentage", 0)
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"   {name}: {score}/{max_score} [{bar}] {pct:.0f}%")

    # 2차 결과 저장
    root_result_path = PROJECT_ROOT / "test_largest_result_retest.json"
    root_result_path.write_text(json.dumps(evaluation_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 2차 결과 파일: {root_result_path}")

    return evaluation_dict


if __name__ == "__main__":
    video = PROJECT_ROOT / "video" / "20251209_110545.mp4"

    if not video.exists():
        print(f"❌ 영상을 찾을 수 없습니다: {video}")
        sys.exit(1)

    print("=" * 60)
    print(f"🧪 GAIM Lab - 용량 최대 영상 2차 분석 (재검사)")
    print(f"📁 영상: {video.name} ({video.stat().st_size / 1024 / 1024:.1f} MB)")
    print("=" * 60)

    analyze_single(video, PROJECT_ROOT / "output" / "largest_video_retest")
