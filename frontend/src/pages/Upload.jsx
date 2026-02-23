import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { analyzeVideoClient, getStoredApiKey, isGitHubPages } from '../lib/clientAnalyzer'
import ApiKeySettings from '../components/ApiKeySettings'
import './Upload.css'

function Upload() {
    const navigate = useNavigate()
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [analysisId, setAnalysisId] = useState(null)
    const [status, setStatus] = useState(null)
    const [result, setResult] = useState(null)
    const [simProgress, setSimProgress] = useState(0)
    const [simMessage, setSimMessage] = useState('')
    const [showApiKeyModal, setShowApiKeyModal] = useState(false)
    const [clientMode, setClientMode] = useState(false)
    const fileInputRef = useRef(null)

    // GitHub Pages 환경 감지
    const isRemote = isGitHubPages()

    // Simulated progress animation during SERVER upload
    useEffect(() => {
        if (!uploading || clientMode) {
            if (!clientMode) setSimProgress(0)
            return
        }
        const messages = [
            [0, '📤 동영상 업로드 중...'],
            [15, '🚀 Gemini API에 전송 중...'],
            [30, '🎞️ 동영상 처리 중...'],
            [50, '🤖 AI가 수업을 분석하고 있어요...'],
            [65, '📊 7차원 평가 진행 중...'],
            [80, '✍️ 피드백 생성 중...'],
            [90, '⏳ 거의 완료...']
        ]
        let current = 0
        const timer = setInterval(() => {
            current += Math.random() * 3 + 0.5
            if (current > 92) current = 92
            setSimProgress(Math.round(current))
            const msg = [...messages].reverse().find(([t]) => current >= t)
            if (msg) setSimMessage(msg[1])
        }, 800)
        return () => clearInterval(timer)
    }, [uploading, clientMode])

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0]
        if (selectedFile) {
            setFile(selectedFile)
            setStatus(null)
            setResult(null)
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) {
            setFile(droppedFile)
            setStatus(null)
            setResult(null)
        }
    }

    /**
     * 클라이언트 사이드 분석 (GitHub Pages용)
     */
    const handleClientAnalysis = async () => {
        const apiKey = getStoredApiKey()
        if (!apiKey) {
            setShowApiKeyModal(true)
            return
        }

        setUploading(true)
        setClientMode(true)
        setSimProgress(0)
        setSimMessage('시작 중...')
        setStatus({ status: 'processing', progress: 0, message: '클라이언트 분석 시작...' })

        try {
            const data = await analyzeVideoClient(file, apiKey, (progress, message) => {
                setSimProgress(progress)
                setSimMessage(message)
                setStatus({ status: 'processing', progress, message })
            })

            setAnalysisId(data.id)
            setStatus({ status: 'completed', progress: 100, message: '분석 완료' })
            setResult(data)
        } catch (error) {
            console.error('Client analysis failed:', error)
            let errorMsg = error.message || '분석 실패'
            if (errorMsg.includes('API_KEY_INVALID') || errorMsg.includes('API key')) {
                errorMsg = 'API Key가 유효하지 않습니다. 설정을 확인해주세요.'
            }
            setStatus({ status: 'failed', message: errorMsg })
        }
        setUploading(false)
        setClientMode(false)
    }

    /**
     * 서버 사이드 분석 (로컬 개발용)
     */
    const handleServerUpload = async () => {
        setUploading(true)
        setClientMode(false)
        setStatus({ status: 'processing', progress: 10, message: '업로드 중...' })
        const formData = new FormData()
        formData.append('file', file)

        try {
            const data = await api.post('/analysis/upload?use_turbo=true&use_text=true', formData)

            setAnalysisId(data.id)

            if (data.status === 'completed' && data.dimensions) {
                setStatus({ status: 'completed', progress: 100, message: '분석 완료' })
                setResult(data)
            } else {
                setStatus(data)
            }
        } catch (error) {
            console.error('Upload failed:', error)
            setStatus({ status: 'failed', message: error.message || '업로드 실패' })
        }
        setUploading(false)
    }

    const handleUpload = () => {
        if (!file) return

        if (isRemote) {
            handleClientAnalysis()
        } else {
            handleServerUpload()
        }
    }

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    return (
        <div className="upload-page">
            <h1 className="page-title">
                <span>📹</span> 수업 분석
            </h1>

            {/* GitHub Pages 클라이언트 모드 배지 */}
            {isRemote && (
                <div className="client-mode-banner">
                    <span className="client-mode-icon">🌐</span>
                    <span>클라이언트 분석 모드 — 브라우저에서 직접 Gemini AI로 분석합니다</span>
                    <button
                        className="client-mode-key-btn"
                        onClick={() => setShowApiKeyModal(true)}
                        title="API Key 설정"
                    >
                        🔑 {getStoredApiKey() ? 'Key 변경' : 'Key 설정'}
                    </button>
                </div>
            )}

            {/* API Key 설정 모달 */}
            <ApiKeySettings
                open={showApiKeyModal}
                onClose={() => setShowApiKeyModal(false)}
                onSave={(key) => {
                    setShowApiKeyModal(false)
                    // 키 저장 후 바로 분석 시작 (파일이 있으면)
                    if (file && !uploading) {
                        setTimeout(() => handleClientAnalysis(), 300)
                    }
                }}
            />

            {/* 업로드 영역 — 분석 중이거나 결과 표시 중에는 숨김 */}
            {!uploading && !result && (
                <div
                    className={`upload-zone card ${file ? 'has-file' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={(e) => e.preventDefault()}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="video/*"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                    />

                    {file ? (
                        <div className="file-preview">
                            <div className="file-icon">🎬</div>
                            <div className="file-info">
                                <div className="file-name">{file.name}</div>
                                <div className="file-size">{formatFileSize(file.size)}</div>
                            </div>
                        </div>
                    ) : (
                        <div className="upload-prompt">
                            <div className="upload-icon">📁</div>
                            <p>클릭하거나 영상 파일을 드래그하세요</p>
                            <span className="upload-hint">MP4, AVI, MOV 지원</span>
                        </div>
                    )}
                </div>
            )}

            {file && !status && !uploading && (
                <button
                    className="btn btn-primary upload-btn"
                    onClick={handleUpload}
                >
                    🚀 분석 시작
                </button>
            )}

            {/* 분석 진행 시각화 */}
            {uploading && (
                <div className="analysis-progress-card card fade-in">
                    <div className="progress-circle-wrap">
                        <svg viewBox="0 0 120 120" className="progress-circle-svg">
                            <circle cx="60" cy="60" r="52" fill="none"
                                stroke="rgba(99,102,241,0.15)" strokeWidth="8" />
                            <circle cx="60" cy="60" r="52" fill="none"
                                stroke="url(#uploadGrad)" strokeWidth="8"
                                strokeDasharray={`${simProgress * 3.27} 327`}
                                strokeLinecap="round"
                                transform="rotate(-90 60 60)"
                                style={{ transition: 'stroke-dasharray 0.8s ease' }} />
                            <defs>
                                <linearGradient id="uploadGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#6366f1" />
                                    <stop offset="100%" stopColor="#a78bfa" />
                                </linearGradient>
                            </defs>
                        </svg>
                        <div className="progress-circle-text">{simProgress}%</div>
                    </div>
                    <h3 className="progress-title-text">
                        {clientMode ? '🌐 클라이언트 AI 분석 중' : '🤖 Gemini AI 분석 중'}
                    </h3>
                    <p className="progress-msg">{simMessage}</p>
                    <div className="progress-steps-mini">
                        {(clientMode
                            ? ['🎞️ 프레임', '🚀 전송', '🤖 분석', '📊 평가', '✅ 완료']
                            : ['📤 업로드', '🚀 전송', '🎞️ 처리', '🤖 분석', '📊 평가', '✅ 완료']
                        ).map((step, i, arr) => (
                            <div key={i} className={`mini-step ${simProgress >= ((i + 1) / arr.length) * 100 ? 'done' : simProgress >= (i / arr.length) * 100 ? 'active' : ''}`}>
                                {step}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 에러 메시지 */}
            {status?.status === 'failed' && !uploading && (
                <div className="error-msg card fade-in">
                    <h3>❌ 분석 실패</h3>
                    <p>{status.message}</p>
                    <div className="error-actions">
                        <button className="btn btn-primary" onClick={() => { setStatus(null); setFile(null) }}>
                            다시 시도
                        </button>
                        {isRemote && (
                            <button className="btn btn-secondary" onClick={() => setShowApiKeyModal(true)}>
                                🔑 API Key 확인
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* 분석 결과 */}
            {result && (
                <div className="result-card card fade-in">
                    <h3>✅ 분석 완료!</h3>

                    <div className="result-summary">
                        <div className="result-score">
                            <div className="score-big">{result.total_score}</div>
                            <div className="score-label">/ 100점</div>
                        </div>
                        <div className="result-grade">{result.grade}</div>
                    </div>

                    <div className="dimensions-list">
                        <h4>차원별 점수</h4>
                        {result.dimensions?.map((dim, idx) => (
                            <div key={idx} className="dimension-item">
                                <span className="dim-name">{dim.name}</span>
                                <div className="dim-bar">
                                    <div
                                        className="dim-fill"
                                        style={{ width: `${dim.percentage}%` }}
                                    />
                                </div>
                                <span className="dim-score">{dim.score}/{dim.max_score}</span>
                            </div>
                        ))}
                    </div>

                    <p className="feedback">{result.overall_feedback}</p>

                    <div className="result-actions">
                        {!isRemote && (
                            <button
                                className="btn btn-primary"
                                onClick={() => navigate(`/analysis/${analysisId}`)}
                            >
                                📊 상세 결과 보기
                            </button>
                        )}
                        <button className="btn btn-secondary" onClick={() => { setFile(null); setStatus(null); setResult(null) }}>
                            🎬 새 분석
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Upload
