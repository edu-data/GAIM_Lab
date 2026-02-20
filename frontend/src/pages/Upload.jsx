import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import RealtimeFeedback from '../components/RealtimeFeedback'
import { API_BASE } from '../apiConfig'
import './Upload.css'

function Upload() {
    const navigate = useNavigate()
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [analysisId, setAnalysisId] = useState(null)
    const [status, setStatus] = useState(null)
    const [result, setResult] = useState(null)
    const [showRealtime, setShowRealtime] = useState(false)
    const fileInputRef = useRef(null)

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0]
        if (selectedFile) {
            setFile(selectedFile)
            setStatus(null)
            setResult(null)
            setShowRealtime(false)
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) {
            setFile(droppedFile)
            setStatus(null)
            setResult(null)
            setShowRealtime(false)
        }
    }

    const handleUpload = async () => {
        if (!file) return

        setUploading(true)
        setStatus({ status: 'processing', progress: 10, message: '업로드 중...' })
        const formData = new FormData()
        formData.append('file', file)

        try {
            // 업로드 + 동기 분석 (Gemini 분석 완료까지 대기)
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
                // 동기 응답: 결과가 바로 포함됨
                setStatus({ status: 'completed', progress: 100, message: '분석 완료' })
                setResult(data)
            } else {
                // 비동기 응답: 폴링 시작
                setStatus(data)
                setShowRealtime(true)
                pollStatus(data.id)
            }
        } catch (error) {
            console.error('Upload failed:', error)
            setStatus({ status: 'failed', message: error.message || '업로드 실패' })
        }
        setUploading(false)
    }

    const pollStatus = async (id) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/analysis/${id}`)
                const data = await response.json()
                setStatus(data)

                if (data.status === 'completed') {
                    clearInterval(interval)
                    // 결과 가져오기
                    const resultResponse = await fetch(`${API_BASE}/analysis/${id}/result`)
                    const resultData = await resultResponse.json()
                    setResult(resultData)
                    setShowRealtime(false)
                } else if (data.status === 'failed') {
                    clearInterval(interval)
                    setShowRealtime(false)
                }
            } catch (error) {
                console.error('Poll failed:', error)
                clearInterval(interval)
            }
        }, 2000)
    }

    const handleAnalysisComplete = (analysisResult) => {
        setResult(analysisResult)
        setShowRealtime(false)
    }

    const handleAnalysisError = (errorMessage) => {
        setStatus({ status: 'failed', message: errorMessage })
        setShowRealtime(false)
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

            {/* 업로드 영역 */}
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

            {file && !status && (
                <button
                    className="btn btn-primary upload-btn"
                    onClick={handleUpload}
                    disabled={uploading}
                >
                    {uploading ? '업로드 중...' : '🚀 분석 시작'}
                </button>
            )}

            {/* 실시간 피드백 컴포넌트 */}
            {showRealtime && analysisId && (
                <RealtimeFeedback
                    analysisId={analysisId}
                    onComplete={handleAnalysisComplete}
                    onError={handleAnalysisError}
                />
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
                        <button className="btn btn-secondary">📄 리포트 다운로드</button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Upload
