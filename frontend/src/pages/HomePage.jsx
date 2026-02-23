import { Link } from 'react-router-dom'
import './HomePage.css'

const agentPipeline = [
    { icon: '📹', name: 'Video' },
    { icon: '📦', name: 'Extractor' },
    { icon: '⚡', name: 'Parallel', sub: '👁️🎨🗣️🔊' },
    { icon: '📚', name: 'Pedagogy' },
    { icon: '💡', name: 'Feedback' },
    { icon: '🧠', name: 'Master' },
    { icon: '📊', name: 'Report' },
]

const features = [
    { icon: '🔴', title: '실시간 코칭 7차원', desc: 'Gemini AI 기반 7차원 수업 평가', badge: 'v8.2', link: '/live', color: '#ef4444' },
    { icon: '🔐', title: '클라이언트 인증', desc: 'GitHub Pages 로그인/회원가입', badge: 'v8.2', link: '/login', color: '#ef4444' },
    { icon: '📈', title: '통계 모듈', desc: "Welch's t-test, Cohen's d 직접 구현", badge: 'v8.2', link: '/cohort', color: '#ef4444' },
    { icon: '📄', title: 'PDF 내보내기', desc: '분석 결과 PDF 저장', badge: 'v8.1', link: '/upload', color: '#f59e0b' },
    { icon: '🤖', title: 'AI 멘토 매칭', desc: '7차원 기반 AI 에이전트 코칭', badge: 'v8.2', link: '/mentor', color: '#f59e0b' },
    { icon: '🤖', title: 'Gemini 7차원 전면 평가', desc: '모든 차원 LLM 평가 (avg +16pt)', badge: 'v8.0', link: '/upload', color: '#f59e0b' },
    { icon: '🎬', title: '클라이언트 사이드 분석', desc: '브라우저에서 직접 영상 분석', badge: 'v8.0', link: '/agents', color: '#3b82f6' },
    { icon: '🎯', title: '성장 경로', desc: '4/8/12주 맞춤 개선 로드맵', badge: 'v7.1', link: '/growth', color: '#3b82f6' },
]

const quickActions = [
    { icon: '🎬', title: '수업 분석', desc: '영상 업로드 후 AI 7차원 평가', link: '/upload', color: '#6366f1' },
    { icon: '🤖', title: 'MAS 분석', desc: '8개 에이전트 파이프라인 실행', link: '/agents', color: '#8b5cf6' },
    { icon: '📈', title: '성장보고서', desc: '차원별 추세·맞춤 로드맵', link: '/growth', color: '#06b6d4' },
    { icon: '🔬', title: '코호트 비교', desc: '집단 간 통계 비교 분석', link: '/cohort', color: '#34d399' },
]

const agents = [
    { emoji: '📦', name: 'Extractor', desc: 'GPU 가속 FFmpeg 프레임·오디오 추출', tech: 'FFmpeg + CUDA' },
    { emoji: '👁️', name: 'Vision', desc: '교사 시선, 제스처, 자세 비언어 분석', tech: 'OpenCV + Gemini' },
    { emoji: '🎨', name: 'Content', desc: '판서, 교수자료, 멀티미디어 분석', tech: 'Gemini AI' },
    { emoji: '🗣️', name: 'STT', desc: '음성→텍스트, 화자분리, 필러 감지', tech: 'Whisper + pyannote' },
    { emoji: '🔊', name: 'Vibe', desc: '억양·속도·에너지 프로소디 분석', tech: 'Librosa' },
    { emoji: '📚', name: 'Pedagogy v8', desc: '시그모이드 연속 채점 + 결정론적 해싱', tech: 'Sigmoid + Gemini' },
    { emoji: '💡', name: 'Feedback', desc: 'LLM + 규칙 기반 맞춤 피드백', tech: 'Gemini LLM' },
    { emoji: '🧠', name: 'Master', desc: '전체 결과 종합, 최종 보고서 생성', tech: 'Aggregation' },
]

