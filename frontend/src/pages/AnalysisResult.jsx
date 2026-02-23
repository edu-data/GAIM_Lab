import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import './AnalysisResult.css'

function AnalysisResult() {
    const { analysisId } = useParams()
    const navigate = useNavigate()
    const [result, setResult] = useState(null)
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [animatedScores, setAnimatedScores] = useState({})

    useEffect(() => {
        let timeoutId = null
        const fetchResult = async () => {
            try {
                // 먼저 상태 확인
                const statusData = await api.analysis.status(analysisId)
                setStatus(statusData)

                if (statusData.status === 'completed') {
                    const resultData = await api.analysis.result(analysisId)
                    setResult(resultData)
                    // Animate scores
                    setTimeout(() => animateScores(resultData), 300)
                } else if (statusData.status === 'failed') {
                    setError(statusData.message || '분석이 실패했습니다.')
                } else if (statusData.status === 'processing' || statusData.status === 'pending') {
                    timeoutId = setTimeout(fetchResult, 2000)
                }
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchResult()
        return () => { if (timeoutId) clearTimeout(timeoutId) }
    }, [analysisId])

    const animateScores = (data) => {
        if (!data?.dimensions) return
        const scores = {}
        data.dimensions.forEach((dim, i) => {
            setTimeout(() => {
                scores[i] = dim.percentage
                setAnimatedScores({ ...scores })
            }, i * 150)
        })
    }

    const getGradeColor = (grade) => {
        if (!grade) return '#666'
        const g = grade.replace('+', '').replace('-', '')
        const colors = {
            'A': '#10b981', 'B': '#6366f1', 'C': '#f59e0b',
            'D': '#ef4444', 'F': '#6b7280'
        }
        return colors[g] || '#6366f1'
    }

    const getGradeEmoji = (grade) => {
        if (!grade) return '📊'
        const g = grade.replace('+', '').replace('-', '')
        return { 'A': '🏆', 'B': '👏', 'C': '💪', 'D': '📝', 'F': '📚' }[g] || '📊'
    }

    const getDimIcon = (name) => {
        const icons = {
            '수업 전문성': '📘', '교수학습 방법': '🎯', '판서 및 언어': '✍️',
            '수업 태도': '💎', '학생 참여': '🙋', '시간 배분': '⏱️', '창의성': '💡'
        }
        return icons[name] || '📊'
    }

    const getBarColor = (pct) => {
        if (pct >= 90) return 'linear-gradient(90deg, #10b981, #34d399)'
        if (pct >= 75) return 'linear-gradient(90deg, #6366f1, #818cf8)'
        if (pct >= 60) return 'linear-gradient(90deg, #f59e0b, #fbbf24)'
        return 'linear-gradient(90deg, #ef4444, #f87171)'
    }

    const renderRadarChart = (dimensions) => {
        if (!dimensions || dimensions.length === 0) return null

        const size = 280
        const center = size / 2
        const radius = 110
        const n = dimensions.length
        const angleStep = (2 * Math.PI) / n

        const maxPoints = dimensions.map((_, i) => {
            const angle = angleStep * i - Math.PI / 2
            return { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) }
        })

        const dataPoints = dimensions.map((dim, i) => {
            const angle = angleStep * i - Math.PI / 2
            const r = (dim.percentage / 100) * radius
            return { x: center + r * Math.cos(angle), y: center + r * Math.sin(angle) }
        })

        const labelPoints = dimensions.map((dim, i) => {
            const angle = angleStep * i - Math.PI / 2
            const r = radius + 28
            return {
                x: center + r * Math.cos(angle),
                y: center + r * Math.sin(angle),
                name: dim.name
            }
        })

        const dataPath = dataPoints.map((p, i) =>
            `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
        ).join(' ') + ' Z'

        return (
            <svg width={size} height={size} className="radar-chart" viewBox={`0 0 ${size} ${size}`}>
                {/* Grid rings */}
                {[0.25, 0.5, 0.75, 1].map((scale, i) => (
                    <polygon
                        key={i}
                        points={maxPoints.map(p => {
                            const dx = p.x - center
                            const dy = p.y - center
                            return `${center + dx * scale},${center + dy * scale}`
                        }).join(' ')}
                        fill="none"
                        stroke="rgba(255,255,255,0.08)"
                        strokeWidth="1"
                    />
                ))}
                {/* Axis lines */}
                {maxPoints.map((p, i) => (
                    <line key={i} x1={center} y1={center} x2={p.x} y2={p.y}
                        stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
                ))}
                {/* Data area */}
                <path d={dataPath} fill="rgba(99, 102, 241, 0.25)" stroke="#6366f1" strokeWidth="2.5" />
                {/* Data dots */}
                {dataPoints.map((p, i) => (
                    <circle key={i} cx={p.x} cy={p.y} r="5" fill="#6366f1" stroke="#fff" strokeWidth="2" />
                ))}
                {/* Labels */}
                {labelPoints.map((p, i) => (
                    <text key={i} x={p.x} y={p.y} textAnchor="middle" dominantBaseline="middle"
                        fill="var(--text-secondary)" fontSize="11" fontWeight="500">
                        {p.name}
                    </text>
                ))}
            </svg>
        )
    }

    // --- PROGRESS VIEW ---
    if (!loading && status && status.status !== 'completed' && status.status !== 'failed') {
        const progress = status.progress || 0
        const steps = [
            { label: '업로드', threshold: 10, icon: '📤' },
            { label: 'Gemini 전송', threshold: 30, icon: '🚀' },
            { label: '영상 처리', threshold: 40, icon: '🎞️' },
            { label: 'AI 분석', threshold: 60, icon: '🤖' },
            { label: '결과 처리', threshold: 80, icon: '📊' },
            { label: '완료', threshold: 100, icon: '✅' },
        ]

        return (
            <div className="result-container">
                <div className="progress-hero">
                    <div className="progress-pulse-ring">
                        <div className="progress-circle">
                            <svg viewBox="0 0 120 120" className="progress-svg">
                                <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(99,102,241,0.15)" strokeWidth="8" />
                                <circle cx="60" cy="60" r="52" fill="none" stroke="url(#progressGrad)" strokeWidth="8"
                                    strokeDasharray={`${progress * 3.27} 327`} strokeLinecap="round"
                                    transform="rotate(-90 60 60)" className="progress-arc" />
                                <defs>
                                    <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="#6366f1" />
                                        <stop offset="100%" stopColor="#a78bfa" />
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div className="progress-pct">{progress}%</div>
                        </div>
                    </div>

                    <h2 className="progress-title">🔄 AI 수업 분석 중</h2>
                    <p className="progress-message">{status.message}</p>

                    <div className="progress-steps">
                        {steps.map((step, i) => (
                            <div key={i} className={`step-item ${progress >= step.threshold ? 'done' : progress >= step.threshold - 10 ? 'active' : ''}`}>
                                <div className="step-icon">{step.icon}</div>
                                <div className="step-label">{step.label}</div>
                                {i < steps.length - 1 && (
                                    <div className={`step-line ${progress >= steps[i + 1].threshold ? 'done' : ''}`} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    // --- LOADING ---
    if (loading && !status) {
        return (
            <div className="result-container">
                <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>분석 결과를 불러오는 중...</p>
                </div>
            </div>
        )
    }

    // --- ERROR ---
    if (error) {
        return (
            <div className="result-container">
                <div className="error-card">
                    <h2>❌ 오류 발생</h2>
                    <p>{error}</p>
                    <button onClick={() => navigate('/upload')}>다시 시도</button>
                </div>
            </div>
        )
    }

    if (!result) return null

    // --- RESULT ---
    return (
        <div className="result-container fade-in">
            {/* Header */}
            <div className="result-header">
                <h1>📊 수업 분석 결과</h1>
                <div className="result-header-row">
                    {result.video_name && <p className="video-name">🎬 {result.video_name}</p>}
                    <button className="btn-pdf" onClick={() => window.print()} title="PDF로 내보내기">
                        📄 PDF 내보내기
                    </button>
                </div>
            </div>

            <div className="result-grid">
                {/* Main Score Card */}
                <div className="score-card main-score">
                    <div className="grade-emoji">{getGradeEmoji(result.grade)}</div>
                    <div className="grade-badge" style={{ background: getGradeColor(result.grade) }}>
                        {result.grade}
                    </div>
                    <div className="total-score">
                        <span className="score-value">{result.total_score}</span>
                        <span className="score-max">/ 100점</span>
                    </div>
                    <div className="score-subtitle">종합 평가 점수</div>
                </div>

                {/* Radar Chart */}
                <div className="chart-card">
                    <h3>🕸️ 7차원 레이더</h3>
                    {renderRadarChart(result.dimensions)}
                </div>

                {/* Dimension Bars */}
                <div className="dimensions-card">
                    <h3>📊 차원별 상세 점수</h3>
                    <div className="dimension-list">
                        {result.dimensions?.map((dim, i) => (
                            <div key={i} className="dimension-item" style={{ animationDelay: `${i * 0.1}s` }}>
                                <div className="dim-header">
                                    <span className="dim-name">
                                        <span className="dim-icon">{getDimIcon(dim.name)}</span>
                                        {dim.name}
                                    </span>
                                    <span className="dim-score">{dim.score}/{dim.max_score}</span>
                                </div>
                                <div className="dim-bar">
                                    <div
                                        className="dim-fill"
                                        style={{
                                            width: `${animatedScores[i] || 0}%`,
                                            background: getBarColor(dim.percentage)
                                        }}
                                    />
                                </div>
                                {dim.feedback && dim.feedback.length > 0 && (
                                    <div className="dim-feedback">
                                        {dim.feedback.map((f, j) => (
                                            <span key={j} className="feedback-chip">{f}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Strengths */}
                <div className="feedback-card strengths">
                    <h3>✅ 강점</h3>
                    <ul>
                        {result.strengths?.map((s, i) => (
                            <li key={i}><span className="list-bullet">💚</span> {s}</li>
                        ))}
                    </ul>
                </div>

                {/* Improvements */}
                <div className="feedback-card improvements">
                    <h3>🔧 개선점</h3>
                    <ul>
                        {result.improvements?.map((s, i) => (
                            <li key={i}><span className="list-bullet">💡</span> {s}</li>
                        ))}
                    </ul>
                </div>

                {/* Overall Feedback */}
                <div className="overall-feedback">
                    <h3>💬 종합 피드백</h3>
                    <p>{result.overall_feedback}</p>
                </div>
            </div>

            {/* Actions */}
            <div className="result-actions no-print">
                <button className="btn-pdf" onClick={() => window.print()}>
                    📄 PDF 내보내기
                </button>
                <button className="btn-secondary" onClick={() => navigate('/dashboard')}>
                    📊 대시보드로
                </button>
                <button className="btn-primary" onClick={() => navigate('/upload')}>
                    🎬 새 분석
                </button>
            </div>
        </div>
    )
}

export default AnalysisResult
