import { useState, useRef } from 'react'
import api from '../lib/api'
import { analyzeVideoClient, getStoredApiKey, isGitHubPages } from '../lib/clientAnalyzer'
import { mean, sd, welchTTest, cohensD, effectSizeLabel } from '../lib/statistics'
import ApiKeySettings from '../components/ApiKeySettings'

// ─── 차원 매핑 ───
const DIMENSIONS = [
    { key: '수업 전문성', field: '수업 전문성' },
    { key: '교수학습 방법', field: '교수학습 방법' },
    { key: '판서 및 언어', field: '판서 및 언어' },
    { key: '수업 태도', field: '수업 태도' },
    { key: '학생 참여', field: '학생 참여' },
    { key: '시간 배분', field: '시간 배분' },
    { key: '창의성', field: '창의성' },
]

function CohortCompare() {
    const [groupA, setGroupA] = useState({ label: '', files: [], results: [] })
    const [groupB, setGroupB] = useState({ label: '', files: [], results: [] })
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState(null)
    const [error, setError] = useState(null)
    const [showApiKeyModal, setShowApiKeyModal] = useState(false)
    const fileRefA = useRef(null)
    const fileRefB = useRef(null)

    const isRemote = isGitHubPages()

    const handleFiles = (e, group) => {
        const files = Array.from(e.target.files).filter(f => f.type.startsWith('video/'))
        const setter = group === 'A' ? setGroupA : setGroupB
        setter(prev => ({ ...prev, files }))
    }

    // 클라이언트 사이드 코호트 비교
    const runClientComparison = async () => {
        const apiKey = getStoredApiKey()
        if (!apiKey) {
            setShowApiKeyModal(true)
            return
        }

        if (groupA.files.length === 0 || groupB.files.length === 0) {
            setError('두 그룹 모두 비디오 파일을 선택해주세요')
            return
        }

        setLoading(true)
        setError(null)
        setResult(null)

        const allFiles = [
            ...groupA.files.map(f => ({ file: f, group: 'A' })),
            ...groupB.files.map(f => ({ file: f, group: 'B' })),
        ]
        const total = allFiles.length
        const resultsA = []
        const resultsB = []

        try {
            for (let i = 0; i < total; i++) {
                const { file, group } = allFiles[i]
                setProgress({
                    current: i + 1,
                    total,
                    group,
                    videoName: file.name,
                    message: `그룹 ${group}: ${file.name} 분석 중...`,
                    pct: Math.round((i / total) * 100),
                })

                const data = await analyzeVideoClient(file, apiKey, (subProg, msg) => {
                    const overallPct = Math.round(((i + subProg / 100) / total) * 100)
                    setProgress(prev => ({ ...prev, pct: overallPct, message: `그룹 ${group}: ${msg}` }))
                })

                if (group === 'A') resultsA.push(data)
                else resultsB.push(data)
            }

            // 통계 계산
            const comparisons = buildComparisons(resultsA, resultsB)
            const labelA = groupA.label || `그룹 A (${groupA.files.length}개)`
            const labelB = groupB.label || `그룹 B (${groupB.files.length}개)`

            setGroupA(prev => ({ ...prev, results: resultsA }))
            setGroupB(prev => ({ ...prev, results: resultsB }))

            setResult({
                group_a: { label: labelA, n_analyses: resultsA.length },
                group_b: { label: labelB, n_analyses: resultsB.length },
                comparisons,
            })
        } catch (e) {
            console.error('Cohort analysis error:', e)
            setError(e.message)
        }

        setProgress(null)
        setLoading(false)
    }

    // 서버 모드
    const runServerComparison = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await api.post('/cohort/compare', {
                group_a: { prefix: groupA.label, label: groupA.label },
                group_b: { prefix: groupB.label, label: groupB.label },
            })
            setResult(data)
        } catch (e) {
            setError(e.message)
        }
        setLoading(false)
    }

    const runComparison = () => {
        if (isRemote) runClientComparison()
        else runServerComparison()
    }

    // 분석 결과에서 통계 비교 생성
    function buildComparisons(groupAResults, groupBResults) {
        const extract = (results, dimName) => results.map(r => {
            const dim = r.dimensions?.find(d => d.name === dimName)
            return dim ? dim.percentage : 0
        })

        const comparisons = []

        // 총점 비교
        const totalsA = groupAResults.map(r => r.total_score || 0)
        const totalsB = groupBResults.map(r => r.total_score || 0)
        const ttTotal = welchTTest(totalsA, totalsB)
        const dTotal = cohensD(totalsA, totalsB)
        comparisons.push({
            dimension: 'total',
            group_a: { mean: +mean(totalsA).toFixed(1), std: +sd(totalsA).toFixed(1), n: totalsA.length },
            group_b: { mean: +mean(totalsB).toFixed(1), std: +sd(totalsB).toFixed(1), n: totalsB.length },
            t_test: ttTotal,
            cohens_d: dTotal,
            effect_size: effectSizeLabel(dTotal),
        })

        // 차원별 비교
        for (const dim of DIMENSIONS) {
            const scoresA = extract(groupAResults, dim.field)
            const scoresB = extract(groupBResults, dim.field)
            const tt = welchTTest(scoresA, scoresB)
            const d = cohensD(scoresA, scoresB)
            comparisons.push({
                dimension: dim.key,
                group_a: { mean: +mean(scoresA).toFixed(1), std: +sd(scoresA).toFixed(1), n: scoresA.length },
                group_b: { mean: +mean(scoresB).toFixed(1), std: +sd(scoresB).toFixed(1), n: scoresB.length },
                t_test: tt,
                cohens_d: d,
                effect_size: effectSizeLabel(d),
            })
        }

        return comparisons
    }

    const effectColor = (size) => {
        if (size === 'large') return '#ff5252'
        if (size === 'medium') return '#ffc107'
        return '#00e676'
    }

    const canRun = isRemote
        ? (groupA.files.length > 0 && groupB.files.length > 0)
        : (groupA.label && groupB.label)

    return (
        <div className="cohort-page">
            <div className="page-header">
                <h2>📊 코호트 비교 분석</h2>
                <p>두 집단의 수업 영상을 분석하여 통계적으로 비교합니다.</p>
            </div>

            <ApiKeySettings
                open={showApiKeyModal}
                onClose={() => setShowApiKeyModal(false)}
                onSave={() => {
                    setShowApiKeyModal(false)
                    if (canRun) setTimeout(() => runClientComparison(), 300)
                }}
            />

            {/* 그룹 입력 섹션 */}
            <div className="cc-input-section">
                <div className="cc-group-input">
                    <h4>그룹 A</h4>
                    <input
                        placeholder="그룹명 (예: 1학년 A반)"
                        value={groupA.label}
                        onChange={e => setGroupA({ ...groupA, label: e.target.value })}
                    />
                    {isRemote && (
                        <>
                            <input
                                ref={fileRefA}
                                type="file"
                                accept="video/*"
                                multiple
                                onChange={e => handleFiles(e, 'A')}
                                style={{ display: 'none' }}
                            />
                            <button
                                className="cc-file-btn"
                                onClick={() => fileRefA.current?.click()}
                            >
                                📂 영상 선택 ({groupA.files.length}개)
                            </button>
                            {groupA.files.length > 0 && (
                                <div className="cc-file-list">
                                    {groupA.files.map(f => (
                                        <span key={f.name} className="cc-file-tag">{f.name}</span>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                    {!isRemote && (
                        <input
                            placeholder="영상 접두사 (예: 2025_classA)"
                            value={groupA.prefix || ''}
                            onChange={e => setGroupA({ ...groupA, prefix: e.target.value })}
                        />
                    )}
                </div>

                <div className="cc-vs">VS</div>

                <div className="cc-group-input">
                    <h4>그룹 B</h4>
                    <input
                        placeholder="그룹명 (예: 1학년 B반)"
                        value={groupB.label}
                        onChange={e => setGroupB({ ...groupB, label: e.target.value })}
                    />
                    {isRemote && (
                        <>
                            <input
                                ref={fileRefB}
                                type="file"
                                accept="video/*"
                                multiple
                                onChange={e => handleFiles(e, 'B')}
                                style={{ display: 'none' }}
                            />
                            <button
                                className="cc-file-btn"
                                onClick={() => fileRefB.current?.click()}
                            >
                                📂 영상 선택 ({groupB.files.length}개)
                            </button>
                            {groupB.files.length > 0 && (
                                <div className="cc-file-list">
                                    {groupB.files.map(f => (
                                        <span key={f.name} className="cc-file-tag">{f.name}</span>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                    {!isRemote && (
                        <input
                            placeholder="영상 접두사 (예: 2025_classB)"
                            value={groupB.prefix || ''}
                            onChange={e => setGroupB({ ...groupB, prefix: e.target.value })}
                        />
                    )}
                </div>
            </div>

            <div style={{ textAlign: 'center', marginBottom: '1.5rem', display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
                {isRemote && (
                    <button className="cc-key-btn" onClick={() => setShowApiKeyModal(true)}>
                        🔑 {getStoredApiKey() ? 'Key 변경' : 'Key 설정'}
                    </button>
                )}
                <button
                    className="cc-compare-btn"
                    onClick={runComparison}
                    disabled={loading || !canRun}
                >
                    {loading ? '분석 중...' : '🔬 비교 분석 실행'}
                </button>
            </div>

            {/* 진행 상황 */}
            {progress && (
                <div className="cc-progress">
                    <div className="cc-progress-header">
                        <span>⏳ {progress.message}</span>
                        <span>{progress.current}/{progress.total}</span>
                    </div>
                    <div className="cc-progress-bar">
                        <div className="cc-progress-fill" style={{ width: `${progress.pct}%` }} />
                    </div>
                    <div className="cc-progress-pct">{progress.pct}%</div>
                </div>
            )}

            {error && <div className="cc-notice">⚠️ {error}</div>}

            {/* 결과 */}
            {result && (
                <>
                    {/* 그룹 정보 */}
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

                    {/* 비교 테이블 */}
                    <div className="cc-table-wrap">
                        <table className="cc-table">
                            <thead>
                                <tr>
                                    <th>차원</th>
                                    <th>{result.group_a.label} (M±SD)</th>
                                    <th>{result.group_b.label} (M±SD)</th>
                                    <th>t</th>
                                    <th>df</th>
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
                                        <td>{c.t_test.df}</td>
                                        <td style={{ color: c.t_test.significant ? '#ff5252' : '#888' }}>
                                            {c.t_test.p < 0.001 ? '< .001' : c.t_test.p.toFixed(3)}{c.t_test.significant ? ' *' : ''}
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
        .cc-input-section { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
        .cc-group-input { flex: 1; background: rgba(26,26,46,0.8); border-radius: 12px; padding: 1rem;
          border: 1px solid rgba(108,99,255,0.15); }
        .cc-group-input h4 { color: #00d2ff; margin-bottom: 0.5rem; }
        .cc-group-input input[type="text"], .cc-group-input input[type="search"],
        .cc-group-input input:not([type="file"]) {
          width: 100%; background: rgba(0,0,0,0.2); border: 1px solid rgba(108,99,255,0.2);
          border-radius: 8px; padding: 0.6rem 0.8rem; color: #e0e0ec; margin-bottom: 0.4rem; font-size: 0.85rem; }
        .cc-file-btn { width: 100%; padding: 0.6rem; background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
          border: 1px dashed rgba(99,102,241,0.4); border-radius: 8px; color: #a5b4fc; cursor: pointer;
          font-size: 0.85rem; margin-bottom: 0.5rem; transition: all 0.2s ease; }
        .cc-file-btn:hover { border-color: #6366f1; background: rgba(99,102,241,0.2); }
        .cc-file-list { display: flex; flex-wrap: wrap; gap: 0.3rem; }
        .cc-file-tag { font-size: 0.72rem; padding: 0.2rem 0.5rem; background: rgba(99,102,241,0.12);
          border-radius: 6px; color: #c7d2fe; }
        .cc-vs { color: #ff5252; font-weight: 700; font-size: 1.3rem; padding-top: 2rem; }
        .cc-compare-btn { padding: 0.8rem 2rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
          color: #fff; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; font-weight: 600; }
        .cc-compare-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .cc-key-btn { padding: 0.8rem 1.2rem; background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3);
          border-radius: 12px; color: #a5b4fc; cursor: pointer; font-size: 0.9rem; }
        .cc-progress { background: rgba(26,26,46,0.8); border-radius: 12px; padding: 1rem;
          border: 1px solid rgba(99,102,241,0.15); margin-bottom: 1rem; }
        .cc-progress-header { display: flex; justify-content: space-between; color: #a5b4fc; font-size: 0.85rem;
          margin-bottom: 0.5rem; }
        .cc-progress-bar { height: 6px; background: rgba(99,102,241,0.15); border-radius: 3px; overflow: hidden; }
        .cc-progress-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #a78bfa);
          border-radius: 3px; transition: width 0.5s ease; }
        .cc-progress-pct { text-align: right; font-size: 0.78rem; color: #6366f1; margin-top: 0.3rem; }
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
