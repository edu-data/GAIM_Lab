import { useState, useEffect, useCallback, useRef } from 'react'
import AgentCard from '../components/AgentCard'
import AgentTimeline from '../components/AgentTimeline'
import {
    extractResources,
    analyzeVision,
    analyzeContent,
    analyzeSTT,
    analyzeVibe,
    evaluatePedagogy,
    generateFeedback,
    generateReport,
} from '../utils/videoAnalyzer'
import './AgentMonitor.css'

// ── 에이전트 정의 ──
const AGENT_DEFS = {
    extractor: { name: 'extractor', role: '리소스 추출기 (Canvas)', icon: '📦', dependencies: [] },
    vision: { name: 'vision', role: '비전 분석 에이전트', icon: '👁️', dependencies: ['extractor'] },
    content: { name: 'content', role: '콘텐츠 분석 에이전트', icon: '🎨', dependencies: ['extractor'] },
    stt: { name: 'stt', role: '음성 활동 에이전트', icon: '🗣️', dependencies: ['extractor'] },
    vibe: { name: 'vibe', role: '음성 프로소디 에이전트', icon: '🔊', dependencies: ['extractor'] },
    pedagogy: { name: 'pedagogy', role: '교육학 평가 에이전트', icon: '📚', dependencies: ['vision', 'content', 'stt', 'vibe'] },
    feedback: { name: 'feedback', role: '피드백 생성 에이전트', icon: '💡', dependencies: ['pedagogy'] },
    master: { name: 'master', role: '종합 분석 마스터', icon: '🧠', dependencies: ['vision', 'content', 'vibe', 'pedagogy', 'feedback'] },
}

function makeAgents(status = 'idle') {
    const out = {}
    for (const [k, v] of Object.entries(AGENT_DEFS)) {
        out[k] = { ...v, status, progress: 0, elapsed_seconds: 0, has_result: false }
    }
    return out
}

