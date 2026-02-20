import { useState, useEffect, useCallback, useRef } from 'react'
import AgentCard from '../components/AgentCard'
import AgentTimeline from '../components/AgentTimeline'
import './AgentMonitor.css'

// ── 에이전트 정의 ──
const AGENT_DEFS = {
    extractor: { name: 'extractor', role: '리소스 추출기 (FFmpeg)', icon: '📦', dependencies: [], baseDuration: 2500 },
    vision: { name: 'vision', role: '비전 분석 에이전트', icon: '👁️', dependencies: ['extractor'], baseDuration: 5500 },
    content: { name: 'content', role: '콘텐츠 분석 에이전트', icon: '🎨', dependencies: ['extractor'], baseDuration: 4200 },
    stt: { name: 'stt', role: '음성→텍스트 에이전트', icon: '🗣️', dependencies: ['extractor'], baseDuration: 8800 },
    vibe: { name: 'vibe', role: '음성 프로소디 에이전트', icon: '🔊', dependencies: ['extractor'], baseDuration: 3500 },
    pedagogy: { name: 'pedagogy', role: '교육학 평가 에이전트', icon: '📚', dependencies: ['vision', 'content', 'stt', 'vibe'], baseDuration: 2000 },
    feedback: { name: 'feedback', role: '피드백 생성 에이전트', icon: '💡', dependencies: ['pedagogy'], baseDuration: 1500 },
    master: { name: 'master', role: '종합 분석 마스터', icon: '🧠', dependencies: ['vision', 'content', 'vibe', 'pedagogy', 'feedback'], baseDuration: 2800 },
}

function makeAgents(status = 'idle') {
    const out = {}
    for (const [k, v] of Object.entries(AGENT_DEFS)) {
        out[k] = { ...v, status, progress: 0, elapsed_seconds: 0, has_result: false }
    }
    return out
}

// ── 시뮬레이션 결과 데이터 ──
const AGENT_RESULTS = {
    extractor: { desc: '프레임 682장 + 오디오 1개 추출', detail: '640×360 @ 1fps, 16kHz WAV' },
    vision: { desc: '제스처 활성 37.2%, 시선 접촉 74.5%', detail: 'MediaPipe Pose Lite' },
    content: { desc: '슬라이드 28장 감지, 텍스트 밀도 85', detail: 'Canny Edge + MSER' },
    stt: { desc: '음성 인식 완료 (2,847 어절)', detail: 'Whisper Large v3' },
    vibe: { desc: '피치 변동 22.5Hz, 침묵 비율 18%', detail: 'Librosa + YIN' },
    pedagogy: { desc: '7차원 평가 완료: 72.3/100 (B)', detail: 'GAIM 평가 프레임워크' },
    feedback: { desc: '맞춤형 피드백 6건 생성', detail: '강점 3건, 개선점 3건' },
    master: { desc: '종합 리포트 생성 완료', detail: '8개 에이전트 결과 통합' },
}

