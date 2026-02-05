"""
GAIM Lab - 향상된 PDF 리포트 생성기 v2.0
7차원 평가 결과를 시각적 PDF 리포트로 변환
새 기능: 세부기준 차트, 타임라인, 액션플랜, AI코칭, QR코드
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import base64
import io

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class GAIMReportGeneratorV2:
    """GAIM Lab 향상된 리포트 생성기 v2.0"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("D:/AI/GAIM_Lab/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.colors = [
            "#4f46e5", "#06b6d4", "#10b981", "#f59e0b", 
            "#ef4444", "#8b5cf6", "#ec4899"
        ]
        
        self.dim_icons = ["📚", "🎯", "🗣️", "🙋", "👥", "⏱️", "💡"]
    
    def _get_korean_grade(self, score: float) -> str:
        """점수를 한글 등급으로 변환"""
        if score >= 90:
            return "탁월"
        elif score >= 80:
            return "우수"
        elif score >= 70:
            return "보통"
        else:
            return "노력요함"
    
    def _get_css(self) -> str:
        """향상된 CSS 스타일 반환"""
        return '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
            min-height: 100vh;
            padding: 40px;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        
        /* Header */
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #334155;
        }
        .logo { font-size: 3rem; margin-bottom: 10px; }
        h1 { 
            font-size: 2rem;
            background: linear-gradient(135deg, #818cf8 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #94a3b8; margin-top: 10px; }
        
        /* Score Section */
        .score-section {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            margin: 40px 0;
            padding: 40px;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #334155;
        }
        .score-circle {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4f46e5, #4338ca);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 40px rgba(79, 70, 229, 0.4);
        }
        .score-value { font-size: 3.5rem; font-weight: 700; }
        .score-max { color: rgba(255,255,255,0.7); }
        .grade {
            font-size: 5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #f59e0b, #f97316);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Cards & Sections */
        .card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #334155;
            margin: 30px 0;
        }
        .card h3 { margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
        
        .chart-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 40px 0;
        }
        
        /* Timeline */
        .timeline {
            display: flex;
            justify-content: space-between;
            position: relative;
            padding: 20px 0;
        }
        .timeline::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #4f46e5, #06b6d4, #10b981);
            border-radius: 2px;
        }
        .timeline-item {
            text-align: center;
            position: relative;
            z-index: 1;
        }
        .timeline-dot {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #4f46e5;
            margin: 0 auto 10px;
            border: 3px solid #1e293b;
        }
        .timeline-label { font-size: 0.9rem; color: #94a3b8; }
        .timeline-value { font-weight: 600; color: #f8fafc; }
        
        /* Criteria Chart */
        .criteria-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .criteria-card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
        }
        .criteria-card h4 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
        }
        .criteria-bar {
            height: 8px;
            background: #334155;
            border-radius: 4px;
            margin: 8px 0;
            overflow: hidden;
        }
        .criteria-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        .criteria-score {
            font-size: 0.85rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }
        
        /* Action Plan */
        .action-plan {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        .week-card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border-top: 4px solid;
        }
        .week-card h4 { margin-bottom: 15px; }
        .week-card ul { list-style: none; }
        .week-card li {
            padding: 8px 0;
            color: #94a3b8;
            border-bottom: 1px solid #334155;
        }
        .week-card li:last-child { border-bottom: none; }
        
        /* AI Tips */
        .tip-card {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(6, 182, 212, 0.1));
            border: 1px solid rgba(79, 70, 229, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
        }
        .tip-card .tip-icon { font-size: 1.5rem; margin-right: 10px; }
        .tip-card .tip-title { font-weight: 600; color: #818cf8; }
        .tip-card .tip-content { color: #94a3b8; margin-top: 10px; line-height: 1.7; }
        
        /* QR Section */
        .qr-section {
            display: flex;
            align-items: center;
            gap: 30px;
            justify-content: center;
        }
        .qr-code {
            width: 120px;
            height: 120px;
            background: white;
            border-radius: 8px;
            padding: 10px;
        }
        .qr-info { text-align: left; }
        .qr-info h4 { margin-bottom: 10px; }
        .qr-info p { color: #94a3b8; font-size: 0.9rem; }
        
        /* Feedback Section */
        .feedback-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        .feedback-card { padding: 25px; border-radius: 16px; }
        .feedback-card.strengths {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .feedback-card.improvements {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .feedback-card ul { list-style: none; }
        .feedback-card li { padding: 8px 0; color: #94a3b8; }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            color: #64748b;
            border-top: 1px solid #334155;
            margin-top: 40px;
        }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            body { padding: 20px; }
            .chart-grid, .feedback-grid, .action-plan { grid-template-columns: 1fr; }
            .score-section { flex-direction: column; gap: 20px; }
            .qr-section { flex-direction: column; text-align: center; }
        }
        
        /* Print Optimization */
        @media print {
            body { background: white; color: black; padding: 20px; }
            .card, .criteria-card, .week-card, .tip-card {
                background: #f8fafc;
                border-color: #e2e8f0;
                page-break-inside: avoid;
            }
            .score-circle { box-shadow: none; border: 2px solid #4f46e5; }
        }
        '''
    
    def _generate_action_plan(self, dimensions: List[Dict]) -> List[Dict]:
        """취약 차원 기반 3주 액션 플랜 생성"""
        weak_dims = sorted(dimensions, key=lambda x: x.get("percentage", 0))[:3]
        
        activities = {
            "수업 전문성": ["학습목표 작성 연습", "교육과정 분석", "수업안 피드백 받기"],
            "교수학습 방법": ["다양한 교수법 연구", "매체 활용 연습", "동료 수업 참관"],
            "판서 및 언어": ["발성 연습", "판서 계획 수립", "녹음 후 자기점검"],
            "수업 태도": ["거울 보며 연습", "제스처 연습", "자신감 훈련"],
            "학생 참여": ["발문 기법 연구", "피드백 전략 학습", "상호작용 시뮬레이션"],
            "시간 배분": ["타이머 활용 연습", "수업 단계별 시간 계획", "모의수업 녹화"],
            "창의성": ["우수 수업 사례 분석", "아이디어 브레인스토밍", "창의적 도입 개발"]
        }
        
        weeks = []
        for i, dim in enumerate(weak_dims):
            name = dim.get("name", "")
            acts = activities.get(name, ["연습하기", "피드백 받기", "개선하기"])
            weeks.append({
                "week": i + 1,
                "focus": name,
                "color": self.colors[i % len(self.colors)],
                "activities": acts
            })
        
        return weeks
    
    def _generate_ai_tips(self, dimensions: List[Dict]) -> List[Dict]:
        """개선점 기반 AI 코칭 팁 생성"""
        tips = []
        weak_dims = [d for d in dimensions if d.get("percentage", 0) < 60]
        
        tip_templates = {
            "수업 태도": {
                "icon": "👀",
                "title": "시선 처리 개선 팁",
                "content": "학생들과 눈을 맞추며 Z자 패턴으로 교실을 스캔하세요. 한 학생에게 3-5초간 시선을 유지하면 개인적 연결감이 형성됩니다."
            },
            "시간 배분": {
                "icon": "⏰",
                "title": "시간 관리 전략",
                "content": "도입 5분, 전개 30분, 정리 5분의 기본 구조를 유지하세요. 스마트워치나 타이머를 활용해 시간 감각을 익히세요."
            },
            "판서 및 언어": {
                "icon": "🎤",
                "title": "발화 속도 조절법",
                "content": "중요한 개념은 천천히, 반복적으로 설명하세요. 1분에 120-150단어 속도가 이상적입니다."
            },
            "학생 참여": {
                "icon": "🙋",
                "title": "효과적인 발문 전략",
                "content": "열린 질문(왜?, 어떻게?)을 사용하고, 대기 시간 3-5초를 확보하세요. 학생 답변을 칭찬하며 확장하세요."
            }
        }
        
        for dim in weak_dims[:3]:
            name = dim.get("name", "")
            if name in tip_templates:
                tips.append(tip_templates[name])
        
        if not tips:
            tips.append({
                "icon": "💪",
                "title": "지속적인 성장을 위해",
                "content": "정기적인 자기 점검과 동료 피드백을 통해 꾸준히 발전하세요. 매 수업 후 5분간 자기 성찰 시간을 가지세요."
            })
        
        return tips
    
    def _generate_qr_code(self, report_path: str, video_name: str, web_url: str = None) -> str:
        """실제 QR 코드 생성 (Base64 인코딩 이미지)"""
        if not HAS_QRCODE:
            # qrcode 라이브러리 없으면 플레이스홀더 반환
            return '''
            <svg viewBox="0 0 100 100" style="width:100%;height:100%">
                <rect width="100" height="100" fill="#fff"/>
                <text x="50" y="55" text-anchor="middle" font-size="10" fill="#64748b">QR Code</text>
            </svg>
            '''
        
        try:
            # QR 코드에 포함할 정보 (웹 URL 우선, 없으면 로컬 경로)
            if web_url:
                qr_data = web_url
            else:
                qr_data = f"GAIM Lab Report\n영상: {video_name}\n생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n경로: {report_path}"
            
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # 이미지로 변환
            img = qr.make_image(fill_color="#1e293b", back_color="white")
            
            # Base64로 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return f'<img src="data:image/png;base64,{b64_img}" alt="QR Code" style="width:100%;height:100%;object-fit:contain;"/>'
            
        except Exception as e:
            print(f"QR 코드 생성 오류: {e}")
            return '<div style="text-align:center;color:#64748b;">QR</div>'
    
    def generate_html_report(self, evaluation: Dict, video_name: str = "lecture", web_url: str = None) -> str:
        """향상된 HTML 리포트 생성
        
        Args:
            evaluation: 평가 결과 딕셔너리
            video_name: 영상 이름
            web_url: QR 코드에 포함할 웹 URL (GitHub Pages 등)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dimensions = evaluation.get("dimensions", [])
        
        # 리포트 경로 미리 정의 (QR 코드 생성에 필요)
        report_path = self.output_dir / f"gaim_report_v2_{timestamp}.html"
        
        # 데이터 준비
        radar_labels = json.dumps([d["name"] for d in dimensions], ensure_ascii=False)
        radar_values = json.dumps([d["percentage"] for d in dimensions])
        action_plan = self._generate_action_plan(dimensions)
        ai_tips = self._generate_ai_tips(dimensions)
        
        # 세부 기준 HTML 생성
        criteria_html = self._build_criteria_section(dimensions)
        
        # 타임라인 HTML
        timeline_html = self._build_timeline_section(evaluation)
        
        # 액션 플랜 HTML
        action_html = self._build_action_plan_section(action_plan)
        
        # AI 팁 HTML
        tips_html = self._build_tips_section(ai_tips)
        
        # 차원별 피드백 HTML
        dim_feedback_html = self._build_dimension_feedback(dimensions)
        
        html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GAIM Lab - 수업 분석 리포트</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>{self._get_css()}</style>
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
            <div class="grade">{self._get_korean_grade(evaluation.get("total_score", 0))}</div>
        </div>
        
        {timeline_html}
        
        <div class="chart-grid">
            <div class="card">
                <h3>📊 7차원 역량 분석</h3>
                <canvas id="radarChart"></canvas>
            </div>
            <div class="card">
                <h3>📈 차원별 달성도</h3>
                <canvas id="barChart"></canvas>
            </div>
        </div>
        
        {criteria_html}
        
        <div class="feedback-grid">
            <div class="feedback-card strengths">
                <h3>✅ 강점</h3>
                <ul>{"".join([f"<li>{s}</li>" for s in evaluation.get("strengths", [])])}</ul>
            </div>
            <div class="feedback-card improvements">
                <h3>🔧 개선점</h3>
                <ul>{"".join([f"<li>{i}</li>" for i in evaluation.get("improvements", [])])}</ul>
            </div>
        </div>
        
        <div class="card">
            <h3>💬 종합 피드백</h3>
            <p style="color: #94a3b8; line-height: 1.8;">{evaluation.get("overall_feedback", "")}</p>
        </div>
        
        {dim_feedback_html}
        
        {tips_html}
        
        {action_html}
        
        <div class="card">
            <h3>📱 리포트 공유</h3>
            <div class="qr-section">
                <div class="qr-code">{self._generate_qr_code(str(report_path), video_name, web_url)}</div>
                <div class="qr-info">
                    <h4>QR 코드로 공유하기</h4>
                    <p>스마트폰으로 QR 코드를 스캔하여<br>이 리포트를 빠르게 공유하세요.</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>GINUE AI Microteaching Lab (GAIM Lab) | 경인교육대학교</p>
            <p style="margin-top: 5px;">Generated: {datetime.now().isoformat()}</p>
        </div>
    </div>
    
    <script>
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {{
                labels: {radar_labels},
                datasets: [{{
                    label: '달성도 (%)',
                    data: {radar_values},
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
        
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: {radar_labels},
                datasets: [{{
                    label: '점수 (100점 환산)',
                    data: {radar_values},
                    backgroundColor: {json.dumps(self.colors[:len(dimensions)])},
                    borderRadius: 6,
                    barThickness: 35
                }}]
            }},
            options: {{
                indexAxis: 'x',
                responsive: true,
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }}, maxRotation: 45, minRotation: 45 }}, grid: {{ display: false }} }},
                    y: {{ beginAtZero: true, max: 100, ticks: {{ color: '#94a3b8', stepSize: 10 }}, grid: {{ color: '#334155' }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    </script>
</body>
</html>'''
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _build_criteria_section(self, dimensions: List[Dict]) -> str:
        """세부 기준(Criteria) 차트 섹션 생성"""
        cards = []
        for i, dim in enumerate(dimensions):
            name = dim.get("name", "")
            criteria = dim.get("criteria", {})
            color = self.colors[i % len(self.colors)]
            icon = self.dim_icons[i % len(self.dim_icons)]
            
            criteria_items = ""
            for crit_name, crit_score in criteria.items():
                max_score = 10  # 기본값
                pct = min(100, (crit_score / max_score) * 100) if max_score > 0 else 0
                criteria_items += f'''
                <div class="criteria-score">
                    <span>{crit_name.replace("_", " ")}</span>
                    <span>{crit_score}점</span>
                </div>
                <div class="criteria-bar">
                    <div class="criteria-fill" style="width: {pct}%; background: {color};"></div>
                </div>'''
            
            cards.append(f'''
            <div class="criteria-card" style="border-color: {color};">
                <h4>{icon} {name} <span style="color: {color};">({dim.get("percentage", 0)}%)</span></h4>
                {criteria_items}
            </div>''')
        
        return f'''
        <div class="card">
            <h3>📋 세부 평가 기준별 점수</h3>
            <div class="criteria-grid">{"".join(cards)}</div>
        </div>'''
    
    def _build_timeline_section(self, evaluation: Dict) -> str:
        """타임라인 섹션 생성"""
        return '''
        <div class="card">
            <h3>⏳ 수업 흐름 타임라인</h3>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #4f46e5;"></div>
                    <div class="timeline-label">도입</div>
                    <div class="timeline-value">~5분</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #06b6d4;"></div>
                    <div class="timeline-label">전개 1</div>
                    <div class="timeline-value">~15분</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #10b981;"></div>
                    <div class="timeline-label">전개 2</div>
                    <div class="timeline-value">~15분</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot" style="background: #f59e0b;"></div>
                    <div class="timeline-label">정리</div>
                    <div class="timeline-value">~5분</div>
                </div>
            </div>
        </div>'''
    
    def _build_action_plan_section(self, action_plan: List[Dict]) -> str:
        """액션 플랜 섹션 생성"""
        weeks_html = ""
        for week in action_plan:
            activities = "".join([f"<li>• {act}</li>" for act in week["activities"]])
            weeks_html += f'''
            <div class="week-card" style="border-color: {week["color"]};">
                <h4>📅 {week["week"]}주차: {week["focus"]}</h4>
                <ul>{activities}</ul>
            </div>'''
        
        return f'''
        <div class="card">
            <h3>📝 3주 액션 플랜</h3>
            <div class="action-plan">{weeks_html}</div>
        </div>'''
    
    def _build_tips_section(self, tips: List[Dict]) -> str:
        """AI 코칭 팁 섹션 생성"""
        tips_html = ""
        for tip in tips:
            tips_html += f'''
            <div class="tip-card">
                <span class="tip-icon">{tip["icon"]}</span>
                <span class="tip-title">{tip["title"]}</span>
                <p class="tip-content">{tip["content"]}</p>
            </div>'''
        
        return f'''
        <div class="card">
            <h3>💡 AI 코칭 팁</h3>
            {tips_html}
        </div>'''
    
    def _build_dimension_feedback(self, dimensions: List[Dict]) -> str:
        """차원별 상세 피드백 생성 - 강점/개선점 분리"""
        items = ""
        for i, d in enumerate(dimensions):
            color = self.colors[i % len(self.colors)]
            icon = self.dim_icons[i % len(self.dim_icons)]
            percentage = d.get("percentage", 0)
            
            # 피드백을 강점과 개선점으로 분류
            strengths = d.get("strengths", [])
            improvements = d.get("improvements", [])
            
            # 기존 feedback 필드도 처리 (퍼센티지로 자동 분류)
            for fb in d.get("feedback", []):
                if percentage >= 70:
                    strengths.append(fb)
                else:
                    improvements.append(fb)
            
            # 강점 HTML
            strengths_html = ""
            if strengths:
                strengths_items = "".join([f"<li>✅ {s}</li>" for s in strengths])
                strengths_html = f'''
                <div class="dim-feedback-box strengths">
                    <h5>💪 강점</h5>
                    <ul>{strengths_items}</ul>
                </div>'''
            
            # 개선점 HTML
            improvements_html = ""
            if improvements:
                improvements_items = "".join([f"<li>🔧 {imp}</li>" for imp in improvements])
                improvements_html = f'''
                <div class="dim-feedback-box improvements">
                    <h5>📈 개선점</h5>
                    <ul>{improvements_items}</ul>
                </div>'''
            
            # 기본 메시지 (피드백이 없는 경우)
            if not strengths and not improvements:
                if percentage >= 80:
                    strengths_html = '<div class="dim-feedback-box strengths"><p>✅ 우수한 수준을 유지하고 있습니다.</p></div>'
                elif percentage >= 60:
                    strengths_html = '<div class="dim-feedback-box strengths"><p>✅ 기본기가 잘 갖춰져 있습니다.</p></div>'
                    improvements_html = '<div class="dim-feedback-box improvements"><p>🔧 조금 더 연습하면 더 좋아질 수 있습니다.</p></div>'
                else:
                    improvements_html = '<div class="dim-feedback-box improvements"><p>🔧 이 영역에 집중적인 연습이 필요합니다.</p></div>'
            
            items += f'''
            <div class="criteria-card dim-feedback-card" style="border-color: {color}; margin-bottom: 20px;">
                <h4>{icon} {d["name"]} 
                    <span class="dim-badge" style="background: {color}20; color: {color};">
                        {d["score"]}/{d["max_score"]} ({percentage}%)
                    </span>
                </h4>
                <div class="dim-feedback-grid">
                    {strengths_html}
                    {improvements_html}
                </div>
            </div>'''
        
        return f'''
        <style>
            .dim-feedback-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 15px;
            }}
            .dim-feedback-box {{
                padding: 15px;
                border-radius: 10px;
            }}
            .dim-feedback-box.strengths {{
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.2);
            }}
            .dim-feedback-box.improvements {{
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.2);
            }}
            .dim-feedback-box h5 {{
                margin-bottom: 10px;
                font-size: 0.9rem;
            }}
            .dim-feedback-box ul {{
                list-style: none;
                margin: 0;
                padding: 0;
            }}
            .dim-feedback-box li {{
                padding: 5px 0;
                color: #94a3b8;
                font-size: 0.9rem;
                line-height: 1.6;
            }}
            .dim-badge {{
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.85rem;
                margin-left: 10px;
            }}
            @media (max-width: 768px) {{
                .dim-feedback-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
        <div class="card">
            <h3>📝 차원별 상세 피드백</h3>
            {items}
        </div>'''


# 직접 실행 테스트
if __name__ == "__main__":
    sample = {
        "total_score": 72.0,
        "grade": "C",
        "dimensions": [
            {"name": "수업 전문성", "score": 17, "max_score": 20, "percentage": 85.0,
             "criteria": {"학습목표_명료성": 9, "학습내용_충실성": 8}, "feedback": ["학습 목표가 명확히 제시됨"]},
            {"name": "교수학습 방법", "score": 16, "max_score": 20, "percentage": 80.0,
             "criteria": {"교수법_다양성": 8, "학습활동_효과성": 8}, "feedback": ["다양한 교수법 활용"]},
            {"name": "판서 및 언어", "score": 8, "max_score": 15, "percentage": 53.3,
             "criteria": {"판서_가독성": 3, "언어_명료성": 4, "발화속도_적절성": 1}, "feedback": ["발화 속도 개선 필요"]},
            {"name": "수업 태도", "score": 5, "max_score": 15, "percentage": 33.3,
             "criteria": {"교사_열정": 2, "학생_소통": 1, "자신감": 2}, "feedback": ["시선 처리 개선 필요"]},
            {"name": "학생 참여", "score": 13, "max_score": 15, "percentage": 86.7,
             "criteria": {"질문_기법": 6, "피드백_제공": 7}, "feedback": ["효과적인 발문 사용"]},
            {"name": "시간 배분", "score": 5, "max_score": 10, "percentage": 50.0,
             "criteria": {"시간_균형": 5}, "feedback": ["시간 배분 연습 필요"]},
            {"name": "창의성", "score": 4, "max_score": 5, "percentage": 80.0,
             "criteria": {"수업_창의성": 4}, "feedback": ["독창적 아이디어 활용"]}
        ],
        "strengths": ["✅ 학생 참여: 86.7%", "✅ 수업 전문성: 85.0%"],
        "improvements": ["🔧 수업 태도: 개선 필요", "🔧 시간 배분: 연습 필요"],
        "overall_feedback": "양호한 수업 시연입니다."
    }
    
    gen = GAIMReportGeneratorV2()
    path = gen.generate_html_report(sample, "test_lecture")
    print(f"Report: {path}")
