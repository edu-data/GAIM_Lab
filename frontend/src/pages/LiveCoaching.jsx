import { useState, useEffect, useRef } from 'react'

function LiveCoaching() {
    const [isActive, setIsActive] = useState(false)
    const [feedback, setFeedback] = useState(null)
    const [summary, setSummary] = useState(null)
    const [transcript, setTranscript] = useState([])
    const wsRef = useRef(null)
    const recognitionRef = useRef(null)

    const startSession = () => {
        setSummary(null)
        setTranscript([])
        setFeedback(null)

        // WebSocket 연결
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
        const ws = new WebSocket(`${protocol}://${window.location.hostname}:8000/api/v1/ws/live-coaching`)
        wsRef.current = ws

        ws.onopen = () => {
            setIsActive(true)
            startSpeechRecognition()
        }

        ws.onmessage = (e) => {
            const data = JSON.parse(e.data)
            if (data.type === 'feedback') {
                setFeedback(data)
                if (data.latest_text !== '(침묵)') {
                    setTranscript(prev => [...prev, data.latest_text])
                }
            } else if (data.type === 'summary') {
                setSummary(data)
                setIsActive(false)
            }
        }

        ws.onerror = () => setIsActive(false)
        ws.onclose = () => setIsActive(false)
    }

    const startSpeechRecognition = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        if (!SpeechRecognition) {
            alert('이 브라우저는 음성인식을 지원하지 않습니다. Chrome을 사용하세요.')
            return
        }

        const recognition = new SpeechRecognition()
        recognition.lang = 'ko-KR'
        recognition.continuous = true
        recognition.interimResults = false

        recognition.onresult = (e) => {
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) {
                    const text = e.results[i][0].transcript
                    if (wsRef.current?.readyState === WebSocket.OPEN) {
                        wsRef.current.send(JSON.stringify({ type: 'text', content: text }))
                    }
                }
            }
        }

        recognition.onerror = (e) => {
            if (e.error !== 'no-speech') console.error('Speech error:', e.error)
        }

        recognition.onend = () => {
            if (isActive) recognition.start() // 자동 재시작
        }

        recognition.start()
        recognitionRef.current = recognition
    }

    const stopSession = () => {
        if (recognitionRef.current) {
            recognitionRef.current.stop()
            recognitionRef.current = null
        }
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'stop' }))
        }
    }

    useEffect(() => {
        return () => {
            if (recognitionRef.current) recognitionRef.current.stop()
            if (wsRef.current) wsRef.current.close()
        }
    }, [])

    return (
        <div className="live-coaching-page">
            <div className="page-header">
                <h2>🔴 실시간 코칭 라이트</h2>
                <p>마이크 기반 실시간 분석 — 필러, 말 속도, 침묵 비율 즉시 피드백</p>
            </div>

            {/* Control */}
            <div className="lc-control">
                {!isActive ? (
                    <button className="lc-start-btn" onClick={startSession}>
                        🎙️ 코칭 시작
                    </button>
                ) : (
                    <button className="lc-stop-btn" onClick={stopSession}>
                        ⏹️ 종료
                    </button>
                )}
                {isActive && <div className="lc-pulse">● LIVE</div>}
            </div>

            {/* Real-time Feedback */}
            {feedback && (
                <div className="lc-dashboard">
                    <div className="lc-metrics">
                        <div className="lc-metric">
                            <div className="lc-metric-value">{feedback.wpm}</div>
                            <div className="lc-metric-label">WPM (말 속도)</div>
                        </div>
                        <div className="lc-metric">
                            <div className="lc-metric-value" style={{
                                color: feedback.filler_count > 5 ? '#ff5252' : feedback.filler_count > 2 ? '#ffc107' : '#00e676'
                            }}>{feedback.filler_count}</div>
                            <div className="lc-metric-label">필러 횟수</div>
                        </div>
                        <div className="lc-metric">
                            <div className="lc-metric-value">{(feedback.silence_ratio * 100).toFixed(0)}%</div>
                            <div className="lc-metric-label">침묵 비율</div>
                        </div>
                        <div className="lc-metric">
                            <div className="lc-metric-value">{feedback.elapsed_sec}s</div>
                            <div className="lc-metric-label">경과 시간</div>
                        </div>
                    </div>

                    {/* Tips */}
                    <div className="lc-tips">
                        {feedback.tips?.map((tip, i) => (
                            <div key={i} className="lc-tip">{tip}</div>
                        ))}
                    </div>

                    {/* Latest text */}
                    <div className="lc-latest">
                        <strong>인식된 텍스트:</strong> {feedback.latest_text}
                    </div>
                </div>
            )}

            {/* Transcript */}
            {transcript.length > 0 && (
                <div className="lc-section">
                    <h3>📝 전체 전사 기록</h3>
                    <div className="lc-transcript">
                        {transcript.map((t, i) => <span key={i}>{t} </span>)}
                    </div>
                </div>
            )}

            {/* Session Summary */}
            {summary && (
                <div className="lc-section lc-summary">
                    <h3>📊 세션 요약</h3>
                    <div className="lc-summary-grid">
                        <div><strong>총 시간:</strong> {(summary.duration_sec / 60).toFixed(1)}분</div>
                        <div><strong>총 단어:</strong> {summary.total_words}개</div>
                        <div><strong>평균 WPM:</strong> {summary.avg_wpm}</div>
                        <div><strong>필러 횟수:</strong> {summary.filler_count}회</div>
                        <div><strong>침묵 비율:</strong> {(summary.silence_ratio * 100).toFixed(0)}%</div>
                    </div>
                </div>
            )}

            <style>{`
        .live-coaching-page { max-width: 800px; margin: 0 auto; }
        .page-header { text-align: center; margin-bottom: 1.5rem; }
        .page-header h2 { font-size: 1.6rem; background: linear-gradient(135deg, #ff5252, #ff8a80);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .page-header p { color: #888; }
        .lc-control { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 1.5rem; }
        .lc-start-btn, .lc-stop-btn { padding: 0.9rem 2rem; border: none; border-radius: 12px;
          font-size: 1.1rem; cursor: pointer; font-weight: 600; }
        .lc-start-btn { background: linear-gradient(135deg, #ff5252, #ff8a80); color: #fff; }
        .lc-stop-btn { background: rgba(255,82,82,0.2); color: #ff5252; border: 2px solid #ff5252; }
        .lc-pulse { color: #ff5252; font-weight: 700; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
        .lc-dashboard { background: rgba(26,26,46,0.8); border-radius: 14px; padding: 1.5rem;
          border: 1px solid rgba(255,82,82,0.2); margin-bottom: 1rem; }
        .lc-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
        .lc-metric { text-align: center; background: rgba(22,33,62,0.6); border-radius: 10px; padding: 1rem; }
        .lc-metric-value { font-size: 1.8rem; font-weight: 700; color: #00d2ff; }
        .lc-metric-label { font-size: 0.75rem; color: #888; margin-top: 0.2rem; }
        .lc-tips { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.8rem; }
        .lc-tip { background: rgba(108,99,255,0.1); border-left: 3px solid #6c63ff;
          padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 0.85rem; color: #ccc; }
        .lc-latest { font-size: 0.85rem; color: #aaa; padding: 0.5rem;
          background: rgba(0,0,0,0.2); border-radius: 6px; }
        .lc-section { background: rgba(26,26,46,0.8); border-radius: 14px; padding: 1.5rem;
          border: 1px solid rgba(108,99,255,0.12); margin-bottom: 1rem; }
        .lc-section h3 { color: #00d2ff; margin-bottom: 0.8rem; }
        .lc-transcript { font-size: 0.85rem; color: #bbb; line-height: 1.7; max-height: 200px;
          overflow-y: auto; padding: 0.5rem; background: rgba(0,0,0,0.15); border-radius: 6px; }
        .lc-summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 0.5rem; font-size: 0.9rem; color: #ccc; }
        @media (max-width: 768px) { .lc-metrics { grid-template-columns: repeat(2, 1fr); } }
      `}</style>
        </div>
    )
}

export default LiveCoaching
