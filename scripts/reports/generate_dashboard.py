"""
GAIM Lab v5.0 - 배치 분석 결과 시각화
Chart.js를 사용한 인터랙티브 대시보드 생성

v5.0: agent_result.json 형식 지원 + 화자분리/발화분석 지표 추가
"""
import json
from pathlib import Path
from datetime import datetime


def generate_visualization_dashboard(batch_dir: str = None):
    """분석 결과 시각화 대시보드 HTML 생성"""

    # 최신 배치 디렉토리 자동 감지
    if batch_dir:
        batch_path = Path(batch_dir)
    else:
        output_dir = Path(r"D:\AI\GAIM_Lab\output")
        batch_dirs = sorted([
            d for d in output_dir.iterdir()
            if d.is_dir() and d.name.startswith("batch_agents_")
        ])
        if not batch_dirs:
            print("❌ 배치 결과 폴더를 찾을 수 없습니다.")
            return None
        batch_path = batch_dirs[-1]

    print(f"📂 배치 폴더: {batch_path.name}")

    # 모든 결과 수집 (v5.0 agent_result.json 형식)
    results = []
    for video_dir in sorted(batch_path.iterdir()):
        if not video_dir.is_dir():
            continue

        # v5.0 에이전트 파이프라인 결과
        result_file = video_dir / "agent_result.json"
        if not result_file.exists():
            continue

        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        ped = data.get("pedagogy", {})
        stt = data.get("stt", {})
        disc = data.get("discourse", {})

        entry = {
            "video_name": video_dir.name,
            "total_score": ped.get("total_score", 0),
            "grade": ped.get("grade", "N/A"),
            "dimensions": ped.get("dimensions", []),
            # v5.0 화자 분리
            "teacher_ratio": stt.get("teacher_ratio", 0),
            "student_turns": stt.get("student_turns", 0),
            "interaction_count": stt.get("interaction_count", 0),
            "question_count": stt.get("question_count", 0),
            "word_count": stt.get("word_count", 0),
            # v5.0 발화 분석
            "has_discourse": bool(disc and disc.get("question_types")),
            "discourse": disc,
        }
        results.append(entry)

    if not results:
        print("❌ 분석 결과가 없습니다.")
        return None

    print(f"📊 {len(results)}개 영상 결과 수집 완료")

    # 통계 계산
    total_scores = [r["total_score"] for r in results]
    avg_score = sum(total_scores) / len(total_scores)
    max_score = max(total_scores)
    min_score = min(total_scores)
    score_range = max_score - min_score

    # 등급 분포 (v5.0 세분화)
    grade_counts = {}
    for r in results:
        g = r["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1

    # 차원별 평균
    dim_names = ["수업 전문성", "교수학습 방법", "판서 및 언어", "수업 태도", "학생 참여", "시간 배분", "창의성"]
    dim_max = [20, 20, 15, 15, 15, 10, 5]
    dim_avgs = []
    for dim_name in dim_names:
        scores = []
        for r in results:
            for d in r.get("dimensions", []):
                if d.get("name") == dim_name:
                    scores.append(d.get("score", 0))
        dim_avgs.append(sum(scores) / len(scores) if scores else 0)

    # v5.0: 화자 분리 평균
    avg_teacher_ratio = sum(r["teacher_ratio"] for r in results) / len(results)
    avg_student_turns = sum(r["student_turns"] for r in results) / len(results)
    avg_interactions = sum(r["interaction_count"] for r in results) / len(results)
    avg_questions = sum(r["question_count"] for r in results) / len(results)

    # 등급별 색상 / 라벨
    grade_labels = list(grade_counts.keys())
    grade_values = list(grade_counts.values())
    grade_colors = []
    for g in grade_labels:
        if g.startswith("A"):
            grade_colors.append("#4CAF50")
        elif g.startswith("B"):
            grade_colors.append("#2196F3")
        elif g.startswith("C"):
            grade_colors.append("#FFC107")
        else:
            grade_colors.append("#FF5722")

    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIM Lab v5.0 배치 분석 대시보드</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 40px 30px;
            background: rgba(255,255,255,0.04);
            border-radius: 24px;
            margin-bottom: 30px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header .version {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .header p {{ color: #8888aa; font-size: 0.95rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(102,126,234,0.15);
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-label {{ color: #8888aa; margin-top: 6px; font-size: 0.85rem; }}
        .section-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #a78bfa;
            margin: 30px 0 16px;
            padding-left: 4px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .chart-card h3 {{
            margin-bottom: 16px;
            color: #a78bfa;
            font-weight: 600;
            font-size: 1rem;
        }}
        .chart-container {{ position: relative; height: 300px; }}
        .table-container {{
            background: rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            overflow-x: auto;
            margin-bottom: 30px;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th, td {{
            padding: 10px 12px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        th {{ color: #a78bfa; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }}
        tr:hover {{ background: rgba(255,255,255,0.04); }}
        .grade-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .grade-A {{ background: rgba(76,175,80,0.2); color: #4CAF50; }}
        .grade-B {{ background: rgba(33,150,243,0.2); color: #64b5f6; }}
        .grade-C {{ background: rgba(255,193,7,0.2); color: #FFC107; }}
        .grade-D {{ background: rgba(255,87,34,0.2); color: #FF5722; }}
        .footer {{
            text-align: center;
            padding: 24px;
            color: #555;
            font-size: 0.85rem;
        }}
        .footer a {{ color: #667eea; text-decoration: none; }}
        .v5-badge {{
            display: inline-block;
            background: rgba(102,126,234,0.15);
            color: #667eea;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: 6px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="header">
        <span class="version">v5.0</span>
        <h1>🎓 GAIM Lab 배치 분석 대시보드</h1>
        <p>18개 강의 영상 7차원 AI 평가 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 배치: {batch_path.name}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{len(results)}</div>
            <div class="stat-label">📹 분석 영상</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_score:.1f}</div>
            <div class="stat-label">📊 평균 점수</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{max_score}</div>
            <div class="stat-label">🏆 최고 점수</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{min_score}</div>
            <div class="stat-label">📉 최저 점수</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{score_range:.1f}</div>
            <div class="stat-label">📏 점수 범위</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_student_turns:.0f}</div>
            <div class="stat-label">🗣️ 평균 학생 발화<span class="v5-badge">NEW</span></div>
        </div>
    </div>

    <h2 class="section-title">📈 점수 분석</h2>
    <div class="charts-grid">
        <div class="chart-card">
            <h3>📊 영상별 총점 분포</h3>
            <div class="chart-container">
                <canvas id="scoreChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>🎯 등급 분포</h3>
            <div class="chart-container">
                <canvas id="gradeChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>📐 차원별 평균 점수</h3>
            <div class="chart-container">
                <canvas id="dimensionChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>🕸️ 차원별 성취율 (레이더)</h3>
            <div class="chart-container">
                <canvas id="radarChart"></canvas>
            </div>
        </div>
    </div>

    <h2 class="section-title">🗣️ 화자 분리 분석 <span class="v5-badge">v5.0 NEW</span></h2>
    <div class="charts-grid">
        <div class="chart-card">
            <h3>👩‍🏫 교사 발화 비율 vs 📊 총점</h3>
            <div class="chart-container">
                <canvas id="teacherRatioChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>🙋 학생 발화 횟수 vs 📊 총점</h3>
            <div class="chart-container">
                <canvas id="studentTurnsChart"></canvas>
            </div>
        </div>
    </div>

    <h2 class="section-title">📋 영상별 상세 결과</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>영상</th>
                    <th>총점</th>
                    <th>등급</th>
                    <th>수업전문성<br><small>/20</small></th>
                    <th>교수학습<br><small>/20</small></th>
                    <th>판서·언어<br><small>/15</small></th>
                    <th>수업태도<br><small>/15</small></th>
                    <th>학생참여<br><small>/15</small></th>
                    <th>시간배분<br><small>/10</small></th>
                    <th>창의성<br><small>/5</small></th>
                    <th>교사비율<span class="v5-badge">NEW</span></th>
                    <th>학생발화<span class="v5-badge">NEW</span></th>
                </tr>
            </thead>
            <tbody>
'''

    # 테이블 행
    for r in sorted(results, key=lambda x: x["total_score"], reverse=True):
        dims = r.get("dimensions", [])

        def get_score(name):
            for d in dims:
                if d.get("name") == name:
                    return d.get("score", 0)
            return 0

        grade = r["grade"]
        grade_class = "A" if grade.startswith("A") else ("B" if grade.startswith("B") else ("C" if grade.startswith("C") else "D"))

        html_content += f'''                <tr>
                    <td style="text-align:left; font-weight:500;">{r["video_name"]}</td>
                    <td><strong>{r["total_score"]}</strong></td>
                    <td><span class="grade-badge grade-{grade_class}">{grade}</span></td>
                    <td>{get_score("수업 전문성")}</td>
                    <td>{get_score("교수학습 방법")}</td>
                    <td>{get_score("판서 및 언어")}</td>
                    <td>{get_score("수업 태도")}</td>
                    <td>{get_score("학생 참여")}</td>
                    <td>{get_score("시간 배분")}</td>
                    <td>{get_score("창의성")}</td>
                    <td>{r["teacher_ratio"]:.0%}</td>
                    <td>{r["student_turns"]}회</td>
                </tr>
'''

    html_content += f'''            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>🔬 GAIM Lab v5.0 — Gemini AI 기반 수업 분석 시스템 |
        <a href="https://github.com/Ginue-AI/GAIM_Lab">GitHub</a></p>
    </div>

    <script>
        Chart.defaults.color = '#8888aa';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';

        // 1. 영상별 점수 바 차트
        new Chart(document.getElementById('scoreChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([r["video_name"][-6:] for r in sorted(results, key=lambda x: x["total_score"], reverse=True)])},
                datasets: [{{
                    label: '총점',
                    data: {json.dumps([r["total_score"] for r in sorted(results, key=lambda x: x["total_score"], reverse=True)])},
                    backgroundColor: {json.dumps([
                        'rgba(76,175,80,0.6)' if r["total_score"] >= 80 else
                        ('rgba(33,150,243,0.6)' if r["total_score"] >= 70 else 'rgba(255,193,7,0.6)')
                        for r in sorted(results, key=lambda x: x["total_score"], reverse=True)
                    ])},
                    borderRadius: 6,
                    borderSkipped: false
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, max: 100, ticks: {{ stepSize: 10 }} }},
                    x: {{ ticks: {{ maxRotation: 45, font: {{ size: 10 }} }} }}
                }}
            }}
        }});

        // 2. 등급 분포 도넛 차트
        new Chart(document.getElementById('gradeChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(grade_labels)},
                datasets: [{{
                    data: {json.dumps(grade_values)},
                    backgroundColor: {json.dumps(grade_colors)},
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ padding: 16 }} }}
                }}
            }}
        }});

        // 3. 차원별 평균 수평 바 차트
        new Chart(document.getElementById('dimensionChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(dim_names)},
                datasets: [{{
                    label: '평균 점수',
                    data: {json.dumps([round(a, 1) for a in dim_avgs])},
                    backgroundColor: [
                        'rgba(255,99,132,0.5)', 'rgba(54,162,235,0.5)',
                        'rgba(255,206,86,0.5)', 'rgba(75,192,192,0.5)',
                        'rgba(153,102,255,0.5)', 'rgba(255,159,64,0.5)',
                        'rgba(199,199,199,0.5)'
                    ],
                    borderRadius: 6, borderSkipped: false
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ x: {{ beginAtZero: true }} }}
            }}
        }});

        // 4. 레이더 차트
        new Chart(document.getElementById('radarChart'), {{
            type: 'radar',
            data: {{
                labels: {json.dumps(dim_names)},
                datasets: [{{
                    label: '평균 성취율 (%)',
                    data: {json.dumps([round(a / m * 100, 1) for a, m in zip(dim_avgs, dim_max)])},
                    backgroundColor: 'rgba(102,126,234,0.2)',
                    borderColor: 'rgba(102,126,234,1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102,126,234,1)'
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true, max: 100,
                        ticks: {{ backdropColor: 'transparent' }},
                        pointLabels: {{ font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});

        // 5. v5.0: 교사 발화 비율 vs 총점 (Scatter)
        new Chart(document.getElementById('teacherRatioChart'), {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: '교사 발화 비율 vs 총점',
                    data: {json.dumps([
                        {"x": round(r["teacher_ratio"] * 100, 1), "y": r["total_score"]}
                        for r in results
                    ])},
                    backgroundColor: 'rgba(255,99,132,0.6)',
                    borderColor: 'rgba(255,99,132,1)',
                    pointRadius: 8,
                    pointHoverRadius: 12
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ title: {{ display: true, text: '교사 발화 비율 (%)' }} }},
                    y: {{ title: {{ display: true, text: '총점' }}, min: 60, max: 90 }}
                }}
            }}
        }});

        // 6. v5.0: 학생 발화 횟수 vs 총점 (Scatter)
        new Chart(document.getElementById('studentTurnsChart'), {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: '학생 발화 횟수 vs 총점',
                    data: {json.dumps([
                        {"x": r["student_turns"], "y": r["total_score"]}
                        for r in results
                    ])},
                    backgroundColor: 'rgba(54,162,235,0.6)',
                    borderColor: 'rgba(54,162,235,1)',
                    pointRadius: 8,
                    pointHoverRadius: 12
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ title: {{ display: true, text: '학생 발화 횟수' }} }},
                    y: {{ title: {{ display: true, text: '총점' }}, min: 60, max: 90 }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    # docs/ 폴더에 저장
    docs_dir = Path(r"D:\AI\GAIM_Lab\docs")
    docs_dir.mkdir(exist_ok=True)
    output_path = docs_dir / "batch_dashboard.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 배치 폴더에도 저장
    batch_output = batch_path / "dashboard.html"
    with open(batch_output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 대시보드 생성 완료:")
    print(f"   - docs: {output_path}")
    print(f"   - batch: {batch_output}")
    return output_path


if __name__ == "__main__":
    generate_visualization_dashboard()
