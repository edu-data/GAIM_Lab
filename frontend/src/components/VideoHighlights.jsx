import { useRef, useState } from 'react'

/**
 * VideoHighlights — 분석 결과와 영상 타임라인 동기화 컴포넌트
 * 
 * Props:
 *   videoUrl: string — 영상 URL (/uploads/... 또는 /output/...)
 *   highlights: Array<{ time: number, label: string, type: string, detail: string }>
 *     - time: 초 단위 타임스탬프
 *     - label: 마커 라벨
 *     - type: 'positive' | 'warning' | 'info'
 *     - detail: 상세 설명
 */
function VideoHighlights({ videoUrl, highlights = [] }) {
    const videoRef = useRef(null)
    const [currentTime, setCurrentTime] = useState(0)
    const [duration, setDuration] = useState(0)
    const [selectedHighlight, setSelectedHighlight] = useState(null)

    const seekTo = (time) => {
        if (videoRef.current) {
            videoRef.current.currentTime = time
            videoRef.current.play()
            setSelectedHighlight(highlights.find(h => h.time === time) || null)
        }
    }

    const formatTime = (sec) => {
        const m = Math.floor(sec / 60)
        const s = Math.floor(sec % 60)
        return `${m}:${s.toString().padStart(2, '0')}`
    }

    const typeConfig = {
        positive: { color: '#00e676', icon: '✅', label: '우수' },
        warning: { color: '#ffc107', icon: '⚠️', label: '주의' },
        info: { color: '#00d2ff', icon: 'ℹ️', label: '정보' },
        silence: { color: '#ff5252', icon: '🔇', label: '침묵' },
    }

    return (
        <div className="vh-container">
            {/* Video Player */}
            <div className="vh-player">
                {videoUrl ? (
                    <video
                        ref={videoRef}
                        src={videoUrl}
                        controls
                        onTimeUpdate={() => setCurrentTime(videoRef.current?.currentTime || 0)}
                        onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
                        className="vh-video"
                    />
                ) : (
                    <div className="vh-no-video">
                        <span>🎬</span>
                        <p>영상 파일이 없습니다</p>
                    </div>
                )}
            </div>

            {/* Timeline with markers */}
            {duration > 0 && highlights.length > 0 && (
                <div className="vh-timeline">
                    <div className="vh-timeline-bar">
                        {/* Progress indicator */}
                        <div className="vh-progress" style={{ width: `${(currentTime / duration) * 100}%` }} />
                        {/* Highlight markers */}
                        {highlights.map((h, i) => {
                            const pos = (h.time / duration) * 100
                            const cfg = typeConfig[h.type] || typeConfig.info
                            return (
                                <div
                                    key={i}
                                    className="vh-marker"
                                    style={{ left: `${pos}%`, borderColor: cfg.color }}
                                    title={`${formatTime(h.time)} — ${h.label}`}
                                    onClick={() => seekTo(h.time)}
                                >
                                    <span className="vh-marker-dot" style={{ background: cfg.color }} />
                                </div>
                            )
                        })}
                    </div>
                    <div className="vh-time-labels">
                        <span>0:00</span>
                        <span>{formatTime(duration)}</span>
                    </div>
                </div>
            )}

            {/* Highlight List */}
            {highlights.length > 0 && (
                <div className="vh-highlight-list">
                    <h4>📌 하이라이트 ({highlights.length}개)</h4>
                    <div className="vh-list">
                        {highlights.map((h, i) => {
                            const cfg = typeConfig[h.type] || typeConfig.info
                            const isActive = selectedHighlight?.time === h.time
                            return (
                                <div
                                    key={i}
                                    className={`vh-item ${isActive ? 'active' : ''}`}
                                    onClick={() => seekTo(h.time)}
                                    style={isActive ? { borderColor: cfg.color } : {}}
                                >
                                    <div className="vh-item-time" style={{ color: cfg.color }}>
                                        {cfg.icon} {formatTime(h.time)}
                                    </div>
                                    <div className="vh-item-label">{h.label}</div>
                                    {h.detail && <div className="vh-item-detail">{h.detail}</div>}
                                    <span className="vh-type-badge" style={{ color: cfg.color, borderColor: cfg.color }}>
                                        {cfg.label}
                                    </span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            <style>{`
        .vh-container { margin-top: 1rem; }
        .vh-player { border-radius: 12px; overflow: hidden; margin-bottom: 0.75rem;
          background: #000; aspect-ratio: 16/9; }
        .vh-video { width: 100%; height: 100%; object-fit: contain; }
        .vh-no-video { display: flex; flex-direction: column; align-items: center;
          justify-content: center; height: 100%; color: #555; }
        .vh-no-video span { font-size: 3rem; }
        .vh-timeline { margin-bottom: 1rem; }
        .vh-timeline-bar { position: relative; height: 12px; background: rgba(255,255,255,0.08);
          border-radius: 6px; cursor: pointer; }
        .vh-progress { position: absolute; top: 0; left: 0; height: 100%;
          background: rgba(108,99,255,0.4); border-radius: 6px; pointer-events: none; }
        .vh-marker { position: absolute; top: -4px; width: 20px; height: 20px;
          transform: translateX(-50%); cursor: pointer; z-index: 2;
          display: flex; align-items: center; justify-content: center; }
        .vh-marker-dot { width: 10px; height: 10px; border-radius: 50%;
          border: 2px solid rgba(255,255,255,0.3); transition: transform 0.2s; }
        .vh-marker:hover .vh-marker-dot { transform: scale(1.5); }
        .vh-time-labels { display: flex; justify-content: space-between;
          font-size: 0.7rem; color: #555; margin-top: 0.2rem; }
        .vh-highlight-list { background: rgba(26,26,46,0.6); border-radius: 12px;
          padding: 1rem; border: 1px solid rgba(108,99,255,0.1); }
        .vh-highlight-list h4 { color: #00d2ff; margin-bottom: 0.7rem; font-size: 0.95rem; }
        .vh-list { display: flex; flex-direction: column; gap: 0.4rem;
          max-height: 300px; overflow-y: auto; }
        .vh-item { background: rgba(22,33,62,0.5); border-radius: 8px; padding: 0.6rem 0.8rem;
          cursor: pointer; border: 1px solid transparent; transition: all 0.2s;
          display: grid; grid-template-columns: 80px 1fr auto; gap: 0.5rem; align-items: center; }
        .vh-item:hover { background: rgba(108,99,255,0.08); }
        .vh-item.active { background: rgba(108,99,255,0.12); }
        .vh-item-time { font-weight: 600; font-size: 0.85rem; }
        .vh-item-label { font-size: 0.85rem; color: #ccc; }
        .vh-item-detail { grid-column: 2; font-size: 0.75rem; color: #777; }
        .vh-type-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border: 1px solid;
          border-radius: 10px; font-weight: 500; }
      `}</style>
        </div>
    )
}

export default VideoHighlights
