"""
GAIM Lab - 검사-재검사 신뢰도 분석
Test-Retest Reliability Analysis for 20251209_110545.mp4
"""

import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# 1차, 2차 결과 로드
with open(PROJECT_ROOT / "test_largest_result.json", encoding="utf-8") as f:
    test1 = json.load(f)
with open(PROJECT_ROOT / "test_largest_result_retest.json", encoding="utf-8") as f:
    test2 = json.load(f)

print("=" * 70)
print("📊 GAIM Lab 검사-재검사 신뢰도 분석 (Test-Retest Reliability)")
print("   영상: 20251209_110545.mp4 (1,653 MB - 최대 용량)")
print("=" * 70)

# ================================================================
# 1. 차원별 점수 비교
# ================================================================
print("\n" + "─" * 70)
print("1️⃣  차원별 점수 비교")
print("─" * 70)
print(f"{'차원':<15} {'1차':>6} {'2차':>6} {'차이':>6} {'일치율':>8}")
print("─" * 70)

dims1 = {d["name"]: d for d in test1["dimensions"]}
dims2 = {d["name"]: d for d in test2["dimensions"]}

dim_names = [d["name"] for d in test1["dimensions"]]
scores1 = []
scores2 = []
pct1_list = []
pct2_list = []
diffs = []

for name in dim_names:
    d1 = dims1[name]
    d2 = dims2[name]
    s1 = d1["score"]
    s2 = d2["score"]
    max_s = d1["max_score"]
    diff = abs(s2 - s1)
    agreement = (1 - diff / max_s) * 100
    
    scores1.append(s1)
    scores2.append(s2)
    pct1_list.append(d1["percentage"])
    pct2_list.append(d2["percentage"])
    diffs.append(diff)
    
    marker = "✅" if diff <= 1 else ("⚠️" if diff <= 3 else "❌")
    print(f"{name:<15} {s1:>6.1f} {s2:>6.1f} {s2-s1:>+6.1f} {agreement:>7.1f}% {marker}")

print("─" * 70)
print(f"{'총점':<15} {test1['total_score']:>6.1f} {test2['total_score']:>6.1f} {test2['total_score']-test1['total_score']:>+6.1f}")
print(f"{'등급':<15} {test1['grade']:>6} {test2['grade']:>6}")

# ================================================================
# 2. Pearson 상관계수
# ================================================================
n = len(scores1)
mean1 = sum(scores1) / n
mean2 = sum(scores2) / n

cov = sum((s1 - mean1) * (s2 - mean2) for s1, s2 in zip(scores1, scores2)) / n
std1 = math.sqrt(sum((s - mean1) ** 2 for s in scores1) / n)
std2 = math.sqrt(sum((s - mean2) ** 2 for s in scores2) / n)

pearson_r = cov / (std1 * std2) if std1 > 0 and std2 > 0 else 0

print(f"\n\n" + "─" * 70)
print("2️⃣  Pearson 상관계수 (r)")
print("─" * 70)
print(f"   r = {pearson_r:.4f}")

if pearson_r >= 0.9:
    r_interp = "매우 높은 상관 (Excellent)"
elif pearson_r >= 0.7:
    r_interp = "높은 상관 (Good)"
elif pearson_r >= 0.5:
    r_interp = "보통 상관 (Moderate)"
else:
    r_interp = "낮은 상관 (Poor)"

print(f"   해석: {r_interp}")

# ================================================================
# 3. ICC (Intraclass Correlation Coefficient) - ICC(3,1) Two-way mixed, consistency
# ================================================================
# ICC 계산: Two-way random, single measures, absolute agreement
# Formula: ICC = (MSR - MSE) / (MSR + (k-1)*MSE + k*(MSC-MSE)/n)
# Simplified for k=2 raters (test-retest):

k = 2  # test, retest
subjects = list(zip(scores1, scores2))

# Overall mean
grand_mean = sum(scores1 + scores2) / (n * k)

# Mean per subject (row means)
row_means = [(s1 + s2) / 2 for s1, s2 in subjects]

# Mean per rater (column means)
col_means = [mean1, mean2]

# SS Between Subjects (SSR)
SSR = k * sum((rm - grand_mean) ** 2 for rm in row_means)

