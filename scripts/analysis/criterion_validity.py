#!/usr/bin/env python3
"""
GAIM Lab — 기준타당도 분석 (Criterion Validity)
================================================
전문가 채점 결과(expert_scores.csv)와 AI 채점 결과를 비교하여
측정 도구의 기준타당도를 검증합니다.

지표:
  • Pearson r     — 선형 상관
  • Spearman ρ    — 순위 상관
  • R²            — 결정계수
  • MAE / RMSE    — 오차 지표
  • Bland-Altman  — 일치도 분석
  • 등급 일치율     — 그레이드 매칭

Usage:
  python criterion_validity.py
  python criterion_validity.py --expert my_expert_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ── 설정 ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_BASE = BASE_DIR / "output"

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

GRADING = {"A+": 90, "A": 85, "A-": 80, "B+": 75, "B": 70,
           "B-": 65, "C+": 60, "C": 55, "C-": 50, "D": 0}


def score_to_grade(score: float) -> str:
    for g, cutoff in sorted(GRADING.items(), key=lambda x: -x[1]):
        if score >= cutoff:
            return g
    return "D"


# ── 데이터 로드 ───────────────────────────────────────────────────────
def load_expert_scores(path: Path) -> Dict[str, Dict[str, float]]:
    """전문가 채점 CSV 로드"""
    data = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            video = row["video"]
            scores = {}
            has_data = False
            for col in DIM_KEYS:
                val = row.get(col, "").strip()
                if val:
                    scores[col] = float(val)
                    has_data = True
            if has_data:
                total = row.get("total_score", "").strip()
                scores["total_score"] = float(total) if total else sum(scores.get(c, 0) for c in DIM_KEYS)
                data[video] = scores
    return data


def load_ai_scores(run_dir: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """최신 batch AI 채점 결과 로드 (기본: 가장 최근 배치)"""
    if run_dir:
        csv_path = Path(run_dir) / "agent_batch_summary.csv"
    else:
        # 가장 최신 배치 찾기
        batch_dirs = sorted([
            d for d in OUTPUT_BASE.iterdir()
            if d.is_dir() and d.name.startswith("batch_agents_")
        ])
        if not batch_dirs:
            print("❌ 배치 분석 결과를 찾을 수 없습니다.")
            sys.exit(1)
        csv_path = batch_dirs[-1] / "agent_batch_summary.csv"

    data = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "success":
                continue
            video = row["video"]
            scores = {}
            for col in DIM_KEYS:
                try:
                    scores[col] = float(row.get(col, 0))
                except (ValueError, TypeError):
                    scores[col] = 0.0
            scores["total_score"] = sum(scores[c] for c in DIM_KEYS)
            data[video] = scores

    print(f"✅ AI 채점: {csv_path.parent.name} ({len(data)}개 영상)")
    return data


# ── 상관 분석 ──────────────────────────────────────────────────────────
def pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    r = np.corrcoef(x, y)[0, 1]
    return float(r) if not np.isnan(r) else 0.0


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    from scipy import stats as sp_stats
    rho, _ = sp_stats.spearmanr(x, y)
    return float(rho)


def r_squared(x: np.ndarray, y: np.ndarray) -> float:
    r = pearson_r(x, y)
    return r ** 2


def mae(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.abs(x - y)))


def rmse(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - y) ** 2)))


def bland_altman(expert: np.ndarray, ai: np.ndarray) -> Dict:
    """Bland-Altman 일치도 분석"""
    means = (expert + ai) / 2
    diffs = ai - expert  # AI - Expert
    mean_diff = float(np.mean(diffs))  # Bias
    sd_diff = float(np.std(diffs, ddof=1))
    loa_upper = mean_diff + 1.96 * sd_diff
    loa_lower = mean_diff - 1.96 * sd_diff
    within_loa = float(np.mean(np.abs(diffs - mean_diff) <= 1.96 * sd_diff) * 100)

    return {
        "mean_diff": round(mean_diff, 3),
        "sd_diff": round(sd_diff, 3),
        "loa_upper": round(loa_upper, 3),
        "loa_lower": round(loa_lower, 3),
        "within_loa_pct": round(within_loa, 1),
        "means": means.tolist(),
        "diffs": diffs.tolist(),
    }


# ── 분석 실행 ──────────────────────────────────────────────────────────
def run_analysis(expert_path: Path):
    expert = load_expert_scores(expert_path)
    if not expert:
        print("❌ 전문가 채점 데이터가 비어 있습니다. expert_scores.csv에 점수를 입력하세요.")
        sys.exit(1)

    ai = load_ai_scores()

    # 공통 영상
    common = sorted(set(expert.keys()) & set(ai.keys()))
    if len(common) < 3:
        print(f"❌ 공통 영상이 {len(common)}개뿐입니다. 최소 3개 이상 필요합니다.")
        sys.exit(1)

    print(f"📊 분석 대상: {len(common)}개 영상")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_BASE / f"criterion_validity_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "meta": {
            "n_videos": len(common),
            "videos": common,
            "timestamp": timestamp,
        },
        "total": {},
        "dimensions": {},
        "grade_match": {},
    }

    # ── 총점 분석 ──
    exp_totals = np.array([expert[v]["total_score"] for v in common])
    ai_totals = np.array([ai[v]["total_score"] for v in common])

    results["total"] = {
        "pearson_r": round(pearson_r(exp_totals, ai_totals), 4),
        "spearman_rho": round(spearman_rho(exp_totals, ai_totals), 4),
        "r_squared": round(r_squared(exp_totals, ai_totals), 4),
        "mae": round(mae(exp_totals, ai_totals), 2),
        "rmse": round(rmse(exp_totals, ai_totals), 2),
        "bland_altman": bland_altman(exp_totals, ai_totals),
        "expert_mean": round(float(np.mean(exp_totals)), 2),
        "ai_mean": round(float(np.mean(ai_totals)), 2),
        "bias": round(float(np.mean(ai_totals - exp_totals)), 2),
    }

    # ── 차원별 분석 ──
    for col, label, max_score in DIM_COLS:
        exp_dim = np.array([expert[v].get(col, 0) for v in common])
        ai_dim = np.array([ai[v].get(col, 0) for v in common])

        # 전문가가 이 차원을 채점했는지 확인
        if np.all(exp_dim == 0):
            continue

        results["dimensions"][col] = {
            "label": label,
            "max": max_score,
            "pearson_r": round(pearson_r(exp_dim, ai_dim), 4),
            "spearman_rho": round(spearman_rho(exp_dim, ai_dim), 4),
            "r_squared": round(r_squared(exp_dim, ai_dim), 4),
            "mae": round(mae(exp_dim, ai_dim), 2),
            "rmse": round(rmse(exp_dim, ai_dim), 2),
            "expert_mean": round(float(np.mean(exp_dim)), 2),
            "ai_mean": round(float(np.mean(ai_dim)), 2),
            "bias": round(float(np.mean(ai_dim - exp_dim)), 2),
        }

    # ── 등급 일치 분석 ──
    exp_grades = [score_to_grade(expert[v]["total_score"]) for v in common]
    ai_grades = [score_to_grade(ai[v]["total_score"]) for v in common]
    exact_match = sum(1 for e, a in zip(exp_grades, ai_grades) if e == a)
    adjacent_match = sum(1 for e, a in zip(exp_grades, ai_grades)
                        if abs(list(GRADING.values()).index(GRADING[e]) - list(GRADING.values()).index(GRADING[a])) <= 1)

    grade_details = []
    for v, eg, ag in zip(common, exp_grades, ai_grades):
        grade_details.append({
            "video": v,
            "expert_score": float(expert[v]["total_score"]),
            "ai_score": float(ai[v]["total_score"]),
            "expert_grade": eg,
            "ai_grade": ag,
            "match": eg == ag,
        })

    results["grade_match"] = {
        "exact_match_pct": round(exact_match / len(common) * 100, 1),
        "adjacent_match_pct": round(adjacent_match / len(common) * 100, 1),
        "details": grade_details,
    }

    # ── CSV 출력 ──
    csv_path = out_dir / "criterion_validity_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "dimension", "label", "max_score",
            "Pearson_r", "Spearman_rho", "R²", "MAE", "RMSE",
            "expert_mean", "ai_mean", "bias",
        ])
        t = results["total"]
        w.writerow([
            "total_score", "총점", 100,
            t["pearson_r"], t["spearman_rho"], t["r_squared"],
            t["mae"], t["rmse"], t["expert_mean"], t["ai_mean"], t["bias"],
        ])
        for col in DIM_KEYS:
            if col in results["dimensions"]:
                d = results["dimensions"][col]
                w.writerow([
                    col, d["label"], d["max"],
                    d["pearson_r"], d["spearman_rho"], d["r_squared"],
                    d["mae"], d["rmse"], d["expert_mean"], d["ai_mean"], d["bias"],
                ])

    # ── JSON 출력 ──
    json_path = out_dir / "criterion_validity_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── HTML 리포트 ──
    html_path = out_dir / "criterion_validity_report.html"
    generate_html_report(results, html_path)

    # ── 콘솔 요약 ──
    print(f"\n{'='*60}")
    print(f"  GAIM Lab 기준타당도 분석 결과")
    print(f"  {len(common)}개 영상 · 전문가 vs AI")
    print(f"{'='*60}")

    t = results["total"]
    print(f"\n📊 총점 상관")
    print(f"   Pearson r:  {t['pearson_r']:.4f}")
    print(f"   Spearman ρ: {t['spearman_rho']:.4f}")
    print(f"   R²:         {t['r_squared']:.4f}")
    print(f"   MAE:        {t['mae']:.2f}점")
    print(f"   RMSE:       {t['rmse']:.2f}점")
    print(f"   편향(Bias):  {t['bias']:+.2f}점 (AI - 전문가)")

    ba = t["bland_altman"]
    print(f"\n📊 Bland-Altman 분석")
    print(f"   평균차: {ba['mean_diff']:.3f} ± {ba['sd_diff']:.3f}")
    print(f"   LoA: [{ba['loa_lower']:.2f}, {ba['loa_upper']:.2f}]")
    print(f"   LoA 이내: {ba['within_loa_pct']:.0f}%")

    gm = results["grade_match"]
    print(f"\n📊 등급 일치")
    print(f"   정확 일치: {gm['exact_match_pct']:.0f}%")
    print(f"   인접 일치: {gm['adjacent_match_pct']:.0f}%")

    if results["dimensions"]:
        print(f"\n📊 차원별 상관")
        print(f"   {'차원':<14} {'Pearson r':>10} {'MAE':>6} {'Bias':>7}")
        print(f"   {'─'*40}")
        for col in DIM_KEYS:
            if col in results["dimensions"]:
                d = results["dimensions"][col]
                print(f"   {d['label']:<12} {d['pearson_r']:>10.4f} {d['mae']:>6.2f} {d['bias']:>+7.2f}")

    print(f"\n📁 결과 저장: {out_dir}")
    print(f"   • {csv_path.name}")
    print(f"   • {json_path.name}")
    print(f"   • {html_path.name}")

    return results, out_dir


# ── HTML 리포트 ───────────────────────────────────────────────────────
def generate_html_report(results: dict, path: Path):
    """기준타당도 분석 HTML 리포트 생성"""
    meta = results["meta"]
    t = results["total"]
    ba = t["bland_altman"]
    gm = results["grade_match"]

    # 총점 산점도 데이터
    scatter_data = json.dumps([
        {"x": gd["expert_score"], "y": gd["ai_score"], "label": gd["video"]}
        for gd in gm["details"]
    ])

    # Bland-Altman 데이터
    ba_data = json.dumps([
        {"x": m, "y": d} for m, d in zip(ba["means"], ba["diffs"])
    ])

    # 차원별 상관 테이블
    dim_rows = ""
    dim_labels_list = []
    dim_r_values = []
    for col in DIM_KEYS:
        if col in results["dimensions"]:
            d = results["dimensions"][col]
            badge = "excellent" if d["pearson_r"] >= 0.7 else "good" if d["pearson_r"] >= 0.5 else "poor"
            verdict = "우수" if d["pearson_r"] >= 0.7 else "양호" if d["pearson_r"] >= 0.5 else "미흡"
            dim_rows += f"""
        <tr>
          <td><strong>{d['label']}</strong></td>
          <td>{d['max']}</td>
          <td><strong>{d['pearson_r']:.4f}</strong></td>
          <td>{d['spearman_rho']:.4f}</td>
          <td>{d['r_squared']:.4f}</td>
          <td>{d['mae']:.2f}</td>
          <td>{d['bias']:+.2f}</td>
          <td><span class="badge {badge}">{verdict}</span></td>
        </tr>"""
            dim_labels_list.append(d["label"])
            dim_r_values.append(d["pearson_r"])

    # 등급 일치 테이블
    grade_rows = ""
    for gd in gm["details"]:
        match_cls = "excellent" if gd["match"] else "poor"
        grade_rows += f"""
        <tr>
          <td>{gd['video']}</td>
          <td>{gd['expert_score']:.1f}</td>
          <td>{gd['ai_score']:.1f}</td>
          <td>{gd['expert_grade']}</td>
          <td>{gd['ai_grade']}</td>
          <td><span class="badge {match_cls}">{'✓' if gd['match'] else '✗'}</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GAIM Lab — 기준타당도 분석 리포트</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root {{
    --bg: #0f0f1a; --surface: #1a1a2e; --card: #16213e;
    --accent: #e040fb; --accent2: #ff6d00; --text: #e0e0ec;
    --text-dim: #888; --success: #00e676; --warning: #ffc107; --danger: #ff5252;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }}
  h1 {{ font-size: 2rem; text-align: center; margin-bottom: 0.5rem;
       background: linear-gradient(135deg, var(--accent), var(--accent2));
       -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .subtitle {{ text-align: center; color: var(--text-dim); margin-bottom: 2rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: var(--card); border-radius: 12px; padding: 1.5rem; text-align: center;
           border: 1px solid rgba(224,64,251,0.2); }}
  .card .value {{ font-size: 1.8rem; font-weight: 700;
                  background: linear-gradient(135deg, var(--accent), var(--accent2));
                  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .card .label {{ color: var(--text-dim); font-size: 0.82rem; margin-top: 0.3rem; }}
  .section {{ background: var(--surface); border-radius: 14px; padding: 1.8rem;
              margin-bottom: 1.5rem; border: 1px solid rgba(224,64,251,0.15); }}
  .section h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: var(--accent2); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th {{ background: rgba(224,64,251,0.15); padding: 0.7rem 0.4rem; text-align: center;
       font-weight: 600; color: var(--accent); border-bottom: 2px solid rgba(224,64,251,0.3); }}
  td {{ padding: 0.55rem 0.4rem; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); }}
  tr:hover {{ background: rgba(224,64,251,0.08); }}
  .badge {{ display: inline-block; padding: 0.2rem 0.7rem; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }}
  .badge.excellent {{ background: rgba(0,230,118,0.15); color: var(--success); }}
  .badge.good {{ background: rgba(255,193,7,0.15); color: var(--warning); }}
  .badge.poor {{ background: rgba(255,82,82,0.15); color: var(--danger); }}
  .chart-container {{ max-width: 500px; margin: 0 auto; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .interpretation {{ background: var(--card); border-radius: 10px; padding: 1.2rem; margin-top: 1rem;
                     border-left: 4px solid var(--accent); font-size: 0.88rem; line-height: 1.6; }}
  .interpretation h3 {{ color: var(--accent); margin-bottom: 0.5rem; }}
  @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  .footer {{ text-align: center; color: var(--text-dim); font-size: 0.8rem; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>🎯 GAIM Lab 기준타당도 분석 리포트</h1>
  <p class="subtitle">{meta['n_videos']}개 영상 · 전문가 채점 vs AI 채점</p>

  <div class="cards">
    <div class="card">
      <div class="value">{t['pearson_r']:.4f}</div>
      <div class="label">Pearson r</div>
    </div>
    <div class="card">
      <div class="value">{t['spearman_rho']:.4f}</div>
      <div class="label">Spearman ρ</div>
    </div>
    <div class="card">
      <div class="value">{t['r_squared']:.4f}</div>
      <div class="label">R²</div>
    </div>
    <div class="card">
      <div class="value">{t['mae']:.1f}</div>
      <div class="label">MAE (점)</div>
    </div>
    <div class="card">
      <div class="value">{t['bias']:+.1f}</div>
      <div class="label">편향 (AI-전문가)</div>
    </div>
    <div class="card">
      <div class="value">{gm['exact_match_pct']:.0f}%</div>
      <div class="label">등급 정확 일치</div>
    </div>
  </div>

  <div class="section">
    <h2>📈 전문가 vs AI 산점도</h2>
    <div class="grid-2">
      <div class="chart-container">
        <canvas id="scatterChart"></canvas>
      </div>
      <div class="chart-container">
        <canvas id="baChart"></canvas>
      </div>
    </div>
    <div class="interpretation">
      <h3>📖 Bland-Altman 분석</h3>
      평균차(Bias): {ba['mean_diff']:.2f} ± {ba['sd_diff']:.2f}<br>
      95% 일치한계(LoA): [{ba['loa_lower']:.1f}, {ba['loa_upper']:.1f}]<br>
      LoA 이내 비율: {ba['within_loa_pct']:.0f}%
    </div>
  </div>

  {"<div class='section'><h2>📊 차원별 상관분석</h2><table><thead><tr><th>차원</th><th>만점</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>MAE</th><th>Bias</th><th>판정</th></tr></thead><tbody>" + dim_rows + "</tbody></table></div>" if dim_rows else ""}

  <div class="section">
    <h2>🏷️ 등급 일치 분석</h2>
    <div class="cards" style="margin-bottom:1rem">
      <div class="card"><div class="value">{gm['exact_match_pct']:.0f}%</div><div class="label">정확 일치</div></div>
      <div class="card"><div class="value">{gm['adjacent_match_pct']:.0f}%</div><div class="label">인접 일치 (±1 등급)</div></div>
    </div>
    <table>
      <thead><tr><th>영상</th><th>전문가 점수</th><th>AI 점수</th><th>전문가 등급</th><th>AI 등급</th><th>일치</th></tr></thead>
      <tbody>{grade_rows}</tbody>
    </table>
  </div>

  <div class="footer">
    GAIM Lab Criterion Validity Analysis · Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  </div>
</div>

<script>
// 산점도
const scatterData = {scatter_data};
new Chart(document.getElementById('scatterChart'), {{
  type: 'scatter',
  data: {{
    datasets: [
      {{
        label: '영상별 점수',
        data: scatterData,
        backgroundColor: 'rgba(224,64,251,0.6)',
        borderColor: '#e040fb',
        pointRadius: 6,
      }},
      {{
        label: '완벽 일치선',
        data: [{{x:40,y:40}},{{x:100,y:100}}],
        type: 'line',
        borderColor: 'rgba(255,255,255,0.3)',
        borderDash: [5,5],
        pointRadius: 0,
        fill: false,
      }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: '전문가 vs AI 총점', color: '#aaa' }}, legend: {{ display: false }} }},
    scales: {{
      x: {{ title: {{ display: true, text: '전문가 점수', color: '#888' }}, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
      y: {{ title: {{ display: true, text: 'AI 점수', color: '#888' }}, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
    }},
  }},
}});

// Bland-Altman
const baDataPoints = {ba_data};
new Chart(document.getElementById('baChart'), {{
  type: 'scatter',
  data: {{
    datasets: [
      {{
        label: '차이',
        data: baDataPoints,
        backgroundColor: 'rgba(255,109,0,0.6)',
        borderColor: '#ff6d00',
        pointRadius: 6,
      }},
      {{
        label: 'Mean',
        data: [{{x: Math.min(...baDataPoints.map(p=>p.x))-2, y: {ba['mean_diff']}}}, {{x: Math.max(...baDataPoints.map(p=>p.x))+2, y: {ba['mean_diff']}}}],
        type: 'line', borderColor: '#fff', borderWidth: 1, pointRadius: 0, fill: false,
      }},
      {{
        label: '+1.96SD',
        data: [{{x: Math.min(...baDataPoints.map(p=>p.x))-2, y: {ba['loa_upper']}}}, {{x: Math.max(...baDataPoints.map(p=>p.x))+2, y: {ba['loa_upper']}}}],
        type: 'line', borderColor: '#ff5252', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false,
      }},
      {{
        label: '-1.96SD',
        data: [{{x: Math.min(...baDataPoints.map(p=>p.x))-2, y: {ba['loa_lower']}}}, {{x: Math.max(...baDataPoints.map(p=>p.x))+2, y: {ba['loa_lower']}}}],
        type: 'line', borderColor: '#ff5252', borderDash: [5,5], borderWidth: 1, pointRadius: 0, fill: false,
      }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Bland-Altman Plot', color: '#aaa' }}, legend: {{ display: false }} }},
    scales: {{
      x: {{ title: {{ display: true, text: '평균 (전문가+AI)/2', color: '#888' }}, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
      y: {{ title: {{ display: true, text: '차이 (AI-전문가)', color: '#888' }}, ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
    }},
  }},
}});
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ── main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GAIM Lab 기준타당도 분석")
    parser.add_argument("--expert", type=str, default="expert_scores.csv",
                        help="전문가 채점 CSV 파일 경로")
    args = parser.parse_args()

    expert_path = Path(args.expert)
    if not expert_path.is_absolute():
        expert_path = BASE_DIR / expert_path

    if not expert_path.exists():
        print(f"❌ 전문가 채점 파일을 찾을 수 없습니다: {expert_path}")
        print(f"   expert_scores.csv 템플릿에 점수를 입력한 후 다시 실행하세요.")
        sys.exit(1)

    run_analysis(expert_path)
