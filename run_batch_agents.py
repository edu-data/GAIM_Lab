"""
🤖 GAIM Lab - 멀티 에이전트 배치 분석 스크립트
18개 영상을 AgentOrchestrator 파이프라인으로 분석
"""

import sys
import io
import os
import json
import csv
import time
from pathlib import Path
from datetime import datetime

# Windows 콘솔 UTF-8
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 프로젝트 루트
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")
sys.path.insert(0, str(GAIM_ROOT))
sys.path.insert(0, str(GAIM_ROOT / "backend" / "app"))

# .env 로드
from dotenv import load_dotenv
load_dotenv(GAIM_ROOT / ".env")
print(f"✅ 환경 변수: GOOGLE_API_KEY={'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")


def load_module_from_path(module_name: str, file_path: Path):
    """특정 경로에서 모듈 직접 로드"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 오케스트레이터 직접 로드 (패키지 __init__.py 우회)
orch_module = load_module_from_path(
    "orchestrator",
    GAIM_ROOT / "core" / "agents" / "orchestrator.py"
)
AgentOrchestrator = orch_module.AgentOrchestrator


def run_single_agent_analysis(video_path: Path, output_dir: Path):
    """
    단일 영상 멀티 에이전트 분석

    Returns:
        (pipeline_result, elapsed_seconds)
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = str(output_dir / "cache")

    orch = AgentOrchestrator()

    # 실시간 로그 출력
    def on_event(event):
        etype = event["type"]
        agent = event["agent"]
        data = event.get("data", {})
        if etype == "agent_start":
            icon = orch.agents.get(agent, None)
            emoji = icon.icon if icon else "▶️"
            print(f"   {emoji} {agent} 시작...")
        elif etype == "agent_done":
            elapsed = data.get("elapsed", 0)
            print(f"   ✅ {agent} 완료 ({elapsed:.1f}s)")
        elif etype == "agent_error":
            err = data.get("error", "unknown")
            print(f"   ❌ {agent} 오류: {err[:60]}")

    orch.on_event(on_event)

    start = time.time()
    result = orch.run_pipeline(str(video_path), temp_dir=cache_dir)
    elapsed = time.time() - start

    # 결과 저장
    result_path = output_dir / "agent_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        # 직렬화 가능한 부분만 저장
        save = {
            "pipeline_id": result.get("pipeline_id"),
            "total_elapsed": result.get("total_elapsed"),
            "event_count": result.get("event_count"),
            "agents": result.get("agents", {}),
        }
        # report에서 주요 점수 추출
        report = result.get("report", {})
        if report:
            ped = report.get("pedagogy", {})
            save["pedagogy"] = ped
            save["feedback"] = report.get("feedback", {})
            save["stt"] = report.get("stt", {})
            save["vision_summary"] = report.get("vision_summary", {})
            save["content_summary"] = report.get("content_summary", {})
            save["vibe_summary"] = report.get("vibe_summary", {})
        json.dump(save, f, ensure_ascii=False, indent=2, default=str)

    return result, elapsed


def extract_scores(result: dict) -> dict:
    """파이프라인 결과에서 점수 추출"""
    report = result.get("report", {})
    ped = report.get("pedagogy", {})
    feedback = report.get("feedback", {})

    dims = ped.get("dimensions", [])

    def get_dim(name):
        for d in dims:
            if d.get("name") == name:
                return d.get("score", 0)
        return 0

    return {
        "total_score": ped.get("total_score", 0),
        "grade": ped.get("grade", "N/A"),
        "teaching_expertise": get_dim("수업 전문성"),
        "teaching_method": get_dim("교수학습 방법"),
        "communication": get_dim("판서 및 언어"),
        "teaching_attitude": get_dim("수업 태도"),
        "student_engagement": get_dim("학생 참여"),
        "time_management": get_dim("시간 배분"),
        "creativity": get_dim("창의성"),
        "strengths_count": len(feedback.get("strengths", [])),
        "improvements_count": len(feedback.get("improvements", [])),
    }


def extract_agent_times(result: dict) -> dict:
    """에이전트별 실행 시간 추출"""
    agents = result.get("agents", {})
    return {
        name: info.get("elapsed_seconds", 0)
        for name, info in agents.items()
    }


