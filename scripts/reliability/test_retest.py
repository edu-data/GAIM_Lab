"""
GAIM Lab v8.0 — 검사-재검사 신뢰도 (Test-Retest Reliability)

동일 영상을 동일 버전에서 N회 분석하여 결과의 일관성을 검증합니다.

사용법:
    python scripts/reliability/test_retest.py --video video/20251209_142648.mp4 --runs 3
    python scripts/reliability/test_retest.py --db data/gaim_lab.db  # 기존 DB에서 중복 분석 추출

출력:
    - 총점 Pearson r, ICC
    - 차원별 Pearson r
    - ±3점, ±5점 일치율
    - data/reliability/test_retest_v8.csv
    - data/reliability/test_retest_report.html
"""

import sys
import os
import json
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import numpy as np

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def pearson_r(x, y):
    """피어슨 상관계수 계산"""
    if len(x) < 2:
        return float('nan')
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if np.std(x) == 0 or np.std(y) == 0:
        return float('nan')
    return float(np.corrcoef(x, y)[0, 1])


def icc_two_way(scores_matrix):
    """ICC(2,1) — 2-way random, single measures
    
    scores_matrix: (n_subjects, n_raters) 2D array
    """
    scores = np.array(scores_matrix, dtype=float)
    n, k = scores.shape
    if n < 2 or k < 2:
        return float('nan')
    
    # 평균
    grand_mean = scores.mean()
    row_means = scores.mean(axis=1)
    col_means = scores.mean(axis=0)
    
    # 분산 요소
    ss_total = np.sum((scores - grand_mean) ** 2)
    ss_rows = k * np.sum((row_means - grand_mean) ** 2)
    ss_cols = n * np.sum((col_means - grand_mean) ** 2)
    ss_error = ss_total - ss_rows - ss_cols
    
    # 평균 제곱
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    
    # ICC(2,1)
    denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    if denom == 0:
        return float('nan')
    
    icc = (ms_rows - ms_error) / denom
    return float(icc)


def agreement_rate(scores1, scores2, threshold=3):
    """±threshold점 일치율"""
    if len(scores1) == 0:
        return 0.0
    diffs = np.abs(np.array(scores1) - np.array(scores2))
    return float(np.mean(diffs <= threshold) * 100)


