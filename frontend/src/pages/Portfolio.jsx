import { useState, useEffect } from 'react'
import {
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
    RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
    BarChart, Bar, Legend
} from 'recharts'
import { API_BASE } from '../apiConfig'
import './Portfolio.css'

function Portfolio() {
    const [studentId, setStudentId] = useState('')
    const [portfolio, setPortfolio] = useState(null)
    const [sessions, setSessions] = useState([])
    const [badges, setBadges] = useState([])
    const [loading, setLoading] = useState(false)
    const [selectedSession, setSelectedSession] = useState(null)
    const [error, setError] = useState(null)
    const [dataSource, setDataSource] = useState(null) // 'db' or 'demo'

    // v7.1: DB에서 분석 이력 로드
    const loadFromDB = async () => {
        setLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE}/history?limit=50`)
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            const data = await res.json()

            if (data.history && data.history.length > 0) {
                // DB 데이터를 세션 형식으로 변환
                const dbSessions = data.history.map(item => ({
                    date: item.created_at?.split('T')[0] || item.video_name || '날짜 없음',
                    total_score: item.total_score || 0,
                    grade: item.grade || 'N/A',
                    video_name: item.video_name || '',
                    dimensions: item.dimensions || [
                        { name: '수업 전문성', score: item.dimension_scores?.['수업 전문성'] || 0, max: 20 },
                        { name: '교수학습 방법', score: item.dimension_scores?.['교수학습 방법'] || 0, max: 20 },
                        { name: '판서 및 언어', score: item.dimension_scores?.['판서 및 언어'] || 0, max: 15 },
                        { name: '수업 태도', score: item.dimension_scores?.['수업 태도'] || 0, max: 15 },
                        { name: '학생 참여', score: item.dimension_scores?.['학생 참여'] || 0, max: 15 },
                        { name: '시간 배분', score: item.dimension_scores?.['시간 배분'] || 0, max: 10 },
                        { name: '창의성', score: item.dimension_scores?.['창의성'] || 0, max: 5 },
                    ]
                }))

                const scores = dbSessions.map(s => s.total_score)
                const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length
                const bestScore = Math.max(...scores)
                const firstScore = scores[scores.length - 1] || 0
                const lastScore = scores[0] || 0
                const improvementRate = firstScore > 0
                    ? Math.round((lastScore - firstScore) / firstScore * 1000) / 10
                    : 0

                setPortfolio({
                    student_id: studentId || 'DB 사용자',
                    name: studentId || '분석 이력',
                    total_sessions: dbSessions.length,
                    average_score: Math.round(avgScore * 10) / 10,
                    best_score: Math.round(bestScore * 10) / 10,
                    improvement_rate: improvementRate,
                })

                // 시간순 정렬 (오래된 것 먼저)
                const sorted = [...dbSessions].reverse()
                setSessions(sorted)
                setSelectedSession(sorted[sorted.length - 1])
                setDataSource('db')

                // 배지 자동 산출
                const autoBadges = []
                if (sorted.length >= 1) autoBadges.push({ badge_id: 'first_session', name: '첫 수업 시연', icon: '🎬', category: 'milestone', points: 10, earned_at: sorted[0].date })
                if (sorted.length >= 5) autoBadges.push({ badge_id: 'five_sessions', name: '꾸준한 연습', icon: '🔄', category: 'milestone', points: 30, earned_at: sorted[4].date })
                if (sorted.length >= 10) autoBadges.push({ badge_id: 'ten_sessions', name: '10회 달성', icon: '🏆', category: 'milestone', points: 50, earned_at: sorted[9].date })
                if (bestScore >= 80) autoBadges.push({ badge_id: 'score_80', name: '우수 수업', icon: '⭐', category: 'achievement', points: 25, earned_at: '-' })
                if (bestScore >= 90) autoBadges.push({ badge_id: 'score_90', name: '모범 수업', icon: '🌟', category: 'achievement', points: 50, earned_at: '-' })
                if (improvementRate >= 10) autoBadges.push({ badge_id: 'improve_10', name: '10% 성장', icon: '📈', category: 'growth', points: 20, earned_at: '-' })
                setBadges(autoBadges)
            } else {
                setError('DB에 분석 이력이 없습니다. 먼저 영상 분석을 실행하세요.')
            }
        } catch (e) {
            console.error('DB load failed, falling back to demo:', e)
            setError(`DB 연결 실패 (${e.message}). 데모 데이터를 표시합니다.`)
            loadDemoData()
        }
        setLoading(false)
    }

    // 기존 데모 데이터 (폴백용)
    const loadDemoData = () => {
        const demoSessions = [
            {
                date: '2026-01-15', total_score: 72, grade: 'C+', dimensions: [
                    { name: '수업 전문성', score: 12, max: 20 }, { name: '교수학습 방법', score: 13, max: 20 },
                    { name: '판서 및 언어', score: 10, max: 15 }, { name: '수업 태도', score: 11, max: 15 },
                    { name: '학생 참여', score: 10, max: 15 }, { name: '시간 배분', score: 7, max: 10 }, { name: '창의성', score: 3, max: 5 }
                ]
            },
            {
                date: '2026-02-05', total_score: 85, grade: 'B+', dimensions: [
                    { name: '수업 전문성', score: 16, max: 20 }, { name: '교수학습 방법', score: 17, max: 20 },
                    { name: '판서 및 언어', score: 13, max: 15 }, { name: '수업 태도', score: 13, max: 15 },
                    { name: '학생 참여', score: 13, max: 15 }, { name: '시간 배분', score: 8, max: 10 }, { name: '창의성', score: 4, max: 5 }
                ]
            }
        ]
        setPortfolio({
            student_id: 'demo_student', name: '김예비 (데모)',
            total_sessions: 2, average_score: 78.5, best_score: 85.0, improvement_rate: 12.5,
        })
        setSessions(demoSessions)
        setSelectedSession(demoSessions[demoSessions.length - 1])
        setBadges([
            { badge_id: 'first_session', name: '첫 수업 시연', icon: '🎬', category: 'milestone', points: 10, earned_at: '2026-01-15' },
            { badge_id: 'score_80', name: '우수 수업', icon: '⭐', category: 'achievement', points: 25, earned_at: '2026-02-05' },
        ])
        setDataSource('demo')
    }

    // 페이지 로드 시 자동으로 DB 조회 시도
    useEffect(() => {
        loadFromDB()
    }, [])

    const getProgressData = () => {
        return sessions.map((s, idx) => ({
            session: `#${idx + 1}`,
            score: s.total_score,
            date: s.date
        }))
    }

    const getDimensionRadarData = (session) => {
        if (!session || !session.dimensions) return []
        return session.dimensions.map(d => ({
            dimension: d.name.slice(0, 4),
            fullName: d.name,
            score: Math.round(d.score / d.max * 100),
            raw: d.score,
            max: d.max
        }))
    }

    const getDimensionComparisonData = () => {
        if (sessions.length < 2) return []
        const first = sessions[0]
        const last = sessions[sessions.length - 1]

        return first.dimensions.map((d, idx) => ({
            dimension: d.name.slice(0, 4),
            fullName: d.name,
            first: Math.round(d.score / d.max * 100),
            last: Math.round(last.dimensions[idx].score / last.dimensions[idx].max * 100),
            growth: Math.round(last.dimensions[idx].score / last.dimensions[idx].max * 100) - Math.round(d.score / d.max * 100)
        }))
    }

    const handleDownloadPDF = () => {
        alert('PDF 포트폴리오 다운로드 기능은 추후 구현 예정입니다.')
    }

    return (
        <div className="portfolio-page">
            <h1 className="page-title">
                <span>📂</span> 포트폴리오
            </h1>

            {/* 학생 검색 */}
            <div className="search-section card">
                <h2>학생 포트폴리오 조회</h2>
                <div className="search-form">
                    <input
                        type="text"
                        placeholder="학번 입력..."
                        value={studentId}
                        onChange={(e) => setStudentId(e.target.value)}
                        className="search-input"
                    />
                    <button className="btn btn-primary" onClick={loadFromDB}>DB 조회</button>
                    <button className="btn btn-secondary" onClick={() => { loadDemoData(); setDataSource('demo') }}>
                        데모 보기
                    </button>
                </div>
                {dataSource && (
                    <div className={`data-source-badge ${dataSource}`}>
                        {dataSource === 'db' ? '📊 DB 실제 데이터' : '🎭 데모 데이터'}
                    </div>
                )}
                {error && <div className="error-message">{error}</div>}
            </div>

            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>로딩 중...</p>
                </div>
            )}

            {portfolio && (
                <div className="portfolio-content fade-in">
                    {/* 프로필 카드 */}
                    <div className="profile-card card">
                        <div className="profile-header">
                            <div className="avatar">👩‍🎓</div>
                            <div className="profile-info">
                                <h2>{portfolio.name}</h2>
                                <span className="student-id">{portfolio.student_id}</span>
                            </div>
                            <button className="btn btn-secondary pdf-btn" onClick={handleDownloadPDF}>
                                📄 PDF 다운로드
                            </button>
                        </div>

                        <div className="profile-stats">
                            <div className="stat">
                                <div className="stat-value">{portfolio.total_sessions}</div>
                                <div className="stat-label">총 세션</div>
                            </div>
                            <div className="stat">
                                <div className="stat-value">{portfolio.average_score}</div>
                                <div className="stat-label">평균 점수</div>
                            </div>
                            <div className="stat">
                                <div className="stat-value">{portfolio.best_score}</div>
                                <div className="stat-label">최고 점수</div>
                            </div>
                            <div className="stat">
                                <div className={`stat-value ${portfolio.improvement_rate >= 0 ? 'positive' : 'negative'}`}>
                                    {portfolio.improvement_rate >= 0 ? '+' : ''}{portfolio.improvement_rate}%
                                </div>
                                <div className="stat-label">개선율</div>
                            </div>
                        </div>
                    </div>

                    {/* 차원별 성장 비교 */}
                    <div className="dimension-comparison-card card">
                        <h3>📊 7차원 역량 발전 비교 (첫 세션 vs 최근 세션)</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={getDimensionComparisonData()} layout="vertical">
                                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8' }} />
                                <YAxis type="category" dataKey="dimension" width={60} tick={{ fill: '#94a3b8' }} />
                                <Tooltip
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            const data = payload[0].payload
                                            return (
                                                <div className="custom-tooltip">
                                                    <p className="tooltip-title">{data.fullName}</p>
                                                    <p>첫 세션: {data.first}%</p>
                                                    <p>최근: {data.last}%</p>
                                                    <p className={data.growth >= 0 ? 'positive' : 'negative'}>
                                                        성장: {data.growth >= 0 ? '+' : ''}{data.growth}%
                                                    </p>
                                                </div>
                                            )
                                        }
                                        return null
                                    }}
                                />
                                <Legend />
                                <Bar dataKey="first" name="첫 세션" fill="#64748b" radius={[0, 4, 4, 0]} />
                                <Bar dataKey="last" name="최근 세션" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* 진척도 차트 */}
                    <div className="progress-card card">
                        <h3>📈 점수 변화 추이</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={getProgressData()}>
                                <XAxis dataKey="session" tick={{ fill: '#94a3b8' }} />
                                <YAxis domain={[60, 100]} tick={{ fill: '#94a3b8' }} />
                                <Tooltip
                                    contentStyle={{
                                        background: '#1e293b',
                                        border: '1px solid #334155',
                                        borderRadius: '8px'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="score"
                                    stroke="#4f46e5"
                                    strokeWidth={3}
                                    dot={{ fill: '#818cf8', strokeWidth: 2, r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* 최근 세션 레이더 차트 */}
                    {selectedSession && (
                        <div className="radar-card card">
                            <h3>🎯 최근 세션 역량 분석 ({selectedSession.date})</h3>
                            <ResponsiveContainer width="100%" height={280}>
                                <RadarChart data={getDimensionRadarData(selectedSession)}>
                                    <PolarGrid stroke="#334155" />
                                    <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                                    <Radar
                                        name="달성률"
                                        dataKey="score"
                                        stroke="#10b981"
                                        fill="#10b981"
                                        fillOpacity={0.4}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* 배지 */}
                    <div className="badges-card card">
                        <h3>🎖️ 획득한 배지</h3>
                        <div className="badges-grid">
                            {badges.map((badge, idx) => (
                                <div key={idx} className={`badge-item ${badge.category}`}>
                                    <div className="badge-icon">{badge.icon}</div>
                                    <div className="badge-info">
                                        <div className="badge-name">{badge.name}</div>
                                        <div className="badge-meta">
                                            <span className="badge-points">+{badge.points}pts</span>
                                            <span className="badge-date">{badge.earned_at}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="total-points">
                            총 포인트: <strong>{badges.reduce((sum, b) => sum + b.points, 0)}</strong>pt
                        </div>
                    </div>

                    {/* 세션 기록 */}
                    <div className="sessions-card card">
                        <h3>📋 수업 시연 기록</h3>
                        <div className="sessions-list">
                            {sessions.map((session, idx) => (
                                <div
                                    key={idx}
                                    className={`session-item ${selectedSession === session ? 'selected' : ''}`}
                                    onClick={() => setSelectedSession(session)}
                                >
                                    <div className="session-number">#{idx + 1}</div>
                                    <div className="session-date">{session.date}</div>
                                    <div className="session-score">{session.total_score}점</div>
                                    <div className={`session-grade grade-${session.grade.replace('+', 'plus')}`}>
                                        {session.grade}
                                    </div>
                                    <div className="session-arrow">→</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Portfolio
