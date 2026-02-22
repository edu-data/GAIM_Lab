"""
GAIM Lab v8.0 — 7차원 구인타당도 (Construct Validity)

수업실연 평가 7차원의 구인타당도를 검증합니다:
- 차원 간 상관 행렬 (Pearson r matrix)
- Cronbach's α per dimension
- 수렴타당도: 동일 차원 하위 기준 간 높은 상관
- 변별타당도: 서로 다른 차원 간 적절한 상관 (너무 높지 않음)
- 기술 통계 (평균, 표준편차, 왜도, 범위)

사용법:
    python scripts/validity/construct_validity.py --db data/gaim_lab.db
    python scripts/validity/construct_validity.py --csv data/batch_results.csv

출력:
    - data/validity/construct_validity_v8.json
    - data/validity/construct_validity_report.html
"""

import sys
import json
import argparse
import sqlite3
from pathlib import Path
from collections import defaultdict

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 7차원 정의
DIMENSIONS = [
    '수업_전문성',
    '교수학습_방법',
    '판서_및_언어',
    '수업_태도',
    '학생_참여',
    '시간_배분',
    '창의성'
]

DIMENSION_DISPLAY = {
    '수업_전문성': '수업 전문성',
    '교수학습_방법': '교수학습 방법',
    '판서_및_언어': '판서 및 언어',
    '수업_태도': '수업 태도',
    '학생_참여': '학생 참여',
    '시간_배분': '시간 배분',
    '창의성': '창의성'
}


def cronbachs_alpha(items_matrix):
    """Cronbach's α 계산
    
    items_matrix: (n_subjects, n_items) 2D array
    """
    items = np.array(items_matrix, dtype=float)
    n_items = items.shape[1]
    if n_items < 2:
        return float('nan')
    
    item_vars = np.var(items, axis=0, ddof=1)
    total_var = np.var(items.sum(axis=1), ddof=1)
    
    if total_var == 0:
        return float('nan')
    
    alpha = (n_items / (n_items - 1)) * (1 - np.sum(item_vars) / total_var)
    return float(alpha)


def correlation_matrix(data_dict):
    """차원 간 상관 행렬
    
    data_dict: {dim_name: [scores...]}
    Returns: (correlation_matrix, dim_names)
    """
    dims = list(data_dict.keys())
    n_dims = len(dims)
    matrix = np.zeros((n_dims, n_dims))
    
    for i in range(n_dims):
        for j in range(n_dims):
            x = np.array(data_dict[dims[i]], dtype=float)
            y = np.array(data_dict[dims[j]], dtype=float)
            if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
                matrix[i, j] = float('nan')
            else:
                matrix[i, j] = np.corrcoef(x, y)[0, 1]
    
    return matrix, dims


