import { useState, useEffect, useRef } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../lib/api'
import { analyzeVideoClient, getStoredApiKey, isGitHubPages } from '../lib/clientAnalyzer'
import ApiKeySettings from '../components/ApiKeySettings'
import './BatchAnalysis.css'

function BatchAnalysis() {
    const [videos, setVideos] = useState([])
    const [selectedVideos, setSelectedVideos] = useState([])
    const [selectAll, setSelectAll] = useState(false)
    const [loading, setLoading] = useState(false)
    const [batchStatus, setBatchStatus] = useState(null)
    const [batchResults, setBatchResults] = useState(null)
    const [polling, setPolling] = useState(false)
    const [showApiKeyModal, setShowApiKeyModal] = useState(false)
    const [clientProgress, setClientProgress] = useState(null)
    const fileInputRef = useRef(null)

    const isRemote = isGitHubPages()

    // 서버 모드: 영상 목록 조회
    useEffect(() => {
        if (!isRemote) {
            fetchVideos()
        }
    }, [isRemote])

    const fetchVideos = async () => {
        try {
            const data = await api.get('/analysis/batch/videos')
            setVideos(data.videos || [])
        } catch (error) {
            console.error('Failed to fetch videos:', error)
        }
    }

    // 클라이언트 모드: 파일 선택
    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files).filter(f => f.type.startsWith('video/'))
        const fileObjs = files.map(f => ({
            name: f.name,
            size_mb: (f.size / (1024 * 1024)).toFixed(1),
            file: f,
        }))
        setVideos(fileObjs)
        setSelectedVideos(fileObjs.map(v => v.name))
        setSelectAll(true)
        setBatchResults(null)
        setBatchStatus(null)
    }

    // 전체 선택/해제
    const handleSelectAll = () => {
        if (selectAll) {
            setSelectedVideos([])
        } else {
            setSelectedVideos(videos.map(v => v.name))
        }
        setSelectAll(!selectAll)
    }

    // 개별 선택
    const handleSelectVideo = (videoName) => {
        if (selectedVideos.includes(videoName)) {
            setSelectedVideos(selectedVideos.filter(v => v !== videoName))
        } else {
            setSelectedVideos([...selectedVideos, videoName])
        }
    }

    // 클라이언트 배치 분석
    const startClientBatchAnalysis = async () => {
        const apiKey = getStoredApiKey()
        if (!apiKey) {
            setShowApiKeyModal(true)
            return
        }

        const selectedFiles = videos.filter(v => selectedVideos.includes(v.name))
        if (selectedFiles.length === 0) {
            alert('분석할 영상을 선택해주세요')
            return
        }

        setLoading(true)
        setBatchResults(null)

        const total = selectedFiles.length
        const results = []

        for (let i = 0; i < total; i++) {
            const video = selectedFiles[i]
            const progress = Math.round((i / total) * 100)

            setBatchStatus({
                status: 'processing',
                total_videos: total,
                completed_videos: i,
                current_video: video.name,
                progress,
            })

            setClientProgress({
                videoIndex: i + 1,
                totalVideos: total,
                videoName: video.name,
                message: `🎬 ${video.name} 분석 중...`,
                subProgress: 0,
            })

            try {
                const data = await analyzeVideoClient(video.file, apiKey, (subProg, msg) => {
                    const overallProgress = Math.round(((i + subProg / 100) / total) * 100)
                    setBatchStatus(prev => ({ ...prev, progress: overallProgress }))
                    setClientProgress(prev => ({ ...prev, subProgress: subProg, message: msg }))
                })

                results.push({
                    video_name: video.name,
                    status: 'success',
                    total_score: data.total_score,
                    grade: data.grade,
                    dimensions: data.dimensions,
                    error: null,
                })
            } catch (error) {
                console.error(`Failed to analyze ${video.name}:`, error)
                results.push({
                    video_name: video.name,
                    status: 'failed',
                    total_score: null,
                    grade: null,
                    dimensions: null,
                    error: error.message,
                })
            }
        }

        // 결과 정리
        const successCount = results.filter(r => r.status === 'success').length
        const failedCount = results.filter(r => r.status !== 'success').length

        setBatchResults({
            success_count: successCount,
            failed_count: failedCount,
            results,
        })
        setBatchStatus({
            status: 'completed',
            total_videos: total,
            completed_videos: total,
            current_video: null,
            progress: 100,
        })
        setClientProgress(null)
        setLoading(false)
    }

    // 서버 배치 분석 시작
    const startServerBatchAnalysis = async () => {
        if (selectedVideos.length === 0) {
            alert('분석할 영상을 선택해주세요')
            return
        }

        setLoading(true)
        try {
            const data = await api.post('/analysis/batch/start', {
                video_names: selectedVideos.length === videos.length ? null : selectedVideos,
                limit: selectedVideos.length === videos.length ? null : selectedVideos.length
            })
            setBatchStatus(data)
            setPolling(true)
        } catch (error) {
            console.error('Failed to start batch:', error)
            alert('배치 분석 시작 실패')
        }
        setLoading(false)
    }

    const startBatchAnalysis = () => {
        if (isRemote) {
            startClientBatchAnalysis()
        } else {
            startServerBatchAnalysis()
        }
    }

    // 서버 모드: 상태 폴링
    useEffect(() => {
        if (!polling || !batchStatus) return

        const interval = setInterval(async () => {
            try {
                const data = await api.get(`/analysis/batch/${batchStatus.id}`)
                setBatchStatus(data)

                if (data.status === 'completed' || data.status === 'failed') {
                    setPolling(false)
                    fetchBatchResults(batchStatus.id)
                }
            } catch (error) {
                console.error('Polling error:', error)
            }
        }, 3000)

        return () => clearInterval(interval)
    }, [polling, batchStatus])

    const fetchBatchResults = async (batchId) => {
        try {
            const data = await api.get(`/analysis/batch/${batchId}/results`)
            setBatchResults(data)
        } catch (error) {
            console.error('Failed to fetch results:', error)
        }
    }

    // 진행률 색상
    const getProgressColor = (progress) => {
        if (progress < 30) return '#ef4444'
        if (progress < 70) return '#f59e0b'
        return '#22c55e'
    }

    // 점수 차트 데이터
    const getChartData = () => {
        if (!batchResults) return []
        return batchResults.results
            .filter(r => r.status === 'success' && r.total_score != null)
            .map(r => ({
                name: r.video_name.replace('.mp4', '').slice(-6),
                score: r.total_score,
                grade: r.grade,
            }))
    }

    const gradeColor = (grade) => {
        if (grade === 'A') return '#22c55e'
        if (grade === 'B') return '#6366f1'
        if (grade?.startsWith('C')) return '#f59e0b'
        return '#ef4444'
    }

    return (
        <div className="batch-analysis">
            <h1 className="page-title">
                <span>📊</span> 일괄 분석
            </h1>
            <p className="page-desc">
                {isRemote
                    ? '비디오 파일을 선택하여 브라우저에서 직접 AI 분석을 실행합니다.'
                    : '2025-12-09 수업 시연 데이터셋(18개 영상)을 일괄 분석합니다.'}
            </p>

            {/* API Key 모달 */}
            <ApiKeySettings
                open={showApiKeyModal}
                onClose={() => setShowApiKeyModal(false)}
                onSave={() => {
                    setShowApiKeyModal(false)
                    if (selectedVideos.length > 0) {
                        setTimeout(() => startClientBatchAnalysis(), 300)
                    }
                }}
            />

            {/* 영상 선택 섹션 */}
            <div className="video-selection card">
                <div className="card-header">
                    <h2>📹 영상 선택</h2>
                    <div className="select-actions">
                        {isRemote && (
                            <>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="video/*"
                                    multiple
                                    onChange={handleFileSelect}
                                    style={{ display: 'none' }}
                                />
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    📂 파일 선택
                                </button>
                            </>
                        )}
                        {videos.length > 0 && (
                            <button
                                className="btn btn-secondary"
                                onClick={handleSelectAll}
                            >
                                {selectAll ? '전체 해제' : '전체 선택'}
                            </button>
                        )}
                        <span className="selection-count">
                            {selectedVideos.length}/{videos.length} 선택됨
                        </span>
                    </div>
                </div>

                {/* 파일 미선택 안내 (GitHub Pages) */}
                {isRemote && videos.length === 0 && (
                    <div className="empty-state">
                        <div className="empty-icon">📁</div>
                        <p>분석할 비디오 파일들을 선택하세요</p>
                        <button
                            className="btn btn-primary"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            📂 비디오 파일 선택
                        </button>
                    </div>
                )}

                <div className="video-grid">
                    {videos.map((video, index) => (
                        <div
                            key={video.name}
                            className={`video-item ${selectedVideos.includes(video.name) ? 'selected' : ''}`}
                            onClick={() => handleSelectVideo(video.name)}
                        >
                            <input
                                type="checkbox"
                                checked={selectedVideos.includes(video.name)}
                                onChange={() => { }}
                            />
                            <div className="video-info">
                                <div className="video-index">{index + 1}</div>
                                <div className="video-name">{video.name}</div>
                                <div className="video-size">{video.size_mb} MB</div>
                            </div>
                        </div>
                    ))}
                </div>

                {videos.length > 0 && (
                    <div className="action-bar">
                        {isRemote && (
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowApiKeyModal(true)}
                                style={{ marginRight: '0.5rem' }}
                            >
                                🔑 {getStoredApiKey() ? 'Key 변경' : 'Key 설정'}
                            </button>
                        )}
                        <button
                            className="btn btn-primary btn-large"
                            onClick={startBatchAnalysis}
                            disabled={loading || selectedVideos.length === 0 || polling}
                        >
                            {loading ? '분석 중...' : polling ? '분석 진행 중...' : '🚀 일괄 분석 시작'}
                        </button>
                    </div>
                )}
            </div>

            {/* 진행 상황 */}
            {batchStatus && batchStatus.status !== 'completed' && (
                <div className="progress-section card">
                    <h2>⏳ 분석 진행 상황</h2>

                    <div className="progress-stats">
                        <div className="stat">
                            <span className="stat-label">상태</span>
                            <span className={`status-badge status-${batchStatus.status}`}>
                                {batchStatus.status === 'pending' && '대기 중'}
                                {batchStatus.status === 'processing' && '분석 중'}
                                {batchStatus.status === 'completed' && '완료'}
                                {batchStatus.status === 'failed' && '실패'}
                            </span>
                        </div>
                        <div className="stat">
                            <span className="stat-label">진행</span>
                            <span className="stat-value">
                                {batchStatus.completed_videos} / {batchStatus.total_videos}
                            </span>
                        </div>
                        <div className="stat">
                            <span className="stat-label">현재 분석</span>
                            <span className="stat-value current-video">
                                {batchStatus.current_video || '-'}
                            </span>
                        </div>
                    </div>

                    {/* 클라이언트 분석 서브 진행 */}
                    {clientProgress && (
                        <div className="client-sub-progress">
                            <p className="sub-progress-msg">{clientProgress.message}</p>
                            <div className="sub-progress-bar">
                                <div
                                    className="sub-progress-fill"
                                    style={{ width: `${clientProgress.subProgress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    <div className="progress-bar-container">
                        <div
                            className="progress-bar-fill"
                            style={{
                                width: `${batchStatus.progress}%`,
                                backgroundColor: getProgressColor(batchStatus.progress)
                            }}
                        ></div>
                        <span className="progress-text">{batchStatus.progress}%</span>
                    </div>
                </div>
            )}

            {/* 분석 결과 */}
            {batchResults && (
                <div className="results-section card">
                    <h2>📈 분석 결과</h2>

                    <div className="results-summary">
                        <div className="summary-stat success">
                            <span className="summary-icon">✅</span>
                            <span className="summary-value">{batchResults.success_count}</span>
                            <span className="summary-label">성공</span>
                        </div>
                        <div className="summary-stat failed">
                            <span className="summary-icon">❌</span>
                            <span className="summary-value">{batchResults.failed_count}</span>
                            <span className="summary-label">실패</span>
                        </div>
                    </div>

                    {/* 점수 차트 */}
                    {getChartData().length > 0 && (
                        <div className="chart-section">
                            <h3>📊 영상별 점수</h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={getChartData()} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={{ background: '#1e2030', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8 }}
                                        labelStyle={{ color: '#e2e8f0' }}
                                    />
                                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                                        {getChartData().map((entry, i) => (
                                            <Cell key={i} fill={gradeColor(entry.grade)} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    <div className="results-list">
                        <table className="results-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>영상 파일</th>
                                    <th>상태</th>
                                    <th>점수</th>
                                    <th>등급</th>
                                    <th>메시지</th>
                                </tr>
                            </thead>
                            <tbody>
                                {batchResults.results.map((result, index) => (
                                    <tr key={index} className={`result-row result-${result.status}`}>
                                        <td>{index + 1}</td>
                                        <td>{result.video_name}</td>
                                        <td>
                                            <span className={`status-icon ${result.status}`}>
                                                {result.status === 'success' ? '✅' : result.status === 'timeout' ? '⏱️' : '❌'}
                                            </span>
                                        </td>
                                        <td className="score-cell">
                                            {result.total_score != null ? result.total_score : '-'}
                                        </td>
                                        <td>
                                            {result.grade && (
                                                <span className="grade-badge" style={{ color: gradeColor(result.grade) }}>
                                                    {result.grade}
                                                </span>
                                            )}
                                        </td>
                                        <td className="error-message">
                                            {result.error || '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}

export default BatchAnalysis
