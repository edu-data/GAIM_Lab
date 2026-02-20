import { useState, useEffect, useCallback } from 'react'
import AgentCard from '../components/AgentCard'
import AgentTimeline from '../components/AgentTimeline'
import { API_BASE } from '../apiConfig'
import './AgentMonitor.css'

const AGENTS_API = `${API_BASE}/agents`

export default function AgentMonitor() {
    const [registry, setRegistry] = useState(null)
    const [activePipeline, setActivePipeline] = useState(null)
    const [pipelines, setPipelines] = useState([])
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [error, setError] = useState(null)

    // 에이전트 레지스트리 로드
    useEffect(() => {
        fetch(`${AGENTS_API}/status`)
            .then(res => res.json())
            .then(data => setRegistry(data))
            .catch(() => setRegistry(getDemoRegistry()))
    }, [])

    // 파이프라인 목록 로드
    useEffect(() => {
        fetch(`${AGENTS_API}/pipelines`)
            .then(res => res.json())
            .then(data => setPipelines(data.pipelines || []))
            .catch(() => { })
    }, [])

    // 활성 파이프라인 폴링
    useEffect(() => {
        if (!activePipeline || activePipeline.status === 'completed' || activePipeline.status === 'failed') return
        const interval = setInterval(() => {
            fetch(`${AGENTS_API}/pipeline/${activePipeline.pipeline_id}`)
                .then(res => res.json())
                .then(data => setActivePipeline(data))
                .catch(() => { })
        }, 1000)
        return () => clearInterval(interval)
    }, [activePipeline])

    // 분석 시작
    const startAnalysis = useCallback(async () => {
        setIsAnalyzing(true)
        setError(null)
        try {
            const res = await fetch(`${AGENTS_API}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            })
            const data = await res.json()
            if (data.pipeline_id) {
                setActivePipeline({
                    pipeline_id: data.pipeline_id,
                    status: 'queued',
                    progress: 0,
                    agents: {},
                })
            }
        } catch (e) {
            setError('분석 시작에 실패했습니다. 백엔드 서버를 확인하세요.')
            setActivePipeline(getDemoPipeline())
        }
        setIsAnalyzing(false)
    }, [])

    // 데모 실행
    const runDemo = () => {
        setActivePipeline(getDemoPipeline())
        simulateDemo()
    }

    const [demoStep, setDemoStep] = useState(-1)

    const simulateDemo = () => {
        setDemoStep(0)
    }

    useEffect(() => {
        if (demoStep < 0) return
        const steps = getDemoSteps()
        if (demoStep >= steps.length) {
            setDemoStep(-1)
            return
        }
        const timer = setTimeout(() => {
            setActivePipeline(prev => ({
                ...prev,
                ...steps[demoStep],
            }))
            setDemoStep(d => d + 1)
        }, 800)
        return () => clearTimeout(timer)
    }, [demoStep])

    const agents = activePipeline?.agents || registry?.agents || {}

    return (
        <div className="agent-monitor">
            <div className="monitor-header">
                <div className="monitor-title">
                    <h2>🤖 멀티 에이전트 모니터</h2>
                    <p className="monitor-subtitle">실시간 에이전트 파이프라인 모니터링</p>
                </div>
                <div className="monitor-actions">
                    <button
                        className="btn-primary"
                        onClick={startAnalysis}
                        disabled={isAnalyzing}
                    >
                        {isAnalyzing ? '⏳ 시작 중...' : '🚀 분석 시작'}
                    </button>
                    <button className="btn-secondary" onClick={runDemo}>
                        🎮 데모 실행
                    </button>
                </div>
            </div>

            {error && <div className="monitor-error">{error}</div>}

            {/* 파이프라인 타임라인 */}
            <div className="glass-card pipeline-section">
                <h3>📊 파이프라인 흐름</h3>
                <AgentTimeline agents={agents} />

                {activePipeline && (
                    <div className="pipeline-status-bar">
                        <div className="status-info">
                            <span className={`status-dot ${activePipeline.status}`} />
                            <span className="status-text">
                                {activePipeline.status === 'completed' ? '✅ 분석 완료' :
                                    activePipeline.status === 'running' ? '⏳ 분석 진행 중' :
                                        activePipeline.status === 'failed' ? '❌ 분석 실패' : '⏸ 대기 중'}
                            </span>
                        </div>
                        <div className="progress-container">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${activePipeline.progress || 0}%` }}
                                />
                            </div>
                            <span className="progress-text">{activePipeline.progress || 0}%</span>
                        </div>
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

            {/* 최근 파이프라인 이력 */}
            {pipelines.length > 0 && (
                <div className="glass-card history-section">
                    <h3>📜 실행 이력</h3>
                    <div className="history-list">
                        {pipelines.map(p => (
                            <div key={p.id} className={`history-item ${p.status}`}>
                                <span className="history-id">{p.id}</span>
                                <span className="history-video">{p.video}</span>
                                <span className={`history-status ${p.status}`}>{p.status}</span>
                                <span className="history-time">{new Date(p.created_at).toLocaleString('ko-KR')}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

// =================================================================
// 데모 데이터
// =================================================================

function getDemoRegistry() {
    return {
        total_agents: 8,
        agents: {
            extractor: { name: 'extractor', role: '리소스 추출기', icon: '📦', status: 'idle', progress: 0, dependencies: [], elapsed_seconds: 0, has_result: false },
            vision: { name: 'vision', role: '비전 분석 에이전트', icon: '👁️', status: 'idle', progress: 0, dependencies: ['extractor'], elapsed_seconds: 0, has_result: false },
            content: { name: 'content', role: '콘텐츠 분석 에이전트', icon: '🎨', status: 'idle', progress: 0, dependencies: ['extractor'], elapsed_seconds: 0, has_result: false },
            stt: { name: 'stt', role: '음성→텍스트 에이전트', icon: '🗣️', status: 'idle', progress: 0, dependencies: ['extractor'], elapsed_seconds: 0, has_result: false },
            vibe: { name: 'vibe', role: '음성 프로소디 에이전트', icon: '🔊', status: 'idle', progress: 0, dependencies: ['extractor'], elapsed_seconds: 0, has_result: false },
            pedagogy: { name: 'pedagogy', role: '교육학 평가 에이전트', icon: '📚', status: 'idle', progress: 0, dependencies: ['vision', 'content', 'stt', 'vibe'], elapsed_seconds: 0, has_result: false },
            feedback: { name: 'feedback', role: '피드백 생성 에이전트', icon: '💡', status: 'idle', progress: 0, dependencies: ['pedagogy'], elapsed_seconds: 0, has_result: false },
            master: { name: 'master', role: '종합 분석 마스터', icon: '🧠', status: 'idle', progress: 0, dependencies: ['vision', 'content', 'vibe', 'pedagogy', 'feedback'], elapsed_seconds: 0, has_result: false },
        }
    }
}

function getDemoPipeline() {
    return { pipeline_id: 'demo-001', status: 'queued', progress: 0, agents: getDemoRegistry().agents }
}

function getDemoSteps() {
    const base = getDemoRegistry().agents
    const step = (updates, progress, status = 'running') => {
        const agents = { ...base }
        for (const [k, v] of Object.entries(updates)) {
            agents[k] = { ...agents[k], ...v }
        }
        return { agents, progress, status }
    }
    return [
        step({ extractor: { status: 'running', progress: 50 } }, 5),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true } }, 12),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'running', progress: 30 }, content: { status: 'running', progress: 20 }, stt: { status: 'running', progress: 40 }, vibe: { status: 'running', progress: 25 } }, 30),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'done', progress: 100, elapsed_seconds: 5.3, has_result: true }, content: { status: 'done', progress: 100, elapsed_seconds: 4.1, has_result: true }, stt: { status: 'done', progress: 100, elapsed_seconds: 8.7, has_result: true }, vibe: { status: 'done', progress: 100, elapsed_seconds: 3.2, has_result: true } }, 55),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'done', progress: 100, elapsed_seconds: 5.3, has_result: true }, content: { status: 'done', progress: 100, elapsed_seconds: 4.1, has_result: true }, stt: { status: 'done', progress: 100, elapsed_seconds: 8.7, has_result: true }, vibe: { status: 'done', progress: 100, elapsed_seconds: 3.2, has_result: true }, pedagogy: { status: 'running', progress: 60 } }, 70),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'done', progress: 100, elapsed_seconds: 5.3, has_result: true }, content: { status: 'done', progress: 100, elapsed_seconds: 4.1, has_result: true }, stt: { status: 'done', progress: 100, elapsed_seconds: 8.7, has_result: true }, vibe: { status: 'done', progress: 100, elapsed_seconds: 3.2, has_result: true }, pedagogy: { status: 'done', progress: 100, elapsed_seconds: 1.8, has_result: true }, feedback: { status: 'running', progress: 50 } }, 80),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'done', progress: 100, elapsed_seconds: 5.3, has_result: true }, content: { status: 'done', progress: 100, elapsed_seconds: 4.1, has_result: true }, stt: { status: 'done', progress: 100, elapsed_seconds: 8.7, has_result: true }, vibe: { status: 'done', progress: 100, elapsed_seconds: 3.2, has_result: true }, pedagogy: { status: 'done', progress: 100, elapsed_seconds: 1.8, has_result: true }, feedback: { status: 'done', progress: 100, elapsed_seconds: 1.2, has_result: true }, master: { status: 'running', progress: 70 } }, 90),
        step({ extractor: { status: 'done', progress: 100, elapsed_seconds: 2.1, has_result: true }, vision: { status: 'done', progress: 100, elapsed_seconds: 5.3, has_result: true }, content: { status: 'done', progress: 100, elapsed_seconds: 4.1, has_result: true }, stt: { status: 'done', progress: 100, elapsed_seconds: 8.7, has_result: true }, vibe: { status: 'done', progress: 100, elapsed_seconds: 3.2, has_result: true }, pedagogy: { status: 'done', progress: 100, elapsed_seconds: 1.8, has_result: true }, feedback: { status: 'done', progress: 100, elapsed_seconds: 1.2, has_result: true }, master: { status: 'done', progress: 100, elapsed_seconds: 2.5, has_result: true } }, 100, 'completed'),
    ]
}
