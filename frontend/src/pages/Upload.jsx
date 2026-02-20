import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE } from '../apiConfig'
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
    const fileInputRef = useRef(null)

    // Simulated progress animation during upload
    useEffect(() => {
        if (!uploading) {
            setSimProgress(0)
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
    }, [uploading])

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

    const handleUpload = async () => {
        if (!file) return

        setUploading(true)
        setStatus({ status: 'processing', progress: 10, message: '업로드 중...' })
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch(`${API_BASE}/analysis/upload?use_turbo=true&use_text=true`, {
                method: 'POST',
                body: formData
            })
            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || '분석 실패')
            }

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
                    <h3 className="progress-title-text">🤖 Gemini AI 분석 중</h3>
                    <p className="progress-msg">{simMessage}</p>
                    <div className="progress-steps-mini">
                        {['📤 업로드', '🚀 전송', '🎞️ 처리', '🤖 분석', '📊 평가', '✅ 완료'].map((step, i) => (
                            <div key={i} className={`mini-step ${simProgress >= (i + 1) * 15 ? 'done' : simProgress >= i * 15 ? 'active' : ''}`}>
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
                    <button className="btn btn-primary" onClick={() => { setStatus(null); setFile(null) }}>
                        다시 시도
                    </button>
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
                        <button
                            className="btn btn-primary"
                            onClick={() => navigate(`/analysis/${analysisId}`)}
                        >
                            📊 상세 결과 보기
                        </button>
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