# SS Between Raters (SSC)
SSC = n * sum((cm - grand_mean) ** 2 for cm in col_means)

# SS Total
SST = sum((s - grand_mean) ** 2 for s in scores1) + sum((s - grand_mean) ** 2 for s in scores2)

# SS Error (Residual)
SSE = SST - SSR - SSC

# Mean Squares
MSR = SSR / (n - 1) if n > 1 else 0
MSC = SSC / (k - 1) if k > 1 else 0
MSE = SSE / ((n - 1) * (k - 1)) if (n - 1) * (k - 1) > 0 else 0

# ICC(2,1) - Two-way random, single measures, absolute agreement
icc_2_1 = (MSR - MSE) / (MSR + (k - 1) * MSE + k * (MSC - MSE) / n) if (MSR + (k - 1) * MSE + k * (MSC - MSE) / n) > 0 else 0

# ICC(3,1) - Two-way mixed, consistency
icc_3_1 = (MSR - MSE) / (MSR + (k - 1) * MSE) if (MSR + (k - 1) * MSE) > 0 else 0

print(f"\n\n" + "─" * 70)
print("3️⃣  ICC (급내상관계수, Intraclass Correlation Coefficient)")
print("─" * 70)
print(f"   ICC(2,1) 절대적 일치도: {icc_2_1:.4f}")
print(f"   ICC(3,1) 일관성:       {icc_3_1:.4f}")

if icc_3_1 >= 0.9:
    icc_interp = "매우 우수 (Excellent, ≥0.90)"
elif icc_3_1 >= 0.75:
    icc_interp = "우수 (Good, 0.75–0.89)"
elif icc_3_1 >= 0.5:
    icc_interp = "보통 (Moderate, 0.50–0.74)"
else:
    icc_interp = "미흡 (Poor, <0.50)"

print(f"   해석: {icc_interp}")
print(f"   (Koo & Li, 2016 기준)")

# ================================================================
# 4. 평균 절대 오차 (MAE) 및 RMSE
# ================================================================
mae = sum(diffs) / n
rmse = math.sqrt(sum(d ** 2 for d in diffs) / n)

# 총점 기준 MAE/RMSE
total_diff = abs(test2["total_score"] - test1["total_score"])

print(f"\n\n" + "─" * 70)
print("4️⃣  오차 분석")
print("─" * 70)
print(f"   차원별 MAE (평균 절대 오차): {mae:.2f}점")
print(f"   차원별 RMSE (평균제곱근오차): {rmse:.2f}점")
print(f"   총점 차이: {total_diff:.1f}점 (100점 만점 기준 {total_diff:.1f}%)")

# ================================================================
# 5. 세부 기준 비교
# ================================================================
print(f"\n\n" + "─" * 70)
print("5️⃣  세부 기준(criteria) 비교")
print("─" * 70)
print(f"{'차원':<15} {'기준':<20} {'1차':>5} {'2차':>5} {'차이':>6}")
print("─" * 70)

criteria_diffs = []
for name in dim_names:
    c1 = dims1[name].get("criteria", {})
    c2 = dims2[name].get("criteria", {})
    for key in c1:
        v1 = c1[key]
        v2 = c2.get(key, 0)
        diff = abs(v2 - v1)
        criteria_diffs.append(diff)
        marker = "✅" if diff == 0 else ("⚠️" if diff <= 1 else "❌")
        print(f"{name:<15} {key:<20} {v1:>5} {v2:>5} {v2-v1:>+6} {marker}")

criteria_exact = sum(1 for d in criteria_diffs if d == 0)
criteria_total = len(criteria_diffs)
criteria_close = sum(1 for d in criteria_diffs if d <= 1)

print("─" * 70)
print(f"   완전 일치: {criteria_exact}/{criteria_total}개 ({criteria_exact/criteria_total*100:.1f}%)")
print(f"   ±1점 이내: {criteria_close}/{criteria_total}개 ({criteria_close/criteria_total*100:.1f}%)")

# ================================================================
# 6. 등급 일치도
# ================================================================
print(f"\n\n" + "─" * 70)
print("6️⃣  등급 일치도")
print("─" * 70)
grade_match = test1["grade"] == test2["grade"]
print(f"   1차 등급: {test1['grade']}")
print(f"   2차 등급: {test2['grade']}")
print(f"   등급 일치: {'✅ 일치' if grade_match else '❌ 불일치'}")

