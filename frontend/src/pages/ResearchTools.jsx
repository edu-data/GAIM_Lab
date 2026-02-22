/**
 * GAIM Lab v8.0 — 연구 도구 (Research Tools)
 * 
 * 통합 페이지: 배치 분석 + 코호트 비교 + A/B 실험
 * 기존 3개 페이지를 탭 방식으로 통합
 */

import { useState } from 'react'
import BatchAnalysis from './BatchAnalysis'
import CohortCompare from './CohortCompare'
import ABExperiment from './ABExperiment'

const tabs = [
    { id: 'batch', label: '📊 배치 분석', icon: '📊', desc: '다수 영상 일괄 분석' },
    { id: 'cohort', label: '👥 코호트 비교', icon: '👥', desc: '집단 간 비교 분석' },
    { id: 'ab', label: '🧪 A/B 실험', icon: '🧪', desc: '교수법 효과 비교' },
]

const tabComponents = {
    batch: BatchAnalysis,
    cohort: CohortCompare,
    ab: ABExperiment,
}

const ResearchTools = () => {
    const [activeTab, setActiveTab] = useState('batch')
    const ActiveComponent = tabComponents[activeTab]

    return (
        <div className="research-tools-page">
            <div className="page-header">
                <h1>🔬 연구 도구</h1>
                <p style={{ color: 'var(--text-secondary, #94a3b8)', marginTop: '0.5rem' }}>
                    수업 분석 데이터를 활용한 연구 도구 모음
                </p>
            </div>

            {/* 탭 네비게이션 */}
            <div style={{
                display: 'flex',
                gap: '0.5rem',
                padding: '0.5rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '1rem',
                marginBottom: '1.5rem',
            }}>
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            flex: 1,
                            padding: '0.75rem 1rem',
                            borderRadius: '0.75rem',
                            border: 'none',
                            background: activeTab === tab.id
                                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                                : 'transparent',
                            color: activeTab === tab.id ? '#fff' : 'var(--text-secondary, #94a3b8)',
                            fontWeight: activeTab === tab.id ? 700 : 500,
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            fontSize: '0.9rem',
                        }}
                    >
                        <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
                        {tab.label.replace(tab.icon + ' ', '')}
                    </button>
                ))}
            </div>

            {/* 탭 콘텐츠 */}
            <ActiveComponent />
        </div>
    )
}

export default ResearchTools
