"""
GAIM Lab - PDF 리포트 생성기
7차원 평가 결과를 PDF 리포트로 변환
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import json


class GAIMReportGenerator:
    """
    GAIM Lab PDF 리포트 생성기
    
    7차원 평가 결과를 시각적 PDF 리포트로 변환
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("D:/AI/GAIM_Lab/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, evaluation: Dict, video_name: str = "lecture") -> str:
        """
        HTML 리포트 생성
        
        Args:
            evaluation: 7차원 평가 결과 딕셔너리
            video_name: 영상 파일명
            
        Returns:
            생성된 HTML 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 차원별 색상 매핑
        colors = [
            "#4f46e5", "#06b6d4", "#10b981", "#f59e0b", 
            "#ef4444", "#8b5cf6", "#ec4899"
        ]
        
        # 레이더 차트 데이터 생성
        dimensions = evaluation.get("dimensions", [])
        radar_labels = [d["name"] for d in dimensions]
        radar_values = [d["percentage"] for d in dimensions]
        
        # HTML 템플릿 생성
        html_content = f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIM Lab - 수업 분석 리포트</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
            min-height: 100vh;
            padding: 40px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #334155;
        }}
        .logo {{ font-size: 3rem; margin-bottom: 10px; }}
        h1 {{ 
            font-size: 2rem;
            background: linear-gradient(135deg, #818cf8 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .subtitle {{ color: #94a3b8; margin-top: 10px; }}
        
        .score-section {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            margin: 40px 0;
            padding: 40px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #334155;
        }}
        .score-circle {{
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4f46e5, #4338ca);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 40px rgba(79, 70, 229, 0.4);
        }}
        .score-value {{ font-size: 3.5rem; font-weight: 700; }}
        .score-max {{ color: rgba(255,255,255,0.7); }}
        .grade {{
            font-size: 5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #f59e0b, #f97316);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .chart-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 40px 0;
        }}
        .chart-card.bar-chart {{
            min-height: 500px;
        }}
        #barChart {{
            height: 450px !important;
        }}
        .chart-card {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #334155;
        }}
        .chart-card h3 {{ margin-bottom: 20px; }}
        
        .dimensions-list {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #334155;
            margin: 40px 0;
        }}
        .dim-item {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 15px;
            background: #1e293b;
            border-radius: 8px;
        }}
        .dim-name {{ width: 150px; font-weight: 600; }}
        .dim-bar {{
            flex: 1;
            height: 12px;
            background: #334155;
            border-radius: 6px;
            overflow: hidden;
            margin: 0 15px;
        }}
        .dim-fill {{ height: 100%; border-radius: 6px; transition: width 0.5s; }}
        .dim-score {{ width: 80px; text-align: right; }}
        
        .feedback-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 40px 0;
        }}
        .feedback-card {{
            padding: 25px;
            border-radius: 16px;
        }}
        .feedback-card.strengths {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .feedback-card.improvements {{
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .feedback-card h3 {{ margin-bottom: 15px; }}
        .feedback-card ul {{ list-style: none; }}
        .feedback-card li {{ padding: 8px 0; color: #94a3b8; }}
        
        .overall-feedback {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 30px;
            border-left: 4px solid #4f46e5;
            margin: 40px 0;
        }}
        
        .dimension-feedbacks {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #334155;
            margin: 40px 0;
        }}
        .dimension-feedbacks h3 {{ margin-bottom: 20px; }}
        .dim-feedback-item {{
            margin-bottom: 20px;
            padding: 20px;
            background: #1e293b;
            border-radius: 12px;
            border-left: 4px solid;
        }}
        .dim-feedback-item h4 {{
            font-size: 1.1rem;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .dim-feedback-item p {{
            color: #94a3b8;
            line-height: 1.7;
            margin: 5px 0;
        }}
        .dim-score-badge {{
            font-size: 0.85rem;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(79, 70, 229, 0.2);
            color: #818cf8;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            border-top: 1px solid #334155;
            margin-top: 40px;
        }}
        
        @media print {{
            body {{ background: white; color: black; }}
            .chart-card, .dimensions-list, .feedback-card, .overall-feedback {{
                background: #f8fafc;
                border-color: #e2e8f0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎓</div>
            <h1>GAIM Lab 수업 분석 리포트</h1>
            <p class="subtitle">{video_name} | {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
        </div>
        
        <div class="score-section">
            <div class="score-circle">
                <div class="score-value">{evaluation.get("total_score", 0)}</div>
                <div class="score-max">/100점</div>
            </div>
            <div class="grade">{evaluation.get("grade", "-")}</div>
        </div>
        
        <div class="chart-section">
            <div class="chart-card">
                <h3>📊 7차원 역량 분석</h3>
                <canvas id="radarChart"></canvas>
            </div>
            <div class="chart-card bar-chart">
                <h3>📈 차원별 달성도</h3>
                <canvas id="barChart" style="height: 450px;"></canvas>
            </div>
        </div>
        
        <div class="dimensions-list">
            <h3>📋 상세 점수</h3>
            {"".join([f'''
            <div class="dim-item">
                <span class="dim-name">{d["name"]}</span>
                <div class="dim-bar">
                    <div class="dim-fill" style="width: {d["percentage"]}%; background: {colors[i % len(colors)]};"></div>
                </div>
                <span class="dim-score">{d["score"]}/{d["max_score"]} ({d["percentage"]}%)</span>
            </div>
            ''' for i, d in enumerate(dimensions)])}
        </div>
        
        <div class="feedback-section">
            <div class="feedback-card strengths">
                <h3>✅ 강점</h3>
                <ul>
                    {"".join([f"<li>{s}</li>" for s in evaluation.get("strengths", [])])}
                </ul>
            </div>
            <div class="feedback-card improvements">
                <h3>🔧 개선점</h3>
                <ul>
                    {"".join([f"<li>{i}</li>" for i in evaluation.get("improvements", [])])}
                </ul>
            </div>
        </div>
        
        <div class="overall-feedback">
            <h3>💬 종합 피드백</h3>
            <p style="margin-top: 15px; color: #94a3b8; line-height: 1.8;">
                {evaluation.get("overall_feedback", "")}
            </p>
        </div>
        
        <div class="dimension-feedbacks">
            <h3>📝 차원별 상세 피드백</h3>
            {"".join([f'''
            <div class="dim-feedback-item" style="border-color: {colors[i % len(colors)]};">
                <h4>
                    <span>{["📚", "🎯", "🗣️", "🙋", "👥", "⏱️", "💡"][i]} {d["name"]}</span>
                    <span class="dim-score-badge">{d["score"]}/{d["max_score"]} ({d["percentage"]}%)</span>
                </h4>
                {"".join([f"<p>• {fb}</p>" for fb in d.get("feedback", [])])}
            </div>
            ''' for i, d in enumerate(dimensions)])}
        </div>
        
        <div class="footer">
            <p>GINUE AI Microteaching Lab (GAIM Lab) | 경인교육대학교</p>
            <p style="margin-top: 5px;">Generated: {datetime.now().isoformat()}</p>
        </div>
    </div>
    
    <script>
        // 레이더 차트
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {{
                labels: {json.dumps(radar_labels, ensure_ascii=False)},
                datasets: [{{
                    label: '달성도 (%)',
                    data: {json.dumps(radar_values)},
                    backgroundColor: 'rgba(79, 70, 229, 0.3)',
                    borderColor: '#818cf8',
                    borderWidth: 2,
                    pointBackgroundColor: '#818cf8'
                }}]
            }},
            options: {{
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{ color: '#94a3b8' }},
                        grid: {{ color: '#334155' }},
                        angleLines: {{ color: '#334155' }},
                        pointLabels: {{ color: '#f8fafc', font: {{ size: 11 }} }}
                    }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        // 100점 만점 수직 라인 그래프
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([d["name"] for d in dimensions], ensure_ascii=False)},
                datasets: [{{
                    label: '점수 (100점 환산)',
                    data: {json.dumps([round(d["percentage"], 1) for d in dimensions])},
                    backgroundColor: {json.dumps(colors[:len(dimensions)])},
                    borderRadius: 6,
                    barThickness: 35
                }}]
            }},
            options: {{
                indexAxis: 'x',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ 
                        ticks: {{ color: '#94a3b8', font: {{ size: 10 }}, maxRotation: 45, minRotation: 45 }}, 
                        grid: {{ display: false }} 
                    }},
                    y: {{ 
                        beginAtZero: true,
                        max: 100,
                        ticks: {{ 
                            color: '#94a3b8',
                            stepSize: 5,
                            autoSkip: false,
                            font: {{ size: 9 }},
                            callback: function(value) {{ return value + '점'; }}
                        }}, 
                        grid: {{ color: '#334155' }} 
                    }}
                }},
                plugins: {{ 
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.raw + '점/100점';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
        
        # 파일 저장
        report_path = self.output_dir / f"gaim_report_{timestamp}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(report_path)
    
    async def generate_pdf_report(self, evaluation: Dict, video_name: str = "lecture") -> str:
        """
        PDF 리포트 생성 (Playwright 사용)
        
        Args:
            evaluation: 7차원 평가 결과
            video_name: 영상 파일명
            
        Returns:
            생성된 PDF 파일 경로
        """
        # 먼저 HTML 생성
        html_path = self.generate_html_report(evaluation, video_name)
        
        try:
            from playwright.async_api import async_playwright
            
            pdf_path = html_path.replace(".html", ".pdf")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file:///{html_path}")
                await page.pdf(path=pdf_path, format="A4", print_background=True)
                await browser.close()
            
            return pdf_path
            
        except ImportError:
            print("Warning: Playwright not installed. Returning HTML report.")
            return html_path
        except Exception as e:
            print(f"Warning: PDF generation failed: {e}. Returning HTML report.")
            return html_path
    
    def generate_portfolio_html(self, portfolio_data: Dict) -> str:
        """
        포트폴리오 HTML 리포트 생성
        
        Args:
            portfolio_data: 학생 포트폴리오 데이터
            
        Returns:
            생성된 HTML 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        student = portfolio_data.get("student", {})
        sessions = portfolio_data.get("sessions", [])
        badges = portfolio_data.get("badges", [])
        
        # 세션별 점수 데이터
        session_labels = [f"#{i+1}" for i in range(len(sessions))]
        session_scores = [s.get("total_score", 0) for s in sessions]
        
        # 최근 세션의 차원 데이터
        latest_dims = sessions[-1].get("dimensions", []) if sessions else []
        dim_names = [d["name"][:4] for d in latest_dims]
        dim_scores = [d["score"] / d["max"] * 100 for d in latest_dims] if latest_dims else []
        
        html_content = f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIM Lab - 학생 포트폴리오</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            min-height: 100vh;
            padding: 40px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
            color: white;
            border-radius: 16px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 10px; }}
        .header .student-info {{ opacity: 0.9; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }}
        .stat-value {{ font-size: 2rem; font-weight: 700; color: #4f46e5; }}
        .stat-label {{ font-size: 0.85rem; color: #64748b; margin-top: 5px; }}
        .stat-value.positive {{ color: #10b981; }}
        
        .section {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }}
        .section h3 {{ margin-bottom: 20px; color: #1e293b; }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .badges-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
        }}
        .badge-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background: #f1f5f9;
            border-radius: 8px;
        }}
        .badge-icon {{ font-size: 1.8rem; }}
        .badge-name {{ font-weight: 600; font-size: 0.9rem; }}
        .badge-date {{ font-size: 0.75rem; color: #64748b; }}
        
        .sessions-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .sessions-table th, .sessions-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        .sessions-table th {{ background: #f8fafc; font-weight: 600; }}
        .grade {{ 
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .grade-A {{ background: #dcfce7; color: #16a34a; }}
        .grade-B {{ background: #dbeafe; color: #2563eb; }}
        .grade-C {{ background: #fef3c7; color: #d97706; }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #64748b;
            font-size: 0.85rem;
        }}
        
        @media print {{
            body {{ padding: 20px; }}
            .section {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 GAIM Lab 학생 포트폴리오</h1>
            <div class="student-info">
                {student.get("name", "학생")} | {student.get("student_id", "")} | 
                생성일: {datetime.now().strftime("%Y년 %m월 %d일")}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(sessions)}</div>
                <div class="stat-label">총 세션</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(session_scores) / len(session_scores) if session_scores else 0:.1f}</div>
                <div class="stat-label">평균 점수</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{max(session_scores) if session_scores else 0:.0f}</div>
                <div class="stat-label">최고 점수</div>
            </div>
            <div class="stat-card">
                <div class="stat-value positive">+{((session_scores[-1] - session_scores[0]) / session_scores[0] * 100) if len(session_scores) >= 2 else 0:.1f}%</div>
                <div class="stat-label">성장률</div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="section">
                <h3>📈 점수 변화 추이</h3>
                <canvas id="progressChart"></canvas>
            </div>
            <div class="section">
                <h3>🎯 최근 역량 분석</h3>
                <canvas id="radarChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h3>🎖️ 획득한 배지 ({len(badges)}개)</h3>
            <div class="badges-grid">
                {"".join([f'''
                <div class="badge-item">
                    <span class="badge-icon">{b.get("icon", "🏅")}</span>
                    <div>
                        <div class="badge-name">{b.get("name", "배지")}</div>
                        <div class="badge-date">{b.get("earned_at", "")}</div>
                    </div>
                </div>
                ''' for b in badges])}
            </div>
        </div>
        
        <div class="section">
            <h3>📋 수업 시연 기록</h3>
            <table class="sessions-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>날짜</th>
                        <th>점수</th>
                        <th>등급</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f'''
                    <tr>
                        <td>{i+1}</td>
                        <td>{s.get("date", "")}</td>
                        <td><strong>{s.get("total_score", 0)}</strong>점</td>
                        <td><span class="grade grade-{s.get('grade', 'C')[0]}">{s.get("grade", "-")}</span></td>
                    </tr>
                    ''' for i, s in enumerate(sessions)])}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>GINUE AI Microteaching Lab (GAIM Lab) | 경인교육대학교</p>
            <p>Generated: {datetime.now().isoformat()}</p>
        </div>
    </div>
    
    <script>
        // 점수 추이 차트
        new Chart(document.getElementById('progressChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(session_labels)},
                datasets: [{{
                    label: '점수',
                    data: {json.dumps(session_scores)},
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.3
                }}]
            }},
            options: {{
                scales: {{ y: {{ min: 50, max: 100 }} }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        // 레이더 차트
        new Chart(document.getElementById('radarChart'), {{
            type: 'radar',
            data: {{
                labels: {json.dumps(dim_names, ensure_ascii=False)},
                datasets: [{{
                    label: '달성률 (%)',
                    data: {json.dumps(dim_scores)},
                    backgroundColor: 'rgba(16, 185, 129, 0.3)',
                    borderColor: '#10b981',
                    borderWidth: 2
                }}]
            }},
            options: {{
                scales: {{ r: {{ beginAtZero: true, max: 100 }} }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    </script>
</body>
</html>
'''
        
        report_path = self.output_dir / f"gaim_portfolio_{timestamp}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(report_path)
    
    async def generate_portfolio_pdf(self, portfolio_data: Dict) -> str:
        """포트폴리오 PDF 생성"""
        html_path = self.generate_portfolio_html(portfolio_data)
        
        try:
            from playwright.async_api import async_playwright
            
            pdf_path = html_path.replace(".html", ".pdf")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file:///{html_path}")
                await page.pdf(path=pdf_path, format="A4", print_background=True)
                await browser.close()
            
            return pdf_path
            
        except Exception as e:
            print(f"Warning: Portfolio PDF generation failed: {e}")
            return html_path


# 직접 실행 테스트
if __name__ == "__main__":
    # 더미 평가 데이터
    sample_evaluation = {
        "total_score": 72.0,
        "grade": "C",
        "dimensions": [
            {"name": "수업 설계", "score": 11.2, "max_score": 15, "percentage": 74.7},
            {"name": "수업 전달", "score": 13.2, "max_score": 20, "percentage": 66.0},
            {"name": "교수학습 상호작용", "score": 10.8, "max_score": 15, "percentage": 72.0},
            {"name": "비언어적 소통", "score": 10.3, "max_score": 15, "percentage": 68.7},
            {"name": "음성 전달", "score": 8.7, "max_score": 10, "percentage": 87.0},
            {"name": "시각 자료 활용", "score": 8.8, "max_score": 10, "percentage": 88.0},
            {"name": "수업 마무리", "score": 9.0, "max_score": 15, "percentage": 60.0}
        ],
        "strengths": ["시각 자료 활용: 88.0%", "음성 전달: 87.0%"],
        "improvements": ["수업 마무리: 추가 연습 필요"],
        "overall_feedback": "양호한 수업 시연입니다. 72.0점(C)으로 기본적인 교수 역량을 갖추고 있으며, 일부 영역에서 보완이 필요합니다."
    }
    
    generator = GAIMReportGenerator()
    report_path = generator.generate_html_report(sample_evaluation, "demo_lecture")
    print(f"Report generated: {report_path}")
