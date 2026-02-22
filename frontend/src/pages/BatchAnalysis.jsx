import { useState, useEffect, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../lib/api'
import './BatchAnalysis.css'

function BatchAnalysis() {
    const [videos, setVideos] = useState([])
    const [selectedVideos, setSelectedVideos] = useState([])
    const [selectAll, setSelectAll] = useState(false)
    const [loading, setLoading] = useState(false)
    const [batchStatus, setBatchStatus] = useState(null)
    const [batchResults, setBatchResults] = useState(null)
    const [polling, setPolling] = useState(false)

    // 영상 목록 조회
    useEffect(() => {
        fetchVideos()
    }, [])

    const fetchVideos = async () => {
        try {
            const data = await api.get('/analysis/batch/videos')
            setVideos(data.videos || [])
        } catch (error) {
            console.error('Failed to fetch videos:', error)
        }
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

    // 배치 분석 시작
    const startBatchAnalysis = async () => {
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

    // 상태 폴링
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

    // 결과 조회
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

    return (
        <div className="batch-analysis">
            <h1 className="page-title">
                <span>📊</span> 일괄 분석
            </h1>
            <p className="page-desc">
                2025-12-09 수업 시연 데이터셋(18개 영상)을 일괄 분석합니다.
            </p>

            {/* 영상 선택 섹션 */}
            <div className="video-selection card">
                <div className="card-header">
                    <h2>📹 영상 선택</h2>
                    <div className="select-actions">
                        <button
                            className="btn btn-secondary"
                            onClick={handleSelectAll}
                        >
                            {selectAll ? '전체 해제' : '전체 선택'}
                        </button>
                        <span className="selection-count">
                            {selectedVideos.length}/{videos.length} 선택됨
                        </span>
                    </div>
                </div>

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

                <div className="action-bar">
                    <button
                        className="btn btn-primary btn-large"
                        onClick={startBatchAnalysis}
                        disabled={loading || selectedVideos.length === 0 || polling}
                    >
                        {loading ? '시작 중...' : polling ? '분석 진행 중...' : '🚀 일괄 분석 시작'}
                    </button>
                </div>
            </div>

            {/* 진행 상황 */}
            {batchStatus && (
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

                    <div className="results-list">
                        <table className="results-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>영상 파일</th>
                                    <th>상태</th>
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
