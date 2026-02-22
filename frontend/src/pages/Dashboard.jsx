import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
    ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
    AreaChart, Area, CartesianGrid
} from 'recharts'
import api from '../lib/api'
import './Dashboard.css'

function Dashboard() {
    const [stats, setStats] = useState({
        totalSessions: 0, averageScore: 0, bestGrade: '-', badges: 0,
        bestScore: 0, scoreRange: 0
    })
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [demoResult, setDemoResult] = useState(null)
    const [demoLoading, setDemoLoading] = useState(false)

    useEffect(() => {
        api.get('/history?limit=50')
            .then(data => {
                const items = data.history || []
                setHistory(items)
                if (items.length > 0) {
                    const scores = items.map(h => h.total_score).filter(s => s > 0)
                    const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0
                    const best = items.reduce((b, h) => h.total_score > b.total_score ? h : b, items[0])
                    const worst = items.reduce((w, h) => h.total_score < w.total_score ? h : w, items[0])
                    setStats({
                        totalSessions: items.length,
                        averageScore: avg,
                        bestGrade: best.grade || '-',
                        bestScore: best.total_score || 0,
                        scoreRange: ((best.total_score || 0) - (worst.total_score || 0)).toFixed(1),
                        badges: Math.floor(items.length / 3)
                    })
                }
                setLoading(false)
            })
            .catch(() => {
                // Demo fallback — API 미연결 시 샘플 데이터 표시
                const demoHistory = [
                    { filename: '20251209_100926.mp4', total_score: 76.1, grade: 'C+', created_at: '2025-12-09T10:09:26' },
                    { filename: '20251209_102400.mp4', total_score: 84.0, grade: 'B', created_at: '2025-12-09T10:24:00' },
                    { filename: '20251209_104016.mp4', total_score: 71.3, grade: 'C', created_at: '2025-12-09T10:40:16' },
                ]
                setHistory(demoHistory)
                setStats({ totalSessions: 3, averageScore: 77.1, bestGrade: 'B', bestScore: 84, scoreRange: 12.7, badges: 1 })
                setLoading(false)
            })
    }, [])

    const runDemo = async () => {
        setDemoLoading(true)
        try {
            const data = await api.post('/analysis/demo')
            setDemoResult(data.gaim_evaluation)
        } catch (e) {
            console.error('Demo failed:', e)
            // Fallback demo result
            setDemoResult({
                total_score: 76.1,
                grade: 'C+',
                dimensions: [
                    { name: '수업 전문성', score: 12, max_score: 15, percentage: 80 },
                    { name: '교수학습 방법', score: 11, max_score: 15, percentage: 73 },
                    { name: '판서 및 언어', score: 11, max_score: 15, percentage: 73 },
                    { name: '수업 태도', score: 11, max_score: 15, percentage: 73 },
                    { name: '학생 참여', score: 10, max_score: 15, percentage: 67 },
                    { name: '시간 배분', score: 11, max_score: 15, percentage: 73 },
                    { name: '창의성', score: 10, max_score: 10, percentage: 100 },
                ],
            })
        }
        setDemoLoading(false)
    }

    const getRadarData = () => {
        if (!demoResult) return []
        return demoResult.dimensions.map(dim => ({
            dimension: dim.name.length > 5 ? dim.name.substring(0, 5) + '..' : dim.name,
            score: dim.percentage,
            fullMark: 100
        }))
    }

    const getDimensionBarData = () => {
        if (!demoResult) return []
        return demoResult.dimensions.map(dim => ({
            name: dim.name.substring(0, 4),
            score: dim.score,
            max: dim.max_score,
            pct: dim.percentage
        }))
    }

    const getHistoryTrend = () => {
        return history.slice().reverse().map((h, i) => ({
            session: `#${i + 1}`,
            score: h.total_score,
            filename: h.filename || 'unknown'
        }))
    }

    const dimIcons = ['📚', '🎯', '✏️', '👨‍🏫', '🙋', '⏱️', '💡']

    return (
        <div className="dashboard">
            <h1 className="page-title"><span>📊</span> 전체 대시보드</h1>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">🎬</div>
                    <div className="stat-value">{loading ? '—' : stats.totalSessions}</div>
                    <div className="stat-label">총 분석 세션</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">📈</div>
                    <div className="stat-value">{loading ? '—' : stats.averageScore}</div>
                    <div className="stat-label">평균 점수</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🏆</div>
                    <div className="stat-value">{loading ? '—' : stats.bestGrade}</div>
                    <div className="stat-label">최고 등급</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🎖️</div>
                    <div className="stat-value">{loading ? '—' : stats.badges}</div>
                    <div className="stat-label">획득 배지</div>
                </div>
            </div>

            {/* Dashboard Grid */}
            <div className="dash-grid">
                {/* Recent Analysis History */}
                <div className="dash-card history-card">
                    <div className="dash-card-header">
                        <h3>📋 최근 분석 이력</h3>
                        <Link to="/batch" className="dash-card-link">전체 보기 →</Link>
                    </div>
                    {history.length === 0 ? (
                        <div className="empty-state">
                            <p>아직 분석 이력이 없습니다</p>
                            <Link to="/upload" className="btn btn-primary" style={{ marginTop: '1rem' }}>🎬 첫 분석 시작</Link>
                        </div>
                    ) : (
                        <div className="history-table-wrap">
                            <table className="history-table">
                                <thead>
                                    <tr>
                                        <th>날짜</th>
                                        <th>파일명</th>
                                        <th>점수</th>
                                        <th>등급</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.slice(0, 8).map((item, i) => (
                                        <tr key={i}>
                                            <td className="td-date">{item.analyzed_at ? new Date(item.analyzed_at).toLocaleDateString('ko-KR') : '-'}</td>
                                            <td className="td-file">{(item.filename || 'unknown').replace('.mp4', '')}</td>
                                            <td className="td-score">{item.total_score}</td>
                                            <td><span className={`grade-badge grade-${(item.grade || '').replace(/[+-]/g, '').toLowerCase()}`}>{item.grade}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Growth Trend */}
                <div className="dash-card trend-card">
                    <div className="dash-card-header">
                        <h3>📈 점수 추세</h3>
                        <Link to="/growth" className="dash-card-link">성장보고서 →</Link>
                    </div>
                    {history.length > 1 ? (
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={getHistoryTrend()}>
                                <defs>
                                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.4} />
                                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0.05} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                                <XAxis dataKey="session" tick={{ fill: '#64748b', fontSize: 11 }} />
                                <YAxis domain={[50, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(22, 22, 48, 0.95)',
                                        border: '1px solid rgba(99,102,241,0.3)',
                                        borderRadius: '10px',
                                        color: '#e2e8f0'
                                    }}
                                />
                                <Area type="monotone" dataKey="score" stroke="#6366f1" fill="url(#areaGrad)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="empty-state">
                            <p>2개 이상의 분석 결과가 필요합니다</p>
                        </div>
                    )}
                </div>

                {/* Quick Demo */}
                <div className="dash-card demo-card">
                    <div className="dash-card-header">
                        <h3>🧪 데모 분석</h3>
                    </div>
                    <p className="demo-desc">7차원 수업 평가 시스템을 체험해 보세요</p>
                    <button className="btn btn-primary" onClick={runDemo} disabled={demoLoading} style={{ width: '100%' }}>
                        {demoLoading ? '분석 중...' : '🚀 데모 실행'}
                    </button>

                    {demoResult && (
                        <div className="demo-result fade-in">
                            <div className="demo-score-row">
                                <div className="demo-score-circle">
                                    <span className="demo-score-num">{demoResult.total_score}</span>
                                    <span className="demo-score-max">/100</span>
                                </div>
                                <span className={`grade-badge-lg grade-${(demoResult.grade || '').replace(/[+-]/g, '').toLowerCase()}`}>
                                    {demoResult.grade}
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Quick Actions */}
                <div className="dash-card actions-card">
                    <div className="dash-card-header">
                        <h3>⚡ 빠른 실행</h3>
                    </div>
                    <div className="actions-list">
                        <Link to="/upload" className="action-item">
                            <span className="action-icon">🎬</span>
                            <div>
                                <div className="action-title">수업 분석</div>
                                <div className="action-desc">영상 업로드 → AI 평가</div>
                            </div>
                        </Link>
                        <Link to="/agents" className="action-item">
                            <span className="action-icon">🤖</span>
                            <div>
                                <div className="action-title">MAS 분석</div>
                                <div className="action-desc">에이전트 파이프라인</div>
                            </div>
                        </Link>
                        <Link to="/cohort" className="action-item">
                            <span className="action-icon">🔬</span>
                            <div>
                                <div className="action-title">코호트 비교</div>
                                <div className="action-desc">집단 비교 분석</div>
                            </div>
                        </Link>
                        <Link to="/live" className="action-item">
                            <span className="action-icon">🔴</span>
                            <div>
                                <div className="action-title">실시간 코칭</div>
                                <div className="action-desc">라이브 피드백</div>
                            </div>
                        </Link>
                    </div>
                </div>
            </div>

            {/* Demo Charts (shown when demo result exists) */}
            {demoResult && (
                <div className="demo-charts fade-in-up">
                    <div className="dash-grid-2">
                        {/* Radar Chart */}
                        <div className="dash-card">
                            <div className="dash-card-header">
                                <h3>🕸️ 7차원 역량 분석</h3>
                            </div>
                            <ResponsiveContainer width="100%" height={280}>
                                <RadarChart data={getRadarData()}>
                                    <PolarGrid stroke="rgba(99,102,241,0.2)" />
                                    <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                                    <Radar name="점수" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} strokeWidth={2} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Dimension Bar */}
                        <div className="dash-card">
                            <div className="dash-card-header">
                                <h3>📊 차원별 점수</h3>
                            </div>
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={getDimensionBarData()}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={{
                                            background: 'rgba(22, 22, 48, 0.95)',
                                            border: '1px solid rgba(99,102,241,0.3)',
                                            borderRadius: '10px',
                                            color: '#e2e8f0'
                                        }}
                                    />
                                    <defs>
                                        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#818cf8" />
                                            <stop offset="100%" stopColor="#4f46e5" />
                                        </linearGradient>
                                    </defs>
                                    <Bar dataKey="score" fill="url(#barGrad)" radius={[6, 6, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Dimension Detail Table */}
                    <div className="dash-card dim-detail-card">
                        <div className="dash-card-header">
                            <h3>📋 7차원 평가 상세</h3>
                        </div>
                        <table className="dim-table">
                            <thead>
                                <tr>
                                    <th>차원</th>
                                    <th>점수</th>
                                    <th>달성률</th>
                                    <th>진행도</th>
                                </tr>
                            </thead>
                            <tbody>
                                {demoResult.dimensions.map((dim, i) => (
                                    <tr key={i}>
                                        <td className="dim-name-cell">
                                            <span className="dim-emoji">{dimIcons[i]}</span>
                                            {dim.name}
                                        </td>
                                        <td className="dim-score-cell">{dim.score}/{dim.max_score}</td>
                                        <td className="dim-pct-cell">{dim.percentage}%</td>
                                        <td className="dim-bar-cell">
                                            <div className="progress-bar">
                                                <div className="progress-fill" style={{ width: `${dim.percentage}%` }}></div>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Feedback */}
                    {demoResult.overall_feedback && (
                        <div className="dash-card">
                            <div className="dash-card-header">
                                <h3>💬 종합 피드백</h3>
                            </div>
                            <p className="feedback-text">{demoResult.overall_feedback}</p>
                            <div className="feedback-grid">
                                <div className="feedback-box strengths">
                                    <h4>✅ 강점</h4>
                                    <ul>{demoResult.strengths?.map((s, i) => <li key={i}>{s}</li>)}</ul>
                                </div>
                                <div className="feedback-box improvements">
                                    <h4>🔧 개선점</h4>
                                    <ul>{demoResult.improvements?.map((s, i) => <li key={i}>{s}</li>)}</ul>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default Dashboard
