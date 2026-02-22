"""
GAIM Lab - 18개 영상 배치 분석
run_sample_analysis 호출을 통한 순차 분석
"""

import sys
import io
import os
import json
import csv
import importlib.util
from pathlib import Path
from datetime import datetime

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent

# .env 로드
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        # 수동 로드
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")

print(f"✅ GOOGLE_API_KEY: {'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")

# run_sample_analysis를 scripts/ 에서 직접 로드
def load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# run_sample_analysis 모듈 로드 — 이 모듈 내에서 GAIM_ROOT가 scripts/ 로 설정되어 있음
# 따라서 scripts/ 경로가 올바르게 해석되도록 해야 함
# 대신 직접 분석 파이프라인을 구성합니다
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
    
    # Phase 1: TimeLapse 분석
    print(f"   🔍 Phase 1: 영상 분석...")
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
    print(f"   📊 Phase 2: 평가 중...")
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
    
    (output_dir / "evaluation_result.json").write_text(json.dumps(evaluation_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Phase 3: 리포트
    try:
        gen = GAIMReportGenerator(output_dir=output_dir)
        gen.generate_html_report(evaluation_dict, video_name)
    except Exception as e:
        print(f"   ⚠️ 리포트 생성 스킵: {e}")
    
    return evaluation_dict


def batch_analyze():
    """18개 영상 배치 분석"""
    video_dir = PROJECT_ROOT / "video"
    output_base = PROJECT_ROOT / "output" / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_base.mkdir(parents=True, exist_ok=True)

    videos = sorted([f for f in video_dir.glob("*.mp4") if "youtube" not in f.name.lower()])

    print("=" * 70)
    print(f"🎬 GAIM Lab 배치 분석 시작")
    print(f"📁 영상 수: {len(videos)}개")
    print(f"📂 출력: {output_base}")
    print("=" * 70)

    results = []
    start_time = datetime.now()

    for i, video in enumerate(videos, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(videos)}] {video.name}")
        print("=" * 70)

        try:
            video_output = output_base / video.stem
            result = analyze_single(video, video_output)

            if result:
                total_score = result.get("total_score", 0)
                grade = result.get("grade", "N/A")
                dims = {d.get("name", ""): d.get("score", 0) for d in result.get("dimensions", [])}

                results.append({
                    "video": video.name,
                    "total_score": total_score,
                    "grade": grade,
                    "dim1_professionalism": dims.get("수업 전문성", 0),
                    "dim2_teaching_method": dims.get("교수학습 방법", 0),
                    "dim3_language": dims.get("판서 및 언어", 0),
                    "dim4_attitude": dims.get("수업 태도", 0),
                    "dim5_participation": dims.get("학생 참여", 0),
                    "dim6_time": dims.get("시간 배분", 0),
                    "dim7_creativity": dims.get("창의성", 0),
                    "status": "success"
                })
                print(f"   🎯 {total_score}점 ({grade})")
            else:
                results.append({"video": video.name, "total_score": 0, "grade": "N/A", "status": "no_result"})

        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({"video": video.name, "total_score": 0, "grade": "ERROR", "status": f"error: {str(e)}"})
            print(f"   ❌ {e}")

    # 저장
    csv_path = output_base / "batch_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    json_path = output_base / "batch_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 요약
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("📊 배치 분석 완료!")
    print("=" * 70)
    print(f"⏱️ 총 소요: {elapsed}")

    ok = [r for r in results if r.get("status") == "success"]
    if ok:
        scores = [r["total_score"] for r in ok]
        print(f"\n✅ 성공: {len(ok)}/{len(results)}개")
        print(f"📈 평균: {sum(scores)/len(scores):.1f}점  최고: {max(scores):.1f}  최저: {min(scores):.1f}")

        grades = {}
        for r in ok:
            g = r["grade"]
            grades[g] = grades.get(g, 0) + 1
        print("\n📊 등급 분포:")
        for gl in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if gl in grades:
                print(f"   {gl}: {'█' * grades[gl]} ({grades[gl]}개)")

    fail = [r for r in results if r.get("status") != "success"]
    if fail:
        print(f"\n❌ 실패: {len(fail)}개")
        for r in fail:
            print(f"   - {r['video']}: {r['status']}")

    print(f"\n📂 CSV: {csv_path}")
    print(f"📂 JSON: {json_path}")
    return results


if __name__ == "__main__":
    batch_analyze()
