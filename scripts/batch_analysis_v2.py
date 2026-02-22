"""
GAIM Lab - 18개 영상 배치 분석 스크립트 V2
run_sample_analysis.py 호출을 통한 순차 분석
"""

import sys
import io
import os
import json
import csv
from pathlib import Path
from datetime import datetime

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 = scripts 디렉토리
SCRIPT_DIR = Path(__file__).resolve().parent

# .env 로드
env_file = SCRIPT_DIR.parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print(f"✅ 환경 변수 로드: GOOGLE_API_KEY={'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")

# run_sample_analysis는 같은 디렉토리에 있음
from run_sample_analysis import run_sample_analysis


def batch_analyze():
    """18개 영상 배치 분석"""
    video_dir = SCRIPT_DIR.parent / "video"
    output_base = SCRIPT_DIR.parent / "output" / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_base.mkdir(parents=True, exist_ok=True)

    # 분석할 영상 목록 (youtube_demo 제외)
    videos = sorted([
        f for f in video_dir.glob("*.mp4")
        if "youtube" not in f.name.lower()
    ])

    print("=" * 70)
    print(f"🎬 GAIM Lab 배치 분석 V2 시작")
    print(f"📁 영상 수: {len(videos)}개")
    print(f"📂 출력: {output_base}")
    print("=" * 70)

    results = []
    start_time = datetime.now()

    for i, video in enumerate(videos, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(videos)}] 분석 중: {video.name}")
        print("=" * 70)

        try:
            video_output = output_base / video.stem
            video_output.mkdir(exist_ok=True)

            result, report_path = run_sample_analysis(
                str(video),
                str(video_output)
            )

            if result:
                # result는 dict 형태
                total_score = result.get("total_score", 0)
                grade = result.get("grade", "N/A")
                
                dims = {}
                for d in result.get("dimensions", []):
                    dims[d.get("dimension", "")] = d.get("score", 0)
                
                results.append({
                    "video": video.name,
                    "total_score": total_score,
                    "grade": grade,
                    "professionalism": dims.get("수업 전문성", 0),
                    "teaching_method": dims.get("교수학습 방법", 0),
                    "language": dims.get("판서 및 언어", 0),
                    "attitude": dims.get("수업 태도", 0),
                    "participation": dims.get("학생 참여", 0),
                    "time_management": dims.get("시간 배분", 0),
                    "creativity": dims.get("창의성", 0),
                    "status": "success"
                })
                print(f"   ✅ 완료: {total_score}점 ({grade})")
            else:
                results.append({
                    "video": video.name,
                    "total_score": 0,
                    "grade": "N/A",
                    "status": "no_result"
                })
                print(f"   ⚠️ 결과 없음")

        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({
                "video": video.name,
                "total_score": 0,
                "grade": "ERROR",
                "status": f"error: {str(e)}"
            })
            print(f"   ❌ 오류: {e}")

    # CSV 요약 저장
    csv_path = output_base / "batch_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    # JSON 요약 저장
    json_path = output_base / "batch_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 최종 요약 출력
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 70)
    print("📊 배치 분석 완료!")
    print("=" * 70)
    print(f"⏱️ 총 소요 시간: {elapsed}")

    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]
    
    if successful:
        avg_score = sum(r["total_score"] for r in successful) / len(successful)
        scores = [r["total_score"] for r in successful]
        print(f"\n✅ 성공: {len(successful)}/{len(results)}개")
        print(f"📈 평균 점수: {avg_score:.1f}점")
        print(f"📊 최고/최저: {max(scores):.1f} / {min(scores):.1f}")

        # 등급 분포
        grades = {}
        for r in successful:
            g = r["grade"]
            grades[g] = grades.get(g, 0) + 1

        print("\n📊 등급 분포:")
        for grade_label in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if grade_label in grades:
                bar = "█" * grades[grade_label]
                print(f"   {grade_label}: {bar} ({grades[grade_label]}개)")

    if failed:
        print(f"\n❌ 실패: {len(failed)}개")
        for r in failed:
            print(f"   - {r['video']}: {r['status']}")

    print(f"\n📂 결과 저장:")
    print(f"   - CSV: {csv_path}")
    print(f"   - JSON: {json_path}")

    return results


if __name__ == "__main__":
    batch_analyze()
