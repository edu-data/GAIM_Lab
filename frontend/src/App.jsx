import { HashRouter as Router, Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import AnalysisResult from './pages/AnalysisResult'
import AgentMonitor from './pages/AgentMonitor'
import LiveCoaching from './pages/LiveCoaching'
import LoginPage from './pages/LoginPage'
import AdminUsers from './pages/AdminUsers'
// v8.0: 통합 페이지
import ResearchTools from './pages/ResearchTools'
import GrowthPortfolio from './pages/GrowthPortfolio'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

const menuItems = [
    { path: '/', icon: '🏠', label: '홈', end: true },
    { path: '/dashboard', icon: '📊', label: '대시보드' },
    { path: '/upload', icon: '🎬', label: '수업 분석' },
    { path: '/agents', icon: '🤖', label: 'MAS 분석' },
    { path: '/research', icon: '🔬', label: '연구 도구' },
    { path: '/growth', icon: '🌱', label: '성장 포트폴리오' },
    { path: '/live', icon: '🔴', label: '실시간 코칭' },
]

function AppContent() {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [collapsed, setCollapsed] = useState(false)
    const location = useLocation()
    const [user, setUser] = useState(() => {
        try { return JSON.parse(localStorage.getItem('gaim_user')) } catch { return null }
    })

    // Re-read user from storage on route change (login/logout updates localStorage)
    useEffect(() => {
        try { setUser(JSON.parse(localStorage.getItem('gaim_user'))) } catch { setUser(null) }
    }, [location.pathname])

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
                        {!collapsed && <span className="sidebar-logo-text">GAIM <span className="version-tag">{typeof __APP_VERSION__ !== 'undefined' ? `v${__APP_VERSION__}` : 'v8.0.0'}</span></span>}
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
                    {user?.role === 'admin' && (
                        <NavLink
                            to="/admin/users"
                            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
                            title="사용자 관리"
                        >
                            <span className="sidebar-item-icon">👑</span>
                            {!collapsed && <span className="sidebar-item-label">사용자 관리</span>}
                        </NavLink>
                    )}
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
                    <ErrorBoundary>
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/upload" element={<Upload />} />
                            <Route path="/agents" element={<AgentMonitor />} />
                            <Route path="/research" element={<ResearchTools />} />
                            <Route path="/growth" element={<GrowthPortfolio />} />
                            <Route path="/live" element={<LiveCoaching />} />
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/admin/users" element={<AdminUsers />} />
                            <Route path="/analysis/:analysisId" element={<AnalysisResult />} />
                            {/* v8.0: backward-compatible redirects */}
                            <Route path="/batch" element={<Navigate to="/research" replace />} />
                            <Route path="/cohort" element={<Navigate to="/research" replace />} />
                            <Route path="/experiment" element={<Navigate to="/research" replace />} />
                            <Route path="/portfolio" element={<Navigate to="/growth" replace />} />
                        </Routes>
                    </ErrorBoundary>
                </main>

                {/* Footer */}
                <footer className="app-footer">
                    <p>© 2026 GINUE AI Microteaching Lab · 경인교육대학교 · GAIM Lab {typeof __APP_VERSION__ !== 'undefined' ? `v${__APP_VERSION__}` : 'v8.0.0'}</p>
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
