import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './MentorMatch.css'

// 데모 멘토 데이터
const DEMO_MENTORS = [
    {
        id: 1,
        name: '김수연 교수',
        avatar: '👩‍🏫',
        title: '수업 전문성 전문가',
        specialty: ['수업 전문성', '교수학습 방법'],
        experience: '15년',
        rating: 4.9,
        reviews: 42,
        bio: '초등교육 수업설계 및 교수법 전문가. 수업목표 수립과 체계적 수업 구성 분야가 전문 영역입니다.',
        tags: ['수업설계', '교육과정', '학습목표'],
    },
    {
        id: 2,
        name: '박지훈 교수',
        avatar: '👨‍🏫',
        title: '학생 참여 전문가',
        specialty: ['학생 참여', '수업 태도'],
        experience: '12년',
        rating: 4.8,
        reviews: 38,
        bio: '학생 중심 교육 전문가. 발문 기법과 학생 피드백 전략 분야에서 다수의 연구를 수행했습니다.',
        tags: ['발문기법', '학생참여', '피드백'],
    },
    {
        id: 3,
        name: '이하은 교수',
        avatar: '👩‍💼',
        title: '교수법 혁신 전문가',
        specialty: ['창의성', '교수학습 방법'],
        experience: '10년',
        rating: 4.7,
        reviews: 29,
        bio: 'ICT 활용 교육 및 창의적 교수법 연구. 블렌디드 러닝과 플립드 러닝 설계 전문가입니다.',
        tags: ['창의교수법', 'ICT활용', '블렌디드러닝'],
    },
    {
        id: 4,
        name: '정민호 교수',
        avatar: '👨‍💻',
        title: '수업 분석 전문가',
        specialty: ['판서 및 언어', '시간 배분'],
        experience: '8년',
        rating: 4.6,
        reviews: 24,
        bio: 'FIAS 상호작용 분석 전문가. 수업 언어 분석과 시간 관리 최적화 연구를 진행하고 있습니다.',
        tags: ['언어분석', '시간관리', 'FIAS'],
    },
]

const DIMENSIONS = [
    '수업 전문성', '교수학습 방법', '판서 및 언어',
    '수업 태도', '학생 참여', '시간 배분', '창의성'
]

function MentorMatch() {
    const navigate = useNavigate()
    const [selectedDims, setSelectedDims] = useState([])
    const [searchQuery, setSearchQuery] = useState('')

    const toggleDim = (dim) => {
        setSelectedDims(prev =>
            prev.includes(dim)
                ? prev.filter(d => d !== dim)
                : [...prev, dim]
        )
    }

    const filteredMentors = DEMO_MENTORS.filter(mentor => {
        const matchesDim = selectedDims.length === 0 ||
            mentor.specialty.some(s => selectedDims.includes(s))
        const matchesSearch = !searchQuery ||
            mentor.name.includes(searchQuery) ||
            mentor.bio.includes(searchQuery) ||
            mentor.tags.some(t => t.includes(searchQuery))
        return matchesDim && matchesSearch
    })

    const renderStars = (rating) => {
        const full = Math.floor(rating)
        const half = rating % 1 >= 0.5
        return (
            <span className="mentor-stars">
                {'★'.repeat(full)}
                {half && '☆'}
                <span className="rating-num">{rating}</span>
            </span>
        )
    }

    return (
        <div className="mentor-container">
            {/* Hero */}
            <div className="mentor-hero">
                <h1>🎓 멘토 매칭</h1>
                <p className="mentor-subtitle">
                    약점 차원 기반으로 최적의 멘토를 추천합니다
                </p>
            </div>

            {/* Filters */}
            <div className="mentor-filters">
                <div className="filter-section">
                    <h3>🔍 개선이 필요한 차원 선택</h3>
                    <div className="dim-tags">
                        {DIMENSIONS.map(dim => (
                            <button
                                key={dim}
                                className={`dim-tag ${selectedDims.includes(dim) ? 'active' : ''}`}
                                onClick={() => toggleDim(dim)}
                            >
                                {dim}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="filter-search">
                    <input
                        type="text"
                        placeholder="멘토 이름 또는 키워드 검색..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="search-input"
                    />
                </div>
            </div>

            {/* Results */}
            <div className="mentor-results">
                <p className="result-count">
                    {filteredMentors.length}명의 멘토를 찾았습니다
                </p>
                <div className="mentor-grid">
                    {filteredMentors.map(mentor => (
                        <div key={mentor.id} className="mentor-card">
                            <div className="mentor-card-header">
                                <div className="mentor-avatar">{mentor.avatar}</div>
                                <div className="mentor-info">
                                    <h3>{mentor.name}</h3>
                                    <p className="mentor-title">{mentor.title}</p>
                                </div>
                            </div>

                            <div className="mentor-meta">
                                <span className="meta-item">📅 경력 {mentor.experience}</span>
                                <span className="meta-item">💬 후기 {mentor.reviews}건</span>
                            </div>

                            <div className="mentor-rating">
                                {renderStars(mentor.rating)}
                            </div>

                            <p className="mentor-bio">{mentor.bio}</p>

                            <div className="mentor-specialties">
                                {mentor.specialty.map(s => (
                                    <span key={s} className="specialty-badge">{s}</span>
                                ))}
                            </div>

                            <div className="mentor-tags">
                                {mentor.tags.map(t => (
                                    <span key={t} className="tag-chip">#{t}</span>
                                ))}
                            </div>

                            <button
                                className="btn-mentor-request"
                                onClick={() => alert(`${mentor.name} 멘토에게 매칭을 요청했습니다! (데모)`)}
                            >
                                🤝 매칭 요청
                            </button>
                        </div>
                    ))}
                </div>

                {filteredMentors.length === 0 && (
                    <div className="no-results">
                        <p>😕 조건에 맞는 멘토가 없습니다</p>
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