function HomePage() {
    return (
        <div className="home-page">
            {/* Hero */}
            <section className="hero">
                <div className="hero-badge">
                    <span className="hero-dot"></span>
                    v8.2 — GitHub Pages 풀스택 · Gemini 실시간 코칭 · 클라이언트 인증
                </div>
                <h1 className="hero-title">
                    <span className="hero-title-gradient">멀티 에이전트</span>
                    <br />수업 분석 플랫폼
                </h1>
                <p className="hero-desc">
                    8개 AI 에이전트가 협업하여 수업 영상을 <strong>7차원 100점 만점</strong>으로
                    자동 평가합니다. 실시간 코칭, 코호트 비교, 성장 로드맵까지 —
                    교원 양성의 새로운 패러다임.
                </p>
                <div className="hero-actions">
                    <Link to="/upload" className="btn btn-primary btn-lg">🎬 수업 분석 시작</Link>
                    <Link to="/dashboard" className="btn btn-secondary btn-lg">📊 대시보드 보기</Link>
                </div>

                {/* Stats */}
                <div className="hero-stats">
                    <div className="hero-stat">
                        <div className="hero-stat-num">8</div>
                        <div className="hero-stat-label">AI 에이전트</div>
                    </div>
                    <div className="hero-stat">
                        <div className="hero-stat-num">18</div>
                        <div className="hero-stat-label">분석 영상</div>
                    </div>
                    <div className="hero-stat">
                        <div className="hero-stat-num">100%</div>
                        <div className="hero-stat-label">성공률</div>
                    </div>
                    <div className="hero-stat">
                        <div className="hero-stat-num">76.1</div>
                        <div className="hero-stat-label">평균 점수</div>
                    </div>
                </div>
            </section>

            {/* Pipeline */}
            <section className="home-section">
                <div className="section-header">
                    <h2>🔗 에이전트 파이프라인</h2>
                    <p>이벤트 기반 아키텍처로 각 에이전트가 순차/병렬 실행됩니다</p>
                </div>
                <div className="pipeline">
                    {agentPipeline.map((node, i) => (
                        <div key={i} className="pipeline-row">
                            <div className="pipe-node">
                                <div className="pipe-icon">{node.icon}</div>
                                <div className="pipe-name">{node.name}</div>
                                {node.sub && <div className="pipe-sub">{node.sub}</div>}
                            </div>
                            {i < agentPipeline.length - 1 && <div className="pipe-arrow">→</div>}
                        </div>
                    ))}
                </div>
            </section>

            {/* Quick Actions */}
            <section className="home-section">
                <div className="section-header">
                    <h2>⚡ 빠른 시작</h2>
                    <p>원하는 기능으로 바로 이동하세요</p>
                </div>
                <div className="quick-grid">
                    {quickActions.map((action, i) => (
                        <Link key={i} to={action.link} className="quick-card" style={{ '--card-color': action.color }}>
                            <div className="quick-card-icon">{action.icon}</div>
                            <h3>{action.title}</h3>
                            <p>{action.desc}</p>
                            <span className="quick-card-arrow">→</span>
                        </Link>
                    ))}
                </div>
            </section>

            {/* 8 Agents */}
            <section className="home-section">
                <div className="section-header">
                    <h2>🤖 8개 AI 에이전트</h2>
                    <p>각 에이전트는 독립적으로 전문 분석을 수행하고 결과를 공유합니다</p>
                </div>
                <div className="agents-grid">
                    {agents.map((agent, i) => (
                        <div key={i} className="agent-card">
                            <div className="agent-emoji">{agent.emoji}</div>
                            <h3>{agent.name}</h3>
                            <p>{agent.desc}</p>
                            <span className="agent-tech">{agent.tech}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* v8.0 Features */}
            <section className="home-section">
                <div className="section-header">
                    <h2>🚀 주요 기능</h2>
                    <p>Gemini 7차원 평가, 클라이언트 인증, 실시간 코칭, 통계 분석 ✅</p>
                </div>
                <div className="features-grid">
                    {features.map((feat, i) => (
                        <Link key={i} to={feat.link} className="feature-card">
                            <div className="feature-icon">{feat.icon}</div>
                            <div className="feature-content">
                                <div className="feature-header">
                                    <h3>{feat.title}</h3>
                                    <span className="feature-badge" style={{ background: `${feat.color}25`, color: feat.color }}>{feat.badge}</span>
                                </div>
                                <p>{feat.desc}</p>
                            </div>
                        </Link>
                    ))}
                </div>
            </section>

            {/* 7-Dimension Framework */}
            <section className="home-section">
                <div className="section-header">
                    <h2>📐 7차원 평가 프레임워크</h2>
                    <p>초등학교 임용 2차 수업실연 평가 기준 기반 100점 만점</p>
                </div>
                <div className="dimension-cards">
                    {[
                        { icon: '📚', name: '수업 전문성', score: '20점', items: '학습목표 명료성, 학습내용 충실성' },
                        { icon: '🎯', name: '교수학습 방법', score: '20점', items: '교수법 다양성, 학습활동 효과성' },
                        { icon: '✏️', name: '판서 및 언어', score: '15점', items: '판서 가독성, 언어 명료성' },
                        { icon: '👨‍🏫', name: '수업 태도', score: '15점', items: '교사 열정, 학생 소통, 자신감' },
                        { icon: '🙋', name: '학생 참여', score: '15점', items: '질문 기법, 피드백 제공' },
                        { icon: '⏱️', name: '시간 배분', score: '10점', items: '수업 단계별 시간 균형' },
                        { icon: '💡', name: '창의성', score: '5점', items: '수업 기법의 창의성' },
                    ].map((dim, i) => (
                        <div key={i} className="dim-card">
                            <span className="dim-icon">{dim.icon}</span>
                            <div className="dim-info">
                                <div className="dim-name">{dim.name}</div>
                                <div className="dim-items">{dim.items}</div>
                            </div>
                            <div className="dim-score">{dim.score}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Results Summary */}
            <section className="home-section">
                <div className="section-header">
                    <h2>📊 분석 결과 요약</h2>
                    <p>GAIM Lab v8.0 — 18개 영상 분석 결과</p>
                </div>
                <div className="results-grid">
                    <div className="result-card">
                        <div className="result-big" style={{ background: 'linear-gradient(135deg, #34d399, #6ee7b7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>18/18</div>
                        <div className="result-label">분석 성공률</div>
                    </div>
                    <div className="result-card">
                        <div className="result-big">76.1</div>
                        <div className="result-label">평균 점수 (C+)</div>
                    </div>
                    <div className="result-card">
                        <div className="result-big">84</div>
                        <div className="result-label">최고 점수 (B)</div>
                    </div>
                    <div className="result-card">
                        <div className="result-big">~1.5분</div>
                        <div className="result-label">영상당 처리 시간</div>
                    </div>
                </div>
                <div className="grade-dist">
                    <div className="grade-bar">
                        <div className="grade-segment a" style={{ width: '28%' }}><span>B 28%</span></div>
                        <div className="grade-segment bplus" style={{ width: '22%' }}><span>C+ 22%</span></div>
                        <div className="grade-segment b" style={{ width: '39%' }}><span>C 39%</span></div>
                        <div className="grade-segment bminus" style={{ width: '6%' }}></div>
                    </div>
                    <div className="grade-legend">
                        <span><span className="legend-dot a"></span> B (5)</span>
                        <span><span className="legend-dot bplus"></span> C+ (4)</span>
                        <span><span className="legend-dot b"></span> C (7)</span>
                        <span><span className="legend-dot bminus"></span> D+ (1)</span>
                    </div>
                </div>
            </section>

            {/* Tech Stack */}
            <section className="home-section">
                <div className="section-header">
                    <h2>⚙️ 기술 스택</h2>
                </div>
                <div className="tech-grid">
                    {[
                        { area: 'AI/ML', items: 'Gemini AI · Whisper · pyannote · OpenCV · Librosa' },
                        { area: 'Backend', items: 'FastAPI · WebSocket · Python 3.9+ · RAG · Pydantic' },
                        { area: 'Frontend', items: 'React 18 · Vite · Recharts · PWA' },
                        { area: '인증', items: 'Google OAuth 2.0 · JWT' },
                        { area: '데이터', items: 'SQLite (WAL) · Growth Analyzer' },
                        { area: '아키텍처', items: 'Pydantic Contract · Pub/Sub MessageBus' },
                    ].map((t, i) => (
                        <div key={i} className="tech-card">
                            <div className="tech-area">{t.area}</div>
                            <div className="tech-items">{t.items}</div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    )
}

export default HomePage