export default function AgentMonitor() {
    const [agents, setAgents] = useState(() => makeAgents())
    const [pipelineStatus, setPipelineStatus] = useState('idle')   // idle | running | completed
    const [pipelineProgress, setPipelineProgress] = useState(0)
    const [isRunning, setIsRunning] = useState(false)
    const [log, setLog] = useState([])
    const [elapsedTotal, setElapsedTotal] = useState(0)
    const [history, setHistory] = useState([])
    const intervalRefs = useRef({})
    const timerRef = useRef(null)
    const startTimeRef = useRef(null)

    // ── 로그 추가 ──
    const addLog = useCallback((msg) => {
        setLog(prev => [...prev, { time: new Date().toLocaleTimeString('ko-KR'), msg }])
    }, [])

    // ── 에이전트 프로그레스 부드럽게 올리기 ──
    const animateAgent = useCallback((name, duration, onComplete) => {
        const startTime = Date.now()
        const tick = () => {
            const elapsed = Date.now() - startTime
            const progress = Math.min(100, Math.round((elapsed / duration) * 100))
            setAgents(prev => ({
                ...prev,
                [name]: { ...prev[name], status: 'running', progress, elapsed_seconds: +(elapsed / 1000).toFixed(1) }
            }))
            if (progress < 100) {
                intervalRefs.current[name] = requestAnimationFrame(tick)
            } else {
                // 완료
                const finalElapsed = +(Date.now() - startTime) / 1000
                setAgents(prev => ({
                    ...prev,
                    [name]: { ...prev[name], status: 'done', progress: 100, elapsed_seconds: +finalElapsed.toFixed(1), has_result: true, result_desc: AGENT_RESULTS[name]?.desc }
                }))
                addLog(`✅ ${AGENT_DEFS[name].icon} ${name} 완료 (${finalElapsed.toFixed(1)}s) — ${AGENT_RESULTS[name]?.desc}`)
                if (onComplete) onComplete()
            }
        }
        setAgents(prev => ({
            ...prev,
            [name]: { ...prev[name], status: 'running', progress: 0 }
        }))
        addLog(`▶️ ${AGENT_DEFS[name].icon} ${name} 시작`)
        intervalRefs.current[name] = requestAnimationFrame(tick)
    }, [addLog])

    // ── 의존성 기반 파이프라인 실행 ──
    const runPipeline = useCallback(() => {
        // 초기화
        setAgents(makeAgents())
        setPipelineStatus('running')
        setPipelineProgress(0)
        setIsRunning(true)
        setLog([])
        setElapsedTotal(0)
        startTimeRef.current = Date.now()

        addLog('🚀 멀티 에이전트 파이프라인 시작')

        // 전체 시간 타이머
        timerRef.current = setInterval(() => {
            setElapsedTotal(+((Date.now() - startTimeRef.current) / 1000).toFixed(1))
        }, 100)

        const completed = new Set()
        const agentNames = Object.keys(AGENT_DEFS)
        const totalAgents = agentNames.length
        let launched = new Set()

        const tryLaunch = () => {
            for (const name of agentNames) {
                if (completed.has(name) || launched.has(name)) continue
                const deps = AGENT_DEFS[name].dependencies
                if (deps.every(d => completed.has(d))) {
                    launched.add(name)
                    // 약간의 랜덤 지연 (50-200ms)
                    const jitter = Math.random() * 150 + 50
                    // ±20% 랜덤 duration
                    const duration = AGENT_DEFS[name].baseDuration * (0.8 + Math.random() * 0.4)
                    setTimeout(() => {
                        animateAgent(name, duration, () => {
                            completed.add(name)
                            setPipelineProgress(Math.round((completed.size / totalAgents) * 100))
                            if (completed.size === totalAgents) {
                                // 전체 완료
                                clearInterval(timerRef.current)
                                const total = +((Date.now() - startTimeRef.current) / 1000).toFixed(1)
                                setElapsedTotal(total)
                                setPipelineStatus('completed')
                                setPipelineProgress(100)
                                setIsRunning(false)
                                addLog(`🎉 전체 파이프라인 완료! (${total}s)`)
                                // 이력 추가
                                setHistory(prev => [{
                                    id: `run-${Date.now().toString(36)}`,
                                    video: 'sample_lecture.mp4',
                                    status: 'completed',
                                    elapsed: total,
                                    agents_count: totalAgents,
                                    created_at: new Date().toISOString()
                                }, ...prev])
                            } else {
                                tryLaunch()
                            }
                        })
                    }, jitter)
                }
            }
        }

        tryLaunch()
    }, [animateAgent, addLog])

    // ── 리셋 ──
    const resetPipeline = useCallback(() => {
        for (const id of Object.values(intervalRefs.current)) cancelAnimationFrame(id)
        if (timerRef.current) clearInterval(timerRef.current)
        intervalRefs.current = {}
        setAgents(makeAgents())
        setPipelineStatus('idle')
        setPipelineProgress(0)
        setIsRunning(false)
        setLog([])
        setElapsedTotal(0)
    }, [])

    // 언마운트 시 클린업
    useEffect(() => {
        return () => {
            for (const id of Object.values(intervalRefs.current)) cancelAnimationFrame(id)
            if (timerRef.current) clearInterval(timerRef.current)
        }
    }, [])

    // 로그 자동 스크롤
    const logEndRef = useRef(null)
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [log])

    return (
        <div className="agent-monitor">
            <div className="monitor-header">
                <div className="monitor-title">
                    <h2>🤖 멀티 에이전트 모니터</h2>
                    <p className="monitor-subtitle">실시간 에이전트 파이프라인 모니터링 — 8개 AI 에이전트 병렬 분석</p>
                </div>
                <div className="monitor-actions">
                    {!isRunning ? (
                        <button className="btn-primary" onClick={runPipeline}>
                            🚀 분석 시작
                        </button>
                    ) : (
                        <button className="btn-secondary" onClick={resetPipeline}>
                            ⏹ 중지
                        </button>
                    )}
                    {pipelineStatus === 'completed' && (
                        <button className="btn-secondary" onClick={resetPipeline}>
                            🔄 초기화
                        </button>
                    )}
                </div>
            </div>

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
                                    pipelineStatus === 'running' ? '⏳ 분석 진행 중' : '⏸ 대기 중'}
                            </span>
                        </div>
                        <div className="progress-container">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${pipelineProgress}%` }}
                                />
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
                        <AgentCard
                            key={agent.name}
                            agent={agent}
                            isActive={agent.status === 'running'}
                        />
                    ))}
                </div>
            </div>

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
                                <span className="history-agents">🤖 {h.agents_count}개 에이전트</span>
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
