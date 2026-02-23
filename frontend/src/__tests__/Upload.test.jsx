import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Upload from '../pages/Upload'

// RealtimeFeedback 컴포넌트 모킹
vi.mock('../components/RealtimeFeedback', () => ({
    default: ({ analysisId, onComplete, onError }) => (
        <div data-testid="realtime-feedback">
            <span>분석 ID: {analysisId}</span>
            <button onClick={() => onComplete({ total_score: 85 })}>
                완료
            </button>
            <button onClick={() => onError('테스트 에러')}>
                에러
            </button>
        </div>
    )
}))

const renderUpload = () => {
    return render(
        <BrowserRouter>
            <Upload />
        </BrowserRouter>
    )
}

describe('Upload 컴포넌트', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('초기 렌더링', () => {
        it('페이지 제목이 표시되어야 한다', () => {
            renderUpload()
            expect(screen.getByText(/수업 분석/i)).toBeInTheDocument()
        })

        it('업로드 영역이 표시되어야 한다', () => {
            renderUpload()
            expect(screen.getByText(/클릭하거나 영상 파일을 드래그하세요/i)).toBeInTheDocument()
        })

        it('지원 포맷이 표시되어야 한다', () => {
            renderUpload()
            expect(screen.getByText(/MP4, AVI, MOV 지원/i)).toBeInTheDocument()
        })
    })

    describe('파일 선택', () => {
        it('파일 선택 시 파일 정보가 표시되어야 한다', async () => {
            renderUpload()

            const file = new File(['video content'], 'lecture.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            await waitFor(() => {
                expect(screen.getByText('lecture.mp4')).toBeInTheDocument()
            })
        })

        it('파일 선택 후 분석 시작 버튼이 표시되어야 한다', async () => {
            renderUpload()

            const file = new File(['video content'], 'lecture.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /분석 시작/i })).toBeInTheDocument()
            })
        })
    })

    describe('드래그 앤 드롭', () => {
        it('드래그 앤 드롭으로 파일 업로드가 가능해야 한다', async () => {
            renderUpload()

            const file = new File(['video content'], 'dropped-video.mp4', { type: 'video/mp4' })
            const dropZone = screen.getByText(/클릭하거나 영상 파일을 드래그하세요/i).parentElement

            fireEvent.drop(dropZone, {
                dataTransfer: {
                    files: [file]
                }
            })

            await waitFor(() => {
                expect(screen.getByText('dropped-video.mp4')).toBeInTheDocument()
            })
        })
    })

    describe('업로드 및 분석', () => {
        it('분석 시작 클릭 시 API 호출이 발생해야 한다', async () => {
            global.fetch = vi.fn().mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ id: 'analysis-123', status: 'processing' })
            })

            renderUpload()

            const file = new File(['video'], 'lecture.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            const button = screen.getByRole('button', { name: /분석 시작/i })
            fireEvent.click(button)

            await waitFor(() => {
                expect(global.fetch).toHaveBeenCalledWith(
                    expect.stringContaining('/api/v1/analysis/upload'),
                    expect.any(Object)
                )
            })
        })

        it('업로드 성공 시 진행 UI가 표시되어야 한다', async () => {
            global.fetch = vi.fn().mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    id: 'analysis-123',
                    status: 'completed',
                    total_score: 85,
                    grade: 'B',
                    dimensions: [{ name: '수업 전문성', score: 16, max_score: 20, percentage: 80, feedback: '' }],
                    overall_feedback: '전반적으로 잘함'
                })
            })

            renderUpload()

            const file = new File(['video'], 'lecture.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            const button = screen.getByRole('button', { name: /분석 시작/i })
            fireEvent.click(button)

            await waitFor(() => {
                expect(screen.getByText('85')).toBeInTheDocument()
            })
        })
    })

    describe('분석 결과', () => {
        it('분석 완료 시 결과가 표시되어야 한다', async () => {
            global.fetch = vi.fn()
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({
                        id: 'analysis-123',
                        status: 'completed',
                        total_score: 85,
                        grade: 'B',
                        dimensions: [
                            { name: '수업 전문성', score: 16, max_score: 20, percentage: 80, feedback: '' },
                        ],
                        overall_feedback: '잘했습니다'
                    })
                })

            renderUpload()

            const file = new File(['video'], 'lecture.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            const button = screen.getByRole('button', { name: /분석 시작/i })
            fireEvent.click(button)

            await waitFor(() => {
                expect(screen.getByText('85')).toBeInTheDocument()
            })
        })
    })

    describe('파일 크기 포맷팅', () => {
        it('파일 크기가 올바르게 표시되어야 한다', async () => {
            renderUpload()

            const content = new Array(1024 * 1024).fill('a').join('')
            const file = new File([content], 'large-video.mp4', { type: 'video/mp4' })
            const input = document.querySelector('input[type="file"]')

            await userEvent.upload(input, file)

            await waitFor(() => {
                expect(screen.getByText(/MB/i)).toBeInTheDocument()
            })
        })
    })
})
