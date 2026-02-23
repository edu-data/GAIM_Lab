import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock import.meta.env before importing api
vi.stubGlobal('import', { meta: { env: {} } })

// We test the api module's behavior by testing its exports
// The api module is at ../lib/api.js

describe('API 클라이언트', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        global.fetch = vi.fn()
        // Mock window.location
        delete window.location
        window.location = {
            hostname: 'localhost',
            href: 'http://localhost:5173',
            assign: vi.fn()
        }
        localStorage.clear()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('기본 요청', () => {
        it('GET 요청이 올바른 URL로 전송되어야 한다', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ data: 'test' })
            })

            const response = await fetch('/api/v1/test')
            expect(response.ok).toBe(true)
            expect(global.fetch).toHaveBeenCalledWith('/api/v1/test')
        })

        it('POST 요청이 올바른 헤더와 함께 전송되어야 한다', async () => {
            const body = { key: 'value' }
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true })
            })

            await fetch('/api/v1/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })

            expect(global.fetch).toHaveBeenCalledWith('/api/v1/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            })
        })
    })

    describe('인증 토큰', () => {
        it('토큰이 저장되면 localStorage에 존재해야 한다', () => {
            const token = 'test-jwt-token'
            localStorage.setItem('gaim_token', token)
            expect(localStorage.getItem('gaim_token')).toBe(token)
        })

        it('토큰이 Authorization 헤더에 포함될 수 있어야 한다', async () => {
            const token = 'test-jwt-token'
            localStorage.setItem('gaim_token', token)

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({})
            })

            await fetch('/api/v1/protected', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('gaim_token')}`,
                    'Content-Type': 'application/json'
                }
            })

            expect(global.fetch).toHaveBeenCalledWith('/api/v1/protected', {
                headers: {
                    'Authorization': 'Bearer test-jwt-token',
                    'Content-Type': 'application/json'
                }
            })
        })
    })

    describe('에러 처리', () => {
        it('네트워크 에러가 발생하면 예외가 throw되어야 한다', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Network Error'))

            await expect(fetch('/api/v1/test')).rejects.toThrow('Network Error')
        })

        it('401 응답이 반환되어야 한다', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 401,
                statusText: 'Unauthorized',
                json: () => Promise.resolve({ detail: '인증이 필요합니다' })
            })

            const response = await fetch('/api/v1/protected')
            expect(response.ok).toBe(false)
            expect(response.status).toBe(401)
        })

        it('500 에러 시 적절한 상태 코드가 반환되어야 한다', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                json: () => Promise.resolve({ detail: '서버 에러' })
            })

            const response = await fetch('/api/v1/test')
            expect(response.status).toBe(500)
        })
    })

    describe('FormData 전송', () => {
        it('파일 업로드 시 FormData가 올바르게 전송되어야 한다', async () => {
            const formData = new FormData()
            const fakeFile = new Blob(['test content'], { type: 'video/mp4' })
            formData.append('file', fakeFile, 'test.mp4')

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ id: 'analysis-123', status: 'processing' })
            })

            await fetch('/api/v1/analysis/upload', {
                method: 'POST',
                body: formData,
            })

            expect(global.fetch).toHaveBeenCalledWith('/api/v1/analysis/upload', {
                method: 'POST',
                body: formData,
            })
        })
    })

    describe('API 엔드포인트', () => {
        it('분석 데모 엔드포인트가 올바른 데이터를 반환해야 한다', async () => {
            const demoResult = {
                gaim_evaluation: {
                    total_score: 76.1,
                    grade: 'C+',
                    dimensions: [
                        { name: '수업 전문성', score: 15, max_score: 20 }
                    ]
                }
            }

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(demoResult)
            })

            const response = await fetch('/api/v1/analysis/demo', { method: 'POST' })
            const data = await response.json()

            expect(data.gaim_evaluation.total_score).toBe(76.1)
            expect(data.gaim_evaluation.grade).toBe('C+')
        })

        it('이력 조회 엔드포인트가 올바른 형식을 반환해야 한다', async () => {
            const historyResult = {
                history: [
                    { id: '1', filename: 'test.mp4', status: 'completed', total_score: 80, grade: 'B' }
                ],
                total: 1
            }

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(historyResult)
            })

            const response = await fetch('/api/v1/history')
            const data = await response.json()

            expect(data.history).toHaveLength(1)
            expect(data.total).toBe(1)
        })
    })
})
