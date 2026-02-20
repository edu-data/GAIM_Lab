import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { AUTH_BASE } from '../apiConfig'
const API_BASE = AUTH_BASE

function LoginPage() {
    const [mode, setMode] = useState('login')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [error, setError] = useState(null)
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const token = params.get('token')
        const uname = params.get('username')
        const displayName = params.get('name')
        if (token && uname) {
            localStorage.setItem('gaim_token', token)
            localStorage.setItem('gaim_user', JSON.stringify({ username: uname, name: displayName }))
            setUser({ username: uname, name: displayName })
            window.history.replaceState({}, '', '/login')
        } else {
            const stored = localStorage.getItem('gaim_user')
            if (stored) setUser(JSON.parse(stored))
        }
    }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        const endpoint = mode === 'login' ? '/login' : '/register'
        const body = mode === 'login'
            ? { username, password }
            : { username, password, name, role: 'student' }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })
            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || `HTTP ${res.status}`)
            }
            const data = await res.json()
            localStorage.setItem('gaim_token', data.access_token)
            localStorage.setItem('gaim_user', JSON.stringify({ username: data.username, name: data.name || data.username, role: data.role }))
            setUser({ username: data.username, name: data.name || data.username, role: data.role })
        } catch (e) {
            setError(e.message)
        }
        setLoading(false)
    }

    const handleGoogleLogin = () => {
        window.location.href = `${window.location.protocol}//${window.location.hostname}:8000/api/v1/auth/google/login`
    }

    const handleLogout = () => {
        localStorage.removeItem('gaim_token')
        localStorage.removeItem('gaim_user')
        setUser(null)
    }

    const [pwCurrent, setPwCurrent] = useState('')
    const [pwNew, setPwNew] = useState('')
    const [pwConfirm, setPwConfirm] = useState('')
    const [pwMsg, setPwMsg] = useState(null)
    const [pwLoading, setPwLoading] = useState(false)

    const handleChangePassword = async (e) => {
        e.preventDefault()
        if (pwNew !== pwConfirm) { setPwMsg('❌ 새 비밀번호가 일치하지 않습니다'); return }
        if (pwNew.length < 4) { setPwMsg('❌ 새 비밀번호는 4자 이상이어야 합니다'); return }
        setPwLoading(true)
        setPwMsg(null)
        try {
            const token = localStorage.getItem('gaim_token')
            const res = await fetch(`${API_BASE}/me/password`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({ current_password: pwCurrent, new_password: pwNew }),
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
            setPwMsg(`✅ ${data.message}`)
            setPwCurrent(''); setPwNew(''); setPwConfirm('')
        } catch (e) { setPwMsg(`❌ ${e.message}`) }
        setPwLoading(false)
    }

    if (user) {
        return (
            <div className="login-page">
                <div className="login-split">
                    <div className="login-brand">
                        <div className="login-brand-content">
                            <div className="login-brand-icon">🤖</div>
                            <h1>MAS <span>v7.1</span></h1>
                            <p>Multi-Agent System for Class Analysis</p>
                            <div className="login-features-mini">
                                <div>🎯 성장 경로 로드맵</div>
                                <div>🔴 실시간 코칭</div>
                                <div>📊 코호트 비교 분석</div>
                                <div>🧪 A/B 루브릭 실험</div>
                            </div>
                        </div>
                    </div>
                    <div className="login-form-area">
                        <div className="login-card">
                            <div className="login-avatar">👤</div>
                            <h2>환영합니다!</h2>
                            <p className="login-username">{user.name || user.username}</p>
                            <p className="login-role">{user.role === 'admin' ? '👑 관리자' : user.role === 'teacher' ? '👨‍🏫 교사' : '🎓 학생'}</p>
                            <div className="login-actions">
                                <Link to="/dashboard" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                                    📊 대시보드
                                </Link>
                                {user.role === 'admin' && (
                                    <Link to="/admin/users" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center', background: 'rgba(245,158,11,0.2)', borderColor: '#f59e0b' }}>
                                        👑 사용자 관리
                                    </Link>
                                )}
                                <button className="btn-logout" onClick={handleLogout}>로그아웃</button>
                            </div>

                            {/* Password Change */}
                            <div className="pw-change-section">
                                <h3>🔑 비밀번호 변경</h3>
                                {pwMsg && <div className={`pw-msg ${pwMsg.startsWith('✅') ? 'success' : 'error'}`}>{pwMsg}</div>}
                                <form onSubmit={handleChangePassword}>
                                    <input type="password" placeholder="현재 비밀번호" required
                                        value={pwCurrent} onChange={e => setPwCurrent(e.target.value)} />
                                    <input type="password" placeholder="새 비밀번호 (4자 이상)" required
                                        value={pwNew} onChange={e => setPwNew(e.target.value)} />
                                    <input type="password" placeholder="새 비밀번호 확인" required
                                        value={pwConfirm} onChange={e => setPwConfirm(e.target.value)} />
                                    <button type="submit" className="btn btn-primary" disabled={pwLoading}>
                                        {pwLoading ? '변경 중...' : '비밀번호 변경'}
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <style>{styles}</style>
            </div>
        )
    }

    return (
        <div className="login-page">
            <div className="login-split">
                {/* Brand Panel */}
                <div className="login-brand">
                    <div className="login-brand-content">
                        <div className="login-brand-icon">🤖</div>
                        <h1>MAS <span>v7.1</span></h1>
                        <p className="login-brand-desc">
                            8개 AI 에이전트가 협업하여 수업 영상을
                            7차원 100점 만점으로 자동 평가합니다
                        </p>
                        <div className="login-features-mini">
                            <div>🎯 성장 경로 로드맵</div>
                            <div>🔴 실시간 코칭</div>
                            <div>📊 코호트 비교 분석</div>
                            <div>🧪 A/B 루브릭 실험</div>
                        </div>
                        <div className="login-stats-mini">
                            <div className="login-stat-item">
                                <strong>8</strong><span>에이전트</span>
                            </div>
                            <div className="login-stat-item">
                                <strong>18</strong><span>영상 분석</span>
                            </div>
                            <div className="login-stat-item">
                                <strong>100%</strong><span>성공률</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Form Panel */}
                <div className="login-form-area">
                    <div className="login-card">
                        <h2>🎓 GAIM Lab</h2>
                        <p className="login-subtitle">AI 수업 분석 시스템에 로그인하세요</p>

                        {/* Google OAuth */}
                        <button className="google-btn" onClick={handleGoogleLogin}>
                            <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" /><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" /><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" /><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" /></svg>
                            Google로 로그인
                        </button>

                        <div className="login-divider"><span>또는</span></div>

                        {/* Form */}
                        <form onSubmit={handleSubmit}>
                            {mode === 'register' && (
                                <input type="text" placeholder="이름" value={name}
                                    onChange={e => setName(e.target.value)} className="login-input" />
                            )}
                            <input type="text" placeholder="아이디" value={username}
                                onChange={e => setUsername(e.target.value)} className="login-input" required />
                            <input type="password" placeholder="비밀번호" value={password}
                                onChange={e => setPassword(e.target.value)} className="login-input" required />
                            {error && <div className="login-error">{error}</div>}
                            <button type="submit" className="login-submit" disabled={loading}>
                                {loading ? '처리 중...' : mode === 'login' ? '로그인' : '회원가입'}
                            </button>
                        </form>

                        <p className="login-toggle">
                            {mode === 'login' ? (
                                <>계정이 없으신가요? <a onClick={() => setMode('register')}>회원가입</a></>
                            ) : (
                                <>이미 계정이 있으신가요? <a onClick={() => setMode('login')}>로그인</a></>
                            )}
                        </p>
                    </div>
                </div>
            </div>
            <style>{styles}</style>
        </div>
    )
}

