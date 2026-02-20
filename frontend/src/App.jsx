import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
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

function App() {
    return (
        <Router>
            <div className="app">
                <header className="app-header">
                    <div className="logo">
                        <span className="logo-icon">🎓</span>
                        <h1>GAIM Lab</h1>
                    </div>
                    <nav className="nav">
                        <a href="/">대시보드</a>
                        <a href="/agents">에이전트</a>
                        <a href="/batch">일괄 분석</a>
                        <a href="/upload">수업 분석</a>
                        <a href="/live">실시간 코칭</a>
                        <a href="/growth">성장 경로</a>
                        <a href="/cohort">코호트</a>
                        <a href="/portfolio">포트폴리오</a>
                        <a href="/experiment">A/B 실험</a>
                        <a href="/login">로그인</a>
                    </nav>
                </header>
                <main className="app-main">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/agents" element={<AgentMonitor />} />
                        <Route path="/batch" element={<BatchAnalysis />} />
                        <Route path="/upload" element={<Upload />} />
                        <Route path="/live" element={<LiveCoaching />} />
                        <Route path="/growth" element={<GrowthPath />} />
                        <Route path="/cohort" element={<CohortCompare />} />
                        <Route path="/portfolio" element={<Portfolio />} />
                        <Route path="/experiment" element={<ABExperiment />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/analysis/:analysisId" element={<AnalysisResult />} />
                    </Routes>
                </main>
                <footer className="app-footer">
                    <p>© 2026 GINUE AI Microteaching Lab | 경인교육대학교</p>
                </footer>
            </div>
        </Router>
    )
}

export default App
