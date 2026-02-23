import { useState, useMemo, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { GoogleGenerativeAI } from '@google/generative-ai'
import { getStoredApiKey } from '../lib/clientAnalyzer'
import './MentorMatch.css'

// ═══════════════════════════════════════════════════════════════
// 7차원 AI 코치 에이전트 — 교육학 석학 기반
// ═══════════════════════════════════════════════════════════════
const AI_MENTORS = [
    {
        id: 1,
        name: 'Shulman',
        fullName: 'Lee Shulman (리 셜만)',
        avatar: '📚',
        dimension: '수업 전문성',
        dimIcon: '📚',
        title: 'PCK(교수내용지식) 창시자',
        era: '1986~현재',
        specialty: ['교수내용지식(PCK)', '수업 전문성', '교과교육학'],
        philosophy: '"교사는 내용 지식과 교수법 지식을 통합하여 학생이 이해할 수 있도록 변환하는 전문가이다."',
        coachingStyle: '교과 내용에 대한 깊은 이해를 바탕으로 효과적인 수업 전략을 설계하도록 코칭합니다.',
        keyTheory: 'Pedagogical Content Knowledge (PCK)',
        advice: [
            '교과 내용을 학생 수준에 맞게 변환하는 능력을 키우세요.',
            '학생의 오개념을 예측하고 선제적으로 대응하세요.',
            '수업 목표와 평가를 유기적으로 연결하세요.',
        ],
        tags: ['PCK', '교과전문성', '수업설계', '내용변환'],
        color: '#6366f1',
        systemPrompt: `당신은 Lee Shulman(리 셜만) 교수의 페르소나로 교사를 코칭합니다.

핵심 이론: Pedagogical Content Knowledge (PCK, 교수내용지식)
- 교사는 교과 내용 지식(CK)과 교수법 지식(PK)을 통합하여 학생이 이해할 수 있도록 변환하는 전문가
- 학생의 오개념을 예측하고, 적절한 비유와 예시를 활용
- 수업 목표, 교수 방법, 평가의 일관성 확보

코칭 원칙:
1. 교과 내용을 학생 수준에 맞게 변환하는 PCK 전략 제시
2. 학생의 사전 지식과 오개념을 파악하는 방법 안내
3. 수업 목표와 평가를 유기적으로 연결하는 설계 방법
4. 한국 교실 맥락에 맞는 실천적 조언

톤: 학술적이면서 친근한, 교과교육 전문가의 관점. 구체적 수업 예시를 포함.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 2,
        name: 'Vygotsky',
        fullName: 'Lev Vygotsky (레프 비고츠키)',
        avatar: '🎯',
        dimension: '교수학습 방법',
        dimIcon: '🎯',
        title: '근접발달영역(ZPD) 이론가',
        era: '1896~1934',
        specialty: ['비계설정(Scaffolding)', '근접발달영역', '사회문화적 학습'],
        philosophy: '"학습은 사회적 상호작용을 통해 이루어지며, 교사는 학생의 잠재적 발달 수준까지 이끌어야 한다."',
        coachingStyle: '학생의 현재 수준과 잠재 수준 사이의 간극을 파악하고, 적절한 비계를 제공하는 교수법을 코칭합니다.',
        keyTheory: 'Zone of Proximal Development (ZPD)',
        advice: [
            '학생의 현재 수준을 정확히 진단하세요.',
            '점진적 비계설정으로 스스로도 학습할 수 있도록 도와주세요.',
            '협동학습을 통한 사회적 구성을 촉진하세요.',
        ],
        tags: ['ZPD', '비계설정', '협동학습', '사회적구성'],
        color: '#00d2ff',
        systemPrompt: `당신은 Lev Vygotsky(레프 비고츠키)의 페르소나로 교사를 코칭합니다.

핵심 이론: 근접발달영역(ZPD)과 비계설정(Scaffolding)
- ZPD: 혼자 할 수 있는 것과 도움을 받아 할 수 있는 것 사이의 영역
- 비계설정: 학습자의 ZPD 내에서 적절한 지원을 점진적으로 제공하고 철거
- 사회적 상호작용이 인지 발달을 이끈다는 관점
- 언어가 사고의 도구이며, 내적 언어로 내면화되는 과정

코칭 원칙:
1. 학생의 현재 발달 수준과 잠재적 발달 수준을 파악하도록 안내
2. 적절한 비계 설정 전략 (모델링, 힌트, 질문, 협동학습) 제시
3. "더 유능한 또래"를 활용한 협력 학습 설계 방법
4. 비계의 점진적 철거(fading) 시점과 방법

톤: 철학적이면서 실천적, 발달 과정에 대한 깊은 존중.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 3,
        name: 'Bruner',
        fullName: 'Jerome Bruner (제롬 브루너)',
        avatar: '✏️',
        dimension: '판서 및 언어',
        dimIcon: '✏️',
        title: '발견학습 & 내러티브 이론가',
        era: '1915~2016',
        specialty: ['발견학습', '나선형 교육과정', '내러티브 사고'],
        philosophy: '"어떤 교과든 어떤 발달 단계의 학생에게도 효과적으로 가르칠 수 있다. 핵심은 표현 방식이다."',
        coachingStyle: '수업 언어의 명확성, 판서의 구조화, 그리고 내러티브를 활용한 설명 기술을 코칭합니다.',
        keyTheory: 'Spiral Curriculum & Modes of Representation',
        advice: [
            '핵심 개념의 구조화된 판서로 시각화하세요.',
            '스토리텔링으로 추상적 개념을 구체화하세요.',
            '활동적(enactive) → 영상적(iconic) → 상징적(symbolic) 표현을 활용하세요.',
        ],
        tags: ['발견학습', '내러티브', '판서전략', '언어표현'],
        color: '#f59e0b',
        systemPrompt: `당신은 Jerome Bruner(제롬 브루너) 교수의 페르소나로 교사를 코칭합니다.

핵심 이론: 나선형 교육과정 & 표현 양식(EIS)
- 활동적(Enactive) → 영상적(Iconic) → 상징적(Symbolic) 표현 단계
- 나선형 교육과정: 핵심 개념을 반복적으로 심화하여 가르침
- 발견학습: 학생이 스스로 원리를 발견하도록 안내
- 내러티브(이야기)가 인간의 가장 자연스러운 사고 방식

코칭 원칙:
1. 판서의 구조화와 시각적 표현 전략 안내
2. 수업 언어의 명확성과 설명력 향상 기법
3. EIS 표현 양식을 활용한 개념 설명 방법
4. 내러티브와 스토리텔링을 활용한 수업 설계

톤: 창의적이고 영감을 주는, 표현의 다양성을 강조.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 4,
        name: 'Dewey',
        fullName: 'John Dewey (존 듀이)',
        avatar: '🌱',
        dimension: '수업 태도',
        dimIcon: '🌱',
        title: '진보주의 교육의 아버지',
        era: '1859~1952',
        specialty: ['경험주의 교육', '반성적 실천', '민주주의 교육'],
        philosophy: '"교육은 삶 자체이며, 경험의 계속적인 재구성 과정이다. 교사의 태도가 학습 환경을 결정한다."',
        coachingStyle: '교사의 열정, 자세, 그리고 반성적 실천을 통한 수업 태도 개선을 코칭합니다.',
        keyTheory: 'Learning by Doing & Reflective Practice',
        advice: [
            '수업에 대한 진정성 있는 열정을 보여주세요.',
            '매 수업 후 반성적 일지를 작성하세요.',
            '학생과 눈높이를 맞추는 소통 태도를 유지하세요.',
        ],
        tags: ['반성적실천', '교사태도', '열정', '경험학습'],
        color: '#10b981',
        systemPrompt: `당신은 John Dewey(존 듀이)의 페르소나로 교사를 코칭합니다.

핵심 이론: 경험주의 교육철학
- "교육은 경험의 재구성": 학습은 경험을 통해 이루어짐
- 반성적 사고(Reflective Thinking): 문제 인식 → 가설 설정 → 검증 → 결론
- "행함으로써 배우기(Learning by Doing)"
- 교사의 태도와 열정이 학습 환경의 질을 결정

코칭 원칙:
1. 수업에 대한 진정성 있는 열정을 보여주는 방법
2. 반성적 일지 작성과 자기 성찰의 구체적 방법
3. 학생과 눈높이를 맞추는 소통 태도
4. 교실을 민주적 공동체로 운영하는 전략

톤: 따뜻하고 격려하는, 실천에서 답을 찾는 실용주의.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 5,
        name: 'Freire',
        fullName: 'Paulo Freire (파울로 프레이리)',
        avatar: '✊',
        dimension: '학생 참여',
        dimIcon: '✊',
        title: '비판적 교육학의 아버지',
        era: '1921~1997',
        specialty: ['대화적 교육', '비판적 의식화', '참여적 학습'],
        philosophy: '"교육은 은행예금식이어서는 안 되며, 대화를 통한 의식화 과정이어야 한다."',
        coachingStyle: '학생의 능동적 참여를 이끌어내는 대화적 교수법과 발문 전략을 코칭합니다.',
        keyTheory: 'Dialogical Education & Critical Pedagogy',
        advice: [
            '일방적 전달이 아닌 대화형 수업을 설계하세요.',
            '학생의 삶과 연결된 문제를 수업 주제로 활용하세요.',
            '개방형 질문으로 비판적 사고를 자극하세요.',
        ],
        tags: ['대화교육', '학생참여', '발문전략', '비판적사고'],
        color: '#ef4444',
        systemPrompt: `당신은 Paulo Freire(파울로 프레이리)의 페르소나로 교사를 코칭합니다.

핵심 이론: 비판적 교육학
- "은행저금식 교육" 비판: 교사가 지식을 예금하듯 전달하는 것에 반대
- "문제제기식 교육": 대화와 비판적 사고를 통한 학습
- 의식화(Conscientização): 사회적 모순을 인식하고 변화시키려는 의식
- 교사-학생의 수평적 관계: 함께 배우는 동반자

코칭 원칙:
1. 교사 중심 강의를 대화 중심 수업으로 전환하도록 안내
2. 학생의 삶과 연결된 "생성적 주제" 발견 방법
3. 비판적 질문으로 학생의 사고를 자극하는 전략
4. 교실에서의 권력 관계를 성찰하고 민주적으로 재구성

톤: 열정적이고 해방적, "왜?"를 끊임없이 묻고 학생의 목소리에 귀 기울이도록 촉구.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 6,
        name: 'Bloom',
        fullName: 'Benjamin Bloom (벤저민 블룸)',
        avatar: '⏱️',
        dimension: '시간 배분',
        dimIcon: '⏱️',
        title: '완전학습 & 교육목표분류학 창시자',
        era: '1913~1999',
        specialty: ['완전학습', '교육목표분류학', '형성평가'],
        philosophy: '"충분한 시간과 적절한 처치를 주어지면 95%의 학습자가 완전학습에 도달할 수 있다."',
        coachingStyle: '학습 목표에 따른 시간 배분 최적화와 완전학습을 위한 수업 구조를 코칭합니다.',
        keyTheory: "Mastery Learning & Bloom's Taxonomy",
        advice: [
            '도입-전개-정리의 시간 비율을 최적화하세요.',
            '고차 사고력 활동에 충분한 시간을 배분하세요.',
            '형성평가를 활용해 학습 도달도를 실시간 확인하세요.',
        ],
        tags: ['완전학습', '시간관리', '블룸분류학', '형성평가'],
        color: '#8b5cf6',
        systemPrompt: `당신은 Benjamin Bloom(벤저민 블룸)의 페르소나로 교사를 코칭합니다.

핵심 이론: 블룸의 교육목표 분류학 & 완전학습
- 인지적 영역 6단계: 기억 → 이해 → 적용 → 분석 → 평가 → 창조
- 완전학습: 충분한 시간과 적절한 교수를 제공하면 95%의 학생이 완전학습 가능
- 형성평가와 교정학습의 중요성
- 도입-전개-정리의 시간 배분 최적화

코칭 원칙:
1. 수업 목표를 블룸의 분류학 수준으로 진단하고 상위 수준으로 끌어올리도록 안내
2. 고차원적 사고(분석, 평가, 창조)를 촉진하는 시간 배분 전략
3. 형성평가 설계와 즉각적 피드백 타이밍
4. 완전학습을 위한 교정학습 및 심화학습 시간 설계

톤: 체계적이고 낙관적, "모든 학생은 배울 수 있다"는 철학.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
    {
        id: 7,
        name: 'Gardner',
        fullName: 'Howard Gardner (하워드 가드너)',
        avatar: '💡',
        dimension: '창의성',
        dimIcon: '💡',
        title: '다중지능 이론 창시자',
        era: '1943~현재',
        specialty: ['다중지능', '창의적 교수법', '개별화 교육'],
        philosophy: '"지능은 단일하지 않으며, 모든 학생은 고유한 지능 프로파일을 가진다. 창의성은 다양성의 산물이다."',
        coachingStyle: '다양한 지능 유형을 활용한 창의적 수업 설계와 혁신적 교수법을 코칭합니다.',
        keyTheory: 'Theory of Multiple Intelligences',
        advice: [
            '단일 방식이 아닌 다양한 표현 방식을 활용하세요.',
            'ICT, 예술, 신체활동 등 다중 채널을 수업에 통합하세요.',
            '학생 개인의 강점 지능을 발견하고 활용하세요.',
        ],
        tags: ['다중지능', '창의성', '개별화', '혁신교수법'],
        color: '#ec4899',
        systemPrompt: `당신은 Howard Gardner(하워드 가드너) 교수의 페르소나로 교사를 코칭합니다.

핵심 이론: 다중지능 이론 (Multiple Intelligences)
- 최소 8가지 독립적 지능: 언어, 논리수학, 공간, 음악, 신체운동, 대인, 자기성찰, 자연탐구
- 모든 학생은 고유한 지능 프로파일을 가짐
- 창의적 교수법은 다양한 지능 채널을 활용하여 모든 학생에게 도달
- 협소한 시험 중심 평가에서 벗어나 다양한 방식의 학습 증거 수집

코칭 원칙:
1. 수업에서 다중지능을 활용한 창의적 활동 설계
2. 시각, 청각, 신체, 음악, 대인, 자기성찰 등 다양한 접근 제안
3. 학생 개인의 강점 지능을 발견하고 활용하는 방법
4. ICT, 예술, 신체활동 등 다중 채널을 수업에 통합

톤: 창의적이고 개방적, 다양성에 대한 깊은 존중.
반드시 한국어로 답변하세요. 답변은 300~500자 내외로 핵심만 간결하게.`,
    },
]

// 코치별 추천 질문
const SUGGESTED_QUESTIONS = {
    Shulman: [
        '교과 내용 지식을 학생이 이해하기 쉽게 변환하는 방법은?',
        '학생의 오개념을 진단하고 교정하는 전략은?',
        '수업 목표와 평가를 효과적으로 연결하려면?',
    ],
    Vygotsky: [
        '학생의 근접발달영역을 파악하는 방법은 무엇인가요?',
        '효과적인 비계 설정과 철거 시점을 어떻게 판단하나요?',
        '또래 학습을 수업에 활용하는 구체적 방법은?',
    ],
    Bruner: [
        '판서를 구조화하고 시각적으로 표현하는 전략은?',
        '추상적 개념을 EIS 표현 양식으로 설명하는 방법은?',
        '내러티브를 활용한 수업 설계 방법을 알려주세요.',
    ],
    Dewey: [
        '수업에서 열정과 진정성을 보여주는 방법은?',
        '반성적 일지를 어떻게 작성하면 효과적인가요?',
        '학생과의 소통 태도를 개선하려면 어떻게 해야 하나요?',
    ],
    Freire: [
        '은행저금식 교육에서 벗어나는 첫 번째 단계는?',
        '대화 중심 수업을 설계하는 구체적 방법은?',
        '학생의 삶과 연결된 "생성적 주제"를 찾는 방법은?',
    ],
    Bloom: [
        '수업 시간을 도입-전개-정리로 최적 배분하는 방법은?',
        '고차 사고력 활동에 충분한 시간을 확보하려면?',
        '형성평가를 효과적으로 활용하는 타이밍 전략은?',
    ],
    Gardner: [
        '수업에서 다중지능을 어떻게 활용하나요?',
        '창의적 수업 활동을 설계하는 방법은?',
        '학생의 강점 지능을 발견하고 활용하려면?',
    ],
}

const DIMENSIONS = AI_MENTORS.map(m => m.dimension)

function MentorMatch() {
    const navigate = useNavigate()
    const [selectedDims, setSelectedDims] = useState([])
    const [searchQuery, setSearchQuery] = useState('')
    const [expandedMentor, setExpandedMentor] = useState(null)

    // ── 챗봇 상태 ──
    const [chatCoach, setChatCoach] = useState(null)      // 선택된 코치 (null이면 채팅 비활성)
    const [chatMessages, setChatMessages] = useState([])
    const [chatInput, setChatInput] = useState('')
    const [chatLoading, setChatLoading] = useState(false)
    const chatRef = useRef(null)     // Gemini chat session
    const chatEndRef = useRef(null)  // 자동 스크롤용

    // 메시지 추가 시 자동 스크롤
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [chatMessages])

    const toggleDim = (dim) => {
        setSelectedDims(prev =>
            prev.includes(dim)
                ? prev.filter(d => d !== dim)
                : [...prev, dim]
        )
    }

    const filteredMentors = useMemo(() => AI_MENTORS.filter(mentor => {
        const matchesDim = selectedDims.length === 0 ||
            selectedDims.includes(mentor.dimension)
        const q = searchQuery.toLowerCase()
        const matchesSearch = !searchQuery ||
            mentor.name.toLowerCase().includes(q) ||
            mentor.fullName.toLowerCase().includes(q) ||
            mentor.dimension.includes(searchQuery) ||
            mentor.coachingStyle.includes(searchQuery) ||
            mentor.tags.some(t => t.includes(searchQuery))
        return matchesDim && matchesSearch
    }), [selectedDims, searchQuery])

    const toggleExpand = (id) => {
        setExpandedMentor(prev => prev === id ? null : id)
    }

    // ═══════════════════════════════════════════════════════════════
    // 챗봇 기능 — Gemini API
    // ═══════════════════════════════════════════════════════════════

    const startCoaching = useCallback((coach) => {
        const apiKey = getStoredApiKey()
        if (!apiKey) {
            alert('⚠️ Gemini API Key가 설정되지 않았습니다.\n설정 > API Key에서 먼저 등록해주세요.')
            return
        }
        try {
            const genAI = new GoogleGenerativeAI(apiKey)
            const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })

            const greeting = `안녕하세요! 저는 ${coach.fullName}입니다. ${coach.dimension} 영역의 AI 코치로서 여러분의 수업 개선을 함께 하겠습니다.\n\n${coach.philosophy}\n\n어떤 부분에서 도움이 필요하신지 편하게 말씀해주세요. 😊`

            const chat = model.startChat({
                history: [
                    { role: 'user', parts: [{ text: '안녕하세요, 코칭을 시작합니다.' }] },
                    { role: 'model', parts: [{ text: greeting }] },
                ],
                generationConfig: { maxOutputTokens: 1024 },
                systemInstruction: coach.systemPrompt,
            })

            chatRef.current = chat
            setChatCoach(coach)
            setChatMessages([{ role: 'assistant', content: greeting }])
            setChatInput('')
        } catch (e) {
            console.error('[CoachChat] init error:', e)
            alert('Gemini 초기화 실패: ' + e.message)
        }
    }, [])

    const closeChat = useCallback(() => {
        setChatCoach(null)
        setChatMessages([])
        setChatInput('')
        setChatLoading(false)
        chatRef.current = null
    }, [])

    const sendMessage = useCallback(async (text) => {
        const msg = (text || chatInput).trim()
        if (!msg || !chatRef.current || chatLoading) return

        setChatInput('')
        setChatMessages(prev => [...prev, { role: 'user', content: msg }])
        setChatLoading(true)

        try {
            const result = await chatRef.current.sendMessage(msg)
            const reply = result.response.text()
            setChatMessages(prev => [...prev, { role: 'assistant', content: reply }])
        } catch (e) {
            console.error('[CoachChat] send error:', e)
            setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: `⚠️ 응답 오류: ${e.message}\n\n다시 시도해주세요.`,
            }])
        } finally {
            setChatLoading(false)
        }
    }, [chatInput, chatLoading])

    const handleChatKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }, [sendMessage])

    // ═══════════════════════════════════════════════════════════════
    // 렌더링
    // ═══════════════════════════════════════════════════════════════

    return (
        <div className="mentor-container">
            {/* Hero */}
            <div className="mentor-hero">
                <div className="mentor-hero-badge">🤖 AI Agent</div>
                <h1>🎓 AI 코치 매칭</h1>
                <p className="mentor-subtitle">
                    7차원 수업 평가 기반 — 교육학 석학 AI 에이전트가 맞춤 코칭을 제공합니다
                </p>
                <div className="mentor-hero-stats">
                    <div className="hero-stat"><span className="hero-stat-num">7</span><span className="hero-stat-lbl">AI 코치</span></div>
                    <div className="hero-stat"><span className="hero-stat-num">7</span><span className="hero-stat-lbl">평가 차원</span></div>
                    <div className="hero-stat"><span className="hero-stat-num">∞</span><span className="hero-stat-lbl">코칭 가능</span></div>
                </div>
            </div>

            {/* Filters */}
            <div className="mentor-filters">
                <div className="filter-section">
                    <h3>🔍 개선이 필요한 차원 선택</h3>
                    <div className="dim-tags">
                        {DIMENSIONS.map((dim, i) => (
                            <button
                                key={dim}
                                className={`dim-tag ${selectedDims.includes(dim) ? 'active' : ''}`}
                                onClick={() => toggleDim(dim)}
                                style={{ '--dim-color': AI_MENTORS[i].color }}
                            >
                                {AI_MENTORS[i].dimIcon} {dim}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="filter-search">
                    <input
                        type="text"
                        placeholder="AI 코치 이름 또는 키워드 검색..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="search-input"
                    />
                </div>
            </div>

            {/* Results */}
            <div className="mentor-results">
                <p className="result-count">
                    {filteredMentors.length}명의 AI 코치를 찾았습니다
                </p>
                <div className="mentor-grid">
                    {filteredMentors.map(mentor => {
                        const isExpanded = expandedMentor === mentor.id
                        return (
                            <div
                                key={mentor.id}
                                className={`mentor-card ${isExpanded ? 'expanded' : ''}`}
                                style={{ '--card-accent': mentor.color }}
                            >
                                {/* Header */}
                                <div className="mentor-card-header">
                                    <div className="mentor-avatar" style={{ background: `linear-gradient(135deg, ${mentor.color}33, ${mentor.color}66)` }}>
                                        {mentor.avatar}
                                    </div>
                                    <div className="mentor-info">
                                        <div className="mentor-name-row">
                                            <h3>{mentor.name}</h3>
                                            <span className="mentor-agent-badge">AI Agent</span>
                                        </div>
                                        <p className="mentor-fullname">{mentor.fullName}</p>
                                        <p className="mentor-title">{mentor.title}</p>
                                    </div>
                                </div>

                                {/* Dimension Badge */}
                                <div className="mentor-dim-badge" style={{ borderColor: `${mentor.color}55`, background: `${mentor.color}15` }}>
                                    <span className="dim-badge-icon">{mentor.dimIcon}</span>
                                    <span className="dim-badge-text">{mentor.dimension}</span>
                                    <span className="dim-badge-era">{mentor.era}</span>
                                </div>

                                {/* Philosophy */}
                                <blockquote className="mentor-philosophy">
                                    {mentor.philosophy}
                                </blockquote>

                                {/* Key Theory */}
                                <div className="mentor-theory">
                                    🎓 <strong>핵심 이론:</strong> {mentor.keyTheory}
                                </div>

                                {/* Coaching Style */}
                                <p className="mentor-coaching">{mentor.coachingStyle}</p>

                                {/* Tags */}
                                <div className="mentor-tags">
                                    {mentor.tags.map(t => (
                                        <span key={t} className="tag-chip" style={{ borderColor: `${mentor.color}33`, color: mentor.color }}>#{t}</span>
                                    ))}
                                </div>

                                {/* Expand/Collapse */}
                                <button className="btn-expand" onClick={() => toggleExpand(mentor.id)}>
                                    {isExpanded ? '▲ 접기' : '▼ 코칭 조언 보기'}
                                </button>

                                {/* Expanded: Advice */}
                                {isExpanded && (
                                    <div className="mentor-advice-section">
                                        <h4>💡 {mentor.name} 코치의 코칭 조언</h4>
                                        <ul className="advice-list">
                                            {mentor.advice.map((a, i) => (
                                                <li key={i}>
                                                    <span className="advice-num">{i + 1}</span>
                                                    {a}
                                                </li>
                                            ))}
                                        </ul>
                                        <div className="mentor-specialties">
                                            <strong>전문 분야:</strong>
                                            {mentor.specialty.map(s => (
                                                <span key={s} className="specialty-badge" style={{ background: `${mentor.color}22`, borderColor: `${mentor.color}44`, color: mentor.color }}>{s}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* CTA — 코칭 시작 (Gemini 챗봇 연결) */}
                                <button
                                    className="btn-mentor-request"
                                    style={{ background: `linear-gradient(135deg, ${mentor.color}, ${mentor.color}cc)` }}
                                    onClick={() => startCoaching(mentor)}
                                >
                                    🤖 {mentor.name} 코치와 코칭 시작
                                </button>
                            </div>
                        )
                    })}
                </div>

                {filteredMentors.length === 0 && (
                    <div className="no-results">
                        <p>해당 조건에 맞는 AI 코치가 없습니다</p>
                        <button onClick={() => { setSelectedDims([]); setSearchQuery('') }}>
                            필터 초기화
                        </button>
                    </div>
                )}
            </div>

            {/* ═══════════════════════════════════════════════════════════
                챗봇 모달 오버레이
            ═══════════════════════════════════════════════════════════ */}
            {chatCoach && (
                <div className="chat-overlay" onClick={(e) => { if (e.target === e.currentTarget) closeChat() }}>
                    <div className="chat-modal">
                        {/* Header */}
                        <div className="chat-header" style={{ background: `linear-gradient(135deg, ${chatCoach.color}, ${chatCoach.color}cc)` }}>
                            <div className="chat-header-info">
                                <div className="chat-header-avatar">{chatCoach.avatar}</div>
                                <div>
                                    <div className="chat-header-name">
                                        {chatCoach.fullName} <span className="chat-header-label">코칭</span>
                                    </div>
                                    <div className="chat-header-theory">{chatCoach.keyTheory}</div>
                                </div>
                            </div>
                            <button className="chat-close" onClick={closeChat}>✕</button>
                        </div>

                        {/* Messages */}
                        <div className="chat-messages">
                            {chatMessages.map((msg, i) => (
                                <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
                                    {msg.role === 'assistant' && (
                                        <div className="chat-msg-avatar" style={{ background: `linear-gradient(135deg, ${chatCoach.color}, ${chatCoach.color}cc)` }}>
                                            {chatCoach.avatar}
                                        </div>
                                    )}
                                    <div
                                        className="chat-msg-bubble"
                                        style={msg.role === 'user' ? { background: `linear-gradient(135deg, ${chatCoach.color}, ${chatCoach.color}cc)` } : undefined}
                                    >
                                        {msg.content}
                                    </div>
                                </div>
                            ))}

                            {/* Typing Indicator */}
                            {chatLoading && (
                                <div className="chat-msg chat-msg-assistant">
                                    <div className="chat-msg-avatar" style={{ background: `linear-gradient(135deg, ${chatCoach.color}, ${chatCoach.color}cc)` }}>
                                        {chatCoach.avatar}
                                    </div>
                                    <div className="chat-msg-bubble chat-typing">
                                        <span style={{ background: chatCoach.color }}></span>
                                        <span style={{ background: chatCoach.color }}></span>
                                        <span style={{ background: chatCoach.color }}></span>
                                    </div>
                                </div>
                            )}

                            {/* Suggested Questions */}
                            {chatMessages.length === 1 && !chatLoading && (
                                <div className="chat-suggestions">
                                    <div className="chat-sug-label">💡 추천 질문</div>
                                    {(SUGGESTED_QUESTIONS[chatCoach.name] || []).map((q, i) => (
                                        <button
                                            key={i}
                                            className="chat-sug-btn"
                                            style={{ borderColor: chatCoach.color + '30' }}
                                            onClick={() => sendMessage(q)}
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            )}

                            <div ref={chatEndRef} />
                        </div>

                        {/* Input */}
                        <div className="chat-input-area">
                            <input
                                className="chat-input"
                                value={chatInput}
                                onChange={e => setChatInput(e.target.value)}
                                onKeyDown={handleChatKeyDown}
                                placeholder={`${chatCoach.name} 코치에게 질문하세요...`}
                                disabled={chatLoading}
                                style={{ borderColor: chatCoach.color + '30' }}
                            />
                            <button
                                className="chat-send"
                                onClick={() => sendMessage()}
                                disabled={chatLoading || !chatInput.trim()}
                                style={{
                                    background: chatLoading || !chatInput.trim() ? '#334155' : `linear-gradient(135deg, ${chatCoach.color}, ${chatCoach.color}cc)`,
                                    opacity: chatLoading || !chatInput.trim() ? 0.5 : 1,
                                }}
                            >
                                전송
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default MentorMatch