const styles = `
    .login-page { display: flex; min-height: calc(100vh - 120px); }
    .login-split { display: flex; width: 100%; border-radius: 16px; overflow: hidden;
        border: 1px solid rgba(99,102,241,0.12); }

    /* Brand Panel */
    .login-brand { flex: 1; background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(167,139,250,0.08) 100%);
        display: flex; align-items: center; justify-content: center; padding: 3rem;
        border-right: 1px solid rgba(99,102,241,0.1); }
    .login-brand-content { text-align: center; max-width: 360px; }
    .login-brand-icon { font-size: 4rem; margin-bottom: 1rem; }
    .login-brand h1 { font-size: 2.5rem; font-weight: 900;
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    .login-brand h1 span { font-size: 0.9rem; font-weight: 700;
        background: rgba(99,102,241,0.25); -webkit-text-fill-color: #a5b4fc;
        padding: 2px 8px; border-radius: 5px; vertical-align: middle; margin-left: 4px; }
    .login-brand-desc { color: #94a3b8; font-size: 0.9rem; line-height: 1.7; margin-bottom: 2rem; }
    .login-brand p { color: #94a3b8; font-size: 0.9rem; }

    .login-features-mini { display: flex; flex-direction: column; gap: 0.5rem; margin: 2rem 0;
        text-align: left; }
    .login-features-mini div { font-size: 0.82rem; color: #94a3b8; padding: 0.5rem 0.75rem;
        background: rgba(99,102,241,0.06); border-radius: 8px; border: 1px solid rgba(99,102,241,0.08); }

    .login-stats-mini { display: flex; gap: 1.5rem; justify-content: center; margin-top: 1.5rem; }
    .login-stat-item { text-align: center; }
    .login-stat-item strong { display: block; font-size: 1.5rem; font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .login-stat-item span { font-size: 0.72rem; color: #64748b; }

    /* Form Area */
    .login-form-area { flex: 1; display: flex; align-items: center; justify-content: center;
        padding: 3rem; background: rgba(10,10,30,0.5); }
    .login-card { width: 100%; max-width: 380px; text-align: center; }
    .login-card h2 { font-size: 1.5rem; margin-bottom: 0.3rem; font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .login-subtitle { color: #64748b; font-size: 0.82rem; margin-bottom: 1.5rem; }

    .google-btn { width: 100%; padding: 0.75rem; background: #fff; color: #333; border: none;
        border-radius: 10px; font-size: 0.88rem; cursor: pointer; display: flex;
        align-items: center; justify-content: center; gap: 0.6rem; font-weight: 500;
        transition: all 0.25s; }
    .google-btn:hover { background: #f0f0f0; transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

    .login-divider { display: flex; align-items: center; margin: 1.2rem 0;
        color: #475569; font-size: 0.78rem; }
    .login-divider::before, .login-divider::after { content: ''; flex: 1;
        border-bottom: 1px solid rgba(99,102,241,0.12); }
    .login-divider span { padding: 0 0.8rem; }

    .login-input { width: 100%; padding: 0.7rem 0.9rem; background: rgba(22,22,48,0.6);
        border: 1px solid rgba(99,102,241,0.15); border-radius: 10px; color: #e2e8f0;
        font-size: 0.88rem; margin-bottom: 0.6rem; outline: none; transition: border-color 0.25s;
        font-family: 'Inter', sans-serif; }
    .login-input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }
    .login-input::placeholder { color: #475569; }

    .login-error { color: #f87171; font-size: 0.8rem; margin-bottom: 0.5rem;
        padding: 0.4rem 0.75rem; background: rgba(239,68,68,0.08); border-radius: 6px; }

    .login-submit { width: 100%; padding: 0.75rem;
        background: linear-gradient(135deg, #6366f1, #a78bfa);
        color: #fff; border: none; border-radius: 10px; font-size: 0.92rem;
        cursor: pointer; font-weight: 700; margin-top: 0.3rem; transition: all 0.25s;
        font-family: 'Inter', sans-serif; }
    .login-submit:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(99,102,241,0.3); }
    .login-submit:disabled { opacity: 0.5; cursor: default; transform: none; }

    .login-toggle { margin-top: 1.25rem; color: #64748b; font-size: 0.8rem; }
    .login-toggle a { color: #818cf8; cursor: pointer; text-decoration: none; font-weight: 600; }
    .login-toggle a:hover { text-decoration: underline; }

    .login-avatar { font-size: 3.5rem; margin-bottom: 0.5rem; }
    .login-username { color: #e2e8f0; font-size: 1.1rem; font-weight: 700; margin-top: 0.3rem; }
    .login-role { color: #64748b; font-size: 0.78rem; margin-bottom: 1.5rem; }

    .login-actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }

    .btn-logout { padding: 0.6rem 1.25rem; background: rgba(239,68,68,0.1); color: #f87171;
        border: 1px solid rgba(239,68,68,0.2); border-radius: 10px; cursor: pointer;
        font-size: 0.85rem; font-weight: 600; transition: all 0.25s; font-family: 'Inter', sans-serif; }
    .btn-logout:hover { background: rgba(239,68,68,0.2); }

    /* Password Change */
    .pw-change-section { margin-top: 1.5rem; padding-top: 1.5rem;
        border-top: 1px solid rgba(99,102,241,0.12); text-align: left; }
    .pw-change-section h3 { font-size: 0.95rem; color: #818cf8; margin-bottom: 0.75rem; text-align: center; }
    .pw-change-section input { width: 100%; padding: 0.6rem 0.8rem; background: rgba(22,22,48,0.6);
        border: 1px solid rgba(99,102,241,0.15); border-radius: 8px; color: #e2e8f0;
        font-size: 0.85rem; margin-bottom: 0.5rem; outline: none; transition: border-color 0.25s;
        font-family: 'Inter', sans-serif; box-sizing: border-box; }
    .pw-change-section input:focus { border-color: #6366f1; }
    .pw-change-section input::placeholder { color: #475569; }
    .pw-change-section .btn { width: 100%; margin-top: 0.3rem; padding: 0.6rem; font-size: 0.85rem; }
    .pw-msg { font-size: 0.8rem; padding: 0.5rem 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; text-align: center; }
    .pw-msg.success { background: rgba(52,211,153,0.1); color: #34d399; }
    .pw-msg.error { background: rgba(239,68,68,0.08); color: #f87171; }

    /* Responsive */
    @media (max-width: 768px) {
        .login-split { flex-direction: column; }
        .login-brand { padding: 2rem; border-right: none; border-bottom: 1px solid rgba(99,102,241,0.1); }
        .login-brand-icon { font-size: 2.5rem; }
        .login-brand h1 { font-size: 1.8rem; }
        .login-features-mini { flex-direction: row; flex-wrap: wrap; }
        .login-features-mini div { flex: 1 1 45%; }
        .login-stats-mini { gap: 1rem; }
        .login-form-area { padding: 2rem; }
        .login-actions { flex-direction: column; }
    }
`

export default LoginPage
