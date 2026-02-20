"""
MAS 동형검사 신뢰도 분석 (Parallel Forms Reliability)
=====================================================
v6와 v7 파이프라인은 동일 구인(교수 역량)을 측정하는 두 가지
동형 검사(Parallel Forms)입니다. 동일 18개 영상에 대한 두 버전의
분석 결과를 비교하여 동형검사 신뢰도를 평가합니다.

이론적 배경:
- 동형검사 신뢰도는 동일 구인을 측정하는 두 가지 '동형'의
  검사를 동일 피험자에게 시행한 후 상관을 구하는 방법입니다.
- v6 → Form A, v7 → Form B로 간주합니다.

측정 지표:
- Pearson r (동형검사 신뢰도 계수)
- ICC(2,1) (절대적 일치도)
- Cronbach's Alpha (내적 일관성)
- MAE & Bland-Altman (체계적 편향 검증)
- 등급 일치율 (분류 일관성)
"""

import csv
import math
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- 데이터 로드 ---
V6_CSV = PROJECT_ROOT / "output" / "batch_agents_20260218_145847" / "agent_batch_summary.csv"
V7_CSV = PROJECT_ROOT / "output" / "batch_agents_20260220_130059" / "agent_batch_summary.csv"

DIMENSIONS = [
    "teaching_expertise", "teaching_method", "communication",
    "teaching_attitude", "student_engagement", "time_management", "creativity"
]
DIM_LABELS = {
    "teaching_expertise": "수업 전문성",
    "teaching_method": "교수학습 방법",
    "communication": "의사소통",
    "teaching_attitude": "수업 태도",
    "student_engagement": "학생 참여",
    "time_management": "시간 배분",
    "creativity": "창의성",
}
DIM_MAX = {
    "teaching_expertise": 20, "teaching_method": 20, "communication": 15,
    "teaching_attitude": 15, "student_engagement": 15, "time_management": 10, "creativity": 5,
}


def load_csv(path):
    """CSV 파일 로드하여 video 키 기준 dict 반환"""
    data = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            video = row["video"].replace(".mp4", "")
            entry = {"total_score": float(row["total_score"]), "grade": row["grade"]}
            for d in DIMENSIONS:
                entry[d] = float(row[d])
            data[video] = entry
    return data


def pearson_r(x, y):
    """Pearson 상관계수 계산"""
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / (n - 1))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / (n - 1))
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1)
    return cov / (sx * sy)


def icc_two_way(x, y):
    """ICC(2,1) - Two-way random, single measures, absolute agreement"""
    n = len(x)
    k = 2  # 두 명의 평가자 (v6, v7)
    
    # Grand mean
    grand_mean = (sum(x) + sum(y)) / (n * k)
    
    # Subject means
    subj_means = [(xi + yi) / k for xi, yi in zip(x, y)]
    
    # Rater means
    rater_means = [sum(x) / n, sum(y) / n]
    
    # Mean squares
    # Between subjects (MSR - row)
    MSR = k * sum((sm - grand_mean) ** 2 for sm in subj_means) / (n - 1)
    
    # Between raters (MSC - column)
    MSC = n * sum((rm - grand_mean) ** 2 for rm in rater_means) / (k - 1)
    
    # Residual error (MSE)
    ss_total = sum((xi - grand_mean) ** 2 for xi in x) + sum((yi - grand_mean) ** 2 for yi in y)
    ss_row = k * sum((sm - grand_mean) ** 2 for sm in subj_means)
    ss_col = n * sum((rm - grand_mean) ** 2 for rm in rater_means)
    ss_error = ss_total - ss_row - ss_col
    df_error = (n - 1) * (k - 1)
    MSE = ss_error / df_error if df_error > 0 else 0
    
    # ICC(2,1) = (MSR - MSE) / (MSR + (k-1)*MSE + k*(MSC-MSE)/n)
    denom = MSR + (k - 1) * MSE + k * (MSC - MSE) / n
    if denom == 0:
        return 0.0
    icc = (MSR - MSE) / denom
    return max(-1.0, min(1.0, icc))


def cronbach_alpha(x, y):
    """Cronbach's Alpha (2 평가자)"""
    n = len(x)
    totals = [xi + yi for xi, yi in zip(x, y)]
    
    var_x = sum((xi - sum(x) / n) ** 2 for xi in x) / (n - 1)
    var_y = sum((yi - sum(y) / n) ** 2 for yi in y) / (n - 1)
    var_t = sum((ti - sum(totals) / n) ** 2 for ti in totals) / (n - 1)
    
    k = 2
    if var_t == 0:
        return 0.0
    alpha = (k / (k - 1)) * (1 - (var_x + var_y) / var_t)
    return alpha


