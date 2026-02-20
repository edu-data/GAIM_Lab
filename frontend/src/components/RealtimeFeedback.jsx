import { useState, useEffect, useRef, useCallback } from 'react';
import { API_HOST } from '../apiConfig';
import './RealtimeFeedback.css';

const WS_BASE = API_HOST
    ? API_HOST.replace(/^https?:\/\//, (m) => m.startsWith('https') ? 'wss://' : 'ws://')
    : 'ws://localhost:8000';

const RealtimeFeedback = ({ analysisId, onComplete, onError }) => {
    const [connected, setConnected] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStage, setCurrentStage] = useState(null);
    const [stages, setStages] = useState([]);
    const [timeline, setTimeline] = useState([]);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [status, setStatus] = useState('connecting'); // connecting, running, complete, error
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    const connectWebSocket = useCallback(() => {
        if (!analysisId) return;

        const wsUrl = `${WS_BASE}/api/v1/ws/analysis/${analysisId}`;

        try {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('WebSocket connected');
                setConnected(true);
                setStatus('running');
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                }
            };

            wsRef.current.onclose = () => {
                console.log('WebSocket disconnected');
                setConnected(false);
                // 완료 상태가 아니면 재연결 시도
                if (status !== 'complete' && status !== 'error') {
                    reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
                }
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setStatus('error');
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            setStatus('error');
        }
    }, [analysisId, status]);

    const handleMessage = (data) => {
        switch (data.type) {
            case 'progress':
                setProgress(data.overall_progress || 0);
                setCurrentStage(data.current_stage);
                setStages(data.stages || []);
                setTimeline(prev => {
                    // 중복 제거하면서 새 이벤트 추가
                    const newEvents = data.timeline || [];
                    const combined = [...prev, ...newEvents];
                    const unique = combined.filter((v, i, a) =>
                        a.findIndex(t => t.timestamp === v.timestamp && t.message === v.message) === i
                    );
                    return unique.slice(-20); // 최근 20개만 유지
                });
                setElapsedTime(data.elapsed_time || 0);
                break;

            case 'complete':
                setProgress(100);
                setStatus('complete');
                setElapsedTime(data.elapsed_time || 0);
                if (onComplete) {
                    onComplete(data.result);
                }
                break;

            case 'error':
                setStatus('error');
                if (onError) {
                    onError(data.message);
                }
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    };

    useEffect(() => {
        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connectWebSocket]);

    // Ping 전송으로 연결 유지
    useEffect(() => {
        const pingInterval = setInterval(() => {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send('ping');
            }
        }, 30000);

        return () => clearInterval(pingInterval);
    }, []);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getStageIcon = (stage) => {
        const icons = {
            upload: '📤',
            audio_extract: '🎵',
            stt: '🗣️',
            vision: '👁️',
            vibe: '🎧',
            text: '📝',
            evaluation: '📊',
            report: '📋'
        };
        return icons[stage.id] || '⚡';
    };

    const getStatusIcon = (stageStatus) => {
        switch (stageStatus) {
            case 'completed': return '✅';
            case 'in_progress': return '🔄';
            case 'pending': return '⏳';
            default: return '○';
        }
    };

    return (
        <div className="realtime-feedback">
            {/* 연결 상태 */}
            <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
                <span className="status-dot"></span>
                {connected ? '실시간 연결됨' : '연결 중...'}
            </div>

            {/* 전체 진행률 */}
            <div className="overall-progress">
                <div className="progress-header">
                    <h3>분석 진행 상황</h3>
                    <span className="elapsed-time">⏱️ {formatTime(elapsedTime)}</span>
                </div>
                <div className="progress-bar-container">
                    <div
                        className="progress-bar-fill"
                        style={{ width: `${progress}%` }}
                    >
                        <span className="progress-text">{progress.toFixed(1)}%</span>
                    </div>
                </div>
                {currentStage && (
                    <div className="current-stage-info">
                        <span className="stage-icon">{getStageIcon(currentStage)}</span>
                        <span className="stage-name">{currentStage.name}</span>
                        <span className="stage-progress">({currentStage.progress}%)</span>
                    </div>
                )}
            </div>

            {/* 단계별 상태 */}
            <div className="stages-list">
                <h4>📋 분석 단계</h4>
                <div className="stages-grid">
                    {stages.map((stage, idx) => (
                        <div
                            key={stage.id}
                            className={`stage-item ${stage.status}`}
                        >
                            <span className="stage-number">{idx + 1}</span>
                            <span className="stage-icon">{getStageIcon(stage)}</span>
                            <span className="stage-label">{stage.name}</span>
                            <span className="stage-status-icon">{getStatusIcon(stage.status)}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 타임라인 */}
            <div className="timeline-section">
                <h4>📜 실시간 로그</h4>
                <div className="timeline-list">
                    {timeline.length === 0 ? (
                        <div className="timeline-empty">분석 이벤트 대기 중...</div>
                    ) : (
                        timeline.slice().reverse().map((event, idx) => (
                            <div key={idx} className="timeline-item">
                                <span className="timeline-time">
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </span>
                                <span className="timeline-message">{event.message}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* 상태 메시지 */}
            {status === 'complete' && (
                <div className="status-message success">
                    ✅ 분석이 완료되었습니다!
                </div>
            )}
            {status === 'error' && (
                <div className="status-message error">
                    ❌ 분석 중 오류가 발생했습니다.
                </div>
            )}
        </div>
    );
};

export default RealtimeFeedback;
