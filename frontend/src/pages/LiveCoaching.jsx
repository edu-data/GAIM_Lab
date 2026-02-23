import { useState, useEffect, useRef, useCallback } from 'react'
import { useCamera } from '../hooks/useCamera'
import { analyzeVideoClient, getStoredApiKey } from '../lib/clientAnalyzer'

// 8에이전트 파이프라인 정의
const AGENTS = [
    { id: 'extractor', icon: '📦', name: 'Extractor', desc: '프레임 추출' },
    { id: 'vision', icon: '👁️', name: 'Vision', desc: '비전 분석' },
    { id: 'content', icon: '🎨', name: 'Content', desc: '콘텐츠 분석' },
    { id: 'stt', icon: '🗣️', name: 'STT', desc: '음성 인식' },
    { id: 'vibe', icon: '🔊', name: 'Vibe', desc: '프로소디' },
    { id: 'pedagogy', icon: '📚', name: 'Pedagogy', desc: '교육학 평가' },
    { id: 'feedback', icon: '💡', name: 'Feedback', desc: '피드백 생성' },
    { id: 'master', icon: '🧠', name: 'Master', desc: '종합 보고서' },
]


// ── 코칭 팁 생성 ──
function generateTips(filler, wpm, silenceRatio, recentWpm) {
    const tips = []
    if (filler > 5) tips.push({ icon: '⚠️', text: `필러 단어가 ${filler}회 감지되었습니다. 의식적으로 줄여보세요.` })
    if (wpm > 180) tips.push({ icon: '⚡', text: '말이 빠릅니다. 핵심 내용에서 속도를 줄여보세요.' })
    else if (wpm > 0 && wpm < 80) tips.push({ icon: '🐌', text: '말이 느립니다. 에너지를 높여 학생 집중도를 유지하세요.' })
    if (silenceRatio > 0.4) tips.push({ icon: '🔇', text: '침묵이 길어지고 있습니다. 발문이나 활동을 시작하세요.' })
    else if (silenceRatio < 0.05 && wpm > 0) tips.push({ icon: '💡', text: '학생에게 생각할 시간을 주세요 (3초 대기).' })
    if (recentWpm && Math.abs(recentWpm - wpm) > 40) tips.push({ icon: '📊', text: '말 속도 변화가 큽니다. 일정한 페이스를 유지하세요.' })
    if (tips.length === 0) tips.push({ icon: '✅', text: '현재 좋은 페이스를 유지하고 있습니다!' })
    return tips
}

// ── WPM 등급 ──
function wpmGrade(wpm) {
    if (wpm === 0) return { label: '대기', color: '#888' }
    if (wpm < 80) return { label: '느림', color: '#ffc107' }
    if (wpm <= 150) return { label: '적정', color: '#00e676' }
    if (wpm <= 180) return { label: '빠름', color: '#ff9800' }
    return { label: '과속', color: '#ff5252' }
}

// 7차원 아이콘 매핑
const DIM_ICONS = {
    '수업 전문성': '📚', '교수학습 방법': '🎯', '판서 및 언어': '✏️',
    '수업 태도': '👨‍🏫', '학생 참여': '🙋', '시간 배분': '⏱️', '창의성': '💡'
}

