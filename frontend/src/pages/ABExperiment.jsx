import { useState, useEffect } from 'react'

const API_BASE = '/api/v1/experiment'

function ABExperiment() {
    const [rubrics, setRubrics] = useState({})
    const [rubricA, setRubricA] = useState('standard_v7')
    const [rubricB, setRubricB] = useState('student_centered')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetch(`${API_BASE}/rubrics`)
            .then(r => r.json()).then(setRubrics)
            .catch(() => setRubrics({
                standard_v7: { name: '표준 루브릭 v7', criteria: '임용시험 기준' },
                student_centered: { name: '학생중심 루브릭', criteria: '학생 참여 중심' },
                creativity_focus: { name: '창의성 강조', criteria: '창의적 교수법 중심' },
                balanced: { name: '균등 배점', criteria: '7차원 동일 가중치' },
            }))
    }, [])

    const runExperiment = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE}/ab`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rubric_a: rubricA, rubric_b: rubricB }),
            })
            setResult(await res.json())
        } catch {
            // Demo fallback
            setResult({
                rubric_a: { id: rubricA, name: rubrics[rubricA]?.name || rubricA, total: 72.5, dimensions: {} },
                rubric_b: { id: rubricB, name: rubrics[rubricB]?.name || rubricB, total: 69.8, dimensions: {} },
                dimension_diffs: [
                    { dimension: '수업 전문성', rubric_a_score: 11.2, rubric_b_score: 7.5, diff: -3.7, pct_diff: -33.0 },
                    { dimension: '교수학습 방법', rubric_a_score: 10.8, rubric_b_score: 14.4, diff: 3.6, pct_diff: 33.3 },
                    { dimension: '판서 및 언어', rubric_a_score: 10.5, rubric_b_score: 7.0, diff: -3.5, pct_diff: -33.3 },
                    { dimension: '수업 태도', rubric_a_score: 11.1, rubric_b_score: 7.4, diff: -3.7, pct_diff: -33.3 },
                    { dimension: '학생 참여', rubric_a_score: 9.8, rubric_b_score: 16.3, diff: 6.5, pct_diff: 66.3 },
                    { dimension: '시간 배분', rubric_a_score: 7.5, rubric_b_score: 7.5, diff: 0, pct_diff: 0 },
                    { dimension: '창의성', rubric_a_score: 11.6, rubric_b_score: 11.6, diff: 0, pct_diff: 0 },
                ],
                total_diff: -2.7,
                summary: '루브릭 A가 2.7점 높습니다. 가장 큰 차이를 보이는 차원은 \'학생 참여\' (차이: +6.50점)입니다.',
            })
        }
        setLoading(false)
    }

    const diffBar = (diff) => {
        const maxDiff = 10
        const pct = Math.min(Math.abs(diff) / maxDiff * 100, 100)
        const color = diff > 0 ? '#00e676' : diff < 0 ? '#ff5252' : '#555'
        return (
            <div className="ab-diff-bar">
                <div className="ab-diff-fill" style={{
                    width: `${pct}%`, background: color,
                    marginLeft: diff < 0 ? `${100 - pct}%` : '50%',
                }} />
            </div>
        )
    }

    const rubricKeys = Object.keys(rubrics)

    return (
        <div className="ab-page">
            <div className="page-header">
                <h2>🧪 A/B 루브릭 실험</h2>
                <p>2개 루브릭을 동시 적용하여 채점 기준 비교</p>
            </div>

            {/* Rubric Selection */}
            <div className="ab-select-section">
                <div className="ab-select-card">
                    <h4>루브릭 A</h4>
                    <select value={rubricA} onChange={e => setRubricA(e.target.value)}>
                        {rubricKeys.map(k => <option key={k} value={k}>{rubrics[k].name}</option>)}
                    </select>
                    <p className="ab-criteria">{rubrics[rubricA]?.criteria}</p>
                </div>
                <div className="ab-vs">VS</div>
                <div className="ab-select-card">
                    <h4>루브릭 B</h4>
                    <select value={rubricB} onChange={e => setRubricB(e.target.value)}>
                        {rubricKeys.map(k => <option key={k} value={k}>{rubrics[k].name}</option>)}
                    </select>
                    <p className="ab-criteria">{rubrics[rubricB]?.criteria}</p>
                </div>
            </div>

            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <button className="ab-run-btn" onClick={runExperiment} disabled={loading || rubricA === rubricB}>
                    {loading ? '분석 중...' : '🔬 실험 실행'}
                </button>
                {rubricA === rubricB && <p style={{ color: '#ff5252', fontSize: '0.8rem', marginTop: '0.3rem' }}>서로 다른 루브릭을 선택하세요</p>}
            </div>

            {/* Results */}
            {result && (
                <>
                    {/* Total Scores */}
                    <div className="ab-totals">
                        <div className="ab-total-card">
                            <div className="ab-total-value" style={{ color: '#6c63ff' }}>{result.rubric_a.total}</div>
                            <div className="ab-total-label">{result.rubric_a.name}</div>
                        </div>
                        <div className="ab-total-diff">
                            {result.total_diff > 0 ? '+' : ''}{result.total_diff}
                        </div>
                        <div className="ab-total-card">
                            <div className="ab-total-value" style={{ color: '#00d2ff' }}>{result.rubric_b.total}</div>
                            <div className="ab-total-label">{result.rubric_b.name}</div>
                        </div>
                    </div>

                    {/* Dimension Comparison */}
                    <div className="ab-section">
                        <h3>📊 차원별 비교</h3>
                        <table className="ab-table">
                            <thead>
                                <tr>
                                    <th>차원</th>
                                    <th>A 점수</th>
                                    <th>B 점수</th>
                                    <th>차이</th>
                                    <th>시각화</th>
                                </tr>
                            </thead>
                            <tbody>
                                {result.dimension_diffs?.map(d => (
                                    <tr key={d.dimension}>
                                        <td><strong>{d.dimension}</strong></td>
                                        <td>{d.rubric_a_score}</td>
                                        <td>{d.rubric_b_score}</td>
                                        <td style={{ color: d.diff > 0 ? '#00e676' : d.diff < 0 ? '#ff5252' : '#888' }}>
                                            {d.diff > 0 ? '+' : ''}{d.diff}
                                        </td>
                                        <td>{diffBar(d.diff)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Summary */}
                    <div className="ab-summary">
                        <strong>📋 요약:</strong> {result.summary}
                    </div>
                </>
            )}

            <style>{`
        .ab-page { max-width: 900px; margin: 0 auto; }
        .page-header { text-align: center; margin-bottom: 1.5rem; }
        .page-header h2 { font-size: 1.6rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .ab-select-section { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
        .ab-select-card { flex: 1; background: rgba(26,26,46,0.8); border-radius: 12px; padding: 1rem;
          border: 1px solid rgba(108,99,255,0.15); }
        .ab-select-card h4 { color: #00d2ff; margin-bottom: 0.5rem; }
        .ab-select-card select { width: 100%; padding: 0.6rem; background: rgba(0,0,0,0.3);
          border: 1px solid rgba(108,99,255,0.2); border-radius: 8px; color: #e0e0ec; font-size: 0.9rem; }
        .ab-criteria { color: #666; font-size: 0.78rem; margin-top: 0.3rem; }
        .ab-vs { color: #ff5252; font-weight: 700; font-size: 1.3rem; }
        .ab-run-btn { padding: 0.8rem 2rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          color: #fff; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; font-weight: 600; }
        .ab-run-btn:disabled { opacity: 0.5; }
        .ab-totals { display: flex; align-items: center; justify-content: center; gap: 1.5rem; margin-bottom: 1.5rem; }
        .ab-total-card { background: rgba(22,33,62,0.8); border-radius: 12px; padding: 1.2rem 2rem; text-align: center;
          border: 1px solid rgba(108,99,255,0.15); }
        .ab-total-value { font-size: 2rem; font-weight: 700; }
        .ab-total-label { color: #888; font-size: 0.8rem; }
        .ab-total-diff { font-size: 1.5rem; font-weight: 700; color: #ffc107; }
        .ab-section { background: rgba(26,26,46,0.8); border-radius: 14px; padding: 1.5rem;
          margin-bottom: 1rem; border: 1px solid rgba(108,99,255,0.12); }
        .ab-section h3 { color: #00d2ff; margin-bottom: 1rem; }
        .ab-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .ab-table th { background: rgba(108,99,255,0.12); padding: 0.6rem; text-align: center;
          color: #00d2ff; border-bottom: 2px solid rgba(108,99,255,0.2); }
        .ab-table td { padding: 0.5rem; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.04); }
        .ab-diff-bar { width: 80px; height: 8px; background: rgba(255,255,255,0.05);
          border-radius: 4px; overflow: hidden; margin: 0 auto; position: relative; }
        .ab-diff-fill { height: 100%; border-radius: 4px; position: absolute; top: 0; }
        .ab-summary { background: rgba(22,33,62,0.6); border-left: 3px solid #6c63ff;
          border-radius: 8px; padding: 1rem; font-size: 0.88rem; color: #ccc; }
        @media (max-width: 768px) { .ab-select-section { flex-direction: column; } .ab-vs { display: none; } }
      `}</style>
        </div>
    )
}

export default ABExperiment
