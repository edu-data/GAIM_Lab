/**
 * GAIM Lab v8.0 — 성장 포트폴리오 (Growth Portfolio)
 * 
 * 통합 페이지: 성장 경로 + 포트폴리오
 * 기존 2개 페이지를 탭 방식으로 통합
 */

import { useState } from 'react'
import GrowthPath from './GrowthPath'
import Portfolio from './Portfolio'

const tabs = [
    { id: 'growth', label: '📈 성장 분석', desc: '차원별 성장 추세 분석' },
    { id: 'portfolio', label: '🏆 포트폴리오', desc: '분석 이력 및 뱃지' },
]

const tabComponents = {
    growth: GrowthPath,
    portfolio: Portfolio,
}

const GrowthPortfolio = () => {
    const [activeTab, setActiveTab] = useState('growth')
    const ActiveComponent = tabComponents[activeTab]

    return (
        <div className="growth-portfolio-page">
            <div className="page-header">
                <h1>🌱 성장 포트폴리오</h1>
                <p style={{ color: 'var(--text-secondary, #94a3b8)', marginTop: '0.5rem' }}>
                    수업 역량의 성장 추이와 포트폴리오 관리
                </p>
            </div>

            {/* 탭 */}
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
                        {tab.label}
                    </button>
                ))}
            </div>

            <ActiveComponent />
        </div>
    )
}

export default GrowthPortfolio
