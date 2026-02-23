import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import './MentorMatch.css'

// ═══════════════════════════════════════════════════════════════
// 7차원 AI 멘토 에이전트 — 교육학 석학 기반
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
            '점진적 비계설정으로 자기주도 학습을 유도하세요.',
            '협동학습을 통한 사회적 구성을 촉진하세요.',
        ],
        tags: ['ZPD', '비계설정', '협동학습', '사회적구성'],
        color: '#00d2ff',
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
        coachingStyle: '수업 언어의 명확성, 판서의 구조화, 그리고 내러티브를 활용한 설명 기법을 코칭합니다.',
        keyTheory: 'Spiral Curriculum & Modes of Representation',
        advice: [
            '핵심 개념을 구조화된 판서로 시각화하세요.',
            '스토리텔링으로 추상적 개념을 구체화하세요.',
            '활동적(enactive) → 영상적(iconic) → 상징적(symbolic) 표현을 활용하세요.',
        ],
        tags: ['발견학습', '내러티브', '판서전략', '언어표현'],
        color: '#f59e0b',
    },
    {
        id: 4,
        name: 'Dewey',
        fullName: 'John Dewey (존 듀이)',
        avatar: '👨‍🏫',
        dimension: '수업 태도',
        dimIcon: '👨‍🏫',
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
    },
    {
        id: 5,
        name: 'Freire',
        fullName: 'Paulo Freire (파울로 프레이리)',
        avatar: '🙋',
        dimension: '학생 참여',
        dimIcon: '🙋',
        title: '비판적 교육학의 선구자',
        era: '1921~1997',
        specialty: ['대화적 교육', '비판적 의식화', '참여적 학습'],
        philosophy: '"교육은 은행저금식이어서는 안 되며, 대화를 통한 의식화 과정이어야 한다."',
        coachingStyle: '학생의 능동적 참여를 이끌어내는 대화적 교수법과 발문 전략을 코칭합니다.',
        keyTheory: 'Dialogical Education & Critical Pedagogy',
        advice: [
            '일방적 전달이 아닌 대화형 수업을 설계하세요.',
            '학생의 삶과 연결된 문제를 수업 소재로 활용하세요.',
            '개방형 질문으로 비판적 사고를 자극하세요.',
        ],
        tags: ['대화교육', '학생참여', '발문전략', '비판적사고'],
        color: '#ef4444',
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
        philosophy: '"충분한 시간과 적절한 도움이 주어지면 95%의 학습자가 완전학습에 도달할 수 있다."',
        coachingStyle: '학습 목표에 따른 시간 배분 최적화와 완전학습을 위한 수업 구조화를 코칭합니다.',
        keyTheory: 'Mastery Learning & Bloom\'s Taxonomy',
        advice: [
            '도입-전개-정리의 시간 비율을 최적화하세요.',
            '고차 사고력 활동에 충분한 시간을 배분하세요.',
            '형성평가를 활용해 학습 도달도를 실시간 점검하세요.',
        ],
        tags: ['완전학습', '시간관리', '블룸분류학', '형성평가'],
        color: '#8b5cf6',
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
        philosophy: '"지능은 단일하지 않으며, 모든 학생은 고유한 지능 프로파일을 가진다. 창의적 접근이 핵심이다."',
        coachingStyle: '다양한 지능 유형을 활용한 창의적 수업 설계와 혁신적 교수법을 코칭합니다.',
        keyTheory: 'Theory of Multiple Intelligences',
        advice: [
            '단일 방식이 아닌 다양한 표현 양식을 활용하세요.',
            'ICT, 예술, 신체활동 등 다중 채널을 수업에 통합하세요.',
            '학생 개인의 강점 지능을 발견하고 활용하세요.',
        ],
        tags: ['다중지능', '창의성', '개별화', '혁신교수법'],
        color: '#ec4899',
    },
]

const DIMENSIONS = AI_MENTORS.map(m => m.dimension)

function MentorMatch() {
    const navigate = useNavigate()
    const [selectedDims, setSelectedDims] = useState([])
    const [searchQuery, setSearchQuery] = useState('')
    const [expandedMentor, setExpandedMentor] = useState(null)

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

    return (
        <div className="mentor-container">
            {/* Hero */}
            <div className="mentor-hero">
                <div className="mentor-hero-badge">🤖 AI Agent</div>
                <h1>🎓 AI 멘토 매칭</h1>
                <p className="mentor-subtitle">
                    7차원 수업 평가 기반 — 교육학 석학 AI 에이전트가 맞춤 코칭을 제공합니다
                </p>
                <div className="mentor-hero-stats">
                    <div className="hero-stat"><span className="hero-stat-num">7</span><span className="hero-stat-lbl">AI 멘토</span></div>
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
                        placeholder="AI 멘토 이름 또는 키워드 검색..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="search-input"
                    />
                </div>
            </div>

            {/* Results */}
            <div className="mentor-results">
                <p className="result-count">
                    {filteredMentors.length}명의 AI 멘토를 찾았습니다
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
                                    🔬 <strong>핵심 이론:</strong> {mentor.keyTheory}
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
                                        <h4>💡 {mentor.name} 멘토의 코칭 조언</h4>
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

                                {/* CTA */}
                                <button
                                    className="btn-mentor-request"
                                    style={{ background: `linear-gradient(135deg, ${mentor.color}, ${mentor.color}cc)` }}
                                    onClick={() => alert(`🤖 ${mentor.name} AI 멘토와의 코칭 세션이 시작됩니다!\n\n"${mentor.philosophy}"\n\n이 기능은 추후 업데이트에서 활성화됩니다.`)}
                                >
                                    🤖 {mentor.name} 멘토와 코칭 시작
                                </button>
                            </div>
                        )
                    })}
                </div>

                {filteredMentors.length === 0 && (
                    <div className="no-results">
                        <p>😕 조건에 맞는 AI 멘토가 없습니다</p>
                        <button onClick={() => { setSelectedDims([]); setSearchQuery('') }}>
                            필터 초기화
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

export default MentorMatch
