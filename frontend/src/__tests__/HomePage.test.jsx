import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import HomePage from '../pages/HomePage'

const renderHomePage = () => {
    return render(
        <BrowserRouter>
            <HomePage />
        </BrowserRouter>
    )
}

describe('HomePage 컴포넌트', () => {
    describe('히어로 섹션', () => {
        it('메인 타이틀이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/멀티 에이전트/)).toBeInTheDocument()
            expect(screen.getByText(/수업 분석 플랫폼/)).toBeInTheDocument()
        })

        it('수업 분석 시작 버튼이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/수업 분석 시작/)).toBeInTheDocument()
        })

        it('대시보드 보기 버튼이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/대시보드 보기/)).toBeInTheDocument()
        })

        it('통계 수치가 표시되어야 한다', () => {
            renderHomePage()
            // Use container queries for elements that appear multiple times
            const container = document.querySelector('.hero-stats')
            expect(container).toBeTruthy()
            expect(container.textContent).toContain('8')
            expect(container.textContent).toContain('18')
            expect(container.textContent).toContain('100%')
            expect(container.textContent).toContain('76.1')
        })
    })

    describe('파이프라인 섹션', () => {
        it('에이전트 파이프라인 제목이 표시되어야 한다', () => {
            renderHomePage()
            // Text appears in both h2 and p, use getAllByText
            expect(screen.getAllByText(/에이전트 파이프라인/).length).toBeGreaterThanOrEqual(1)
        })

        it('파이프라인 노드가 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText('Video')).toBeInTheDocument()
            expect(screen.getByText('Parallel')).toBeInTheDocument()
            expect(screen.getAllByText('Extractor').length).toBeGreaterThanOrEqual(1)
            expect(screen.getAllByText('Report').length).toBeGreaterThanOrEqual(1)
        })
    })

    describe('7차원 평가 프레임워크', () => {
        it('섹션 제목이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/7차원 평가 프레임워크/)).toBeInTheDocument()
        })

        it('7개 차원이 모두 표시되어야 한다', () => {
            renderHomePage()
            const dimensions = ['수업 전문성', '교수학습 방법', '판서 및 언어', '수업 태도', '학생 참여', '시간 배분', '창의성']
            dimensions.forEach(dim => {
                expect(screen.getByText(dim)).toBeInTheDocument()
            })
        })

        it('배점이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getAllByText('20점').length).toBeGreaterThanOrEqual(1)
            expect(screen.getByText('5점')).toBeInTheDocument()
        })
    })

    describe('8개 에이전트 섹션', () => {
        it('섹션 제목이 표시되어야 한다', () => {
            renderHomePage()
            // "8개 AI 에이전트" appears in both section header and hero desc
            expect(screen.getAllByText(/8개 AI 에이전트/).length).toBeGreaterThanOrEqual(1)
        })

        it('주요 에이전트가 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText('Vision')).toBeInTheDocument()
            expect(screen.getByText('STT')).toBeInTheDocument()
            expect(screen.getByText('Pedagogy v8')).toBeInTheDocument()
            // Master appears in both pipeline and agents section
            expect(screen.getAllByText('Master').length).toBeGreaterThanOrEqual(1)
        })
    })

    describe('기술 스택 섹션', () => {
        it('기술 스택 제목이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/기술 스택/)).toBeInTheDocument()
        })

        it('주요 기술이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText('AI/ML')).toBeInTheDocument()
            expect(screen.getByText('Backend')).toBeInTheDocument()
            expect(screen.getByText('Frontend')).toBeInTheDocument()
        })
    })

    describe('분석 결과 요약', () => {
        it('분석 결과 요약 제목이 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText(/분석 결과 요약/)).toBeInTheDocument()
        })

        it('주요 통계가 표시되어야 한다', () => {
            renderHomePage()
            expect(screen.getByText('18/18')).toBeInTheDocument()
            // "평균 점수" appears in both hero stats and results section
            expect(screen.getAllByText(/평균 점수/).length).toBeGreaterThanOrEqual(1)
        })
    })
})
