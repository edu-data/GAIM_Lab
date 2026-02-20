import { useState, useEffect } from 'react'

const API_BASE = '/api/v1/auth'

function LoginPage() {
    const [mode, setMode] = useState('login')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [error, setError] = useState(null)
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        // Check for Google OAuth callback token
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
            // Check stored token
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
            localStorage.setItem('gaim_user', JSON.stringify({ username: data.username, role: data.role }))
            setUser({ username: data.username, role: data.role })
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

    if (user) {
        return (
            <div className="login-page">
                <div className="login-card">
                    <div className="login-avatar">👤</div>
                    <h2>환영합니다!</h2>
                    <p className="login-username">{user.name || user.username}</p>
                    <p className="login-role">{user.role || 'user'}</p>
                    <button className="login-logout-btn" onClick={handleLogout}>로그아웃</button>
                </div>
                <style>{styles}</style>
            </div>
        )
    }

    return (
        <div className="login-page">
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
            <style>{styles}</style>
        </div>
    )
}

const styles = `
  .login-page { display: flex; justify-content: center; align-items: center; min-height: 70vh; }
  .login-card { background: rgba(26,26,46,0.9); border-radius: 16px; padding: 2rem;
    width: 100%; max-width: 400px; border: 1px solid rgba(108,99,255,0.2); text-align: center; }
  .login-card h2 { font-size: 1.5rem; margin-bottom: 0.3rem;
    background: linear-gradient(135deg, #6c63ff, #00d2ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .login-subtitle { color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }
  .google-btn { width: 100%; padding: 0.75rem; background: #fff; color: #333; border: none;
    border-radius: 10px; font-size: 0.9rem; cursor: pointer; display: flex;
    align-items: center; justify-content: center; gap: 0.6rem; font-weight: 500; }
  .google-btn:hover { background: #f5f5f5; }
  .login-divider { display: flex; align-items: center; margin: 1.2rem 0; color: #555; font-size: 0.8rem; }
  .login-divider::before, .login-divider::after { content: ''; flex: 1; border-bottom: 1px solid #333; }
  .login-divider span { padding: 0 0.8rem; }
  .login-input { width: 100%; padding: 0.7rem 0.9rem; background: rgba(0,0,0,0.3);
    border: 1px solid rgba(108,99,255,0.2); border-radius: 8px; color: #e0e0ec;
    font-size: 0.9rem; margin-bottom: 0.6rem; }
  .login-input:focus { outline: none; border-color: #6c63ff; }
  .login-error { color: #ff5252; font-size: 0.82rem; margin-bottom: 0.5rem; }
  .login-submit { width: 100%; padding: 0.75rem; background: linear-gradient(135deg, #6c63ff, #00d2ff);
    color: #fff; border: none; border-radius: 10px; font-size: 0.95rem;
    cursor: pointer; font-weight: 600; margin-top: 0.3rem; }
  .login-submit:disabled { opacity: 0.5; }
  .login-toggle { margin-top: 1rem; color: #888; font-size: 0.82rem; }
  .login-toggle a { color: #6c63ff; cursor: pointer; text-decoration: underline; }
  .login-avatar { font-size: 3rem; margin-bottom: 0.5rem; }
  .login-username { color: #fff; font-size: 1.1rem; font-weight: 600; }
  .login-role { color: #888; font-size: 0.8rem; margin-bottom: 1rem; }
  .login-logout-btn { padding: 0.6rem 1.5rem; background: rgba(255,82,82,0.15); color: #ff5252;
    border: 1px solid #ff5252; border-radius: 8px; cursor: pointer; }
`

export default LoginPage