export default function AgentMonitor() {
    const [agents, setAgents] = useState(() => makeAgents())
    const [pipelineStatus, setPipelineStatus] = useState('idle')
    const [pipelineProgress, setPipelineProgress] = useState(0)
    const [isRunning, setIsRunning] = useState(false)
    const [log, setLog] = useState([])
    const [elapsedTotal, setElapsedTotal] = useState(0)
    const [history, setHistory] = useState([])

    // 비디오 업로드 상태
    const [videoFile, setVideoFile] = useState(null)
    const [videoPreview, setVideoPreview] = useState(null)
    const [videoDuration, setVideoDuration] = useState(0)
    const fileInputRef = useRef(null)

    // 분석 결과
    const [finalReport, setFinalReport] = useState(null)

    const timerRef = useRef(null)
    const startTimeRef = useRef(null)
    const abortRef = useRef(false)

    const logEndRef = useRef(null)
    useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [log])

    // ── 로그 ──
    const addLog = useCallback((msg) => {
        setLog(prev => [...prev, { time: new Date().toLocaleTimeString('ko-KR'), msg }])
    }, [])

    // ── 에이전트 상태 업데이트 ──
    const updateAgent = useCallback((name, updates) => {
        setAgents(prev => ({ ...prev, [name]: { ...prev[name], ...updates } }))
    }, [])

    // ── 비디오 파일 선택 ──
    const handleFileSelect = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        setVideoFile(file)
        setFinalReport(null)
        setPipelineStatus('idle')
        setAgents(makeAgents())
        setLog([])

        const url = URL.createObjectURL(file)
        setVideoPreview(url)
        const tempVideo = document.createElement('video')
        tempVideo.src = url
        tempVideo.onloadedmetadata = () => {
            setVideoDuration(tempVideo.duration)
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        const file = e.dataTransfer.files[0]
        if (file && file.type.startsWith('video/')) {
            // 파일 입력에 직접 설정할 수 없으므로 수동 처리
            setVideoFile(file)
            setFinalReport(null)
            setPipelineStatus('idle')
            setAgents(makeAgents())
            setLog([])
            const url = URL.createObjectURL(file)
            setVideoPreview(url)
            const tempVideo = document.createElement('video')
            tempVideo.src = url
            tempVideo.onloadedmetadata = () => { setVideoDuration(tempVideo.duration) }
        }
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const formatDuration = (sec) => {
        const m = Math.floor(sec / 60)
        const s = Math.floor(sec % 60)
        return `${m}:${String(s).padStart(2, '0')}`
    }

    // ── 실제 분석 실행 ──
    const runAnalysis = useCallback(async () => {
        if (!videoFile) return
        abortRef.current = false

        setAgents(makeAgents())
        setPipelineStatus('running')
        setPipelineProgress(0)
        setIsRunning(true)
        setLog([])
        setElapsedTotal(0)
        setFinalReport(null)
        startTimeRef.current = Date.now()

        timerRef.current = setInterval(() => {
            setElapsedTotal(+((Date.now() - startTimeRef.current) / 1000).toFixed(1))
        }, 100)

        addLog(`🚀 실제 비디오 분석 시작: ${videoFile.name} (${formatSize(videoFile.size)})`)
        const completedAgents = {}
        let extractResult, visionResult, contentResult, sttResult, vibeResult, pedagogyResult, feedbackResult

        try {
            // ─── Phase 1: Extractor ───
            const extStart = Date.now()
            updateAgent('extractor', { status: 'running', progress: 0 })
            addLog('▶️ 📦 extractor 시작 — 비디오에서 프레임+오디오 추출')

            extractResult = await extractResources(videoFile, (p) => {
                updateAgent('extractor', { progress: p })
            })

            const extElapsed = +((Date.now() - extStart) / 1000).toFixed(1)
            updateAgent('extractor', { status: 'done', progress: 100, elapsed_seconds: extElapsed, has_result: true, result_desc: `${extractResult.totalFrames}프레임 + 오디오 추출 (${extractResult.videoWidth}×${extractResult.videoHeight})` })
            addLog(`✅ 📦 extractor 완료 (${extElapsed}s) — ${extractResult.totalFrames}프레임 + 오디오 추출`)
            completedAgents.extractor = true
            setPipelineProgress(12)

            if (abortRef.current) throw new Error('중지됨')

            // ─── Phase 2: Vision + Content + STT + Vibe (동시) ───
            addLog('▶️ 👁️🎨🗣️🔊 분석 에이전트 4개 동시 시작')
            updateAgent('vision', { status: 'running', progress: 0 })
            updateAgent('content', { status: 'running', progress: 0 })
            updateAgent('stt', { status: 'running', progress: 0 })
            updateAgent('vibe', { status: 'running', progress: 0 })

            const visionStart = Date.now()
            const contentStart = Date.now()
            const sttStart = Date.now()
            const vibeStart = Date.now()

            // 순차 실행 (메인 스레드이므로 진행 UI 업데이트를 위해 비동기 청크로)
            visionResult = await runAsync(() => analyzeVision(extractResult.frames, (p) => {
                updateAgent('vision', { progress: p })
            }))
            const visElapsed = +((Date.now() - visionStart) / 1000).toFixed(1)
            updateAgent('vision', { status: 'done', progress: 100, elapsed_seconds: visElapsed, has_result: true, result_desc: visionResult.desc })
            addLog(`✅ 👁️ vision 완료 (${visElapsed}s) — ${visionResult.desc}`)
            completedAgents.vision = true
            setPipelineProgress(25)

            if (abortRef.current) throw new Error('중지됨')

            contentResult = await runAsync(() => analyzeContent(extractResult.frames, (p) => {
                updateAgent('content', { progress: p })
            }))
            const contElapsed = +((Date.now() - contentStart) / 1000).toFixed(1)
            updateAgent('content', { status: 'done', progress: 100, elapsed_seconds: contElapsed, has_result: true, result_desc: contentResult.desc })
            addLog(`✅ 🎨 content 완료 (${contElapsed}s) — ${contentResult.desc}`)
            completedAgents.content = true
            setPipelineProgress(38)

            if (abortRef.current) throw new Error('중지됨')

            sttResult = await runAsync(() => analyzeSTT(extractResult.audioData, (p) => {
                updateAgent('stt', { progress: p })
            }))
            const sttElapsed = +((Date.now() - sttStart) / 1000).toFixed(1)
            updateAgent('stt', { status: 'done', progress: 100, elapsed_seconds: sttElapsed, has_result: true, result_desc: sttResult.desc })
            addLog(`✅ 🗣️ stt 완료 (${sttElapsed}s) — ${sttResult.desc}`)
            completedAgents.stt = true
            setPipelineProgress(50)

            if (abortRef.current) throw new Error('중지됨')

            vibeResult = await runAsync(() => analyzeVibe(extractResult.audioData, (p) => {
                updateAgent('vibe', { progress: p })
            }))
            const vibeElapsed = +((Date.now() - vibeStart) / 1000).toFixed(1)
            updateAgent('vibe', { status: 'done', progress: 100, elapsed_seconds: vibeElapsed, has_result: true, result_desc: vibeResult.desc })
            addLog(`✅ 🔊 vibe 완료 (${vibeElapsed}s) — ${vibeResult.desc}`)
            completedAgents.vibe = true
            setPipelineProgress(62)

            if (abortRef.current) throw new Error('중지됨')

            // ─── Phase 3: Pedagogy ───
            const pedStart = Date.now()
            updateAgent('pedagogy', { status: 'running', progress: 0 })
            addLog('▶️ 📚 pedagogy 시작 — 7차원 평가')

            pedagogyResult = await runAsync(() => evaluatePedagogy(visionResult, contentResult, sttResult, vibeResult, (p) => {
                updateAgent('pedagogy', { progress: p })
            }))
            const pedElapsed = +((Date.now() - pedStart) / 1000).toFixed(1)
            updateAgent('pedagogy', { status: 'done', progress: 100, elapsed_seconds: pedElapsed, has_result: true, result_desc: pedagogyResult.desc })
            addLog(`✅ 📚 pedagogy 완료 (${pedElapsed}s) — ${pedagogyResult.desc}`)
            completedAgents.pedagogy = true
            setPipelineProgress(75)

            if (abortRef.current) throw new Error('중지됨')

            // ─── Phase 4: Feedback ───
            const fbStart = Date.now()
            updateAgent('feedback', { status: 'running', progress: 0 })
            addLog('▶️ 💡 feedback 시작 — 맞춤형 피드백 생성')

            feedbackResult = await runAsync(() => generateFeedback(pedagogyResult, visionResult, vibeResult, (p) => {
                updateAgent('feedback', { progress: p })
            }))
            const fbElapsed = +((Date.now() - fbStart) / 1000).toFixed(1)
            updateAgent('feedback', { status: 'done', progress: 100, elapsed_seconds: fbElapsed, has_result: true, result_desc: feedbackResult.desc })
            addLog(`✅ 💡 feedback 완료 (${fbElapsed}s) — ${feedbackResult.desc}`)
            completedAgents.feedback = true
            setPipelineProgress(87)

            if (abortRef.current) throw new Error('중지됨')

            // ─── Phase 5: Master ───
            const masterStart = Date.now()
            updateAgent('master', { status: 'running', progress: 0 })
            addLog('▶️ 🧠 master 시작 — 종합 리포트 생성')

            const masterResult = await runAsync(() => generateReport(
                extractResult, visionResult, contentResult, sttResult, vibeResult, pedagogyResult, feedbackResult,
                (p) => { updateAgent('master', { progress: p }) }
            ))
            const masterElapsed = +((Date.now() - masterStart) / 1000).toFixed(1)
            updateAgent('master', { status: 'done', progress: 100, elapsed_seconds: masterElapsed, has_result: true, result_desc: masterResult.desc })
            addLog(`✅ 🧠 master 완료 (${masterElapsed}s) — ${masterResult.desc}`)

            // ── 완료 ──
            clearInterval(timerRef.current)
            const totalTime = +((Date.now() - startTimeRef.current) / 1000).toFixed(1)
            setElapsedTotal(totalTime)
            setPipelineStatus('completed')
            setPipelineProgress(100)
            setIsRunning(false)
            setFinalReport(masterResult.report)
            addLog(`🎉 전체 파이프라인 완료! (${totalTime}s) — 총점: ${pedagogyResult.totalScore}/100 (${pedagogyResult.grade})`)

            setHistory(prev => [{
                id: `run-${Date.now().toString(36)}`,
                video: videoFile.name,
                status: 'completed',
                elapsed: totalTime,
                score: pedagogyResult.totalScore,
                grade: pedagogyResult.grade,
                created_at: new Date().toISOString(),
            }, ...prev])

        } catch (e) {
            clearInterval(timerRef.current)
            const totalTime = +((Date.now() - startTimeRef.current) / 1000).toFixed(1)
            setElapsedTotal(totalTime)
            setPipelineStatus('failed')
            setIsRunning(false)
            addLog(`❌ 분석 실패: ${e.message}`)
        }
    }, [videoFile, addLog, updateAgent])

    // ── 값비싼 동기 연산을 비동기로 래핑 (UI freeze 방지) ──
    function runAsync(fn) {
        return new Promise(resolve => setTimeout(() => resolve(fn()), 10))
    }

    // ── 리셋 ──
    const resetPipeline = useCallback(() => {
        abortRef.current = true
        if (timerRef.current) clearInterval(timerRef.current)
        setAgents(makeAgents())
        setPipelineStatus('idle')
        setPipelineProgress(0)
        setIsRunning(false)
        setLog([])
        setElapsedTotal(0)
        setFinalReport(null)
    }, [])

    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current)
        }
    }, [])

    return (
        <div className="agent-monitor">
            <div className="monitor-header">
                <div className="monitor-title">
                    <h2>🤖 멀티 에이전트 모니터</h2>
                    <p className="monitor-subtitle">동영상을 업로드하면 8개 AI 에이전트가 실제 분석합니다</p>
                </div>
                <div className="monitor-actions">
                    {videoFile && !isRunning && pipelineStatus !== 'completed' && (
                        <button className="btn-primary" onClick={runAnalysis}>
                            🚀 분석 시작
                        </button>
                    )}
                    {isRunning && (
                        <button className="btn-secondary" onClick={resetPipeline}>
                            ⏹ 중지
                        </button>
                    )}
                    {pipelineStatus === 'completed' && (
                        <button className="btn-secondary" onClick={resetPipeline}>
                            🔄 새 분석
                        </button>
                    )}
                </div>
            </div>

            {/* 비디오 업로드 영역 */}
            {!isRunning && pipelineStatus !== 'completed' && (
                <div className="glass-card upload-section">
                    <div
                        className={`video-upload-zone ${videoFile ? 'has-file' : ''}`}
                        onClick={() => fileInputRef.current?.click()}
                        onDrop={handleDrop}
                        onDragOver={e => e.preventDefault()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="video/*"
                            onChange={handleFileSelect}
                            style={{ display: 'none' }}
                        />

                        {videoFile ? (
                            <div className="video-file-info">
                                <div className="video-thumb-wrap">
                                    {videoPreview && (
                                        <video
                                            src={videoPreview}
                                            className="video-thumb"
                                            muted
                                            preload="metadata"
                                        />
                                    )}
                                </div>
                                <div className="video-details">
                                    <span className="video-name">🎬 {videoFile.name}</span>
                                    <span className="video-meta">{formatSize(videoFile.size)} · {videoDuration > 0 ? formatDuration(videoDuration) : '...'}</span>
                                    <span className="video-change">클릭하여 다른 동영상 선택</span>
                                </div>
                            </div>
                        ) : (
                            <div className="upload-empty">
                                <div className="upload-icon-big">📹</div>
                                <p className="upload-cta">클릭하거나 동영상을 드래그하세요</p>
                                <span className="upload-hint">MP4, AVI, WebM 지원 · 최대 5분 권장</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* 파이프라인 타임라인 */}
            <div className="glass-card pipeline-section">
                <h3>📊 파이프라인 흐름</h3>
                <AgentTimeline agents={agents} />

                {pipelineStatus !== 'idle' && (
                    <div className="pipeline-status-bar">
                        <div className="status-info">
                            <span className={`status-dot ${pipelineStatus}`} />
                            <span className="status-text">
                                {pipelineStatus === 'completed' ? '✅ 분석 완료' :
                                    pipelineStatus === 'running' ? '⏳ 분석 진행 중' :
                                        pipelineStatus === 'failed' ? '❌ 분석 실패' : '⏸ 대기 중'}
                            </span>
                        </div>
                        <div className="progress-container">
                            <div className="progress-bar">
                                <div className="progress-fill" style={{ width: `${pipelineProgress}%` }} />
                            </div>
                            <span className="progress-text">{pipelineProgress}%</span>
                        </div>
                        <span className="elapsed-label">⏱️ {elapsedTotal}s</span>
                    </div>
                )}
            </div>

            {/* 에이전트 카드 그리드 */}
            <div className="glass-card agents-section">
                <h3>🧩 에이전트 상태</h3>
                <div className="agents-grid">
                    {Object.values(agents).map(agent => (
                        <AgentCard key={agent.name} agent={agent} isActive={agent.status === 'running'} />
                    ))}
                </div>
            </div>

            {/* 분석 결과 */}
            {finalReport && (
                <div className="glass-card result-section">
                    <h3>📊 분석 결과</h3>
                    <div className="result-summary">
                        <div className="result-score-big">
                            <span className="score-number">{finalReport.totalScore}</span>
                            <span className="score-label">/100</span>
                        </div>
                        <div className={`result-grade grade-${finalReport.grade.replace('+', 'p')}`}>
                            {finalReport.grade}
                        </div>
                    </div>

                    <div className="dimensions-grid">
                        {finalReport.dimensions.map((dim, i) => (
                            <div key={i} className="dim-item">
                                <div className="dim-header">
                                    <span className="dim-name">{dim.name}</span>
                                    <span className="dim-score">{dim.score}/{dim.max}</span>
                                </div>
                                <div className="dim-bar">
                                    <div
                                        className="dim-fill"
                                        style={{ width: `${(dim.score / dim.max) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>

                    {finalReport.feedback && (
                        <div className="feedback-list">
                            {finalReport.feedback.strengths.map((s, i) => (
                                <div key={`s${i}`} className="feedback-item strength">✅ {s.message}</div>
                            ))}
                            {finalReport.feedback.improvements.map((s, i) => (
                                <div key={`i${i}`} className="feedback-item improve">⚠️ {s.message}</div>
                            ))}
                            {finalReport.feedback.tips.map((t, i) => (
                                <div key={`t${i}`} className="feedback-item tip">{t}</div>
                            ))}
                        </div>
                    )}

                    <div className="result-metrics">
                        <div className="metric"><span className="metric-label">영상 길이</span><span className="metric-value">{formatDuration(finalReport.summary.duration)}</span></div>
                        <div className="metric"><span className="metric-label">해상도</span><span className="metric-value">{finalReport.summary.resolution}</span></div>
                        <div className="metric"><span className="metric-label">분석 프레임</span><span className="metric-value">{finalReport.summary.totalFrames}장</span></div>
                        <div className="metric"><span className="metric-label">제스처 활성</span><span className="metric-value">{finalReport.metrics.gestureActivity}%</span></div>
                        <div className="metric"><span className="metric-label">슬라이드</span><span className="metric-value">{finalReport.metrics.slideCount}장</span></div>
                        <div className="metric"><span className="metric-label">음성 활성</span><span className="metric-value">{finalReport.metrics.speechActivity}%</span></div>
                        <div className="metric"><span className="metric-label">추정 어절</span><span className="metric-value">{finalReport.metrics.estimatedWords}어절</span></div>
                        <div className="metric"><span className="metric-label">침묵 비율</span><span className="metric-value">{finalReport.metrics.silenceRatio}%</span></div>
                    </div>
                </div>
            )}

            {/* 실행 로그 */}
            {log.length > 0 && (
                <div className="glass-card log-section">
                    <h3>📜 실행 로그</h3>
                    <div className="log-container">
                        {log.map((entry, i) => (
                            <div key={i} className="log-entry">
                                <span className="log-time">{entry.time}</span>
                                <span className="log-msg">{entry.msg}</span>
                            </div>
                        ))}
                        <div ref={logEndRef} />
                    </div>
                </div>
            )}

            {/* 실행 이력 */}
            {history.length > 0 && (
                <div className="glass-card history-section">
                    <h3>📋 실행 이력</h3>
                    <div className="history-list">
                        {history.map(h => (
                            <div key={h.id} className={`history-item ${h.status}`}>
                                <span className="history-id">{h.id}</span>
                                <span className="history-video">{h.video}</span>
                                <span className="history-score">{h.score}점 ({h.grade})</span>
                                <span className="history-elapsed">⏱️ {h.elapsed}s</span>
                                <span className={`history-status ${h.status}`}>{h.status === 'completed' ? '✅ 완료' : h.status}</span>
                                <span className="history-time">{new Date(h.created_at).toLocaleString('ko-KR')}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
