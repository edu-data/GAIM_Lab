"""
🔄 교차 분석 (Cross-Analysis) — 검사-재검사 신뢰도 검증
같은 영상을 2회 분석하여 결과 일치도를 확인한다.

사용법:
  python cross_analysis.py [video1.mp4] [video2.mp4]
  기본값: video/ 폴더의 처음 2개 영상
"""

import sys
import json
import csv
import time
import math
from pathlib import Path
from datetime import datetime

GAIM_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(GAIM_ROOT))

from dotenv import load_dotenv
load_dotenv(GAIM_ROOT / ".env")

import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

orch_module = load_module_from_path(
    "orchestrator", GAIM_ROOT / "core" / "agents" / "orchestrator.py"
)
AgentOrchestrator = orch_module.AgentOrchestrator


def run_analysis(video_path: Path, output_dir: Path):
    """단일 분석 실행"""
    orch = AgentOrchestrator()
    cache_dir = str(output_dir / "cache")
    result = orch.run_pipeline(str(video_path), temp_dir=cache_dir)
    # 결과 저장
    result_file = output_dir / "agent_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    return result


def extract_scores(result):
    """결과에서 차원별 점수 추출"""
    report = result.get("report", {})
    ped = report.get("pedagogy", {})
    dims = ped.get("dimensions", [])

    scores = {}
    for d in dims:
        scores[d["name"]] = d["score"]
    scores["total"] = ped.get("total_score", 0)
    scores["grade"] = ped.get("grade", "")
    return scores


def compute_agreement(scores1, scores2):
    """두 분석 결과의 일치도 계산"""
    dims = [k for k in scores1 if k not in ("grade",)]

    results = []
    for dim in dims:
        s1 = scores1.get(dim, 0)
        s2 = scores2.get(dim, 0)
        diff = abs(s1 - s2)
        results.append({
            "dimension": dim,
            "run1": s1,
            "run2": s2,
            "abs_diff": round(diff, 1),
            "match": "✅" if diff < 1.5 else "⚠️",
        })

    # Pearson r
    values1 = [scores1.get(d, 0) for d in dims]
    values2 = [scores2.get(d, 0) for d in dims]

    n = len(values1)
    mean1 = sum(values1) / n
    mean2 = sum(values2) / n
    cov = sum((a - mean1) * (b - mean2) for a, b in zip(values1, values2)) / n
    std1 = math.sqrt(sum((a - mean1) ** 2 for a in values1) / n)
    std2 = math.sqrt(sum((b - mean2) ** 2 for b in values2) / n)
    pearson_r = cov / (std1 * std2) if std1 > 0 and std2 > 0 else 0.0

    return results, pearson_r


def main():
    # 영상 선택
    video_dir = GAIM_ROOT / "video"
    if len(sys.argv) > 1:
        videos = [Path(v) for v in sys.argv[1:]]
    else:
        videos = sorted(video_dir.glob("*.mp4"))[:2]

    if not videos:
        print("❌ 분석할 영상이 없습니다.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = GAIM_ROOT / "output" / f"cross_analysis_{timestamp}"
    output_base.mkdir(parents=True, exist_ok=True)

    all_results = []

    for video in videos:
        print(f"\n{'='*60}")
        print(f"📹 영상: {video.name}")
        print(f"{'='*60}")

        # Run 1
        out1 = output_base / video.stem / "run1"
        out1.mkdir(parents=True, exist_ok=True)
        print(f"\n🔄 Run 1 시작...")
        t1_start = time.time()
        result1 = run_analysis(video, out1)
        t1 = time.time() - t1_start
        scores1 = extract_scores(result1)
        print(f"  ✅ Run 1 완료: {scores1.get('total', 0)}점 ({scores1.get('grade', '')}) [{t1:.0f}s]")

        # Run 2
        out2 = output_base / video.stem / "run2"
        out2.mkdir(parents=True, exist_ok=True)
        print(f"\n🔄 Run 2 시작...")
        t2_start = time.time()
        result2 = run_analysis(video, out2)
        t2 = time.time() - t2_start
        scores2 = extract_scores(result2)
        print(f"  ✅ Run 2 완료: {scores2.get('total', 0)}점 ({scores2.get('grade', '')}) [{t2:.0f}s]")

        # 일치도 분석
        agreement, pearson_r = compute_agreement(scores1, scores2)

        print(f"\n📊 일치도 분석:")
        print(f"  {'차원':<15s} {'Run1':>8s} {'Run2':>8s} {'차이':>8s} {'판정':>5s}")
        print(f"  {'-'*45}")
        for a in agreement:
            print(f"  {a['dimension']:<15s} {a['run1']:>8.1f} {a['run2']:>8.1f} {a['abs_diff']:>8.1f} {a['match']:>5s}")

        total_diff = abs(scores1.get("total", 0) - scores2.get("total", 0))
        max_dim_diff = max(a["abs_diff"] for a in agreement)
        print(f"\n  총점 차이: {total_diff:.1f}pt (목표: < 2.0)")
        print(f"  차원별 최대 차이: {max_dim_diff:.1f}pt (목표: < 1.5)")
        print(f"  Pearson r: {pearson_r:.4f} (목표: > 0.95)")
        print(f"  등급 일치: {scores1.get('grade')} vs {scores2.get('grade')} {'✅' if scores1.get('grade') == scores2.get('grade') else '⚠️'}")

        # Diarization method
        stt1 = result1.get("report", {}).get("stt", {})
        stt2 = result2.get("report", {}).get("stt", {})
        print(f"  화자분리 방법: Run1={stt1.get('diarization_method', 'N/A')}, Run2={stt2.get('diarization_method', 'N/A')}")

        all_results.append({
            "video": video.name,
            "run1_total": scores1.get("total", 0),
            "run2_total": scores2.get("total", 0),
            "total_diff": total_diff,
            "max_dim_diff": max_dim_diff,
            "pearson_r": pearson_r,
            "grade_match": scores1.get("grade") == scores2.get("grade"),
        })

    # 요약 CSV
    csv_path = output_base / "cross_analysis_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["video", "run1_total", "run2_total",
                                                "total_diff", "max_dim_diff", "pearson_r", "grade_match"])
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n{'='*60}")
    print(f"📊 교차 분석 최종 요약")
    print(f"{'='*60}")
    for r in all_results:
        status = "✅ PASS" if r["total_diff"] < 2.0 and r["pearson_r"] > 0.95 else "⚠️ CHECK"
        print(f"  {r['video']}: 차이={r['total_diff']:.1f}pt, r={r['pearson_r']:.4f} → {status}")
    print(f"\n📂 결과: {output_base}")


if __name__ == "__main__":
    main()
