/**
 * GAIM Lab — 클라이언트 사이드 인증 모듈
 * 
 * GitHub Pages 환경에서 백엔드 없이 작동하는 로컬 인증 시스템
 * - SHA-256 기반 비밀번호 해싱
 * - localStorage 기반 세션/사용자 저장
 * - 서버 API와 동일한 인터페이스 제공
 */

const USERS_KEY = 'gaim_local_users'
const TOKEN_KEY = 'gaim_token'
const USER_KEY = 'gaim_user'

// ─── SHA-256 해싱 (Web Crypto API) ───

async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message)
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

// ─── 로컬 사용자 DB ───

function getUsers() {
    try {
        return JSON.parse(localStorage.getItem(USERS_KEY)) || {}
    } catch {
        return {}
    }
}

function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

// ─── 초기 관리자 계정 시드 ───

let _adminReady = null

async function ensureAdmin() {
    const users = getUsers()
    if (!users['admin']) {
        users['admin'] = {
            username: 'admin',
            name: '관리자',
            role: 'admin',
            password_hash: await sha256('admin1234'),
            created_at: new Date().toISOString(),
        }
        saveUsers(users)
    }
}

// 모듈 로드 시 admin 시드 — 프로미스 캐싱
_adminReady = ensureAdmin()

// ─── 가짜 JWT 토큰 생성 ───

function createLocalToken(user) {
    const payload = {
        sub: user.username,
        name: user.name,
        role: user.role,
        exp: Date.now() + 24 * 60 * 60 * 1000, // 24시간
    }
    // UTF-8 safe base64: 한글 등 비-Latin1 문자 지원
    const bytes = new TextEncoder().encode(JSON.stringify(payload))
    const binary = Array.from(bytes, b => String.fromCharCode(b)).join('')
    return btoa(binary)
}

// ─── 공개 API ───

/**
 * 로그인
 * @param {{ username: string, password: string }} body
 * @returns {Promise<{ access_token, username, name, role }>}
 */
export async function localLogin(body) {
    // admin 시드 완료 대기
    await _adminReady

    const { username, password } = body
    const users = getUsers()
    const user = users[username]

    if (!user) {
        throw new Error('아이디 또는 비밀번호가 올바르지 않습니다.')
    }

    const hash = await sha256(password)
    if (hash !== user.password_hash) {
        throw new Error('아이디 또는 비밀번호가 올바르지 않습니다.')
    }

    const token = createLocalToken(user)

    // last_login 업데이트
    user.last_login = new Date().toISOString()
    saveUsers(users)

    return {
        access_token: token,
        username: user.username,
        name: user.name,
        role: user.role,
    }
}

/**
 * 회원가입
 * @param {{ username: string, password: string, name: string, role?: string }} body
 * @returns {Promise<{ access_token, username, name, role }>}
 */
export async function localRegister(body) {
    const { username, password, name, role = 'student' } = body

    if (!username || username.length < 2) {
        throw new Error('아이디는 2자 이상이어야 합니다.')
    }
    if (!password || password.length < 4) {
        throw new Error('비밀번호는 4자 이상이어야 합니다.')
    }

    const users = getUsers()
    if (users[username]) {
        throw new Error('이미 존재하는 아이디입니다.')
    }

    const hash = await sha256(password)
    const newUser = {
        username,
        name: name || username,
        role,
        password_hash: hash,
        created_at: new Date().toISOString(),
        last_login: new Date().toISOString(),
    }
    users[username] = newUser
    saveUsers(users)

    const token = createLocalToken(newUser)

    return {
        access_token: token,
        username: newUser.username,
        name: newUser.name,
        role: newUser.role,
    }
}

/**
 * 비밀번호 변경
 * @param {{ current_password: string, new_password: string }} body
 * @param {string} currentUsername
 * @returns {Promise<{ message: string }>}
 */
export async function localChangePassword(body, currentUsername) {
    const { current_password, new_password } = body
    const users = getUsers()
    const user = users[currentUsername]

    if (!user) throw new Error('사용자를 찾을 수 없습니다.')

    const currentHash = await sha256(current_password)
    if (currentHash !== user.password_hash) {
        throw new Error('현재 비밀번호가 올바르지 않습니다.')
    }

    if (new_password.length < 4) {
        throw new Error('새 비밀번호는 4자 이상이어야 합니다.')
    }

    user.password_hash = await sha256(new_password)
    saveUsers(users)

    return { message: '비밀번호가 변경되었습니다.' }
}

/**
 * GitHub Pages 환경인지 확인
 */
export function isGitHubPages() {
    if (typeof window === 'undefined') return false
    return window.location.hostname.includes('github.io')
        || (typeof import.meta !== 'undefined' && import.meta.env?.GITHUB_PAGES === 'true')
}
