"""
GAIM Lab - 배치 분석 결과 시각화
Chart.js를 사용한 인터랙티브 대시보드 생성
"""
import json
from pathlib import Path
from datetime import datetime

def generate_visualization_dashboard():
    """분석 결과 시각화 대시보드 HTML 생성"""
    batch_dir = Path(r"D:\AI\GAIM_Lab\output\batch_v2_20260206_181255")
    
    # 모든 결과 수집
    results = []
    for video_dir in sorted(batch_dir.iterdir()):
        if not video_dir.is_dir():
            continue
        eval_file = video_dir / "evaluation_result.json"
        if not eval_file.exists():
            continue
            
        with open(eval_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["video_name"] = video_dir.name
            results.append(data)
    
    # 통계 계산
    total_scores = [r["total_score"] for r in results]
    avg_score = sum(total_scores) / len(total_scores)
    max_score = max(total_scores)
    min_score = min(total_scores)
    
    # 등급 분포
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for r in results:
        grade = r.get("grade", "N/A")
        if grade in grade_counts:
            grade_counts[grade] += 1
    
    # 차원별 평균 점수 계산
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
    
    # HTML 생성
    html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIM Lab 배치 분석 결과 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header p {{ color: #a0a0a0; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-value {{
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-label {{ color: #a0a0a0; margin-top: 10px; }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-card h3 {{
            margin-bottom: 20px;
            color: #667eea;
        }}
        .chart-container {{ position: relative; height: 300px; }}
        .table-container {{
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #667eea; font-weight: 600; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .grade-A {{ color: #4CAF50; font-weight: bold; }}
        .grade-B {{ color: #2196F3; font-weight: bold; }}
        .grade-C {{ color: #FFC107; font-weight: bold; }}
        .grade-D {{ color: #FF5722; font-weight: bold; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 GAIM Lab 배치 분석 결과</h1>
        <p>18개 강의 영상 7차원 평가 대시보드 | 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{len(results)}</div>
            <div class="stat-label">📹 분석 영상 수</div>
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
    </div>
    
    <div class="charts-grid">
        <div class="chart-card">
            <h3>📈 영상별 총점 분포</h3>
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
            <h3>📊 차원별 평균 점수</h3>
            <div class="chart-container">
                <canvas id="dimensionChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>🕸️ 차원별 성취율 (레이더 차트)</h3>
            <div class="chart-container">
                <canvas id="radarChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="table-container">
        <h3 style="color: #667eea; margin-bottom: 20px;">📋 영상별 상세 결과</h3>
        <table>
            <thead>
                <tr>
                    <th>영상</th>
                    <th>총점</th>
                    <th>등급</th>
                    <th>수업전문성</th>
                    <th>교수학습</th>
                    <th>의사소통</th>
                    <th>수업태도</th>
                    <th>학생참여</th>
                    <th>시간배분</th>
                    <th>창의성</th>
                </tr>
            </thead>
            <tbody>
'''
    
    # 테이블 행 추가
    for r in sorted(results, key=lambda x: x["total_score"], reverse=True):
        dims = r.get("dimensions", [])
        def get_score(name):
            for d in dims:
                if d.get("name") == name:
                    return d.get("score", 0)
            return 0
        
        grade = r.get("grade", "N/A")
        html_content += f'''                <tr>
                    <td>{r["video_name"]}</td>
                    <td><strong>{r["total_score"]}</strong></td>
                    <td class="grade-{grade}">{grade}</td>
                    <td>{get_score("수업 전문성")}/20</td>
                    <td>{get_score("교수학습 방법")}/20</td>
                    <td>{get_score("판서 및 언어")}/15</td>
                    <td>{get_score("수업 태도")}/15</td>
                    <td>{get_score("학생 참여")}/15</td>
                    <td>{get_score("시간 배분")}/10</td>
                    <td>{get_score("창의성")}/5</td>
                </tr>
'''
    
    html_content += f'''            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>🔬 GAIM Lab - Gemini AI 기반 수업 분석 시스템</p>
    </div>
    
    <script>
        // 영상별 점수 차트
        const scoreCtx = document.getElementById('scoreChart').getContext('2d');
        new Chart(scoreCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([r["video_name"][:8] for r in sorted(results, key=lambda x: x["total_score"], reverse=True)])},
                datasets: [{{
                    label: '총점',
                    data: {json.dumps([r["total_score"] for r in sorted(results, key=lambda x: x["total_score"], reverse=True)])},
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#a0a0a0' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#a0a0a0', maxRotation: 45 }}
                    }}
                }}
            }}
        }});
        
        // 등급 분포 파이 차트
        const gradeCtx = document.getElementById('gradeChart').getContext('2d');
        new Chart(gradeCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['A등급', 'B등급', 'C등급'],
                datasets: [{{
                    data: [{grade_counts["A"]}, {grade_counts["B"]}, {grade_counts["C"]}],
                    backgroundColor: ['#4CAF50', '#2196F3', '#FFC107'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#fff' }}
                    }}
                }}
            }}
        }});
        
        // 차원별 평균 점수 차트
        const dimCtx = document.getElementById('dimensionChart').getContext('2d');
        new Chart(dimCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(dim_names)},
                datasets: [{{
                    label: '평균 점수',
                    data: {json.dumps([round(a, 1) for a in dim_avgs])},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)',
                        'rgba(199, 199, 199, 0.6)'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#a0a0a0' }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#a0a0a0' }}
                    }}
                }}
            }}
        }});
        
        // 레이더 차트 (차원별 성취율)
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {{
                labels: {json.dumps(dim_names)},
                datasets: [{{
                    label: '평균 성취율 (%)',
                    data: {json.dumps([round(a/m*100, 1) for a, m in zip(dim_avgs, dim_max)])},
                    backgroundColor: 'rgba(102, 126, 234, 0.3)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#fff' }}
                    }}
                }},
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{ color: '#a0a0a0', backdropColor: 'transparent' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        pointLabels: {{ color: '#fff' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    # 저장
    output_path = batch_dir / "dashboard.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ 대시보드 생성 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_visualization_dashboard()
