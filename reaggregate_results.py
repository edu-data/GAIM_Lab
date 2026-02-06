"""
기존 배치 분석 결과 재집계 스크립트
"""
import json
import csv
from pathlib import Path

batch_dir = Path(r"D:\AI\GAIM_Lab\output\batch_v2_20260206_181255")
results = []

def get_dim_score(dims_list, dim_name):
    for d in dims_list:
        if d.get("name") == dim_name:
            return d.get("score", 0)
    return 0

for video_dir in sorted(batch_dir.iterdir()):
    if video_dir.is_dir():
        eval_file = video_dir / "evaluation_result.json"
        if eval_file.exists():
            with open(eval_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            dims = data.get("dimensions", [])
            results.append({
                "video": f"{video_dir.name}.mp4",
                "total_score": data.get("total_score", 0),
                "grade": data.get("grade", "N/A"),
                "teaching_expertise": get_dim_score(dims, "수업 전문성"),
                "teaching_method": get_dim_score(dims, "교수학습 방법"),
                "communication": get_dim_score(dims, "판서 및 언어"),
                "teaching_attitude": get_dim_score(dims, "수업 태도"),
                "student_engagement": get_dim_score(dims, "학생 참여"),
                "time_management": get_dim_score(dims, "시간 배분"),
                "creativity": get_dim_score(dims, "창의성"),
                "status": "success"
            })

# CSV 저장
csv_path = batch_dir / "batch_summary_fixed.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"✅ 재집계 완료: {len(results)}개")
avg_score = sum(r["total_score"] for r in results) / len(results)
print(f"📊 평균 점수: {avg_score:.1f}점")
print(f"📁 저장: {csv_path}")
for r in results:
    print(f"  - {r['video']}: {r['total_score']}점 ({r['grade']})")
