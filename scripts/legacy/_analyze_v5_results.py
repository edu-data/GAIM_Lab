"""v5.0 배치 결과 분석"""
import json, os, statistics

d = "D:/AI/GAIM_Lab/output/batch_agents_20260218_112157"

dirs = sorted([x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))])
print(f"Total directories: {len(dirs)}")

scores = []
grades = []
dim_scores = {}

for sd in dirs:
    fp = os.path.join(d, sd, "agent_result.json")
    if not os.path.exists(fp):
        print(f"  MISSING: {sd}")
        continue

    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)

    ped = data.get("pedagogy", {})
    total = ped.get("total_score", 0)
    grade = ped.get("grade", "?")
    scores.append(total)
    grades.append(grade)

    # Dimension breakdown
    for dim in ped.get("dimensions", []):
        name = dim["name"]
        if name not in dim_scores:
            dim_scores[name] = []
        dim_scores[name].append(dim["score"])

    # Check discourse
    disc = data.get("discourse", {})
    has_disc = bool(disc and disc.get("question_types"))

    print(f"  {sd}: {total:.1f} ({grade}) | discourse: {'✅' if has_disc else '❌'}")

print(f"\n{'='*60}")
print(f"📊 v5.0 배치 결과 요약 ({len(scores)}개 영상)")
print(f"{'='*60}")
print(f"평균: {statistics.mean(scores):.1f}")
print(f"표준편차: {statistics.stdev(scores):.1f}")
print(f"범위: {min(scores):.1f} ~ {max(scores):.1f} ({max(scores)-min(scores):.1f}pt)")
print(f"중앙값: {statistics.median(scores):.1f}")

# Grade distribution
from collections import Counter
gc = Counter(grades)
print(f"\n등급 분포: {dict(sorted(gc.items()))}")

# v4.2 comparison
v42_range = 80.6 - 70.9
v50_range = max(scores) - min(scores)
print(f"\n📈 v4.2 → v5.0 비교:")
print(f"  v4.2 범위: 70.9 ~ 80.6 ({v42_range:.1f}pt)")
print(f"  v5.0 범위: {min(scores):.1f} ~ {max(scores):.1f} ({v50_range:.1f}pt)")
print(f"  범위 확대: {v50_range/v42_range:.1f}x")
print(f"  v4.2 평균: 75.6, v5.0 평균: {statistics.mean(scores):.1f}")

# Dimension averages
print(f"\n📐 차원별 평균:")
for name, vals in dim_scores.items():
    max_score = {"수업 전문성": 20, "교수학습 방법": 20, "판서 및 언어": 15, "수업 태도": 15, "학생 참여": 15, "시간 배분": 10, "창의성": 5}.get(name, 15)
    avg = statistics.mean(vals)
    print(f"  {name}: {avg:.1f}/{max_score} ({avg/max_score*100:.0f}%)")