def bland_altman(x, y):
    """Bland-Altman 분석: 평균 차이, 차이의 SD, 95% LoA"""
    diffs = [yi - xi for xi, yi in zip(x, y)]
    n = len(diffs)
    mean_diff = sum(diffs) / n
    sd_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / (n - 1))
    loa_lower = mean_diff - 1.96 * sd_diff
    loa_upper = mean_diff + 1.96 * sd_diff
    return {
        "mean_diff": round(mean_diff, 2),
        "sd_diff": round(sd_diff, 2),
        "loa_lower": round(loa_lower, 2),
        "loa_upper": round(loa_upper, 2),
    }


def interpret_icc(val):
    if val >= 0.90:
        return "우수 (Excellent)"
    elif val >= 0.75:
        return "양호 (Good)"
    elif val >= 0.50:
        return "보통 (Moderate)"
    else:
        return "미흡 (Poor)"


def interpret_r(val):
    abs_val = abs(val)
    if abs_val >= 0.90:
        return "매우 강함"
    elif abs_val >= 0.70:
        return "강함"
    elif abs_val >= 0.50:
        return "보통"
    elif abs_val >= 0.30:
        return "약함"
    else:
        return "매우 약함"


def main():
    print("=" * 70)
    print("  MAS 동형검사 신뢰도 분석 (Parallel Forms Reliability)")
    print("  Form A = v6 Pipeline  |  Form B = v7 Pipeline")
    print("=" * 70)
    
    v6 = load_csv(V6_CSV)
    v7 = load_csv(V7_CSV)
    
    # 공통 비디오 정렬
    common = sorted(set(v6.keys()) & set(v7.keys()))
    print(f"\n📊 공통 영상 수: {len(common)}")
    
    # --- 1. 총점 비교 ---
    v6_scores = [v6[v]["total_score"] for v in common]
    v7_scores = [v7[v]["total_score"] for v in common]
    
    print(f"\n{'─' * 70}")
    print("📈 1. 총점 기술통계")
    print(f"{'─' * 70}")
    print(f"  {'':20s}  {'v6':>10s}  {'v7':>10s}  {'차이':>10s}")
    print(f"  {'평균':20s}  {sum(v6_scores)/len(v6_scores):10.2f}  {sum(v7_scores)/len(v7_scores):10.2f}  {sum(v7_scores)/len(v7_scores) - sum(v6_scores)/len(v6_scores):+10.2f}")
    print(f"  {'표준편차':20s}  {(sum((s - sum(v6_scores)/len(v6_scores))**2 for s in v6_scores)/(len(v6_scores)-1))**0.5:10.2f}  {(sum((s - sum(v7_scores)/len(v7_scores))**2 for s in v7_scores)/(len(v7_scores)-1))**0.5:10.2f}")
    print(f"  {'최고':20s}  {max(v6_scores):10.1f}  {max(v7_scores):10.1f}")
    print(f"  {'최저':20s}  {min(v6_scores):10.1f}  {min(v7_scores):10.1f}")
    
    # --- 2. 영상별 점수 비교 ---
    print(f"\n{'─' * 70}")
    print("📋 2. 영상별 점수 비교")
    print(f"{'─' * 70}")
    print(f"  {'영상':22s}  {'v6':>6s}  {'v7':>6s}  {'차이':>8s}  {'v6등급':>6s}  {'v7등급':>6s}  {'일치':>4s}")
    
    grade_match = 0
    abs_diffs = []
    
    for v in common:
        diff = v7[v]["total_score"] - v6[v]["total_score"]
        abs_diffs.append(abs(diff))
        match = "✓" if v6[v]["grade"] == v7[v]["grade"] else "✗"
        if v6[v]["grade"] == v7[v]["grade"]:
            grade_match += 1
        print(f"  {v:22s}  {v6[v]['total_score']:6.1f}  {v7[v]['total_score']:6.1f}  {diff:+8.1f}  {v6[v]['grade']:>6s}  {v7[v]['grade']:>6s}  {match:>4s}")
    
    mae = sum(abs_diffs) / len(abs_diffs)
    
    # --- 3. 상관 분석 ---
    r_total = pearson_r(v6_scores, v7_scores)
    icc_total = icc_two_way(v6_scores, v7_scores)
    alpha_total = cronbach_alpha(v6_scores, v7_scores)
    ba = bland_altman(v6_scores, v7_scores)
    
    print(f"\n{'─' * 70}")
    print("🔬 3. 동형검사 신뢰도 계수 (Parallel Forms Reliability Coefficients)")
    print(f"{'─' * 70}")
    print(f"  동형검사 신뢰도 계수 (r) = {r_total:.4f}  ({interpret_r(r_total)})")
    print(f"  ICC(2,1)           = {icc_total:.4f}  ({interpret_icc(icc_total)})")
    print(f"  Cronbach's α       = {alpha_total:.4f}")
    print(f"  등급 일치율          = {grade_match}/{len(common)} ({grade_match/len(common)*100:.1f}%)")
    print(f"  평균 절대 차이 (MAE) = {mae:.2f}점")
    print(f"  Bland-Altman:")
    print(f"    평균 차이 (Bias)   = {ba['mean_diff']:+.2f}점")
    print(f"    차이 SD           = {ba['sd_diff']:.2f}점")
    print(f"    95% LoA           = [{ba['loa_lower']:.2f}, {ba['loa_upper']:.2f}]")
    
    # --- 4. 차원별 신뢰도 ---
    print(f"\n{'─' * 70}")
    print("📊 4. 차원별 동형검사 신뢰도")
    print(f"{'─' * 70}")
    print(f"  {'차원':18s}  {'배점':>4s}  {'r':>7s}  {'ICC':>7s}  {'α':>7s}  {'MAE':>7s}  {'해석':10s}")
    
    dim_results = {}
    for d in DIMENSIONS:
        v6d = [v6[v][d] for v in common]
        v7d = [v7[v][d] for v in common]
        
        r_d = pearson_r(v6d, v7d)
        icc_d = icc_two_way(v6d, v7d)
        alpha_d = cronbach_alpha(v6d, v7d)
        mae_d = sum(abs(y - x) for x, y in zip(v6d, v7d)) / len(v6d)
        
        label = DIM_LABELS[d]
        maxp = DIM_MAX[d]
        print(f"  {label:18s}  {maxp:4d}  {r_d:7.4f}  {icc_d:7.4f}  {alpha_d:7.4f}  {mae_d:7.2f}  {interpret_icc(icc_d)}")
        
        dim_results[d] = {
            "label": label, "max": maxp,
            "r": round(r_d, 4), "icc": round(icc_d, 4),
            "alpha": round(alpha_d, 4), "mae": round(mae_d, 2),
            "v6_mean": round(sum(v6d) / len(v6d), 2),
            "v7_mean": round(sum(v7d) / len(v7d), 2),
        }
    
    # --- 5. 종합 판정 ---
    print(f"\n{'─' * 70}")
    print("✅ 5. 종합 판정")
    print(f"{'─' * 70}")
    
    # 전체 신뢰도 수준
    overall_level = interpret_icc(icc_total)
    print(f"  동형검사 유형: Form A (v6) vs Form B (v7)")
    print(f"  동일 피험자: 18개 수업 영상")
    print(f"  총점 ICC = {icc_total:.4f} → {overall_level}")
    print(f"  총점 Pearson r = {r_total:.4f} → {interpret_r(r_total)}")
    
    strong_dims = [d for d in DIMENSIONS if dim_results[d]["icc"] >= 0.50]
    weak_dims = [d for d in DIMENSIONS if dim_results[d]["icc"] < 0.50]
    
    if strong_dims:
        print(f"\n  🟢 신뢰도 보통 이상 차원 ({len(strong_dims)}개):")
        for d in strong_dims:
            print(f"     - {DIM_LABELS[d]}: ICC={dim_results[d]['icc']:.4f}")
    
    if weak_dims:
        print(f"\n  🟡 신뢰도 개선 필요 차원 ({len(weak_dims)}개):")
        for d in weak_dims:
            print(f"     - {DIM_LABELS[d]}: ICC={dim_results[d]['icc']:.4f}")
    
    # --- JSON 결과 저장 ---
    result = {
        "analysis_type": "동형검사 신뢰도 (Parallel Forms Reliability)",
        "form_a": "v6 Pipeline",
        "form_b": "v7 Pipeline",
        "version": "v6 vs v7",
        "n_videos": len(common),
        "total_score": {
            "pearson_r": round(r_total, 4),
            "icc": round(icc_total, 4),
            "cronbach_alpha": round(alpha_total, 4),
            "mae": round(mae, 2),
            "grade_agreement": f"{grade_match}/{len(common)}",
            "grade_agreement_pct": round(grade_match / len(common) * 100, 1),
            "bland_altman": ba,
            "v6_mean": round(sum(v6_scores) / len(v6_scores), 2),
            "v7_mean": round(sum(v7_scores) / len(v7_scores), 2),
        },
        "dimensions": dim_results,
        "video_comparison": [
            {
                "video": v,
                "v6_score": v6[v]["total_score"], "v7_score": v7[v]["total_score"],
                "diff": round(v7[v]["total_score"] - v6[v]["total_score"], 1),
                "v6_grade": v6[v]["grade"], "v7_grade": v7[v]["grade"],
            }
            for v in common
        ],
    }
    
    out_path = PROJECT_ROOT / "output" / "reliability_v6_v7.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n  📁 결과 저장: {out_path}")
    
    print(f"\n{'=' * 70}")
    print("  분석 완료")
    print(f"{'=' * 70}")
    
    return result


if __name__ == "__main__":
    main()
