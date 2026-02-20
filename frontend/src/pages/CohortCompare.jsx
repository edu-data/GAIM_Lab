import { useState } from 'react'

const API_BASE = '/api/v1/cohort'

function CohortCompare() {
    const [groupA, setGroupA] = useState({ prefix: '', label: '' })
    const [groupB, setGroupB] = useState({ prefix: '', label: '' })
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const runComparison = async () => {
        if (!groupA.prefix || !groupB.prefix) return
        setLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE}/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group_a: groupA, group_b: groupB }),
            })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            setResult(await res.json())
        } catch (e) {
            setError(e.message)
            // Demo fallback
            setResult(generateDemoResult())
        }
        setLoading(false)
    }

    const generateDemoResult = () => ({
        group_a: { prefix: groupA.prefix, label: groupA.label || groupA.prefix, n_analyses: 12 },
        group_b: { prefix: groupB.prefix, label: groupB.label || groupB.prefix, n_analyses: 10 },
        comparisons: [
            { dimension: 'total', group_a: { mean: 72.5, std: 8.3, n: 12 }, group_b: { mean: 68.1, std: 9.1, n: 10 }, t_test: { t: 1.23, p: 0.11, significant: false }, cohens_d: 0.51, effect_size: 'medium' },
            { dimension: '수업 전문성', group_a: { mean: 78.2, std: 7.1, n: 12 }, group_b: { mean: 71.3, std: 8.9, n: 10 }, t_test: { t: 2.1, p: 0.04, significant: true }, cohens_d: 0.86, effect_size: 'large' },
            { dimension: '교수학습 방법', group_a: { mean: 74.1, std: 9.2, n: 12 }, group_b: { mean: 70.8, std: 7.6, n: 10 }, t_test: { t: 0.95, p: 0.17, significant: false }, cohens_d: 0.39, effect_size: 'small' },
            { dimension: '판서 및 언어', group_a: { mean: 69.4, std: 10.1, n: 12 }, group_b: { mean: 67.2, std: 11.3, n: 10 }, t_test: { t: 0.51, p: 0.31, significant: false }, cohens_d: 0.21, effect_size: 'small' },
            { dimension: '수업 태도', group_a: { mean: 75.8, std: 6.5, n: 12 }, group_b: { mean: 72.1, std: 8.0, n: 10 }, t_test: { t: 1.28, p: 0.11, significant: false }, cohens_d: 0.51, effect_size: 'medium' },
            { dimension: '학생 참여', group_a: { mean: 65.3, std: 12.0, n: 12 }, group_b: { mean: 60.2, std: 11.5, n: 10 }, t_test: { t: 1.07, p: 0.14, significant: false }, cohens_d: 0.43, effect_size: 'small' },
            { dimension: '시간 배분', group_a: { mean: 71.0, std: 8.8, n: 12 }, group_b: { mean: 69.5, std: 9.4, n: 10 }, t_test: { t: 0.41, p: 0.34, significant: false }, cohens_d: 0.17, effect_size: 'small' },
            { dimension: '창의성', group_a: { mean: 68.2, std: 11.4, n: 12 }, group_b: { mean: 63.8, std: 10.7, n: 10 }, t_test: { t: 0.99, p: 0.16, significant: false }, cohens_d: 0.40, effect_size: 'small' },
        ],
    })

    const effectColor = (size) => {
        if (size === 'large') return '#ff5252'
        if (size === 'medium') return '#ffc107'
        return '#00e676'
    }

    return (
        <div className="cohort-page">
            <div className="page-header">
                <h2>📊 코호트 비교 분석</h2>
                <p>학급/대학/연도별 집단 간 비교 통계</p>
            </div>

            {/* Input Section */}
            <div className="cc-input-section">
                <div className="cc-group-input">
                    <h4>그룹 A</h4>
                    <input placeholder="영상 접두사 (예: 2025_classA)"
                        value={groupA.prefix} onChange={e => setGroupA({ ...groupA, prefix: e.target.value })} />
                    <input placeholder="라벨 (예: 1학년 A반)"
                        value={groupA.label} onChange={e => setGroupA({ ...groupA, label: e.target.value })} />
                </div>
                <div className="cc-vs">VS</div>
                <div className="cc-group-input">
                    <h4>그룹 B</h4>
                    <input placeholder="영상 접두사 (예: 2025_classB)"
                        value={groupB.prefix} onChange={e => setGroupB({ ...groupB, prefix: e.target.value })} />
                    <input placeholder="라벨 (예: 1학년 B반)"
                        value={groupB.label} onChange={e => setGroupB({ ...groupB, label: e.target.value })} />
                </div>
            </div>

            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <button className="cc-compare-btn" onClick={runComparison} disabled={loading || !groupA.prefix || !groupB.prefix}>
                    {loading ? '분석 중...' : '🔬 비교 분석 실행'}
                </button>
            </div>

            {error && <div className="cc-notice">⚠️ API 연결 실패 — 데모 데이터를 표시합니다.</div>}

            {/* Results */}
            {result && (
                <>
                    {/* Group Info */}
                    <div className="cc-group-info">
                        <div className="cc-group-badge" style={{ borderColor: '#6c63ff' }}>
                            <strong>{result.group_a.label}</strong>
                            <span>{result.group_a.n_analyses}건 분석</span>
                        </div>
                        <div className="cc-group-badge" style={{ borderColor: '#00d2ff' }}>
                            <strong>{result.group_b.label}</strong>
                            <span>{result.group_b.n_analyses}건 분석</span>
                        </div>
                    </div>

                    {/* Comparison Table */}
                    <div className="cc-table-wrap">
                        <table className="cc-table">
                            <thead>
                                <tr>
                                    <th>차원</th>
                                    <th>{result.group_a.label} (M±SD)</th>
                                    <th>{result.group_b.label} (M±SD)</th>
                                    <th>t</th>
                                    <th>p</th>
                                    <th>Cohen's d</th>
                                    <th>효과 크기</th>
                                </tr>
                            </thead>
                            <tbody>
                                {result.comparisons?.map(c => (
                                    <tr key={c.dimension} className={c.dimension === 'total' ? 'cc-total-row' : ''}>
                                        <td><strong>{c.dimension === 'total' ? '총점' : c.dimension}</strong></td>
                                        <td>{c.group_a.mean} ± {c.group_a.std}</td>
                                        <td>{c.group_b.mean} ± {c.group_b.std}</td>
                                        <td>{c.t_test.t}</td>
                                        <td style={{ color: c.t_test.significant ? '#ff5252' : '#888' }}>
                                            {c.t_test.p}{c.t_test.significant ? ' *' : ''}
                                        </td>
                                        <td>{c.cohens_d}</td>
                                        <td><span className="cc-effect" style={{ color: effectColor(c.effect_size) }}>
                                            {c.effect_size === 'large' ? '대' : c.effect_size === 'medium' ? '중' : '소'}
                                        </span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="cc-legend">
                        <span>* p &lt; .05 유의</span>
                        <span>Cohen's d: <span style={{ color: '#00e676' }}>소(&lt;0.5)</span> <span style={{ color: '#ffc107' }}>중(0.5~0.8)</span> <span style={{ color: '#ff5252' }}>대(≥0.8)</span></span>
                    </div>
                </>
            )}

            <style>{`
        .cohort-page { max-width: 950px; margin: 0 auto; }
        .page-header { text-align: center; margin-bottom: 1.5rem; }
        .page-header h2 { font-size: 1.6rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .cc-input-section { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
        .cc-group-input { flex: 1; background: rgba(26,26,46,0.8); border-radius: 12px; padding: 1rem;
          border: 1px solid rgba(108,99,255,0.15); }
        .cc-group-input h4 { color: #00d2ff; margin-bottom: 0.5rem; }
        .cc-group-input input { width: 100%; background: rgba(0,0,0,0.2); border: 1px solid rgba(108,99,255,0.2);
          border-radius: 8px; padding: 0.6rem 0.8rem; color: #e0e0ec; margin-bottom: 0.4rem; font-size: 0.85rem; }
        .cc-vs { color: #ff5252; font-weight: 700; font-size: 1.3rem; }
        .cc-compare-btn { padding: 0.8rem 2rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          color: #fff; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; font-weight: 600; }
        .cc-compare-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .cc-notice { background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.3);
          border-radius: 8px; padding: 0.6rem; color: #ffc107; font-size: 0.82rem; margin-bottom: 1rem; }
        .cc-group-info { display: flex; gap: 1rem; margin-bottom: 1rem; justify-content: center; }
        .cc-group-badge { background: rgba(22,33,62,0.8); border-radius: 10px; padding: 0.7rem 1.2rem;
          border-left: 3px solid; display: flex; flex-direction: column; gap: 0.2rem; }
        .cc-group-badge strong { color: #eee; } .cc-group-badge span { color: #888; font-size: 0.78rem; }
        .cc-table-wrap { overflow-x: auto; margin-bottom: 0.75rem; }
        .cc-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .cc-table th { background: rgba(108,99,255,0.12); padding: 0.65rem 0.5rem; text-align: center;
          color: #00d2ff; font-weight: 600; border-bottom: 2px solid rgba(108,99,255,0.25); }
        .cc-table td { padding: 0.55rem 0.5rem; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.04); }
        .cc-table tr:hover { background: rgba(108,99,255,0.06); }
        .cc-total-row { background: rgba(108,99,255,0.08); }
        .cc-effect { font-weight: 600; }
        .cc-legend { display: flex; justify-content: center; gap: 2rem; font-size: 0.78rem; color: #777; }
        @media (max-width: 768px) { .cc-input-section { flex-direction: column; } .cc-vs { display: none; } }
      `}</style>
        </div>
    )
}

export default CohortCompare