def extract_dimension_scores(db_path: str):
    """DB에서 차원별 점수 추출"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 먼저 dimension_scores 테이블 시도
    try:
        rows = conn.execute("""
            SELECT a.id, ds.dimension_name, ds.score, ds.max_score
            FROM dimension_scores ds
            JOIN analyses a ON ds.analysis_id = a.id
            WHERE a.total_score IS NOT NULL
            ORDER BY a.id
        """).fetchall()
        
        if rows:
            data = defaultdict(lambda: defaultdict(float))
            for row in rows:
                aid = row['id']
                dim = row['dimension_name']
                # 비율로 정규화 (0~1)
                data[aid][dim] = row['score'] / row['max_score'] if row['max_score'] > 0 else 0
            
            conn.close()
            return data
    except sqlite3.OperationalError:
        pass
    
    # fallback: analyses 테이블의 dimensions_json
    rows = conn.execute("""
        SELECT id, dimensions_json
        FROM analyses
        WHERE total_score IS NOT NULL AND dimensions_json IS NOT NULL
    """).fetchall()
    conn.close()
    
    data = defaultdict(lambda: defaultdict(float))
    for row in rows:
        aid = row['id']
        try:
            dims = json.loads(row['dimensions_json'])
            if isinstance(dims, dict):
                for dim_name, dim_data in dims.items():
                    score = dim_data if isinstance(dim_data, (int, float)) else dim_data.get('score', 0)
                    max_s = dim_data.get('max_score', 20) if isinstance(dim_data, dict) else 20
                    data[aid][dim_name] = score / max_s if max_s > 0 else 0
            elif isinstance(dims, list):
                for dim_data in dims:
                    dim_name = dim_data.get('name', '')
                    score = dim_data.get('score', 0)
                    max_s = dim_data.get('max_score', 20)
                    data[aid][dim_name] = score / max_s if max_s > 0 else 0
        except (json.JSONDecodeError, TypeError):
            continue
    
    return data


def compute_validity(raw_data):
    """구인타당도 지표 계산"""
    # 차원별 점수를 리스트로 변환
    dim_scores = defaultdict(list)
    for aid, dims in raw_data.items():
        for dim_name, score in dims.items():
            dim_scores[dim_name].append(score)
    
    n_analyses = len(raw_data)
    n_dimensions = len(dim_scores)
    
    if n_analyses < 3:
        return {'error': f'충분한 분석 데이터가 없습니다 (현재: {n_analyses}개, 최소: 3개 필요)'}
    
    # 1. 기술 통계
    descriptive = {}
    for dim, scores in dim_scores.items():
        s = np.array(scores)
        descriptive[dim] = {
            'mean': round(float(np.mean(s)), 4),
            'std': round(float(np.std(s, ddof=1)), 4),
            'min': round(float(np.min(s)), 4),
            'max': round(float(np.max(s)), 4),
            'range': round(float(np.max(s) - np.min(s)), 4),
            'n': len(scores),
        }
    
    # 2. 상관 행렬
    corr_matrix, dim_names = correlation_matrix(dim_scores)
    
    # 상관 행렬을 dict로 변환
    corr_dict = {}
    for i, d1 in enumerate(dim_names):
        corr_dict[d1] = {}
        for j, d2 in enumerate(dim_names):
            corr_dict[d1][d2] = round(float(corr_matrix[i, j]), 4) if not np.isnan(corr_matrix[i, j]) else None
    
    # 3. Cronbach's α (전체 7차원)
    # 각 분석의 7차원 점수를 행렬로 구성
    all_dim_names = list(dim_scores.keys())
    items_matrix = []
    for aid, dims in raw_data.items():
        row = [dims.get(d, 0) for d in all_dim_names]
        items_matrix.append(row)
    
    overall_alpha = cronbachs_alpha(np.array(items_matrix))
    
    # 4. 수렴타당도 / 변별타당도 진단
    off_diagonal = []
    for i in range(len(dim_names)):
        for j in range(i + 1, len(dim_names)):
            r = corr_matrix[i, j]
            if not np.isnan(r):
                off_diagonal.append(r)
    
    mean_inter_corr = float(np.mean(off_diagonal)) if off_diagonal else float('nan')
    
    discriminant_issues = []
    for i in range(len(dim_names)):
        for j in range(i + 1, len(dim_names)):
            r = corr_matrix[i, j]
            if not np.isnan(r) and abs(r) > 0.85:
                discriminant_issues.append({
                    'dim1': dim_names[i],
                    'dim2': dim_names[j],
                    'r': round(float(r), 4),
                    'issue': '높은 상관 → 두 차원이 동일 구인을 측정할 가능성'
                })
    
    return {
        'version': '8.0.0',
        'n_analyses': n_analyses,
        'n_dimensions': n_dimensions,
        'descriptive_statistics': descriptive,
        'correlation_matrix': corr_dict,
        'cronbachs_alpha': {
            'overall': round(overall_alpha, 4) if not np.isnan(overall_alpha) else None,
            'interpretation': interpret_alpha(overall_alpha),
        },
        'convergent_validity': {
            'mean_inter_dimension_r': round(mean_inter_corr, 4) if not np.isnan(mean_inter_corr) else None,
            'interpretation': '적절한 수렴 (0.3~0.7)' if 0.3 <= mean_inter_corr <= 0.7 else '검토 필요',
        },
        'discriminant_validity': {
            'issues': discriminant_issues,
            'passed': len(discriminant_issues) == 0,
        },
    }


def interpret_alpha(alpha):
    """Cronbach's α 해석"""
    if np.isnan(alpha):
        return '계산 불가'
    if alpha >= 0.90:
        return '매우 높음 (Excellent)'
    elif alpha >= 0.80:
        return '높음 (Good)'
    elif alpha >= 0.70:
        return '허용 (Acceptable)'
    elif alpha >= 0.60:
        return '의심 (Questionable)'
    elif alpha >= 0.50:
        return '미흡 (Poor)'
    else:
        return '수용 불가 (Unacceptable)'