def run_batch():
    """18개 영상 멀티 에이전트 배치 분석"""
    video_dir = GAIM_ROOT / "video"
    video_files = sorted(video_dir.glob("20251209_*.mp4"))

    print("=" * 70)
    print("🤖 GAIM Lab 멀티 에이전트 배치 분석")
    print(f"📁 영상 폴더: {video_dir}")
    print(f"🎬 분석 대상: {len(video_files)}개 영상")
    print(f"🔗 파이프라인: EXTRACT → VISION+CONTENT+STT+VIBE → PEDAGOGY → FEEDBACK → MASTER")
    print("=" * 70)

    batch_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_dir = GAIM_ROOT / "output" / f"batch_agents_{batch_time}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_start = time.time()

    for idx, vp in enumerate(video_files, 1):
        print(f"\n{'=' * 70}")
        print(f"📹 [{idx}/{len(video_files)}] {vp.name}")
        print("=" * 70)

        output_dir = batch_dir / vp.stem

        try:
            result, elapsed = run_single_agent_analysis(vp, output_dir)
            scores = extract_scores(result)
            agent_times = extract_agent_times(result)

            entry = {
                "video": vp.name,
                **scores,
                "analysis_time": round(elapsed, 1),
                "pipeline_id": result.get("pipeline_id", ""),
                "agent_times": agent_times,
                "status": "success",
            }
            results.append(entry)

            score = scores["total_score"]
            grade = scores["grade"]
            print(f"\n🏆 결과: {score:.1f}점 ({grade}) | ⏱️ {elapsed:.1f}초")
            print(f"   강점 {scores['strengths_count']}개 / 개선점 {scores['improvements_count']}개")

        except Exception as e:
            elapsed = time.time() - (total_start if idx == 1 else time.time())
            results.append({
                "video": vp.name,
                "total_score": 0,
                "grade": "ERROR",
                "teaching_expertise": 0, "teaching_method": 0,
                "communication": 0, "teaching_attitude": 0,
                "student_engagement": 0, "time_management": 0,
                "creativity": 0,
                "strengths_count": 0, "improvements_count": 0,
                "analysis_time": 0,
                "pipeline_id": "",
                "agent_times": {},
                "status": f"error: {str(e)[:100]}",
            })
            print(f"❌ 오류: {e}")

    total_elapsed = time.time() - total_start

    # ============================================================
    # CSV 요약 저장
    # ============================================================
    csv_path = batch_dir / "agent_batch_summary.csv"
    fieldnames = [
        "video", "total_score", "grade",
        "teaching_expertise", "teaching_method", "communication",
        "teaching_attitude", "student_engagement", "time_management",
        "creativity", "strengths_count", "improvements_count",
        "analysis_time", "status"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    # ============================================================
    # JSON 전체 결과 저장
    # ============================================================
    json_path = batch_dir / "agent_batch_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "batch_time": batch_time,
            "total_videos": len(video_files),
            "total_time_seconds": round(total_elapsed, 1),
            "total_time_minutes": round(total_elapsed / 60, 1),
            "pipeline": "AgentOrchestrator (v4.0)",
            "agents": ["extractor", "vision", "content", "stt", "vibe", "pedagogy", "feedback", "master"],
            "results": results,
        }, f, ensure_ascii=False, indent=2, default=str)

    # ============================================================
    # 결과 요약 출력
    # ============================================================
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]

    print("\n" + "=" * 70)
    print("📊 멀티 에이전트 배치 분석 완료!")
    print("=" * 70)

    if successful:
        scores = [r["total_score"] for r in successful]
        avg = sum(scores) / len(scores)
        times = [r["analysis_time"] for r in successful]
        avg_time = sum(times) / len(times)

        print(f"\n📈 통계:")
        print(f"   ✅ 성공: {len(successful)}/{len(video_files)}개")
        print(f"   ❌ 실패: {len(failed)}/{len(video_files)}개")
        print(f"   📊 평균 점수: {avg:.1f}점")
        print(f"   🔝 최고 점수: {max(scores):.1f}점")
        print(f"   🔻 최저 점수: {min(scores):.1f}점")
        print(f"   ⏱️ 평균 분석 시간: {avg_time:.1f}초")
        print(f"   ⏱️ 총 소요 시간: {total_elapsed/60:.1f}분")

        # 등급 분포
        from collections import Counter
        grade_dist = Counter(r["grade"] for r in successful)
        print(f"\n📋 등급 분포:")
        for grade in ["S", "A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if grade in grade_dist:
                bar = "█" * grade_dist[grade]
                print(f"   {grade:>3}: {bar} ({grade_dist[grade]})")

        # 에이전트별 평균 시간
        agent_names = ["extractor", "vision", "content", "stt", "vibe", "pedagogy", "feedback", "master"]
        print(f"\n🤖 에이전트별 평균 처리 시간:")
        for aname in agent_names:
            at = [r["agent_times"].get(aname, 0) for r in successful if r.get("agent_times")]
            if at:
                avg_at = sum(at) / len(at)
                print(f"   {aname:>12}: {avg_at:.1f}초")

    print(f"\n📋 개별 결과:")
    for r in results:
        icon = "✅" if r["status"] == "success" else "❌"
        print(f"   {icon} {r['video']}: {r['total_score']:.1f}점 ({r['grade']}) [{r['analysis_time']:.0f}s]")

    print(f"\n📂 출력: {batch_dir}")
    print(f"   - CSV: {csv_path.name}")
    print(f"   - JSON: {json_path.name}")

    return results, str(batch_dir)


if __name__ == "__main__":
    run_batch()