def extract_from_db(db_path: str):
    """기존 DB에서 동일 영상의 중복 분석 결과 추출"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 동일 video_path를 가진 분석 결과를 그룹별로 추출
    rows = conn.execute("""
        SELECT video_path, total_score, dimensions_json, created_at
        FROM analyses
        WHERE total_score IS NOT NULL
        ORDER BY video_path, created_at
    """).fetchall()
    conn.close()
    
    groups = defaultdict(list)
    for row in rows:
        video = row['video_path'] or 'unknown'
        # video_path에서 파일명만 추출
        video_key = Path(video).stem
        score = row['total_score']
        dims = json.loads(row['dimensions_json']) if row['dimensions_json'] else {}
        groups[video_key].append({
            'total_score': score,
            'dimensions': dims,
            'created_at': row['created_at']
        })
    
    return groups


def compute_reliability(groups: dict):
    """신뢰도 지표 계산
    
    groups: {video_key: [{'total_score': ..., 'dimensions': {...}}, ...]}
    """
    # 2회 이상 분석된 영상만 필터
    paired = {k: v for k, v in groups.items() if len(v) >= 2}
    
    if not paired:
        return {
            'error': '2회 이상 분석된 영상이 없습니다. --runs 옵션으로 반복 분석을 실행하세요.',
            'total_pairs': 0,
        }
    
    # 첫 번째와 두 번째 분석 결과를 비교 (Test-Retest)
    scores_run1 = []
    scores_run2 = []
    dim_scores = defaultdict(lambda: {'run1': [], 'run2': []})
    
    for video_key, runs in paired.items():
        run1 = runs[0]
        run2 = runs[1]
        
        scores_run1.append(run1['total_score'])
        scores_run2.append(run2['total_score'])
        
        # 차원별 점수
        for dim_name, dim_data in run1.get('dimensions', {}).items():
            score1 = dim_data if isinstance(dim_data, (int, float)) else dim_data.get('score', 0)
            score2 = 0
            if dim_name in run2.get('dimensions', {}):
                d2 = run2['dimensions'][dim_name]
                score2 = d2 if isinstance(d2, (int, float)) else d2.get('score', 0)
            dim_scores[dim_name]['run1'].append(score1)
            dim_scores[dim_name]['run2'].append(score2)
    
    # 총점 분석
    r_total = pearson_r(scores_run1, scores_run2)
    
    # ICC 계산 (모든 paired의 총점)
    icc_matrix = np.array([scores_run1, scores_run2]).T  # (n_videos, 2_runs)
    icc_value = icc_two_way(icc_matrix)
    
    # 일치율
    agree_3 = agreement_rate(scores_run1, scores_run2, threshold=3)
    agree_5 = agreement_rate(scores_run1, scores_run2, threshold=5)
    
    # 차원별 상관
    dim_reliability = {}
    for dim_name, data in dim_scores.items():
        r = pearson_r(data['run1'], data['run2'])
        dim_reliability[dim_name] = {
            'pearson_r': round(r, 4) if not np.isnan(r) else None,
            'n_pairs': len(data['run1']),
        }
    
    # MAD (평균 절대 편차)
    diffs = np.abs(np.array(scores_run1) - np.array(scores_run2))
    mad = float(np.mean(diffs))
    
    return {
        'version': '8.0.0',
        'timestamp': datetime.now().isoformat(),
        'total_pairs': len(paired),
        'total_videos_analyzed': sum(len(v) for v in groups.values()),
        'total_score': {
            'pearson_r': round(r_total, 4) if not np.isnan(r_total) else None,
            'icc_2_1': round(icc_value, 4) if not np.isnan(icc_value) else None,
            'mad': round(mad, 2),
            'agreement_3pt': round(agree_3, 1),
            'agreement_5pt': round(agree_5, 1),
        },
        'dimension_reliability': dim_reliability,
        'interpretation': {
            'pearson_r': interpret_r(r_total),
            'icc': interpret_icc(icc_value),
            'agreement_3pt': '합격' if agree_3 >= 70 else '미달',
        },
        'targets': {
            'pearson_r': '>= 0.80',
            'agreement_3pt': '>= 70%',
        },
    }


def interpret_r(r):
    """Pearson r 해석"""
    if np.isnan(r):
        return '계산 불가'
    if r >= 0.90:
        return '매우 높음 (Excellent)'
    elif r >= 0.80:
        return '높음 (Good) ✅'
    elif r >= 0.70:
        return '허용 (Acceptable)'
    elif r >= 0.60:
        return '의심 (Questionable)'
    else:
        return '낮음 (Poor) ❌'


def interpret_icc(icc):
    """ICC 해석 (Cicchetti, 1994 기준)"""
    if np.isnan(icc):
        return '계산 불가'
    if icc >= 0.75:
        return '우수 (Excellent)'
    elif icc >= 0.60:
        return '양호 (Good)'
    elif icc >= 0.40:
        return '보통 (Fair)'
    else:
        return '미흡 (Poor)'


def generate_html_report(results: dict, output_path: Path):
    """HTML 리포트 생성"""
    ts = results.get('total_score', {})
    dims = results.get('dimension_reliability', {})
    interp = results.get('interpretation', {})
    
    dim_rows = ""
    for name, data in dims.items():
        r_val = data.get('pearson_r', 'N/A')
        r_str = f"{r_val:.4f}" if isinstance(r_val, float) else str(r_val)
        dim_rows += f"<tr><td>{name}</td><td>{r_str}</td><td>{data.get('n_pairs', 0)}</td></tr>\n"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>GAIM Lab v8.0 — 검사-재검사 신뢰도 보고서</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 2rem auto; padding: 1rem; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #818cf8; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }}
        h2 {{ color: #a5b4fc; margin-top: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #1e293b; color: #94a3b8; font-weight: 600; }}
        .metric {{ font-size: 2rem; font-weight: 700; }}
        .good {{ color: #34d399; }}
        .warn {{ color: #fbbf24; }}
        .bad {{ color: #f87171; }}
        .card {{ background: #1e293b; border-radius: 1rem; padding: 1.5rem; margin: 1rem 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
        .interpretation {{ font-size: 0.9rem; color: #94a3b8; }}
    </style>
</head>
<body>
    <h1>🔍 검사-재검사 신뢰도 보고서</h1>
    <p>GAIM Lab v{results.get('version', '8.0.0')} · {results.get('timestamp', '')[:10]} · 분석 쌍: {results.get('total_pairs', 0)}개</p>
    
    <h2>📊 총점 신뢰도</h2>
    <div class="grid">
        <div class="card">
            <div class="interpretation">Pearson r</div>
            <div class="metric {'good' if (ts.get('pearson_r') or 0) >= 0.80 else 'warn' if (ts.get('pearson_r') or 0) >= 0.60 else 'bad'}">{ts.get('pearson_r', 'N/A')}</div>
            <div class="interpretation">{interp.get('pearson_r', '')}</div>
        </div>
        <div class="card">
            <div class="interpretation">ICC(2,1)</div>
            <div class="metric {'good' if (ts.get('icc_2_1') or 0) >= 0.75 else 'warn' if (ts.get('icc_2_1') or 0) >= 0.60 else 'bad'}">{ts.get('icc_2_1', 'N/A')}</div>
            <div class="interpretation">{interp.get('icc', '')}</div>
        </div>
        <div class="card">
            <div class="interpretation">±3점 일치율</div>
            <div class="metric {'good' if (ts.get('agreement_3pt') or 0) >= 70 else 'bad'}">{ts.get('agreement_3pt', 'N/A')}%</div>
            <div class="interpretation">목표: ≥ 70%</div>
        </div>
    </div>
    
    <div class="card">
        <p><strong>MAD (평균 절대 편차):</strong> {ts.get('mad', 'N/A')}점</p>
        <p><strong>±5점 일치율:</strong> {ts.get('agreement_5pt', 'N/A')}%</p>
    </div>
    
    <h2>📐 차원별 신뢰도</h2>
    <table>
        <tr><th>차원</th><th>Pearson r</th><th>분석 쌍</th></tr>
        {dim_rows}
    </table>
    
    <h2>🎯 목표 달성 여부</h2>
    <table>
        <tr><th>지표</th><th>현재</th><th>목표</th><th>판정</th></tr>
        <tr>
            <td>Pearson r</td>
            <td>{ts.get('pearson_r', 'N/A')}</td>
            <td>≥ 0.80</td>
            <td>{'✅' if (ts.get('pearson_r') or 0) >= 0.80 else '❌'}</td>
        </tr>
        <tr>
            <td>±3점 일치율</td>
            <td>{ts.get('agreement_3pt', 'N/A')}%</td>
            <td>≥ 70%</td>
            <td>{'✅' if (ts.get('agreement_3pt') or 0) >= 70 else '❌'}</td>
        </tr>
    </table>
</body>
</html>"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    print(f"[✅] HTML 리포트 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='GAIM Lab 검사-재검사 신뢰도 분석')
    parser.add_argument('--db', type=str, default='data/gaim_lab.db',
                        help='SQLite DB 경로 (기존 분석 결과에서 추출)')
    parser.add_argument('--video', type=str, default=None,
                        help='반복 분석할 영상 경로 (새로 분석 실행)')
    parser.add_argument('--runs', type=int, default=2,
                        help='반복 분석 횟수 (--video와 함께 사용)')
    parser.add_argument('--output', type=str, default='data/reliability',
                        help='출력 디렉토리')
    args = parser.parse_args()
    
    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = PROJECT_ROOT / args.db
    
    if args.video:
        # TODO: 반복 분석 실행 후 DB에 저장
        print(f"[INFO] 영상 {args.video}를 {args.runs}회 반복 분석합니다...")
        print("[WARN] 반복 분석 실행은 아직 구현되지 않았습니다. --db 옵션으로 기존 결과를 분석하세요.")
        return
    
    if not db_path.exists():
        print(f"[ERROR] DB 파일을 찾을 수 없습니다: {db_path}")
        print("[TIP] 먼저 배치 분석을 2회 이상 실행하세요.")
        return
    
    print(f"[INFO] DB에서 분석 결과 추출: {db_path}")
    groups = extract_from_db(str(db_path))
    
    print(f"[INFO] 총 {len(groups)}개 영상, {sum(len(v) for v in groups.values())}개 분석 결과")
    
    results = compute_reliability(groups)
    
    if 'error' in results:
        print(f"[ERROR] {results['error']}")
        return
    
    # 결과 출력
    ts = results['total_score']
    print(f"\n{'='*50}")
    print(f"📊 검사-재검사 신뢰도 결과 (v{results['version']})")
    print(f"{'='*50}")
    print(f"분석 쌍: {results['total_pairs']}개")
    print(f"Pearson r: {ts['pearson_r']}  ({results['interpretation']['pearson_r']})")
    print(f"ICC(2,1):  {ts['icc_2_1']}  ({results['interpretation']['icc']})")
    print(f"MAD:       {ts['mad']}점")
    print(f"±3점 일치: {ts['agreement_3pt']}%  ({results['interpretation']['agreement_3pt']})")
    print(f"±5점 일치: {ts['agreement_5pt']}%")
    
    # CSV 저장
    csv_path = output_dir / 'test_retest_v8.csv'
    import csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value', 'Interpretation'])
        writer.writerow(['Pearson r', ts['pearson_r'], results['interpretation']['pearson_r']])
        writer.writerow(['ICC(2,1)', ts['icc_2_1'], results['interpretation']['icc']])
        writer.writerow(['MAD', ts['mad'], ''])
        writer.writerow(['±3pt Agreement', f"{ts['agreement_3pt']}%", results['interpretation']['agreement_3pt']])
        writer.writerow(['±5pt Agreement', f"{ts['agreement_5pt']}%", ''])
    print(f"\n[✅] CSV 저장: {csv_path}")
    
    # JSON 저장
    json_path = output_dir / 'test_retest_v8.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[✅] JSON 저장: {json_path}")
    
    # HTML 리포트
    html_path = output_dir / 'test_retest_report.html'
    generate_html_report(results, html_path)


if __name__ == '__main__':
    main()
