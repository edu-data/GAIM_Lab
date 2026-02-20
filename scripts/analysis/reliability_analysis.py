#!/usr/bin/env python3
"""
GAIM Lab — 신뢰도 분석 (Cronbach's α / ICC)
===========================================
9회 반복 배치 분석 데이터를 활용하여 7차원 평가 도구의 신뢰도를 계량화합니다.

지표:
  • Cronbach's α  — 7차원 내적 합치도 (internal consistency)
  • ICC(2,1)      — 절대 일치도 (single measures, two-way random)
  • ICC(2,k)      — 평균 측도 신뢰도 (average measures)
  • SEM           — 측정 표준오차 (Standard Error of Measurement)
  • CV            — 변동계수 (Coefficient of Variation)

Usage:
  python reliability_analysis.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ── 설정 ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent  # scripts/analysis → GAIM_Lab
OUTPUT_BASE = PROJECT_ROOT / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

# 차원 매핑 (CSV 컬럼명 → 한글 표기)
DIM_COLS = [
    ("teaching_expertise", "수업 전문성", 20),
    ("teaching_method",    "교수학습 방법", 20),
    ("communication",      "판서 및 언어", 15),
    ("teaching_attitude",  "수업 태도", 15),
    ("student_engagement", "학생 참여", 15),
    ("time_management",    "시간 배분", 10),
    ("creativity",         "창의성", 5),
]
DIM_KEYS = [c for c, _, _ in DIM_COLS]
DIM_LABELS = {c: l for c, l, _ in DIM_COLS}
DIM_MAX = {c: m for c, _, m in DIM_COLS}


# ── 데이터 로드 ───────────────────────────────────────────────────────
def load_batch_runs() -> Tuple[List[str], List[str], np.ndarray]:
    """
    모든 agent_batch_summary.csv 파일을 로드합니다.
    품질 필터링: 총점 평균이 이상치인 실행(all-zero, 비정상 평균)은 제외합니다.

    Returns:
        run_ids: 실행 ID 리스트 (길이 R)
        videos:  영상 이름 리스트 (길이 N)
        data:    (R, N, D) 배열 — R개 실행, N개 영상, D개 차원
    """
    batch_dirs = sorted([
        d for d in OUTPUT_BASE.iterdir()
        if d.is_dir() and d.name.startswith("batch_agents_")
    ])

    candidates = []

    for bd in batch_dirs:
        csv_path = bd / "agent_batch_summary.csv"
        if not csv_path.exists():
            continue

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        rows = [r for r in rows if r.get("status") == "success"]
        if len(rows) < 10:
            continue

        videos = [r["video"] for r in rows]
        scores = []
        for r in rows:
            dims = []
            for col in DIM_KEYS:
                try:
                    dims.append(float(r.get(col, 0)))
                except (ValueError, TypeError):
                    dims.append(0.0)
            scores.append(dims)

        arr = np.array(scores)  # (N, D)
        run_mean = arr.sum(axis=1).mean()

        # 품질 필터: 총점 평균 0이거나 비정상적으로 낮은 경우 제외
        if run_mean < 30:
            print(f"   ⚠️ {bd.name} 제외 (총점 평균 {run_mean:.1f} — 비정상)")
            continue

        candidates.append((bd.name, videos, scores, run_mean))

    if not candidates:
        print("❌ 유효한 배치 실행 데이터를 찾을 수 없습니다.")
        sys.exit(1)

    # 이상치 실행 필터링: IQR 기반
    means = np.array([c[3] for c in candidates])
    q1, q3 = np.percentile(means, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 2.0 * iqr, q3 + 2.0 * iqr  # 넉넉한 기준

    filtered = []
    for name, vids, sc, m in candidates:
        if lower <= m <= upper:
            filtered.append((name, vids, sc))
        else:
            print(f"   ⚠️ {name} 제외 (총점 평균 {m:.1f} — IQR 이상치)")

    if not filtered:
        print("❌ 필터링 후 유효한 실행이 없습니다.")
        sys.exit(1)

    # 공통 영상 목록
    video_set = filtered[0][1]
    for _, vids, _ in filtered[1:]:
        video_set = [v for v in video_set if v in vids]

    # 최종 데이터 구성
    all_runs = []
    run_ids = []
    for name, vids, sc in filtered:
        vid_idx = {v: i for i, v in enumerate(vids)}
        ordered = [sc[vid_idx[v]] for v in video_set if v in vid_idx]
        if len(ordered) == len(video_set):
            all_runs.append(ordered)
            run_ids.append(name)

    data = np.array(all_runs, dtype=np.float64)  # (R, N, D)
    print(f"✅ {len(run_ids)}회 실행, {len(video_set)}개 영상, {len(DIM_KEYS)}차원 로드 완료")
    return run_ids, video_set, data


# ── Cronbach's α ──────────────────────────────────────────────────────
def cronbachs_alpha(item_scores: np.ndarray) -> float:
    """
    Cronbach's α 계산.

    Args:
        item_scores: (N, K) 배열 — N명 피험자, K개 항목
    Returns:
        alpha 값
    """
    N, K = item_scores.shape
    if K < 2:
        return float("nan")

    item_vars = item_scores.var(axis=0, ddof=1)
    total_var = item_scores.sum(axis=1).var(ddof=1)

    if total_var == 0:
        return 1.0

    alpha = (K / (K - 1)) * (1 - item_vars.sum() / total_var)
    return float(alpha)


# ── ICC ──────────────────────────────────────────────────────────────
def compute_icc(ratings: np.ndarray) -> Dict[str, float]:
    """
    ICC(2,1)과 ICC(2,k) 계산 — Two-way random effects, absolute agreement.

    Args:
        ratings: (N, K) 배열 — N개 대상, K명 평가자
    Returns:
        {'icc21': float, 'icc2k': float, 'sem': float}
    """
    n, k = ratings.shape
    if n < 2 or k < 2:
        return {"icc21": float("nan"), "icc2k": float("nan"), "sem": float("nan")}

    # Grand mean
    grand_mean = ratings.mean()

    # Sum of squares
    row_means = ratings.mean(axis=1)
    col_means = ratings.mean(axis=0)

    # Between-subjects (rows)
    SS_between = k * np.sum((row_means - grand_mean) ** 2)
    df_between = n - 1

    # Between-raters (columns)
    SS_raters = n * np.sum((col_means - grand_mean) ** 2)
    df_raters = k - 1

    # Residual (error)
    SS_total = np.sum((ratings - grand_mean) ** 2)
    SS_error = SS_total - SS_between - SS_raters
    df_error = (n - 1) * (k - 1)

    # Mean squares
    MS_between = SS_between / df_between if df_between > 0 else 0
    MS_raters = SS_raters / df_raters if df_raters > 0 else 0
    MS_error = SS_error / df_error if df_error > 0 else 0

    # ICC(2,1) — Single measures, two-way random, absolute agreement
    denom_21 = MS_between + (k - 1) * MS_error + k * (MS_raters - MS_error) / n
    icc21 = (MS_between - MS_error) / denom_21 if denom_21 != 0 else float("nan")

    # ICC(2,k) — Average measures
    denom_2k = MS_between + (MS_raters - MS_error) / n
    icc2k = (MS_between - MS_error) / denom_2k if denom_2k != 0 else float("nan")

    # SEM = sqrt(MS_error)
    sem = math.sqrt(MS_error) if MS_error >= 0 else 0.0

    return {"icc21": float(icc21), "icc2k": float(icc2k), "sem": float(sem)}


# ── 재검사 상관 ────────────────────────────────────────────────────────
def test_retest_correlation(data: np.ndarray) -> Dict:
    """
    연속 실행 간 재검사 상관(test-retest r)과 일치도를 계산합니다.

    Args:
        data: (R, N, D) 배열
    Returns:
        dict with pairwise r and agreement metrics
    """
    R, N, D = data.shape
    totals = data.sum(axis=2)  # (R, N)

    pairs = []
    for i in range(R):
        for j in range(i + 1, R):
            r_val = float(np.corrcoef(totals[i], totals[j])[0, 1])
            diff = np.abs(totals[i] - totals[j])
            mad = float(np.mean(diff))  # Mean Absolute Difference
            agree_5 = float(np.mean(diff <= 5) * 100)  # ±5점 이내 비율
            agree_3 = float(np.mean(diff <= 3) * 100)  # ±3점 이내 비율
            pairs.append({
                "run_a": i, "run_b": j,
                "pearson_r": round(r_val, 4) if not np.isnan(r_val) else 0.0,
                "mad": round(mad, 2),
                "agree_5pt_pct": round(agree_5, 1),
                "agree_3pt_pct": round(agree_3, 1),
            })

    # 차원별 재검사 상관
    dim_retest = {}
    for d_idx, (col, label, _) in enumerate(DIM_COLS):
        dim_r_values = []
        dim_mad_values = []
        for i in range(R):
            for j in range(i + 1, R):
                rv = np.corrcoef(data[i, :, d_idx], data[j, :, d_idx])[0, 1]
                if not np.isnan(rv):
                    dim_r_values.append(rv)
                dim_mad_values.append(np.mean(np.abs(data[i, :, d_idx] - data[j, :, d_idx])))
        dim_retest[col] = {
            "label": label,
            "mean_r": round(float(np.mean(dim_r_values)), 4) if dim_r_values else 0.0,
            "min_r": round(float(np.min(dim_r_values)), 4) if dim_r_values else 0.0,
            "max_r": round(float(np.max(dim_r_values)), 4) if dim_r_values else 0.0,
            "mean_mad": round(float(np.mean(dim_mad_values)), 2),
        }

    r_values = [p["pearson_r"] for p in pairs]
    return {
        "pairs": pairs,
        "n_pairs": len(pairs),
        "mean_r": round(float(np.mean(r_values)), 4) if r_values else 0.0,
        "min_r": round(float(np.min(r_values)), 4) if r_values else 0.0,
        "max_r": round(float(np.max(r_values)), 4) if r_values else 0.0,
        "mean_mad": round(float(np.mean([p["mad"] for p in pairs])), 2),
        "mean_agree_5pt": round(float(np.mean([p["agree_5pt_pct"] for p in pairs])), 1),
        "mean_agree_3pt": round(float(np.mean([p["agree_3pt_pct"] for p in pairs])), 1),
        "dimensions": dim_retest,
    }


# ── 분석 실행 ──────────────────────────────────────────────────────────
def run_analysis():
    run_ids, videos, data = load_batch_runs()
    R, N, D = data.shape

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_BASE / f"reliability_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "meta": {
            "runs": R,
            "videos": N,
            "dimensions": D,
            "run_ids": run_ids,
            "timestamp": timestamp,
        },
        "cronbachs_alpha": {},
        "icc": {},
        "test_retest": {},
        "dimension_stats": {},
    }

    # ── 1. Cronbach's α (각 실행별) ──
    alphas = []
    for r_idx in range(R):
        scores = data[r_idx]  # (N, D)
        a = cronbachs_alpha(scores)
        alphas.append(a)

    results["cronbachs_alpha"] = {
        "per_run": {run_ids[i]: round(alphas[i], 4) for i in range(R)},
        "mean": round(float(np.mean(alphas)), 4),
        "std": round(float(np.std(alphas, ddof=1)), 4) if R > 1 else 0.0,
        "min": round(float(np.min(alphas)), 4),
        "max": round(float(np.max(alphas)), 4),
    }

    # ── 2. ICC — 차원별 & 총점 ──
    icc_results = {}

    totals = data.sum(axis=2)  # (R, N)
    total_ratings = totals.T  # (N, R)
    icc_total = compute_icc(total_ratings)
    icc_results["total_score"] = {
        "label": "총점",
        "max": 100,
        "icc21": round(icc_total["icc21"], 4),
        "icc2k": round(icc_total["icc2k"], 4),
        "sem": round(icc_total["sem"], 2),
    }

    for d_idx, (col, label, max_score) in enumerate(DIM_COLS):
        dim_ratings = data[:, :, d_idx].T  # (N, R)
        icc_dim = compute_icc(dim_ratings)

        dim_means = dim_ratings.mean(axis=1)
        dim_stds = dim_ratings.std(axis=1, ddof=1)
        cv_values = np.where(dim_means > 0, dim_stds / dim_means * 100, 0)
        cv_mean = float(np.nanmean(cv_values))

        icc_results[col] = {
            "label": label,
            "max": max_score,
            "icc21": round(icc_dim["icc21"], 4),
            "icc2k": round(icc_dim["icc2k"], 4),
            "sem": round(icc_dim["sem"], 2),
            "cv_mean_pct": round(cv_mean, 2),
        }

    results["icc"] = icc_results

    # ── 3. 재검사 상관 (Test-Retest) ──
    retest = test_retest_correlation(data)
    results["test_retest"] = retest

    # ── 4. 차원별 기술통계 ──
    for d_idx, (col, label, max_score) in enumerate(DIM_COLS):
        all_scores = data[:, :, d_idx].flatten()
        results["dimension_stats"][col] = {
            "label": label,
            "max": max_score,
            "mean": round(float(np.mean(all_scores)), 2),
            "std": round(float(np.std(all_scores, ddof=1)), 2),
            "min": round(float(np.min(all_scores)), 1),
            "max_observed": round(float(np.max(all_scores)), 1),
            "range": round(float(np.ptp(all_scores)), 1),
        }

    all_totals = data.sum(axis=2).flatten()
    results["dimension_stats"]["total_score"] = {
        "label": "총점",
        "max": 100,
        "mean": round(float(np.mean(all_totals)), 2),
        "std": round(float(np.std(all_totals, ddof=1)), 2),
        "min": round(float(np.min(all_totals)), 1),
        "max_observed": round(float(np.max(all_totals)), 1),
        "range": round(float(np.ptp(all_totals)), 1),
    }

    # ── CSV 출력 ──
    csv_path = out_dir / "reliability_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "dimension", "label", "max_score",
            "ICC(2,1)", "ICC(2,k)", "SEM", "CV(%)",
            "test_retest_r", "MAD",
            "mean", "std", "min", "max_observed",
        ])
        for key in ["total_score"] + DIM_KEYS:
            icc = icc_results[key]
            stats = results["dimension_stats"][key]
            tr = retest["dimensions"].get(key, {})
            w.writerow([
                key, icc["label"], icc["max"],
                icc["icc21"], icc["icc2k"], icc["sem"],
                icc.get("cv_mean_pct", ""),
                tr.get("mean_r", retest["mean_r"]),
                tr.get("mean_mad", retest["mean_mad"]),
                stats["mean"], stats["std"], stats["min"], stats["max_observed"],
            ])

    # ── JSON 출력 ──
    json_path = out_dir / "reliability_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── HTML 리포트 ──
    html_path = out_dir / "reliability_report.html"
    generate_html_report(results, html_path)

    # ── 콘솔 요약 ──
    print(f"\n{'='*60}")
    print(f"  GAIM Lab 신뢰도 분석 결과")
    print(f"  {R}회 실행 × {N}개 영상 × {D}차원")
    print(f"{'='*60}")

    print(f"\n📊 Cronbach's α (내적 합치도)")
    print(f"   평균: {results['cronbachs_alpha']['mean']:.4f}")
    print(f"   범위: {results['cronbachs_alpha']['min']:.4f} ~ {results['cronbachs_alpha']['max']:.4f}")
    ca = results["cronbachs_alpha"]["mean"]
    print(f"   판정: {'✅ 우수 (≥0.8)' if ca >= 0.8 else '⚠️ 양호 (≥0.7)' if ca >= 0.7 else '❌ 미흡 (<0.7)'}")

    print(f"\n📊 재검사 신뢰도 (Test-Retest)")
    print(f"   평균 Pearson r: {retest['mean_r']:.4f}")
    print(f"   범위: {retest['min_r']:.4f} ~ {retest['max_r']:.4f}")
    print(f"   평균 절대차(MAD): {retest['mean_mad']:.2f}점")
    print(f"   ±5점 이내 일치: {retest['mean_agree_5pt']:.1f}%")
    print(f"   ±3점 이내 일치: {retest['mean_agree_3pt']:.1f}%")

    print(f"\n📊 ICC (급내 상관계수)")
    print(f"   {'차원':<14} {'ICC(2,1)':>9} {'ICC(2,k)':>9} {'SEM':>6} {'Retest r':>10}")
    print(f"   {'─'*52}")
    for key in ["total_score"] + DIM_KEYS:
        icc = icc_results[key]
        label = icc["label"]
        i21, i2k, sem = icc["icc21"], icc["icc2k"], icc["sem"]
        tr_r = retest["dimensions"].get(key, {}).get("mean_r", retest["mean_r"])
        print(f"   {label:<12} {i21:>9.4f} {i2k:>9.4f} {sem:>6.2f} {tr_r:>10.4f}")

    print(f"\n📁 결과 저장: {out_dir}")
    print(f"   • {csv_path.name}")
    print(f"   • {json_path.name}")
    print(f"   • {html_path.name}")

    return results, out_dir


# ── HTML 리포트 ───────────────────────────────────────────────────────
def generate_html_report(results: dict, path: Path):
    """신뢰도 분석 결과 HTML 리포트 생성 (Jinja2 템플릿 기반, v7.1)"""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        # jinja2 미설치 시 간단한 string.Template 폴백
        print("⚠️ jinja2 미설치 — pip install jinja2 권장")
        _generate_html_fallback(results, path)
        return

    ca = results["cronbachs_alpha"]
    icc = results["icc"]
    stats = results["dimension_stats"]
    retest = results["test_retest"]

    # ICC 테이블 데이터 준비
    icc_table = []
    for key in ["total_score"] + DIM_KEYS:
        d = icc[key]
        s = stats[key]
        icc_table.append({
            "label": d["label"], "max": d["max"],
            "icc21": d["icc21"], "icc2k": d["icc2k"], "sem": d["sem"],
            "cv": f'{d["cv_mean_pct"]:.1f}%' if "cv_mean_pct" in d else "—",
            "mean": s["mean"], "std": s["std"],
            "badge": "excellent" if d["icc21"] >= 0.75 else "good" if d["icc21"] >= 0.50 else "poor",
            "verdict": "우수" if d["icc21"] >= 0.75 else "양호" if d["icc21"] >= 0.50 else "미흡",
        })

    # Cronbach's α per-run 테이블
    alpha_table = []
    for rid, val in ca["per_run"].items():
        alpha_table.append({
            "run_id": rid.replace("batch_agents_", ""),
            "alpha": val,
            "badge": "excellent" if val >= 0.8 else "good" if val >= 0.7 else "poor",
            "verdict": "우수" if val >= 0.8 else "양호" if val >= 0.7 else "미흡",
        })

    # 재검사 테이블
    retest_table = []
    for k in DIM_KEYS:
        d = retest["dimensions"][k]
        retest_table.append({
            "label": d["label"], "mean_r": d["mean_r"],
            "min_r": d["min_r"], "max_r": d["max_r"], "mean_mad": d["mean_mad"],
            "badge": "excellent" if d["mean_r"] >= 0.7 else "good" if d["mean_r"] >= 0.5 else "poor",
            "verdict": "우수" if d["mean_r"] >= 0.7 else "양호" if d["mean_r"] >= 0.5 else "미흡",
        })

    # 차트 데이터
    icc_chart_labels = [icc[k]["label"] for k in ["total_score"] + DIM_KEYS]
    icc_chart_values = [icc[k]["icc21"] for k in ["total_score"] + DIM_KEYS]

    # Jinja2 렌더링
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("reliability_report.html")

    # retest dict를 dot-access 가능한 객체로 변환
    class DotDict(dict):
        __getattr__ = dict.__getitem__

    html = template.render(
        meta=DotDict(results["meta"]),
        ca=DotDict(ca),
        ca_mean=ca["mean"],
        retest=DotDict(retest),
        icc_table=icc_table,
        alpha_table=alpha_table,
        retest_table=retest_table,
        icc_chart_labels=icc_chart_labels,
        icc_chart_values=icc_chart_values,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _generate_html_fallback(results: dict, path: Path):
    """jinja2 미설치 시 최소한의 HTML 리포트 생성"""
    ca = results["cronbachs_alpha"]
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>GAIM Lab 신뢰도</title></head>
<body style="font-family:sans-serif;background:#1a1a2e;color:#e0e0ec;padding:2rem">
<h1>GAIM Lab 신뢰도 분석</h1>
<p>Cronbach's α 평균: <strong>{ca['mean']:.4f}</strong></p>
<p>⚠️ 전체 리포트를 보려면 <code>pip install jinja2</code> 후 재실행하세요.</p>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ── main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_analysis()
