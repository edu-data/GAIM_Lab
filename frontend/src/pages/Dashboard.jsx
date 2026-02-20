import { useState, useEffect } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import './Dashboard.css'

function Dashboard() {
    const [stats, setStats] = useState({
        totalSessions: 0,
        averageScore: 0,
        bestGrade: '-',
        badges: 0
    })
    const [demoResult, setDemoResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [history, setHistory] = useState([])

    // v7.0: Fetch real analysis history from DB
    useEffect(() => {
        fetch('/api/v1/history?limit=50')
            .then(r => r.json())
            .then(data => {
                const items = data.history || []
                setHistory(items)
                if (items.length > 0) {
                    const scores = items.map(h => h.total_score).filter(s => s > 0)
                    const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0
                    const best = items.reduce((b, h) => h.total_score > b.total_score ? h : b, items[0])
                    setStats({
                        totalSessions: items.length,
                        averageScore: avg,
                        bestGrade: best.grade || '-',
                        badges: Math.floor(items.length / 3)
                    })
                }
            })
            .catch(() => { }) // API may not be running
    }, [])

    const runDemo = async () => {
        setLoading(true)
        try {
            const response = await fetch('/api/v1/analysis/demo', { method: 'POST' })
            const data = await response.json()
            setDemoResult(data.gaim_evaluation)
        } catch (error) {
            console.error('Demo failed:', error)
        }
        setLoading(false)
    }

    // 레이더 차트 데이터 변환
    const getRadarData = () => {
        if (!demoResult) return []
        return demoResult.dimensions.map(dim => ({
            dimension: dim.name.replace('_', ' '),
            score: dim.percentage,
            fullMark: 100
        }))
    }

    // 바 차트 데이터 변환
    const getBarData = () => {
        if (!demoResult) return []
        return demoResult.dimensions.map(dim => ({
            name: dim.name.substring(0, 4),
            score: dim.score,
            max: dim.max_score
        }))
    }

    return (
        <div className="dashboard">
            <h1 className="page-title">
                <span>📊</span> 대시보드
            </h1>

            {/* 통계 카드 */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">🎬</div>
                    <div className="stat-value">{stats.totalSessions}</div>
                    <div className="stat-label">총 세션</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">📈</div>
                    <div className="stat-value">{stats.averageScore}</div>
                    <div className="stat-label">평균 점수</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🏆</div>
                    <div className="stat-value">{stats.bestGrade}</div>
                    <div className="stat-label">최고 등급</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🎖️</div>
                    <div className="stat-value">{stats.badges}</div>
                    <div className="stat-label">획득 배지</div>
                </div>
            </div>

            {/* 데모 분석 */}
            <div className="demo-section card">
                <h2>🧪 데모 분석</h2>
                <p className="demo-desc">
                    GAIM Lab의 7차원 수업 평가 시스템을 체험해 보세요.
                </p>
                <button
                    className="btn btn-primary"
                    onClick={runDemo}
                    disabled={loading}
                >
                    {loading ? '분석 중...' : '🚀 데모 실행'}
                </button>

                {demoResult && (
                    <div className="demo-result fade-in">
                        {/* 총점 */}
                        <div className="score-card">
                            <div className="score-circle">
                                <div className="score-value">{demoResult.total_score}</div>
                                <div className="score-max">/100</div>
                            </div>
                            <div className="grade-badge">{demoResult.grade}</div>
                        </div>

                        {/* 7차원 평가표 (초등 임용 2차 기준) */}
                        <div className="dimension-table-section">
                            <h3>📋 7차원 평가 상세 (초등 임용 2차 수업 시연 기준)</h3>
                            <table className="dimension-table">
                                <thead>
                                    <tr>
                                        <th>차원</th>
                                        <th>세부 기준</th>
                                        <th>점수</th>
                                        <th>달성률</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {demoResult.dimensions.map((dim, idx) => (
                                        <tr key={idx} className="dimension-row">
                                            <td className="dim-name">
                                                <span className="dim-icon">{['📚', '🎯', '✏️', '👨‍🏫', '🙋', '⏱️', '💡'][idx]}</span>
                                                {dim.name}
                                            </td>
                                            <td className="dim-criteria">
                                                {dim.criteria && Object.entries(dim.criteria).map(([key, val]) => (
                                                    <span key={key} className="criteria-item">
                                                        {key.replace(/_/g, ' ')}: {val}점
                                                    </span>
                                                ))}
                                            </td>
                                            <td className="dim-score">{dim.score} / {dim.max_score}</td>
                                            <td className="dim-percentage">
                                                <div className="progress-bar">
                                                    <div
                                                        className="progress-fill"
                                                        style={{ width: `${dim.percentage}%` }}
                                                    ></div>
                                                </div>
                                                <span>{dim.percentage}%</span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* 레이더 차트 */}
                        <div className="chart-container">
                            <h3>📊 7차원 역량 분석</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <RadarChart data={getRadarData()}>
                                    <PolarGrid stroke="#334155" />
                                    <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                                    <Radar
                                        name="점수"
                                        dataKey="score"
                                        stroke="#818cf8"
                                        fill="#4f46e5"
                                        fillOpacity={0.5}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* 차원별 점수 바 */}
                        <div className="chart-container">
                            <h3>📈 차원별 점수</h3>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={getBarData()}>
                                    <XAxis dataKey="name" tick={{ fill: '#94a3b8' }} />
                                    <YAxis tick={{ fill: '#94a3b8' }} />
                                    <Tooltip
                                        contentStyle={{
                                            background: '#1e293b',
                                            border: '1px solid #334155',
                                            borderRadius: '8px'
                                        }}
                                    />
                                    <Bar dataKey="score" fill="url(#colorGradient)" radius={[4, 4, 0, 0]} />
                                    <defs>
                                        <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#818cf8" />
                                            <stop offset="100%" stopColor="#4f46e5" />
                                        </linearGradient>
                                    </defs>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* 피드백 */}
                        <div className="feedback-section">
                            <h3>💬 종합 피드백</h3>
                            <p className="feedback-text">{demoResult.overall_feedback}</p>

                            <div className="feedback-grid">
                                <div className="feedback-card strengths">
                                    <h4>✅ 강점</h4>
                                    <ul>
                                        {demoResult.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                                    </ul>
                                </div>
                                <div className="feedback-card improvements">
                                    <h4>🔧 개선점</h4>
                                    <ul>
                                        {demoResult.improvements?.map((i, idx) => <li key={idx}>{i}</li>)}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Dashboard