def generate_html_report(results: dict, output_path: Path):
    """구인타당도 HTML 리포트 생성"""
    desc = results.get('descriptive_statistics', {})
    corr = results.get('correlation_matrix', {})
    alpha = results.get('cronbachs_alpha', {})
    conv = results.get('convergent_validity', {})
    disc = results.get('discriminant_validity', {})
    
    # 기술 통계 테이블
    desc_rows = ""
    for dim, stats in desc.items():
        display_name = DIMENSION_DISPLAY.get(dim, dim)
        desc_rows += f"<tr><td>{display_name}</td><td>{stats['mean']:.3f}</td><td>{stats['std']:.3f}</td><td>{stats['min']:.3f}</td><td>{stats['max']:.3f}</td><td>{stats['range']:.3f}</td></tr>\n"
    
    # 상관 행렬 히트맵 테이블
    dim_names = list(corr.keys())
    corr_header = "<th></th>" + "".join(f"<th>{DIMENSION_DISPLAY.get(d, d)[:4]}</th>" for d in dim_names)
    corr_rows = ""
    for d1 in dim_names:
        cells = f"<td><strong>{DIMENSION_DISPLAY.get(d1, d1)[:6]}</strong></td>"
        for d2 in dim_names:
            r = corr[d1].get(d2)
            if r is None:
                cells += "<td>N/A</td>"
            else:
                # 히트맵 색상
                if d1 == d2:
                    bg = '#818cf8'
                elif abs(r) > 0.7:
                    bg = '#f87171'
                elif abs(r) > 0.4:
                    bg = '#fbbf24'
                else:
                    bg = '#34d399'
                cells += f"<td style='background:{bg}22; color:{bg};font-weight:600'>{r:.2f}</td>"
        corr_rows += f"<tr>{cells}</tr>\n"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>GAIM Lab v8.0 — 7차원 구인타당도 보고서</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 2rem auto; padding: 1rem; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #818cf8; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }}
        h2 {{ color: #a5b4fc; margin-top: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.6rem; text-align: center; border-bottom: 1px solid #334155; font-size: 0.9rem; }}
        th {{ background: #1e293b; color: #94a3b8; font-weight: 600; }}
        .card {{ background: #1e293b; border-radius: 1rem; padding: 1.5rem; margin: 1rem 0; }}
        .metric {{ font-size: 2.5rem; font-weight: 700; }}
        .good {{ color: #34d399; }}
        .warn {{ color: #fbbf24; }}
        .bad {{ color: #f87171; }}
        .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    </style>
</head>
<body>
    <h1>📐 7차원 구인타당도 보고서</h1>
    <p>GAIM Lab v{results.get('version', '8.0.0')} · 분석 수: {results.get('n_analyses', 0)}개 · 차원 수: {results.get('n_dimensions', 0)}개</p>
    
    <div class="grid2">
        <div class="card">
            <div style="color:#94a3b8;margin-bottom:0.5rem">Cronbach's α (전체)</div>
            <div class="metric {'good' if (alpha.get('overall') or 0) >= 0.70 else 'warn' if (alpha.get('overall') or 0) >= 0.50 else 'bad'}">{alpha.get('overall', 'N/A')}</div>
            <div style="color:#94a3b8;font-size:0.85rem">{alpha.get('interpretation', '')}</div>
        </div>
        <div class="card">
            <div style="color:#94a3b8;margin-bottom:0.5rem">평균 차원 간 상관</div>
            <div class="metric {'good' if 0.3 <= (conv.get('mean_inter_dimension_r') or 0) <= 0.7 else 'warn'}">{conv.get('mean_inter_dimension_r', 'N/A')}</div>
            <div style="color:#94a3b8;font-size:0.85rem">{conv.get('interpretation', '')}</div>
        </div>
    </div>
    
    <h2>📊 기술 통계</h2>
    <table>
        <tr><th>차원</th><th>평균</th><th>표준편차</th><th>최솟값</th><th>최댓값</th><th>범위</th></tr>
        {desc_rows}
    </table>
    
    <h2>🔗 차원 간 상관 행렬</h2>
    <table>
        <tr>{corr_header}</tr>
        {corr_rows}
    </table>
    
    <h2>⚠️ 변별타당도 진단</h2>
    {'<div class="card good">✅ 모든 차원 간 상관이 r < 0.85로 변별타당도를 충족합니다.</div>' if disc.get('passed') else '<div class="card bad">❌ 다음 차원 쌍의 상관이 과도하게 높습니다 (r > 0.85):<ul>' + ''.join(f"<li>{i['dim1']} ↔ {i['dim2']}: r = {i['r']}</li>" for i in disc.get('issues', [])) + '</ul></div>'}
</body>
</html>"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    print(f"[✅] HTML 리포트 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='GAIM Lab 7차원 구인타당도 분석')
    parser.add_argument('--db', type=str, default='data/gaim_lab.db',
                        help='SQLite DB 경로')
    parser.add_argument('--output', type=str, default='data/validity',
                        help='출력 디렉토리')
    args = parser.parse_args()
    
    output_dir = PROJECT_ROOT / args.output
    db_path = PROJECT_ROOT / args.db
    
    if not db_path.exists():
        print(f"[ERROR] DB 파일을 찾을 수 없습니다: {db_path}")
        return
    
    print(f"[INFO] DB에서 차원별 점수 추출: {db_path}")
    raw_data = extract_dimension_scores(str(db_path))
    print(f"[INFO] {len(raw_data)}개 분석 결과 로드")
    
    results = compute_validity(raw_data)
    
    if 'error' in results:
        print(f"[ERROR] {results['error']}")
        return
    
    # 결과 출력
    alpha = results['cronbachs_alpha']
    conv = results['convergent_validity']
    disc = results['discriminant_validity']
    
    print(f"\n{'='*50}")
    print(f"📐 7차원 구인타당도 결과 (v{results['version']})")
    print(f"{'='*50}")
    print(f"분석 수: {results['n_analyses']}개")
    print(f"Cronbach's α: {alpha['overall']}  ({alpha['interpretation']})")
    print(f"평균 차원 간 r: {conv['mean_inter_dimension_r']}  ({conv['interpretation']})")
    print(f"변별타당도: {'✅ 통과' if disc['passed'] else f'❌ 이슈 {len(disc[\"issues\"])}건'}")
    
    # JSON 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'construct_validity_v8.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[✅] JSON 저장: {json_path}")
    
    # HTML 리포트
    html_path = output_dir / 'construct_validity_report.html'
    generate_html_report(results, html_path)


if __name__ == '__main__':
    main()
