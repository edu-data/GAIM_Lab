/**
 * GAIM Lab v8.0 — 중앙 API 클라이언트
 * 
 * 에러 #2 방지: 모든 API 호출은 이 모듈을 통해 수행
 * - baseURL 자동 감지 (로컬 dev proxy / Cloud Run)
 * - 인증 토큰 자동 첨부
 * - 에러 핸들링 (401 → 로그인 리다이렉트, 5xx → 알림)
 */

import { API_BASE, AUTH_BASE, API_HOST } from '../apiConfig'

/**
 * @typedef {Object} ApiOptions
 * @property {Object} [headers] - 추가 헤더
 * @property {string} [contentType] - Content-Type (기본: application/json)
 * @property {boolean} [auth] - 인증 토큰 첨부 여부 (기본: true)
 * @property {boolean} [raw] - true면 Response 객체 반환 (기본: false → JSON 파싱)
 */

/**
 * 인증 토큰 가져오기
 */
function getAuthToken() {
    try {
        const user = JSON.parse(localStorage.getItem('gaim_user'))
        return user?.token || localStorage.getItem('gaim_token') || null
    } catch {
        return null
    }
}

/**
 * 에러 처리
 */
async function handleError(response) {
    if (response.status === 401) {
        // 인증 만료 → 로그인 페이지로
        localStorage.removeItem('gaim_user')
        localStorage.removeItem('gaim_token')
        if (window.location.hash !== '#/login') {
            window.location.hash = '#/login'
        }
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.')
    }

    let detail = `HTTP ${response.status}`
    try {
        const body = await response.json()
        detail = body.detail || body.message || detail
    } catch { /* ignore */ }

    throw new Error(detail)
}

/**
 * 범용 fetch 래퍼
 */
async function request(url, method = 'GET', body = null, options = {}) {
    const { auth = true, raw = false, contentType, headers: extraHeaders = {} } = options

    const headers = { ...extraHeaders }

    // 인증 토큰 자동 첨부
    if (auth) {
        const token = getAuthToken()
        if (token) headers['Authorization'] = `Bearer ${token}`
    }

    // Content-Type (FormData는 자동 설정)
    if (body && !(body instanceof FormData)) {
        headers['Content-Type'] = contentType || 'application/json'
    }

    const fetchOptions = { method, headers }
    if (body) {
        fetchOptions.body = body instanceof FormData ? body : JSON.stringify(body)
    }

    const response = await fetch(url, fetchOptions)

    if (!response.ok) {
        await handleError(response)
    }

    if (raw) return response
    return response.json()
}

/**
 * API 클라이언트
 */
const api = {
    // === 일반 API (API_BASE = /api/v1) ===
    get: (path, options) => request(`${API_BASE}${path}`, 'GET', null, options),
    post: (path, body, options) => request(`${API_BASE}${path}`, 'POST', body, options),
    put: (path, body, options) => request(`${API_BASE}${path}`, 'PUT', body, options),
    delete: (path, options) => request(`${API_BASE}${path}`, 'DELETE', null, options),

    // === 인증 API (AUTH_BASE = /api/v1/auth) ===
    auth: {
        login: (body) => request(`${AUTH_BASE}/login`, 'POST', body, { auth: false }),
        register: (body) => request(`${AUTH_BASE}/register`, 'POST', body, { auth: false }),
        me: () => request(`${AUTH_BASE}/me`, 'GET'),
        changePassword: (body) => request(`${AUTH_BASE}/me/password`, 'PUT', body),
        listUsers: () => request(`${AUTH_BASE}/users`, 'GET'),
        createUser: (body) => request(`${AUTH_BASE}/users`, 'POST', body),
        updateUser: (username, body) => request(`${AUTH_BASE}/users/${username}`, 'PUT', body),
        deleteUser: (username) => request(`${AUTH_BASE}/users/${username}`, 'DELETE'),
        resetPassword: (username, body) => request(`${AUTH_BASE}/users/${username}/reset-password`, 'POST', body),
    },

    // === 분석 API ===
    analysis: {
        upload: (formData) => request(`${API_BASE}/analysis/upload`, 'POST', formData),
        status: (id) => request(`${API_BASE}/analysis/${id}`, 'GET'),
        result: (id) => request(`${API_BASE}/analysis/${id}/result`, 'GET'),
    },

    // === WebSocket URL 생성 ===
    wsUrl: (path) => {
        const wsBase = API_HOST
            ? API_HOST.replace(/^https?:\/\//, (m) => m.startsWith('https') ? 'wss://' : 'ws://')
            : `ws://${window.location.host}`
        return `${wsBase}/api/v1${path}`
    },

    // === 유틸리티 ===
    getBaseUrl: () => API_BASE,
    getHostUrl: () => API_HOST,
}

export default api
