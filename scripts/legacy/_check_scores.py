import json, os, statistics
from collections import Counter

d = "D:/AI/GAIM_Lab/output/batch_agents_20260218_112157"
dirs = sorted([x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))])

scores = []
grades = []
all_data = []

for sd in dirs:
    fp = os.path.join(d, sd, "agent_result.json")
    if not os.path.exists(fp):
        continue
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    ped = data.get("pedagogy", {})
    s = ped.get("total_score", 0)
    g = ped.get("grade", "?")
    scores.append(s)
    grades.append(g)
    all_data.append((sd, s, g))

# Write results to file for easy reading
with open("D:/AI/GAIM_Lab/_v5_summary.txt", "w", encoding="utf-8") as out:
    out.write("GAIM Lab v5.0 - 18 Video Batch Results\n")
    out.write("=" * 50 + "\n\n")
    for sd, s, g in all_data:
        out.write(f"{sd}: {s:.1f} ({g})\n")
    out.write(f"\n--- Summary ({len(scores)} videos) ---\n")
    out.write(f"Avg: {statistics.mean(scores):.1f}\n")
    out.write(f"SD: {statistics.stdev(scores):.1f}\n")
    out.write(f"Range: {min(scores):.1f} - {max(scores):.1f} (spread: {max(scores)-min(scores):.1f})\n")
    out.write(f"Median: {statistics.median(scores):.1f}\n")
    out.write(f"Grades: {dict(Counter(grades))}\n")
    v42r = 80.6 - 70.9
    v50r = max(scores) - min(scores)
    out.write(f"\nv4.2 range: 9.7pt  |  v5.0 range: {v50r:.1f}pt  |  {v50r/v42r:.1f}x wider\n")

print("Written to _v5_summary.txt")