function LiveCoaching() {
    const [phase, setPhase] = useState('idle') // idle | recording | analyzing | done
    const [elapsed, setElapsed] = useState(0)
    const [analyzeMsg, setAnalyzeMsg] = useState('')
    const [analyzeProgress, setAnalyzeProgress] = useState(0)
    const [agentStates, setAgentStates] = useState({}) // {agentId: 'idle'|'running'|'done'}
    const [transcript, setTranscript] = useState([]) // {text, time}
    const [metrics, setMetrics] = useState({ wpm: 0, fillerCount: 0, silenceRatio: 0, totalWords: 0 })
    const [tips, setTips] = useState([])
    const [wpmHistory, setWpmHistory] = useState([])
    const [sessionReport, setSessionReport] = useState(null)
    const [interimText, setInterimText] = useState('')
    // ── Camera (via useCamera hook) ──
    const [movementHistory, setMovementHistory] = useState([])
    const startTimeRef_cam = useRef(0) // shared with startTimeRef for movement history elapsed calc

    const onCameraFrame = useCallback(({ avgMovement }) => {
        const elapsed = (Date.now() - startTimeRef_cam.current) / 1000
        setMovementHistory(prev => {
            if (prev.length === 0 || elapsed - (prev[prev.length - 1]?.t || 0) >= 10)
                return [...prev, { t: Math.round(elapsed), mov: avgMovement }]
            return prev
        })
    }, [])

    const { videoRef, canvasRef, streamRef, cameraOn, error: cameraError, metrics: videoMetrics, startCamera, stopCamera, resetMetrics: resetCameraMetrics } = useCamera({
        onFrame: onCameraFrame
    })

    // Live frame capture for analysis (bypasses WebM seeking issues)
    const capturedFramesRef = useRef([])
    const frameIntervalRef = useRef(null)

    const recognitionRef = useRef(null)
    const timerRef = useRef(null)
    const startTimeRef = useRef(0)
    const lastSpeechRef = useRef(0)
    const silenceCountRef = useRef(0)
    const totalSegmentsRef = useRef(0)
    const allWordsRef = useRef([])
    const wpmWindowRef = useRef([]) // {time, words}
    const transcriptEndRef = useRef(null)

    // ── 메트릭 업데이트 ──
    const updateMetrics = useCallback((newText) => {
        const now = Date.now()
        const elapsedSec = (now - startTimeRef.current) / 1000
        totalSegmentsRef.current += 1

        if (!newText || !newText.trim()) {
            silenceCountRef.current += 1
        } else {
            const words = newText.trim().split(/\s+/).filter(Boolean)
            allWordsRef.current.push(...words)
            wpmWindowRef.current.push({ time: now, count: words.length })
            lastSpeechRef.current = now
        }

        // 최근 30초 윈도우 WPM
        const windowStart = now - 30000
        const recentEntries = wpmWindowRef.current.filter(e => e.time > windowStart)
        const recentWords = recentEntries.reduce((s, e) => s + e.count, 0)
        const recentDuration = Math.max((now - Math.max(windowStart, startTimeRef.current)) / 1000, 1)
        const recentWpm = (recentWords / recentDuration) * 60

        const totalWords = allWordsRef.current.length
        const wpm = elapsedSec > 0 ? (totalWords / elapsedSec) * 60 : 0
        const silenceRatio = totalSegmentsRef.current > 0
            ? silenceCountRef.current / totalSegmentsRef.current
            : 0

        // 필러 카운트
        const allText = allWordsRef.current.join(' ')
        const fillerCount = (allText.match(/(?:^|\s)(음|어|그|저|이제|뭐|아|에|그러니까|있잖아)(?=\s|$)/gi) || []).length
            + (allText.match(/\b(um|uh|like|you know|so|well|basically|actually)\b/gi) || []).length

        const m = {
            wpm: Math.round(wpm),
            recentWpm: Math.round(recentWpm),
            fillerCount,
            silenceRatio: Math.round(silenceRatio * 1000) / 1000,
            totalWords,
            elapsed: Math.round(elapsedSec),
        }
        setMetrics(m)
        setTips(generateTips(fillerCount, wpm, silenceRatio, recentWpm))

        // WPM 히스토리 (5초 간격으로 기록)
        setWpmHistory(prev => {
            if (prev.length === 0 || elapsedSec - (prev[prev.length - 1]?.t || 0) >= 5) {
                return [...prev, { t: Math.round(elapsedSec), wpm: Math.round(wpm), recentWpm: Math.round(recentWpm) }]
            }
            return prev
        })
    }, [])

    // ── 음성 인식 시작 ──
    const startRecognition = useCallback(() => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        if (!SR) {
            alert('이 브라우저는 음성인식을 지원하지 않습니다. Chrome을 사용하세요.')
            return
        }

        const recog = new SR()
        recog.lang = 'ko-KR'
        recog.continuous = true
        recog.interimResults = true

        recog.onresult = (e) => {
            let finalText = ''
            let interim = ''
            for (let i = e.resultIndex; i < e.results.length; i++) {
                const t = e.results[i][0].transcript
                if (e.results[i].isFinal) {
                    finalText += t
                } else {
                    interim += t
                }
            }
            setInterimText(interim)
            if (finalText) {
                const entry = { text: finalText.trim(), time: Math.round((Date.now() - startTimeRef.current) / 1000) }
                setTranscript(prev => [...prev, entry])
                updateMetrics(finalText)
            }
        }

        recog.onerror = (e) => {
            if (e.error === 'no-speech') {
                updateMetrics('')
            } else if (e.error !== 'aborted') {
                console.warn('Speech error:', e.error)
            }
        }

        recog.onend = () => {
            // 자동 재시작 (recording 중일 때만)
            if (recognitionRef.current) {
                try { recognitionRef.current.start() } catch (e) { /* already started */ }
            }
        }

        recog.start()
        recognitionRef.current = recog
    }, [updateMetrics])

    // ── 카메라 시작/종료: useCamera 훅으로 대체됨 ──
    // startCamera, stopCamera, videoRef, canvasRef, cameraOn, videoMetrics
    // 모두 useCamera 훅에서 제공 (L60~74 참조)

    // ── 라이브 프레임 캡처 시작 (카메라 캔버스에서 주기적 캡처) ──
    const startFrameCapture = useCallback(() => {
        capturedFramesRef.current = []
        // 카메라 캔버스에서 5초마다 프레임 캡처 (최대 8장)
        frameIntervalRef.current = setInterval(() => {
            const canvas = canvasRef.current
            const video = videoRef.current
            if (!canvas || !video || !video.videoWidth) return
            if (capturedFramesRef.current.length >= 8) return // 최대 8장

            // 캔버스에 현재 비디오 프레임 그리기
            canvas.width = Math.min(video.videoWidth, 640)
            canvas.height = Math.round(canvas.width * (video.videoHeight / video.videoWidth))
            const ctx = canvas.getContext('2d')
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7)
            const base64 = dataUrl.split(',')[1]
            capturedFramesRef.current.push(base64)
        }, 5000) // 5초 간격
    }, [canvasRef, videoRef])

    // ── 세션 시작 ──
    const startSession = () => {
        // 초기화
        setPhase('recording')
        setTranscript([])
        setMetrics({ wpm: 0, fillerCount: 0, silenceRatio: 0, totalWords: 0 })
        setTips([])
        setWpmHistory([])
        setSessionReport(null)
        setInterimText('')
        setElapsed(0)
        setAnalyzeProgress(0)
        setAgentStates({})
        resetCameraMetrics()
        setMovementHistory([])
        allWordsRef.current = []
        wpmWindowRef.current = []
        silenceCountRef.current = 0
        totalSegmentsRef.current = 0
        capturedFramesRef.current = []

        startTimeRef.current = Date.now()
        startTimeRef_cam.current = Date.now() // sync for movement history elapsed
        lastSpeechRef.current = Date.now()

        // 타이머
        timerRef.current = setInterval(() => {
            const sec = Math.round((Date.now() - startTimeRef.current) / 1000)
            setElapsed(sec)
            if (Date.now() - lastSpeechRef.current > 3000) updateMetrics('')
        }, 1000)

        startRecognition()
        // 카메라는 useEffect에서 phase='recording' 후 DOM 렌더 완료 시 시작
    }

    // ── 에이전트 상태 업데이트 헬퍼 ──
    const setAgentRunning = (id) => setAgentStates(prev => ({ ...prev, [id]: 'running' }))
    const setAgentDone = (id) => setAgentStates(prev => ({ ...prev, [id]: 'done' }))

    // ── 세션 종료 ──
    const stopSession = async () => {
        if (recognitionRef.current) { const r = recognitionRef.current; recognitionRef.current = null; r.stop() }
        if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
        if (frameIntervalRef.current) { clearInterval(frameIntervalRef.current); frameIntervalRef.current = null }

        // 마지막 프레임 캡처 (세션 종료 직전)
        const canvas = canvasRef.current
        const video = videoRef.current
        if (canvas && video && video.videoWidth && capturedFramesRef.current.length < 8) {
            canvas.width = Math.min(video.videoWidth, 640)
            canvas.height = Math.round(canvas.width * (video.videoHeight / video.videoWidth))
            const ctx = canvas.getContext('2d')
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7)
            capturedFramesRef.current.push(dataUrl.split(',')[1])
        }

        const capturedFrames = [...capturedFramesRef.current]
        stopCamera()

        const durationSec = (Date.now() - startTimeRef.current) / 1000
        const totalWords = allWordsRef.current.length
        const avgWpm = durationSec > 0 ? (totalWords / durationSec) * 60 : 0
        const silenceRatio = totalSegmentsRef.current > 0
            ? silenceCountRef.current / totalSegmentsRef.current : 0
        const allText = allWordsRef.current.join(' ')
        const uniqueWords = new Set(allWordsRef.current.map(w => w.toLowerCase())).size

        const baseReport = {
            durationSec: Math.round(durationSec),
            totalWords,
            avgWpm: Math.round(avgWpm),
            silenceRatio: Math.round(silenceRatio * 1000) / 1000,
            uniqueWords,
        }

        // 8에이전트 Gemini 영상 분석 (사전 캡처된 프레임 사용)
        const apiKey = getStoredApiKey()
        if (apiKey && capturedFrames.length > 0) {
            setPhase('analyzing')
            setAnalyzeProgress(0)
            setAgentStates(Object.fromEntries(AGENTS.map(a => [a.id, 'idle'])))
            setAnalyzeMsg('📦 영상 프레임 추출 중...')

            try {
                const videoFile = null // 프레임이 이미 캡처됨

                // 전사 텍스트 데이터
                const transcriptData = totalWords > 5 ? {
                    text: allText,
                    durationSec,
                    avgWpm,
                    fillerCount: metrics.fillerCount,
                    silenceRatio,
                } : null

                const result = await analyzeVideoClient(videoFile, apiKey, (progress, msg) => {
                    setAnalyzeProgress(progress)
                    setAnalyzeMsg(msg)

                    // 에이전트 상태 매핑 (진행률 기반)
                    if (progress >= 5) { setAgentRunning('extractor') }
                    if (progress >= 15) { setAgentDone('extractor'); setAgentRunning('vision'); setAgentRunning('content'); setAgentRunning('stt'); setAgentRunning('vibe') }
                    if (progress >= 50) { setAgentDone('vision'); setAgentDone('content'); setAgentDone('stt'); setAgentDone('vibe'); setAgentRunning('pedagogy') }
                    if (progress >= 70) { setAgentDone('pedagogy'); setAgentRunning('feedback') }
                    if (progress >= 85) { setAgentDone('feedback'); setAgentRunning('master') }
                    if (progress >= 95) { setAgentDone('master') }
                }, transcriptData, capturedFrames)

                setSessionReport({
                    ...baseReport,
                    dimensions: result.dimensions,
                    overall: result.total_score,
                    grade: result.grade,
                    strengths: result.strengths,
                    improvements: result.improvements,
                    overall_feedback: result.overall_feedback,
                    isGemini: true,
                })
                setPhase('done')
                return
            } catch (e) {
                console.error('[LiveCoaching] 8-agent analysis failed:', e)
                setAnalyzeMsg('⚠️ 영상 분석 실패, 기본 평가로 전환...')
                await new Promise(r => setTimeout(r, 1500))
            }
        }

        // Fallback: 기본 메트릭 기반 간이 리포트
        setSessionReport({
            ...baseReport,
            dimensions: null,
            overall: null,
            grade: null,
            isGemini: false,
        })
        setPhase('done')
    }

    // ── cleanup ──
    useEffect(() => {
        return () => {
            if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null }
            if (timerRef.current) clearInterval(timerRef.current)
            stopCamera()
        }
    }, [stopCamera])

    // ── 카메라 자동 시작: phase가 'recording'이 되면 DOM 렌더 후 카메라 시작 ──
    useEffect(() => {
        if (phase === 'recording') {
            // requestAnimationFrame으로 DOM 렌더 완료 보장
            const raf = requestAnimationFrame(() => { startCamera() })
            return () => cancelAnimationFrame(raf)
        }
    }, [phase, startCamera])

    // ── 카메라 켜지면 프레임 캡처 시작 ──
    useEffect(() => {
        if (cameraOn && phase === 'recording') {
            startFrameCapture()
        }
        return () => {
            if (frameIntervalRef.current) { clearInterval(frameIntervalRef.current); frameIntervalRef.current = null }
        }
    }, [cameraOn, phase, startFrameCapture])

    // auto-scroll transcript
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [transcript])

    const fmtTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
    const wg = wpmGrade(metrics.wpm)

    return (
        <div className="lc-page">
            {/* Hidden canvas for frame analysis */}
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {/* ── Header ── */}
            <div className="lc-header">
                <h2>🔴 실시간 코칭</h2>
                <p>마이크 + 카메라 기반 실시간 수업 분석 — 음성·제스처 즉시 피드백</p>
            </div>

            {/* ── Control ── */}
            <div className="lc-controls">
                {phase === 'idle' && (
                    <button className="lc-btn lc-btn-start" onClick={startSession}>
                        <span className="lc-btn-icon">🎙️</span> 코칭 시작
                    </button>
                )}
                {phase === 'recording' && (
                    <>
                        <div className="lc-live-badge">
                            <span className="lc-dot"></span> LIVE
                        </div>
                        <div className="lc-timer">{fmtTime(elapsed)}</div>
                        <button className="lc-btn lc-btn-stop" onClick={stopSession}>
                            ⏹️ 종료
                        </button>
                    </>
                )}
                {(phase === 'done' || phase === 'analyzing') && (
                    <button className="lc-btn lc-btn-start" onClick={startSession} disabled={phase === 'analyzing'}>
                        <span className="lc-btn-icon">🔄</span> 새 세션
                    </button>
                )}
            </div>

            {/* ── Recording Dashboard ── */}
            {phase === 'recording' && (
                <div className="lc-dashboard">
                    {/* Camera + Metrics row */}
                    <div className="lc-cam-row">
                        {/* Camera Preview */}
                        <div className="lc-cam-box">
                            <video ref={videoRef} autoPlay muted playsInline className="lc-cam-video" />
                            {!cameraOn && (
                                <div className="lc-cam-off">
                                    {cameraError
                                        ? `❌ 카메라 오류: ${cameraError}`
                                        : '📷 카메라 연결 중...'}
                                </div>
                            )}
                            {cameraOn && (
                                <div className="lc-cam-overlay">
                                    <span className="lc-cam-dot"></span>
                                    <span>🎥 움직임: {videoMetrics.movement}</span>
                                </div>
                            )}
                        </div>

                        {/* Metric Cards */}
                        <div className="lc-metric-grid">
                            <div className="lc-metric-card">
                                <div className="lc-metric-val" style={{ color: wg.color }}>{metrics.wpm}</div>
                                <div className="lc-metric-sub">{wg.label}</div>
                                <div className="lc-metric-lbl">WPM (말 속도)</div>
                            </div>
                            <div className="lc-metric-card">
                                <div className="lc-metric-val" style={{
                                    color: metrics.fillerCount > 5 ? '#ff5252' : metrics.fillerCount > 2 ? '#ffc107' : '#00e676'
                                }}>{metrics.fillerCount}</div>
                                <div className="lc-metric-sub">{metrics.fillerCount > 5 ? '많음' : metrics.fillerCount > 2 ? '보통' : '좋음'}</div>
                                <div className="lc-metric-lbl">필러 횟수</div>
                            </div>
                            <div className="lc-metric-card">
                                <div className="lc-metric-val">{(metrics.silenceRatio * 100).toFixed(0)}%</div>
                                <div className="lc-metric-sub">{metrics.silenceRatio > 0.4 ? '과다' : metrics.silenceRatio > 0.15 ? '양호' : '적극'}</div>
                                <div className="lc-metric-lbl">침묵 비율</div>
                            </div>
                            <div className="lc-metric-card">
                                <div className="lc-metric-val">{metrics.totalWords}</div>
                                <div className="lc-metric-sub">단어</div>
                                <div className="lc-metric-lbl">발화량</div>
                            </div>
                            {cameraOn && (
                                <div className="lc-metric-card">
                                    <div className="lc-metric-val" style={{ color: '#e040fb' }}>{videoMetrics.gestureCount}</div>
                                    <div className="lc-metric-sub">회</div>
                                    <div className="lc-metric-lbl">움직임 감지</div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tips */}
                    <div className="lc-tips-box">
                        {tips.map((tip, i) => (
                            <div key={i} className="lc-tip-item">
                                <span className="lc-tip-icon">{tip.icon}</span>
                                <span>{tip.text}</span>
                            </div>
                        ))}
                    </div>

                    {/* WPM Timeline mini chart */}
                    {wpmHistory.length > 1 && (
                        <div className="lc-chart-box">
                            <div className="lc-chart-title">📈 말 속도 추이</div>
                            <div className="lc-chart">
                                {(() => {
                                    const maxW = Math.max(...wpmHistory.map(h => h.wpm), 200)
                                    return wpmHistory.map((h, i) => (
                                        <div key={i} className="lc-bar-col" title={`${fmtTime(h.t)} — ${h.wpm} WPM`}>
                                            <div className="lc-bar" style={{
                                                height: `${(h.wpm / maxW) * 100}%`,
                                                background: h.wpm > 180 ? '#ff5252' : h.wpm < 80 ? '#ffc107' : 'linear-gradient(180deg, #00d2ff, #6c63ff)'
                                            }}></div>
                                            {i % 3 === 0 && <div className="lc-bar-label">{fmtTime(h.t)}</div>}
                                        </div>
                                    ))
                                })()}
                            </div>
                        </div>
                    )}

                    {/* Live Transcript */}
                    <div className="lc-transcript-box">
                        <div className="lc-transcript-title">📝 실시간 전사</div>
                        <div className="lc-transcript-scroll">
                            {transcript.map((t, i) => (
                                <span key={i} className="lc-transcript-chunk">
                                    <span className="lc-transcript-time">[{fmtTime(t.time)}]</span> {t.text}{' '}
                                </span>
                            ))}
                            {interimText && <span className="lc-interim">{interimText}</span>}
                            <span ref={transcriptEndRef}></span>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Analyzing Phase — 8에이전트 파이프라인 ── */}
            {phase === 'analyzing' && (
                <div className="lc-analyzing">
                    <h3>🤖 8에이전트 수업 분석 중</h3>
                    <p>{analyzeMsg}</p>

                    {/* 진행률 바 */}
                    <div className="lc-analyze-progress">
                        <div className="lc-analyze-bar" style={{ width: `${analyzeProgress}%` }}></div>
                    </div>
                    <div className="lc-analyze-pct">{Math.round(analyzeProgress)}%</div>

                    {/* 에이전트 파이프라인 */}
                    <div className="lc-agent-pipeline">
                        {AGENTS.map((agent) => {
                            const state = agentStates[agent.id] || 'idle'
                            return (
                                <div key={agent.id} className={`lc-agent-card lc-agent-${state}`}>
                                    <div className="lc-agent-icon">{agent.icon}</div>
                                    <div className="lc-agent-name">{agent.name}</div>
                                    <div className="lc-agent-desc">{agent.desc}</div>
                                    <div className="lc-agent-status">
                                        {state === 'idle' && '⏳'}
                                        {state === 'running' && <span className="lc-agent-spinner"></span>}
                                        {state === 'done' && '✅'}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* ── Session Report ── */}
            {phase === 'done' && sessionReport && (
                <div className="lc-report">
                    <div className="lc-report-header">
                        <h3>📊 세션 리포트 {sessionReport.isGemini && <span className="lc-gemini-tag">✨ 8에이전트 7차원</span>}</h3>
                        {sessionReport.grade && (
                            <div className="lc-grade-badge" data-grade={sessionReport.grade}>
                                {sessionReport.grade}
                            </div>
                        )}
                    </div>

                    {/* Summary stats */}
                    <div className="lc-summary-grid">
                        <div className="lc-sum-item">
                            <div className="lc-sum-val">{fmtTime(sessionReport.durationSec)}</div>
                            <div className="lc-sum-lbl">총 시간</div>
                        </div>
                        <div className="lc-sum-item">
                            <div className="lc-sum-val">{sessionReport.totalWords}</div>
                            <div className="lc-sum-lbl">총 단어</div>
                        </div>
                        <div className="lc-sum-item">
                            <div className="lc-sum-val">{sessionReport.avgWpm}</div>
                            <div className="lc-sum-lbl">평균 WPM</div>
                        </div>
                        <div className="lc-sum-item">
                            <div className="lc-sum-val">{(sessionReport.silenceRatio * 100).toFixed(0)}%</div>
                            <div className="lc-sum-lbl">침묵 비율</div>
                        </div>
                        <div className="lc-sum-item">
                            <div className="lc-sum-val">{sessionReport.uniqueWords}</div>
                            <div className="lc-sum-lbl">고유 어휘</div>
                        </div>
                    </div>

                    {/* 7차원 교원임용 평가 (Gemini) */}
                    {sessionReport.dimensions && (
                        <div className="lc-dims-section">
                            <h4>📐 7차원 수업 평가</h4>
                            <div className="lc-dims-list">
                                {sessionReport.dimensions.map((d, i) => (
                                    <div key={i} className="lc-dim-row">
                                        <div className="lc-dim-name">{DIM_ICONS[d.name] || '📊'} {d.name}</div>
                                        <div className="lc-dim-bar-track">
                                            <div className="lc-dim-bar-fill" style={{
                                                width: `${d.percentage}%`,
                                                background: d.percentage >= 80 ? 'linear-gradient(90deg, #00e676, #00d2ff)'
                                                    : d.percentage >= 60 ? 'linear-gradient(90deg, #ffc107, #ff9800)'
                                                        : 'linear-gradient(90deg, #ff5252, #ff8a80)'
                                            }}></div>
                                        </div>
                                        <div className="lc-dim-score">{d.score}/{d.max_score}</div>
                                    </div>
                                ))}
                                {sessionReport.dimensions.map((d, i) => (
                                    d.feedback && (
                                        <div key={`fb-${i}`} className="lc-dim-feedback">
                                            <strong>{DIM_ICONS[d.name] || '📊'} {d.name}:</strong> {d.feedback}
                                        </div>
                                    )
                                ))}
                            </div>
                        </div>
                    )}

                    {/* API Key 없을 때 안내 */}
                    {!sessionReport.isGemini && (
                        <div className="lc-no-gemini">
                            <p>💡 <strong>Google API Key</strong>를 설정하면 세션 종료 시 8에이전트가 녹화된 영상을 분석하여 7차원 수업 평가를 수행합니다.</p>
                            <p style={{ fontSize: '0.85rem', opacity: 0.7 }}>설정 → 🔑 API Key 설정 (수업 분석 페이지에서 가능)</p>
                        </div>
                    )}

                    {/* 강점 / 개선점 */}
                    {sessionReport.strengths && sessionReport.strengths.length > 0 && (
                        <div className="lc-feedback-section">
                            <div className="lc-feedback-box lc-strengths">
                                <h4>✅ 강점</h4>
                                <ul>{sessionReport.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
                            </div>
                            {sessionReport.improvements && sessionReport.improvements.length > 0 && (
                                <div className="lc-feedback-box lc-improvements">
                                    <h4>🔧 개선점</h4>
                                    <ul>{sessionReport.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 종합 피드백 */}
                    {sessionReport.overall_feedback && (
                        <div className="lc-overall-feedback">
                            <h4>💬 종합 피드백</h4>
                            <p>{sessionReport.overall_feedback}</p>
                        </div>
                    )}

                    {/* WPM chart */}
                    {wpmHistory.length > 1 && (
                        <div className="lc-chart-box lc-chart-report">
                            <div className="lc-chart-title">📈 말 속도 변화 추이</div>
                            <div className="lc-chart">
                                {(() => {
                                    const maxW = Math.max(...wpmHistory.map(h => h.wpm), 200)
                                    return wpmHistory.map((h, i) => (
                                        <div key={i} className="lc-bar-col" title={`${fmtTime(h.t)} — ${h.wpm} WPM`}>
                                            <div className="lc-bar" style={{
                                                height: `${(h.wpm / maxW) * 100}%`,
                                                background: h.wpm > 180 ? '#ff5252' : h.wpm < 80 ? '#ffc107' : 'linear-gradient(180deg, #00d2ff, #6c63ff)'
                                            }}></div>
                                            <div className="lc-bar-label">{fmtTime(h.t)}</div>
                                        </div>
                                    ))
                                })()}
                            </div>
                        </div>
                    )}

                    {/* Full transcript */}
                    <div className="lc-transcript-box">
                        <div className="lc-transcript-title">📝 전체 전사 기록</div>
                        <div className="lc-transcript-scroll">
                            {transcript.map((t, i) => (
                                <span key={i} className="lc-transcript-chunk">
                                    <span className="lc-transcript-time">[{fmtTime(t.time)}]</span> {t.text}{' '}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Overall Score */}
                    {sessionReport.overall != null && (
                        <div className="lc-overall">
                            <div className="lc-overall-score">{sessionReport.overall}<span className="lc-overall-unit">점</span></div>
                            <div className="lc-overall-label">7차원 종합 점수</div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Idle Info ── */}
            {phase === 'idle' && (
                <div className="lc-info">
                    <div className="lc-info-card">
                        <h3>🎯 실시간 코칭은 어떻게 작동하나요?</h3>
                        <div className="lc-info-steps">
                            <div className="lc-info-step">
                                <div className="lc-step-num">1</div>
                                <div>
                                    <strong>코칭 시작</strong>
                                    <p>"코칭 시작" 버튼을 클릭하고 마이크 접근을 허용합니다.</p>
                                </div>
                            </div>
                            <div className="lc-info-step">
                                <div className="lc-step-num">2</div>
                                <div>
                                    <strong>수업 진행</strong>
                                    <p>평소처럼 수업을 진행하면 AI가 실시간으로 음성을 분석합니다.</p>
                                </div>
                            </div>
                            <div className="lc-info-step">
                                <div className="lc-step-num">3</div>
                                <div>
                                    <strong>즉시 피드백</strong>
                                    <p>말 속도, 필러 사용, 침묵 비율에 대한 피드백을 즉시 확인합니다.</p>
                                </div>
                            </div>
                            <div className="lc-info-step">
                                <div className="lc-step-num">4</div>
                                <div>
                                    <strong>세션 리포트</strong>
                                    <p>종료 시 7차원 평가와 종합 리포트를 확인할 수 있습니다.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="lc-info-card lc-info-req">
                        <h4>⚙️ 요구 사항</h4>
                        <ul>
                            <li>Chrome 브라우저 권장 (Web Speech API 지원)</li>
                            <li>마이크 + 카메라 접근 권한 필요</li>
                            <li>인터넷 연결 필요 (음성인식 서버 사용)</li>
                        </ul>
                    </div>
                </div>
            )}

            <style>{`
.lc-page { max-width: 880px; margin: 0 auto; padding: 0 1rem; }

/* Header */
.lc-header { text-align: center; margin-bottom: 2rem; }
.lc-header h2 {
    font-size: 1.8rem; font-weight: 800; margin-bottom: 0.3rem;
    background: linear-gradient(135deg, #ff5252, #ff8a80, #ff5252);
    background-size: 200% 200%; animation: gradShift 3s ease infinite;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.lc-header p { color: #999; font-size: 0.9rem; }
@keyframes gradShift { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }

/* Controls */
.lc-controls {
    display: flex; align-items: center; justify-content: center; gap: 1.2rem;
    margin-bottom: 2rem; min-height: 56px;
}
.lc-btn {
    padding: 0.85rem 2.2rem; border: none; border-radius: 14px;
    font-size: 1.05rem; cursor: pointer; font-weight: 700;
    transition: all 0.25s ease; display: flex; align-items: center; gap: 0.5rem;
}
.lc-btn-start {
    background: linear-gradient(135deg, #ff5252, #ff8a80); color: #fff;
    box-shadow: 0 4px 20px rgba(255,82,82,0.35);
}
.lc-btn-start:hover { transform: translateY(-2px); box-shadow: 0 6px 28px rgba(255,82,82,0.5); }
.lc-btn-stop {
    background: rgba(255,82,82,0.12); color: #ff5252; border: 2px solid rgba(255,82,82,0.4);
}
.lc-btn-stop:hover { background: rgba(255,82,82,0.2); }
.lc-btn-icon { font-size: 1.2rem; }
.lc-live-badge {
    display: flex; align-items: center; gap: 0.4rem;
    color: #ff5252; font-weight: 800; font-size: 1rem; letter-spacing: 0.05em;
}
.lc-dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    background: #ff5252; animation: dotPulse 1.2s ease infinite;
}
@keyframes dotPulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,82,82,0.5)} 50%{box-shadow:0 0 0 8px rgba(255,82,82,0)} }
.lc-timer { font-size: 1.6rem; font-weight: 700; color: #fff; font-variant-numeric: tabular-nums; }

/* Dashboard */
.lc-dashboard { display: flex; flex-direction: column; gap: 1rem; }

/* Camera + Metrics Row */
.lc-cam-row { display: flex; gap: 1rem; align-items: stretch; }
.lc-cam-box {
    width: 280px; min-height: 210px; flex-shrink: 0; border-radius: 14px; overflow: hidden;
    background: rgba(0,0,0,0.4); border: 1px solid rgba(108,99,255,0.2); position: relative;
}
.lc-cam-video { width: 100%; height: 100%; object-fit: cover; display: block; border-radius: 14px; }
.lc-cam-off {
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    color: #888; font-size: 0.9rem; background: rgba(0,0,0,0.6);
}
.lc-cam-overlay {
    position: absolute; bottom: 0; left: 0; right: 0; padding: 0.4rem 0.6rem;
    background: linear-gradient(transparent, rgba(0,0,0,0.7));
    display: flex; align-items: center; gap: 0.4rem; font-size: 0.72rem; color: #0f0;
}
.lc-cam-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #0f0;
    animation: dotPulse 1.2s ease infinite;
}

/* Metric Cards */
.lc-metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px,1fr)); gap: 0.6rem; flex: 1; }
.lc-metric-card {
    text-align: center; padding: 1rem 0.4rem; border-radius: 14px;
    background: rgba(26,26,46,0.85); border: 1px solid rgba(108,99,255,0.12);
    backdrop-filter: blur(8px);
}
.lc-metric-val { font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
.lc-metric-sub { font-size: 0.7rem; font-weight: 600; margin: 0.15rem 0 0.3rem; color: #aaa; text-transform: uppercase; letter-spacing: 0.05em; }
.lc-metric-lbl { font-size: 0.72rem; color: #777; }

/* Tips */
.lc-tips-box {
    display: flex; flex-direction: column; gap: 0.4rem;
    background: rgba(26,26,46,0.7); border-radius: 12px; padding: 1rem;
    border: 1px solid rgba(108,99,255,0.1);
}
.lc-tip-item {
    display: flex; align-items: flex-start; gap: 0.5rem;
    font-size: 0.85rem; color: #ccc; padding: 0.45rem 0.6rem;
    border-radius: 8px; background: rgba(108,99,255,0.06);
    border-left: 3px solid #6c63ff;
}
.lc-tip-icon { font-size: 1rem; flex-shrink: 0; }

/* Chart */
.lc-chart-box {
    background: rgba(26,26,46,0.7); border-radius: 12px; padding: 1rem;
    border: 1px solid rgba(108,99,255,0.1);
}
.lc-chart-title { font-size: 0.85rem; color: #00d2ff; font-weight: 600; margin-bottom: 0.6rem; }
.lc-chart { display: flex; align-items: flex-end; gap: 3px; height: 80px; }
.lc-chart-report .lc-chart { height: 100px; }
.lc-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.lc-bar { width: 100%; min-height: 2px; border-radius: 3px 3px 0 0; transition: height 0.3s ease; }
.lc-bar-label { font-size: 0.55rem; color: #666; margin-top: 3px; }

/* Transcript */
.lc-transcript-box {
    background: rgba(26,26,46,0.7); border-radius: 12px; padding: 1rem;
    border: 1px solid rgba(108,99,255,0.1);
}
.lc-transcript-title { font-size: 0.85rem; color: #00d2ff; font-weight: 600; margin-bottom: 0.5rem; }
.lc-transcript-scroll {
    max-height: 180px; overflow-y: auto; font-size: 0.82rem; color: #bbb;
    line-height: 1.8; padding: 0.5rem; background: rgba(0,0,0,0.15); border-radius: 8px;
}
.lc-transcript-chunk { }
.lc-transcript-time { color: #6c63ff; font-size: 0.7rem; font-weight: 600; }
.lc-interim { color: #666; font-style: italic; }

/* ═══ SESSION REPORT ═══ */
.lc-report { display: flex; flex-direction: column; gap: 1.2rem; }
.lc-report-header {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 0.8rem; border-bottom: 1px solid rgba(108,99,255,0.15);
}
.lc-report-header h3 {
    font-size: 1.3rem; font-weight: 700;
    background: linear-gradient(90deg, #00d2ff, #6c63ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.lc-grade-badge {
    font-size: 1.6rem; font-weight: 900; padding: 0.3rem 1.2rem; border-radius: 12px;
    background: linear-gradient(135deg, #00d2ff, #6c63ff); color: #fff;
    box-shadow: 0 4px 16px rgba(0,210,255,0.3);
}
.lc-grade-badge[data-grade="A+"],.lc-grade-badge[data-grade="A"] { background: linear-gradient(135deg, #00e676, #00b0ff); }
.lc-grade-badge[data-grade="B+"],.lc-grade-badge[data-grade="B"] { background: linear-gradient(135deg, #ffc107, #ff9800); }
.lc-grade-badge[data-grade="C"],.lc-grade-badge[data-grade="D"] { background: linear-gradient(135deg, #ff5252, #e040fb); }

/* Summary Grid */
.lc-summary-grid {
    display: grid; grid-template-columns: repeat(3,1fr); gap: 0.75rem;
}
.lc-sum-item {
    text-align: center; padding: 1rem; border-radius: 12px;
    background: rgba(26,26,46,0.8); border: 1px solid rgba(108,99,255,0.1);
}
.lc-sum-val { font-size: 1.6rem; font-weight: 800; color: #00d2ff; }
.lc-sum-lbl { font-size: 0.72rem; color: #888; margin-top: 0.2rem; }

/* Dimensions */
.lc-dims-section {
    background: rgba(26,26,46,0.7); border-radius: 14px; padding: 1.2rem;
    border: 1px solid rgba(108,99,255,0.1);
}
.lc-dims-section h4 { color: #00d2ff; margin-bottom: 0.8rem; font-size: 1rem; }
.lc-dims-list { display: flex; flex-direction: column; gap: 0.5rem; }
.lc-dim-row { display: flex; align-items: center; gap: 0.6rem; }
.lc-dim-name { width: 110px; font-size: 0.8rem; color: #ccc; flex-shrink: 0; }
.lc-dim-bar-track {
    flex: 1; height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;
}
.lc-dim-bar-fill { height: 100%; border-radius: 5px; transition: width 0.6s ease; }
.lc-dim-score { width: 32px; text-align: right; font-size: 0.85rem; font-weight: 700; color: #fff; }

/* Overall */
.lc-overall {
    text-align: center; padding: 1.5rem; border-radius: 16px;
    background: linear-gradient(135deg, rgba(0,210,255,0.1), rgba(108,99,255,0.1));
    border: 1px solid rgba(0,210,255,0.2);
}
.lc-overall-score {
    font-size: 3.2rem; font-weight: 900;
    background: linear-gradient(135deg, #00d2ff, #6c63ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.lc-overall-unit { font-size: 1rem; }
.lc-overall-label { font-size: 0.85rem; color: #999; margin-top: 0.2rem; }

/* ═══ ANALYZING PHASE ═══ */
.lc-analyzing {
    text-align: center; padding: 3rem 1rem;
    background: rgba(26,26,46,0.8); border-radius: 16px;
    border: 1px solid rgba(108,99,255,0.2);
}
.lc-analyzing h3 {
    font-size: 1.2rem; margin: 1.2rem 0 0.5rem;
    background: linear-gradient(90deg, #00d2ff, #6c63ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.lc-analyzing p { color: #999; font-size: 0.85rem; }
.lc-analyzing-spinner {
    width: 48px; height: 48px; margin: 0 auto;
    border: 4px solid rgba(108,99,255,0.2); border-top-color: #6c63ff;
    border-radius: 50%; animation: lcSpin 0.8s linear infinite;
}
@keyframes lcSpin { to { transform: rotate(360deg); } }

/* ═══ 8-AGENT PROGRESS BAR ═══ */
.lc-analyze-progress {
    width: 100%; height: 6px; background: rgba(108,99,255,0.15);
    border-radius: 3px; margin: 1rem 0 0.5rem; overflow: hidden;
}
.lc-analyze-bar {
    height: 100%; border-radius: 3px; transition: width 0.4s ease;
    background: linear-gradient(90deg, #6c63ff, #00d2ff, #00e676);
    background-size: 200% 200%; animation: shimmer 2s linear infinite;
}
@keyframes shimmer { 0%{background-position:0% 50%} 100%{background-position:200% 50%} }
.lc-analyze-pct { color: #6c63ff; font-weight: 700; font-size: 0.9rem; }

/* ═══ 8-AGENT PIPELINE CARDS ═══ */
.lc-agent-pipeline {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem;
    margin-top: 1.2rem;
}
.lc-agent-card {
    background: rgba(26,26,46,0.6); border-radius: 10px;
    padding: 0.7rem 0.5rem; text-align: center;
    border: 1px solid rgba(108,99,255,0.1); transition: all 0.3s ease;
    position: relative;
}
.lc-agent-idle { opacity: 0.5; }
.lc-agent-running {
    opacity: 1; border-color: rgba(108,99,255,0.5);
    box-shadow: 0 0 12px rgba(108,99,255,0.2);
    animation: agentPulse 1.5s ease-in-out infinite;
}
.lc-agent-done {
    opacity: 1; border-color: rgba(0,230,118,0.4);
    background: rgba(0,230,118,0.06);
}
@keyframes agentPulse {
    0%,100% { box-shadow: 0 0 8px rgba(108,99,255,0.15); }
    50% { box-shadow: 0 0 18px rgba(108,99,255,0.35); }
}
.lc-agent-icon { font-size: 1.5rem; margin-bottom: 0.3rem; }
.lc-agent-name { font-size: 0.75rem; font-weight: 700; color: #e0e0e0; }
.lc-agent-desc { font-size: 0.65rem; color: #888; margin-top: 0.15rem; }
.lc-agent-status { margin-top: 0.4rem; font-size: 0.85rem; min-height: 1.2rem; }
.lc-agent-spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid rgba(108,99,255,0.2); border-top-color: #6c63ff;
    border-radius: 50%; animation: lcSpin 0.6s linear infinite;
}

/* ═══ GEMINI TAG ═══ */
.lc-gemini-tag {
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    background: linear-gradient(135deg, #6c63ff, #00d2ff); color: #fff;
    padding: 0.15rem 0.5rem; border-radius: 8px; margin-left: 0.5rem;
    vertical-align: middle;
}

/* ═══ DIMENSION FEEDBACK ═══ */
.lc-dim-feedback {
    background: rgba(108,99,255,0.06); border-radius: 8px;
    padding: 0.6rem 0.8rem; margin-top: 0.5rem;
    font-size: 0.82rem; color: #bbb; line-height: 1.5;
    border-left: 3px solid rgba(108,99,255,0.3);
}
.lc-dim-feedback strong { color: #ddd; }

/* ═══ STRENGTHS / IMPROVEMENTS ═══ */
.lc-feedback-section {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;
}
.lc-feedback-box {
    background: rgba(26,26,46,0.8); border-radius: 12px;
    padding: 1rem; border: 1px solid rgba(108,99,255,0.1);
}
.lc-feedback-box h4 { font-size: 0.95rem; margin-bottom: 0.6rem; }
.lc-feedback-box ul { padding-left: 1rem; margin: 0; }
.lc-feedback-box li { color: #bbb; font-size: 0.85rem; margin-bottom: 0.3rem; line-height: 1.5; }
.lc-strengths { border-left: 3px solid #00e676; }
.lc-improvements { border-left: 3px solid #ffc107; }

/* ═══ OVERALL FEEDBACK ═══ */
.lc-overall-feedback {
    background: rgba(26,26,46,0.8); border-radius: 12px;
    padding: 1rem 1.2rem; margin-top: 1rem;
    border: 1px solid rgba(108,99,255,0.15);
}
.lc-overall-feedback h4 { font-size: 0.95rem; margin-bottom: 0.5rem; color: #ddd; }
.lc-overall-feedback p { color: #bbb; font-size: 0.85rem; line-height: 1.6; }

/* ═══ NO-GEMINI INFO ═══ */
.lc-no-gemini {
    background: rgba(255,193,7,0.08); border-radius: 12px;
    padding: 1rem 1.2rem; margin-top: 1rem;
    border: 1px solid rgba(255,193,7,0.2); text-align: center;
}
.lc-no-gemini p { color: #ccc; font-size: 0.88rem; margin: 0.3rem 0; }

/* ═══ IDLE INFO ═══ */
.lc-info { display: flex; flex-direction: column; gap: 1rem; }
.lc-info-card {
    background: rgba(26,26,46,0.8); border-radius: 14px; padding: 1.5rem;
    border: 1px solid rgba(108,99,255,0.1);
}
.lc-info-card h3 {
    font-size: 1.1rem; margin-bottom: 1rem;
    background: linear-gradient(90deg, #00d2ff, #6c63ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.lc-info-steps { display: flex; flex-direction: column; gap: 0.8rem; }
.lc-info-step { display: flex; align-items: flex-start; gap: 0.8rem; }
.lc-step-num {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #6c63ff, #00d2ff); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.85rem;
}
.lc-info-step strong { color: #eee; display: block; margin-bottom: 0.15rem; }
.lc-info-step p { color: #999; font-size: 0.85rem; margin: 0; }
.lc-info-req h4 { color: #ffc107; margin-bottom: 0.6rem; }
.lc-info-req ul { color: #bbb; font-size: 0.85rem; padding-left: 1.2rem; }
.lc-info-req li { margin-bottom: 0.3rem; }

/* ═══ RESPONSIVE ═══ */
@media (max-width: 768px) {
    .lc-cam-row { flex-direction: column; }
    .lc-cam-box { width: 100%; min-height: 180px; }
    .lc-metric-grid { grid-template-columns: repeat(2,1fr); }
    .lc-summary-grid { grid-template-columns: repeat(2,1fr); }
    .lc-dim-name { width: 85px; font-size: 0.72rem; }
    .lc-header h2 { font-size: 1.4rem; }
}
@media (max-width: 480px) {
    .lc-metric-grid { grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .lc-summary-grid { grid-template-columns: 1fr 1fr; }
    .lc-controls { flex-wrap: wrap; }
    .lc-cam-box { min-height: 140px; }
    .lc-feedback-section { grid-template-columns: 1fr; }
    .lc-agent-pipeline { grid-template-columns: repeat(2, 1fr); }
}
            `}</style>
        </div>
    )
}

export default LiveCoaching
