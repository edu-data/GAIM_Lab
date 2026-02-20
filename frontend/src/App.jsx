import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Portfolio from './pages/Portfolio'
import BatchAnalysis from './pages/BatchAnalysis'
import AnalysisResult from './pages/AnalysisResult'
import AgentMonitor from './pages/AgentMonitor'
import GrowthPath from './pages/GrowthPath'
import LiveCoaching from './pages/LiveCoaching'
import CohortCompare from './pages/CohortCompare'
import LoginPage from './pages/LoginPage'
import ABExperiment from './pages/ABExperiment'
import './App.css'

const menuItems = [
    { path: '/', icon: '🏠', label: '홈', end: true },
    { path: '/dashboard', icon: '📊', label: '대시보드' },
    { path: '/upload', icon: '🎬', label: '수업 분석' },
    { path: '/agents', icon: '🤖', label: 'MAS 분석' },
    { path: '/batch', icon: '📦', label: '배치 분석' },
    { path: '/growth', icon: '📈', label: '성장보고서' },
    { path: '/cohort', icon: '🔬', label: '코호트 비교' },
    { path: '/live', icon: '🔴', label: '실시간 코칭' },
    { path: '/portfolio', icon: '📁', label: '포트폴리오' },
    { path: '/experiment', icon: '🧪', label: 'A/B 실험' },
]

function AppContent() {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [collapsed, setCollapsed] = useState(false)
    const location = useLocation()
    const user = (() => {
        try { return JSON.parse(localStorage.getItem('gaim_user')) } catch { return null }
    })()

    // Close mobile sidebar on route change
    useEffect(() => {
        setSidebarOpen(false)
    }, [location.pathname])

    return (
        <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
            {/* Mobile overlay */}
            {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <span className="sidebar-logo-icon">🤖</span>
                        {!collapsed && <span className="sidebar-logo-text">MAS <span className="version-tag">v7.1</span></span>}
                    </div>
                    <button className="sidebar-collapse-btn" onClick={() => setCollapsed(!collapsed)} title={collapsed ? '펼치기' : '접기'}>
                        {collapsed ? '▶' : '◀'}
                    </button>
                </div>

                <nav className="sidebar-nav">
                    {menuItems.map(item => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.end}
                            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
                            title={item.label}
                        >
                            <span className="sidebar-item-icon">{item.icon}</span>
                            {!collapsed && <span className="sidebar-item-label">{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <NavLink to="/login" className={({ isActive }) => `sidebar-item sidebar-login ${isActive ? 'active' : ''}`}>
                        <span className="sidebar-item-icon">👤</span>
                        {!collapsed && <span className="sidebar-item-label">{user ? (user.name || user.username) : '로그인'}</span>}
                    </NavLink>
                </div>
            </aside>

            {/* Main Area */}
            <div className="main-area">
                {/* Topbar */}
                <header className="topbar">
                    <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
                        <span></span><span></span><span></span>
                    </button>
                    <div className="topbar-left">
                        <h2 className="topbar-title">GAIM Lab</h2>
                        <span className="topbar-subtitle">Multi-Agent System for Class Analysis</span>
                    </div>
                    <div className="topbar-right">
                        <a href="https://github.com/edu-data/GAIM_Lab" target="_blank" rel="noopener noreferrer" className="topbar-link">
                            GitHub
                        </a>
                        <a href="https://edu-data.github.io/mas/mas-index.html" target="_blank" rel="noopener noreferrer" className="topbar-link">
                            Docs
                        </a>
                    </div>
                </header>

                {/* Content */}
                <main className="content-area">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/upload" element={<Upload />} />
                        <Route path="/agents" element={<AgentMonitor />} />
                        <Route path="/batch" element={<BatchAnalysis />} />
                        <Route path="/growth" element={<GrowthPath />} />
                        <Route path="/cohort" element={<CohortCompare />} />
                        <Route path="/live" element={<LiveCoaching />} />
                        <Route path="/portfolio" element={<Portfolio />} />
                        <Route path="/experiment" element={<ABExperiment />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/analysis/:analysisId" element={<AnalysisResult />} />
                    </Routes>
                </main>

                {/* Footer */}
                <footer className="app-footer">
                    <p>© 2026 GINUE AI Microteaching Lab · 경인교육대학교 · MAS v7.1</p>
                </footer>
            </div>
        </div>
    )
}

function App() {
    return (
        <Router>
            <AppContent />
        </Router>
    )
}

export default App
