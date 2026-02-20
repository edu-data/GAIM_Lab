import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import VideoHighlights from '../components/VideoHighlights'
import './AnalysisResult.css'

const API_BASE = 'http://localhost:8000/api/v1'

function AnalysisResult() {
    const { analysisId } = useParams()
    const navigate = useNavigate()
    const [result, setResult] = useState(null)
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchResult = async () => {
            try {
                // 먼저 상태 확인
                const statusRes = await fetch(`${API_BASE}/analysis/status/${analysisId}`)
                if (!statusRes.ok) throw new Error('분석 상태를 확인할 수 없습니다.')
                const statusData = await statusRes.json()
                setStatus(statusData)

                if (statusData.status === 'completed') {
                    // 결과 조회
                    const resultRes = await fetch(`${API_BASE}/analysis/result/${analysisId}`)
                    if (!resultRes.ok) throw new Error('분석 결과를 불러올 수 없습니다.')
                    const resultData = await resultRes.json()
                    setResult(resultData)
                } else if (statusData.status === 'failed') {
                    setError('분석이 실패했습니다.')
                }
                // 진행 중이면 폴링
                else if (statusData.status === 'processing' || statusData.status === 'pending') {
                    setTimeout(fetchResult, 2000)
                }
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchResult()
    }, [analysisId])

    const getGradeColor = (grade) => {
        const colors = {
            'S': '#FFD700', 'A': '#4CAF50', 'B': '#2196F3',
            'C': '#FF9800', 'D': '#f44336', 'F': '#9E9E9E'
        }
        return colors[grade] || '#666'
    }

    const renderRadarChart = (dimensions) => {
        if (!dimensions || dimensions.length === 0) return null

        const size = 200
        const center = size / 2
        const radius = 80
        const angleStep = (2 * Math.PI) / dimensions.length

        const points = dimensions.map((dim, i) => {
            const angle = angleStep * i - Math.PI / 2
            const r = (dim.score / dim.max_score) * radius
            return {
                x: center + r * Math.cos(angle),
                y: center + r * Math.sin(angle),
                label: dim.dimension.replace('_', ' '),
                score: dim.score,
                max: dim.max_score
            }
        })

        const pathData = points.map((p, i) =>
            `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
        ).join(' ') + ' Z'

        return (
            <svg width={size} height={size} className="radar-chart">
                {/* 배경 그리드 */}
                {[0.25, 0.5, 0.75, 1].map((scale, i) => (
                    <polygon
                        key={i}
                        points={dimensions.map((_, j) => {
                            const angle = angleStep * j - Math.PI / 2
                            const r = radius * scale
                            return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`
                        }).join(' ')}
                        fill="none"
                        stroke="rgba(255,255,255,0.1)"
                    />
                ))}

                {/* 데이터 영역 */}
                <path d={pathData} fill="rgba(99, 102, 241, 0.3)" stroke="#6366f1" strokeWidth="2" />

                {/* 데이터 포인트 */}
                {points.map((p, i) => (
                    <circle key={i} cx={p.x} cy={p.y} r="4" fill="#6366f1" />
                ))}
            </svg>
        )
    }

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

    if (status && status.status !== 'completed') {
        return (
            <div className="result-container">
                <div className="progress-card">
                    <h2>🔄 분석 진행 중</h2>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${status.progress}%` }}
                        ></div>
                    </div>
                    <p className="progress-text">{status.progress}% - {status.message}</p>
                </div>
            </div>
        )
    }

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

    return (
        <div className="result-container">
            <div className="result-header">
                <h1>📊 수업 분석 결과</h1>
                <p className="video-name">{result.video_name}</p>
            </div>

            <div className="result-grid">
                {/* 총점 카드 */}
                <div className="score-card main-score">
                    <div className="grade-badge" style={{ background: getGradeColor(result.grade) }}>
                        {result.grade}
                    </div>
                    <div className="total-score">
                        <span className="score-value">{result.total_score?.toFixed(1)}</span>
                        <span className="score-max">/ 100점</span>
                    </div>
                </div>

                {/* 레이더 차트 */}
                <div className="chart-card">
                    <h3>7차원 평가</h3>
                    {renderRadarChart(result.dimensions)}
                </div>

                {/* 차원별 점수 */}
                <div className="dimensions-card">
                    <h3>차원별 상세 점수</h3>
                    <div className="dimension-list">
                        {result.dimensions?.map((dim, i) => (
                            <div key={i} className="dimension-item">
                                <div className="dim-header">
                                    <span className="dim-name">{dim.dimension.replace(/_/g, ' ')}</span>
                                    <span className="dim-score">{dim.score}/{dim.max_score}</span>
                                </div>
                                <div className="dim-bar">
                                    <div
                                        className="dim-fill"
                                        style={{ width: `${(dim.score / dim.max_score) * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 강점 */}
                <div className="feedback-card strengths">
                    <h3>✅ 강점</h3>
                    <ul>
                        {result.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                </div>

                {/* 개선점 */}
                <div className="feedback-card improvements">
                    <h3>🔧 개선점</h3>
                    <ul>
                        {result.improvements?.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                </div>

                {/* 종합 피드백 */}
                <div className="overall-feedback">
                    <h3>💬 종합 피드백</h3>
                    <p>{result.overall_feedback}</p>
                </div>

                {/* 영상 하이라이트 (v7.1) */}
                {result.video_url && (
                    <div className="highlights-section">
                        <h3>🎬 영상 하이라이트</h3>
                        <VideoHighlights
                            videoUrl={result.video_url}
                            highlights={result.highlights || [
                                { time: 30, label: '수업 도입 시작', type: 'info', detail: '동기유발 활동' },
                                { time: 120, label: '교수학습 전략 우수', type: 'positive', detail: '학생 참여 유도 구간' },
                                { time: 300, label: '긴 침묵 구간', type: 'warning', detail: '3초 이상 침묵 발생' },
                            ]}
                        />
                    </div>
                )}
            </div>

            <div className="result-actions">
                <button className="btn-secondary" onClick={() => navigate('/')}>
                    대시보드로
                </button>
                <button className="btn-primary" onClick={() => navigate('/upload')}>
                    새 분석
                </button>
            </div>
        </div>
    )
}

export default AnalysisResult
