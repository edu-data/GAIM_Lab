import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorBoundary from '../components/ErrorBoundary'

// 에러를 발생시키는 테스트용 컴포넌트
function BrokenComponent() {
    throw new Error('테스트 에러 발생')
}

function GoodComponent() {
    return <div>정상 콘텐츠</div>
}

describe('ErrorBoundary 컴포넌트', () => {
    // suppress console.error for expected errors
    const originalError = console.error
    beforeEach(() => {
        console.error = vi.fn()
    })
    afterEach(() => {
        console.error = originalError
    })

    it('정상적인 자식 컴포넌트를 렌더링해야 한다', () => {
        render(
            <ErrorBoundary>
                <GoodComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText('정상 콘텐츠')).toBeInTheDocument()
    })

    it('에러 발생 시 fallback UI를 표시해야 한다', () => {
        render(
            <ErrorBoundary>
                <BrokenComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText('문제가 발생했습니다')).toBeInTheDocument()
    })

    it('에러 발생 시 에러 메시지를 표시해야 한다', () => {
        render(
            <ErrorBoundary>
                <BrokenComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText('테스트 에러 발생')).toBeInTheDocument()
    })

    it('다시 시도 버튼이 표시되어야 한다', () => {
        render(
            <ErrorBoundary>
                <BrokenComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText(/다시 시도/)).toBeInTheDocument()
    })

    it('홈으로 버튼이 표시되어야 한다', () => {
        render(
            <ErrorBoundary>
                <BrokenComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText(/홈으로/)).toBeInTheDocument()
    })

    it('다시 시도 클릭 시 에러 상태가 초기화되어야 한다', () => {
        let shouldThrow = true
        function MaybeErrorComponent() {
            if (shouldThrow) throw new Error('일시적 에러')
            return <div>복구됨</div>
        }

        render(
            <ErrorBoundary>
                <MaybeErrorComponent />
            </ErrorBoundary>
        )
        expect(screen.getByText('문제가 발생했습니다')).toBeInTheDocument()

        // 다시 시도 시 shouldThrow를 false로 전환
        shouldThrow = false
        const retryBtn = screen.getByText(/다시 시도/)
        fireEvent.click(retryBtn)

        // 에러 boundary가 리셋되어 정상 콘텐츠를 렌더링해야 함
        expect(screen.getByText('복구됨')).toBeInTheDocument()
    })
})
