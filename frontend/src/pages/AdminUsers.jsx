import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AUTH_BASE } from '../apiConfig'
import './AdminUsers.css'

const API = AUTH_BASE

function AdminUsers() {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showCreate, setShowCreate] = useState(false)
    const [newUser, setNewUser] = useState({ username: '', password: '', name: '', role: 'student', email: '' })
    const [resetPw, setResetPw] = useState({ username: null, password: '' })
    const [msg, setMsg] = useState(null)
    const navigate = useNavigate()

    const token = localStorage.getItem('gaim_token')
    const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API}/users`, { headers })
            if (res.status === 401 || res.status === 403) {
                navigate('/login')
                return
            }
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            setUsers(await res.json())
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchUsers() }, [])

    const flash = (m) => { setMsg(m); setTimeout(() => setMsg(null), 3000) }

    const handleCreate = async (e) => {
        e.preventDefault()
        try {
            const res = await fetch(`${API}/users`, {
                method: 'POST', headers, body: JSON.stringify(newUser)
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail)
            flash(`✅ ${data.message}`)
            setShowCreate(false)
            setNewUser({ username: '', password: '', name: '', role: 'student', email: '' })
            fetchUsers()
        } catch (e) { flash(`❌ ${e.message}`) }
    }

    const handleUpdate = async (username, field, value) => {
        try {
            const res = await fetch(`${API}/users/${username}`, {
                method: 'PUT', headers, body: JSON.stringify({ [field]: value })
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail)
            flash(`✅ ${data.message}`)
            fetchUsers()
        } catch (e) { flash(`❌ ${e.message}`) }
    }

    const handleDelete = async (username) => {
        if (!confirm(`정말 '${username}' 사용자를 삭제하시겠습니까?`)) return
        try {
            const res = await fetch(`${API}/users/${username}`, { method: 'DELETE', headers })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail)
            flash(`✅ ${data.message}`)
            fetchUsers()
        } catch (e) { flash(`❌ ${e.message}`) }
    }

    const handleResetPassword = async (e) => {
        e.preventDefault()
        try {
            const res = await fetch(`${API}/users/${resetPw.username}/reset-password`, {
                method: 'POST', headers,
                body: JSON.stringify({ new_password: resetPw.password })
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail)
            flash(`✅ ${data.message}`)
            setResetPw({ username: null, password: '' })
        } catch (e) { flash(`❌ ${e.message}`) }
    }

    const roleLabel = { admin: '👑 관리자', teacher: '👨‍🏫 교사', student: '🎓 학생' }
    const roleColor = { admin: '#f59e0b', teacher: '#818cf8', student: '#34d399' }

    if (loading) return <div className="admin-page"><div className="admin-loading">로딩 중...</div></div>
    if (error) return <div className="admin-page"><div className="admin-error">⚠️ {error}</div></div>

    return (
        <div className="admin-page">
            <div className="admin-header">
                <h1 className="page-title"><span>👑</span> 사용자 관리</h1>
                <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
                    {showCreate ? '✕ 닫기' : '➕ 새 사용자'}
                </button>
            </div>

            {msg && <div className="admin-flash">{msg}</div>}

            {/* Create User Form */}
            {showCreate && (
                <div className="admin-card create-card fade-in-up">
                    <h3>새 사용자 추가</h3>
                    <form onSubmit={handleCreate} className="create-form">
                        <input placeholder="아이디 *" required value={newUser.username}
                            onChange={e => setNewUser({ ...newUser, username: e.target.value })} />
                        <input placeholder="비밀번호 *" type="password" required value={newUser.password}
                            onChange={e => setNewUser({ ...newUser, password: e.target.value })} />
                        <input placeholder="이름" value={newUser.name}
                            onChange={e => setNewUser({ ...newUser, name: e.target.value })} />
                        <input placeholder="이메일" type="email" value={newUser.email}
                            onChange={e => setNewUser({ ...newUser, email: e.target.value })} />
                        <select value={newUser.role}
                            onChange={e => setNewUser({ ...newUser, role: e.target.value })}>
                            <option value="student">🎓 학생</option>
                            <option value="teacher">👨‍🏫 교사</option>
                            <option value="admin">👑 관리자</option>
                        </select>
                        <button type="submit" className="btn btn-primary">생성</button>
                    </form>
                </div>
            )}

            {/* Password Reset Modal */}
            {resetPw.username && (
                <div className="modal-overlay" onClick={() => setResetPw({ username: null, password: '' })}>
                    <div className="modal-card" onClick={e => e.stopPropagation()}>
                        <h3>🔑 비밀번호 초기화</h3>
                        <p>사용자: <strong>{resetPw.username}</strong></p>
                        <form onSubmit={handleResetPassword}>
                            <input placeholder="새 비밀번호" type="password" required value={resetPw.password}
                                onChange={e => setResetPw({ ...resetPw, password: e.target.value })} />
                            <div className="modal-actions">
                                <button type="button" className="btn-cancel"
                                    onClick={() => setResetPw({ username: null, password: '' })}>취소</button>
                                <button type="submit" className="btn btn-primary">초기화</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* User Stats */}
            <div className="admin-stats">
                <div className="stat-mini">
                    <span className="stat-num">{users.length}</span>
                    <span className="stat-label">전체 사용자</span>
                </div>
                <div className="stat-mini">
                    <span className="stat-num">{users.filter(u => u.is_active).length}</span>
                    <span className="stat-label">활성 계정</span>
                </div>
                <div className="stat-mini">
                    <span className="stat-num">{users.filter(u => u.role === 'admin').length}</span>
                    <span className="stat-label">관리자</span>
                </div>
                <div className="stat-mini">
                    <span className="stat-num">{users.filter(u => u.role === 'teacher').length}</span>
                    <span className="stat-label">교사</span>
                </div>
            </div>

            {/* Users Table */}
            <div className="admin-card">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>아이디</th>
                            <th>이름</th>
                            <th>이메일</th>
                            <th>역할</th>
                            <th>상태</th>
                            <th>가입일</th>
                            <th>최근 로그인</th>
                            <th>관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.username} className={!u.is_active ? 'inactive-row' : ''}>
                                <td>{u.id}</td>
                                <td className="username-cell">
                                    {u.provider === 'google' && <span className="provider-badge">G</span>}
                                    {u.username}
                                </td>
                                <td>{u.name}</td>
                                <td>{u.email || '-'}</td>
                                <td>
                                    <select className="role-select"
                                        style={{ color: roleColor[u.role] }}
                                        value={u.role}
                                        onChange={e => handleUpdate(u.username, 'role', e.target.value)}>
                                        <option value="student">🎓 학생</option>
                                        <option value="teacher">👨‍🏫 교사</option>
                                        <option value="admin">👑 관리자</option>
                                    </select>
                                </td>
                                <td>
                                    <button
                                        className={`status-toggle ${u.is_active ? 'active' : 'inactive'}`}
                                        onClick={() => handleUpdate(u.username, 'is_active', !u.is_active)}>
                                        {u.is_active ? '✅ 활성' : '⛔ 비활성'}
                                    </button>
                                </td>
                                <td className="date-cell">{u.created_at?.slice(0, 10) || '-'}</td>
                                <td className="date-cell">{u.last_login?.slice(0, 16)?.replace('T', ' ') || '-'}</td>
                                <td className="action-cell">
                                    <button className="btn-sm btn-reset" title="비밀번호 초기화"
                                        onClick={() => setResetPw({ username: u.username, password: '' })}>🔑</button>
                                    <button className="btn-sm btn-delete" title="삭제"
                                        onClick={() => handleDelete(u.username)}>🗑️</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default AdminUsers
