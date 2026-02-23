import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// Mock the imports that AgentMonitor depends on
vi.mock('../hooks/useAsyncTask', () => ({
    useAsyncTask: () => ({
        runTask: async ({ }, fn) => fn(),
        cancel: vi.fn(),
        isRunning: false,
    })
}))

vi.mock('../components/AgentCard', () => ({
    default: ({ agent }) => (
        <div data-testid={`agent-${agent.name}`}>
            {agent.icon} {agent.name} ({agent.status})
        </div>
    )
}))

vi.mock('../components/AgentTimeline', () => ({
    default: ({ agents }) => (
        <div data-testid="agent-timeline">
            Timeline ({Object.keys(agents).length} agents)
        </div>
    )
}))

vi.mock('../utils/videoAnalyzer', () => ({
    extractResources: vi.fn(),
    analyzeVision: vi.fn(),
    analyzeContent: vi.fn(),
    analyzeSTT: vi.fn(),
    analyzeVibe: vi.fn(),
    evaluatePedagogy: vi.fn(),
    generateFeedback: vi.fn(),
    generateReport: vi.fn(),
}))

// Dynamically import after mocks
const { default: AgentMonitor } = await import('../pages/AgentMonitor')

const renderAgentMonitor = () => {
    return render(
        <BrowserRouter>
            <AgentMonitor />
        </BrowserRouter>
    )
}

describe('AgentMonitor 컴포넌트', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('초기 렌더링', () => {
        it('모니터 제목이 표시되어야 한다', () => {
            renderAgentMonitor()
            expect(screen.getByText(/멀티 에이전트 모니터/)).toBeInTheDocument()
        })

        it('동영상 업로드 안내가 표시되어야 한다', () => {
            renderAgentMonitor()
            expect(screen.getByText(/클릭하거나 동영상을 드래그하세요/)).toBeInTheDocument()
        })

        it('파이프라인 타임라인이 표시되어야 한다', () => {
            renderAgentMonitor()
            expect(screen.getByTestId('agent-timeline')).toBeInTheDocument()
        })

        it('8개 에이전트 카드가 모두 표시되어야 한다', () => {
            renderAgentMonitor()
            const agentNames = ['extractor', 'vision', 'content', 'stt', 'vibe', 'pedagogy', 'feedback', 'master']
            agentNames.forEach(name => {
                expect(screen.getByTestId(`agent-${name}`)).toBeInTheDocument()
            })
        })
    })

    describe('업로드 영역', () => {
        it('파일 형식 안내가 표시되어야 한다', () => {
            renderAgentMonitor()
            expect(screen.getByText(/MP4, AVI, WebM 지원/)).toBeInTheDocument()
        })

        it('숨겨진 file input이 존재해야 한다', () => {
            renderAgentMonitor()
            const input = document.querySelector('input[type="file"]')
            expect(input).toBeTruthy()
            expect(input.accept).toBe('video/*')
        })
    })

    describe('초기 상태', () => {
        it('분석 시작 전에는 분석 시작 버튼이 없어야 한다', () => {
            renderAgentMonitor()
            expect(screen.queryByText('🚀 분석 시작')).not.toBeInTheDocument()
        })

        it('초기 상태에서 에이전트는 idle 상태여야 한다', () => {
            renderAgentMonitor()
            const agentCards = screen.getAllByText(/idle/)
            expect(agentCards.length).toBe(8)
        })
    })
})