# 강점 영역 일치
print(f"\n   1차 강점: {', '.join(test1.get('strengths', []))}")
print(f"   2차 강점: {', '.join(test2.get('strengths', []))}")
s1_set = set(test1.get("strengths", []))
s2_set = set(test2.get("strengths", []))
print(f"   강점 일치: {'✅ 일치' if s1_set == s2_set else '⚠️ 부분 불일치'}")

# ================================================================
# 종합 판정
# ================================================================
print(f"\n\n" + "=" * 70)
print("🏆 검사-재검사 신뢰도 종합 판정")
print("=" * 70)

reliability_score = 0
reliability_max = 5
notes = []

# 1) ICC 기준
if icc_3_1 >= 0.75:
    reliability_score += 1
    notes.append(f"✅ ICC(3,1) = {icc_3_1:.4f} → 우수 수준")
else:
    notes.append(f"⚠️ ICC(3,1) = {icc_3_1:.4f} → 개선 필요")

# 2) Pearson r
if pearson_r >= 0.7:
    reliability_score += 1
    notes.append(f"✅ Pearson r = {pearson_r:.4f} → 높은 상관")
else:
    notes.append(f"⚠️ Pearson r = {pearson_r:.4f} → 개선 필요")

# 3) 총점 차이
if total_diff <= 5:
    reliability_score += 1
    notes.append(f"✅ 총점 차이 = {total_diff:.1f}점 → 허용 범위")
else:
    notes.append(f"⚠️ 총점 차이 = {total_diff:.1f}점 → 큼")

# 4) 등급 일치
if grade_match:
    reliability_score += 1
    notes.append(f"✅ 등급 일치 ({test1['grade']})")
else:
    notes.append(f"⚠️ 등급 불일치 ({test1['grade']} → {test2['grade']})")

# 5) 세부 기준 일치
if criteria_close / criteria_total >= 0.8:
    reliability_score += 1
    notes.append(f"✅ 세부기준 ±1점 이내 {criteria_close/criteria_total*100:.0f}%")
else:
    notes.append(f"⚠️ 세부기준 ±1점 이내 {criteria_close/criteria_total*100:.0f}%")

for note in notes:
    print(f"   {note}")

print(f"\n   📊 신뢰도 점수: {reliability_score}/{reliability_max}")

if reliability_score >= 4:
    verdict = "🟢 높은 신뢰도 (High Reliability)"
elif reliability_score >= 3:
    verdict = "🟡 양호한 신뢰도 (Acceptable Reliability)"
else:
    verdict = "🔴 낮은 신뢰도 (Low Reliability)"

print(f"   🏆 종합 판정: {verdict}")

# ================================================================
# JSON 결과 저장
# ================================================================
reliability_result = {
    "video": "20251209_110545.mp4",
    "file_size_mb": 1653.42,
    "test1_score": test1["total_score"],
    "test1_grade": test1["grade"],
    "test2_score": test2["total_score"],
    "test2_grade": test2["grade"],
    "score_difference": test2["total_score"] - test1["total_score"],
    "grade_match": grade_match,
    "pearson_r": round(pearson_r, 4),
    "icc_2_1": round(icc_2_1, 4),
    "icc_3_1": round(icc_3_1, 4),
    "mae": round(mae, 2),
    "rmse": round(rmse, 2),
    "criteria_exact_match_rate": round(criteria_exact / criteria_total * 100, 1),
    "criteria_within_1pt_rate": round(criteria_close / criteria_total * 100, 1),
    "reliability_score": f"{reliability_score}/{reliability_max}",
    "verdict": verdict,
    "dimensions_comparison": [
        {
            "name": name,
            "test1_score": dims1[name]["score"],
            "test2_score": dims2[name]["score"],
            "difference": dims2[name]["score"] - dims1[name]["score"],
            "max_score": dims1[name]["max_score"]
        }
        for name in dim_names
    ]
}

result_path = PROJECT_ROOT / "test_retest_reliability.json"
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(reliability_result, f, ensure_ascii=False, indent=2)
print(f"\n📄 신뢰도 분석 결과: {result_path}")
