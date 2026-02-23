import { useState, useEffect } from 'react'
import api from '../lib/api'
import { isGitHubPages } from '../lib/clientAuth'

const PERIOD_TABS = [
    { key: '4주', label: '4주 단기', icon: '⚡', color: '#00d2ff' },
    { key: '8주', label: '8주 중기', icon: '📈', color: '#6c63ff' },
    { key: '12주', label: '12주 장기', icon: '🎯', color: '#00e676' },
]

function GrowthPath() {
    const [growth, setGrowth] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [activePeriod, setActivePeriod] = useState('4주')
    const [prefix, setPrefix] = useState('20251209')
    const isRemote = isGitHubPages()

    useEffect(() => { loadGrowthData() }, [prefix])

    const loadGrowthData = async () => {
        setLoading(true)
        setError(null)
        if (isRemote) {
            // GitHub Pages: 데모 데이터 직접 로드
            setGrowth(generateDemoData())
            setLoading(false)
            return
        }
        try {
            const data = await api.get(`/growth/${prefix}`)
            setGrowth(data)
        } catch (e) {
            setError(e.message)
            // Demo fallback
            setGrowth(generateDemoData())
        }
        setLoading(false)
    }

    const generateDemoData = () => ({
        sessions: 5,
        profile: { strengths: ['수업 전문성', '교수학습 방법'], weaknesses: ['창의성', '학생 참여', '시간 배분'] },
        roadmap: {
            '4주': {
                label: '기초 역량 강화', focus: '인식 및 습관화',
                target_dimensions: ['창의성', '학생 참여', '시간 배분'],
                expected_improvement: 7,
                weeks: [
                    { week: 1, focus_dimension: '창의성', goal: '다양한 매체(영상, 실물, ICT)를 활용하세요', activity: '자기 수업 영상 분석 (10분)', target_score: 51.7, current_score: 50 },
                    { week: 2, focus_dimension: '학생 참여', goal: '모든 학생이 참여할 수 있는 구조화된 활동을 설계하세요', activity: '동료 수업 참관 및 피드백 작성', target_score: 55, current_score: 52 },
                    { week: 3, focus_dimension: '시간 배분', goal: '단계별 시간 배분을 사전에 계획하세요', activity: '교수법 논문/자료 1편 읽기', target_score: 58, current_score: 54 },
                    { week: 4, focus_dimension: '창의성', goal: '수업 설계에 창의적 요소를 통합하세요', activity: '마이크로티칭 실습 및 자기 피드백', target_score: 60, current_score: 55 },
                ],
            },
            '8주': {
                label: '심화 적용', focus: '전략적 실천',
                target_dimensions: ['창의성', '학생 참여', '시간 배분'],
                expected_improvement: 15,
                weeks: Array.from({ length: 8 }, (_, i) => ({
                    week: i + 1, focus_dimension: ['창의성', '학생 참여', '시간 배분'][i % 3],
                    goal: '전략적 교수법 적용 연습', activity: '마이크로티칭 실습',
                    target_score: 53 + (i + 1) * 2, current_score: 50 + (i % 3) * 5,
                })),
            },
            '12주': {
                label: '전문성 내면화', focus: '자기 모니터링 & 코칭',
                target_dimensions: ['창의성', '학생 참여', '시간 배분'],
                expected_improvement: 20,
                weeks: Array.from({ length: 12 }, (_, i) => ({
                    week: i + 1, focus_dimension: ['창의성', '학생 참여', '시간 배분'][i % 3],
                    goal: '전문성 내면화를 위한 심화 실습', activity: '수업 일지 작성 및 성찰',
                    target_score: 50 + (i + 1) * 1.7, current_score: 50 + (i % 3) * 5,
                })),
            },
        },
    })

    const roadmap = growth?.roadmap?.[activePeriod]
    const activeTab = PERIOD_TABS.find(t => t.key === activePeriod)

    return (
        <div className="growth-path-page">
            <div className="page-header">
                <h2>🎯 성장 경로 (Growth Path)</h2>
                <p>반복 분석 결과 기반 개인별 개선 로드맵</p>
            </div>

            {isRemote && <div className="gp-local-badge">📊 샘플 데이터 — 성장 경로 데모를 표시합니다</div>}
            {!isRemote && error && <div className="gp-notice">⚠️ API 연결 실패 — 데모 데이터를 표시합니다.</div>}

            {/* Period Tabs */}
            <div className="gp-tabs">
                {PERIOD_TABS.map(tab => (
                    <button
                        key={tab.key}
                        className={`gp-tab ${activePeriod === tab.key ? 'active' : ''}`}
                        onClick={() => setActivePeriod(tab.key)}
                        style={activePeriod === tab.key ? { borderColor: tab.color, color: tab.color } : {}}
                    >
                        <span className="tab-icon">{tab.icon}</span>
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="gp-loading">로딩 중...</div>
            ) : roadmap ? (
                <>
                    {/* Summary Cards */}
                    <div className="gp-summary">
                        <div className="gp-card">
                            <div className="gp-card-value" style={{ color: activeTab.color }}>{roadmap.label}</div>
                            <div className="gp-card-label">프로그램 유형</div>
                        </div>
                        <div className="gp-card">
                            <div className="gp-card-value" style={{ color: activeTab.color }}>+{roadmap.expected_improvement}%</div>
                            <div className="gp-card-label">예상 향상량</div>
                        </div>
                        <div className="gp-card">
                            <div className="gp-card-value" style={{ color: activeTab.color }}>{roadmap.target_dimensions?.length || 0}개</div>
                            <div className="gp-card-label">집중 차원</div>
                        </div>
                        <div className="gp-card">
                            <div className="gp-card-value" style={{ color: activeTab.color }}>{roadmap.focus}</div>
                            <div className="gp-card-label">핵심 전략</div>
                        </div>
                    </div>

                    {/* Target Dimensions */}
                    <div className="gp-section">
                        <h3>📌 집중 차원</h3>
                        <div className="gp-chips">
                            {roadmap.target_dimensions?.map(d => (
                                <span key={d} className="gp-chip">{d}</span>
                            ))}
                        </div>
                    </div>

                    {/* Weekly Plan */}
                    <div className="gp-section">
                        <h3>📅 주차별 계획</h3>
                        <div className="gp-timeline">
                            {roadmap.weeks?.map(w => (
                                <div key={w.week} className="gp-week-card">
                                    <div className="gp-week-header">
                                        <span className="gp-week-badge" style={{ background: activeTab.color }}>
                                            {w.week}주차
                                        </span>
                                        <span className="gp-week-dim">{w.focus_dimension}</span>
                                    </div>
                                    <div className="gp-week-body">
                                        <div className="gp-week-goal">
                                            <strong>🎯 목표:</strong> {w.goal}
                                        </div>
                                        <div className="gp-week-activity">
                                            <strong>📝 활동:</strong> {w.activity}
                                        </div>
                                        <div className="gp-week-progress">
                                            <div className="gp-progress-bar">
                                                <div className="gp-progress-current"
                                                    style={{ width: `${w.current_score}%`, background: '#555' }} />
                                                <div className="gp-progress-target"
                                                    style={{ width: `${w.target_score}%`, background: activeTab.color, opacity: 0.4 }} />
                                            </div>
                                            <div className="gp-progress-labels">
                                                <span>현재 {w.current_score}%</span>
                                                <span>목표 {w.target_score}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            ) : (
                <div className="gp-empty">성장 데이터가 없습니다. 먼저 수업 분석을 진행하세요.</div>
            )}

            <style>{`
        .growth-path-page { max-width: 900px; margin: 0 auto; }
        .page-header { text-align: center; margin-bottom: 1.5rem; }
        .page-header h2 { font-size: 1.6rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .page-header p { color: #888; font-size: 0.9rem; }
        .gp-notice { background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.3);
          border-radius: 8px; padding: 0.7rem 1rem; color: #ffc107; margin-bottom: 1rem; font-size: 0.85rem; }
        .gp-local-badge { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
          border-radius: 8px; padding: 0.7rem 1rem; color: #a5b4fc; margin-bottom: 1rem; font-size: 0.85rem; text-align: center; }
        .gp-tabs { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; justify-content: center; }
        .gp-tab { background: rgba(255,255,255,0.05); border: 2px solid transparent;
          border-radius: 12px; padding: 0.8rem 1.5rem; color: #aaa; cursor: pointer;
          font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s; }
        .gp-tab:hover { background: rgba(108,99,255,0.1); }
        .gp-tab.active { background: rgba(108,99,255,0.12); color: #fff; }
        .tab-icon { font-size: 1.2rem; }
        .gp-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 0.75rem; margin-bottom: 1.5rem; }
        .gp-card { background: rgba(22,33,62,0.8); border-radius: 12px; padding: 1.2rem;
          text-align: center; border: 1px solid rgba(108,99,255,0.15); }
        .gp-card-value { font-size: 1.3rem; font-weight: 700; }
        .gp-card-label { color: #888; font-size: 0.78rem; margin-top: 0.3rem; }
        .gp-section { background: rgba(26,26,46,0.8); border-radius: 14px; padding: 1.5rem;
          margin-bottom: 1.2rem; border: 1px solid rgba(108,99,255,0.12); }
        .gp-section h3 { color: #00d2ff; font-size: 1.05rem; margin-bottom: 1rem; }
        .gp-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        .gp-chip { background: rgba(108,99,255,0.15); color: #a5a0ff; padding: 0.4rem 0.9rem;
          border-radius: 20px; font-size: 0.82rem; }
        .gp-timeline { display: flex; flex-direction: column; gap: 0.75rem; }
        .gp-week-card { background: rgba(22,33,62,0.6); border-radius: 10px; padding: 1rem;
          border: 1px solid rgba(108,99,255,0.1); }
        .gp-week-header { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.7rem; }
        .gp-week-badge { color: #fff; font-size: 0.75rem; font-weight: 600;
          padding: 0.25rem 0.7rem; border-radius: 8px; }
        .gp-week-dim { color: #ccc; font-size: 0.85rem; font-weight: 500; }
        .gp-week-body { display: flex; flex-direction: column; gap: 0.4rem; }
        .gp-week-goal, .gp-week-activity { font-size: 0.85rem; color: #bbb; }
        .gp-week-goal strong, .gp-week-activity strong { color: #ddd; }
        .gp-week-progress { margin-top: 0.5rem; }
        .gp-progress-bar { position: relative; height: 6px; background: rgba(255,255,255,0.05);
          border-radius: 3px; overflow: hidden; }
        .gp-progress-current, .gp-progress-target { position: absolute; top: 0; left: 0;
          height: 100%; border-radius: 3px; }
        .gp-progress-labels { display: flex; justify-content: space-between;
          font-size: 0.72rem; color: #777; margin-top: 0.3rem; }
        .gp-loading, .gp-empty { text-align: center; color: #888; padding: 3rem; }
        @media (max-width: 768px) {
          .gp-tabs { flex-direction: column; }
          .gp-summary { grid-template-columns: 1fr 1fr; }
        }
      `}</style>
        </div>
    )
}

export default GrowthPath
