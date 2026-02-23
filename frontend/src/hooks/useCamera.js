/**
 * GAIM Lab v8.0 — useCamera Hook
 * 
 * 카메라 스트림 라이프사이클과 프레임 분석을 관리하는 커스텀 훅.
 * LiveCoaching 및 향후 영상 분석 컴포넌트에서 재사용 가능.
 * 
 * 에러 방지:
 *  - 컴포넌트 언마운트 시 스트림 자동 정리
 *  - 카메라 접근 실패 시 graceful degradation
 *  - videoRef가 렌더링되기 전 접근 방지 (retry 로직)
 */

import { useState, useRef, useCallback, useEffect } from 'react'

/**
 * @param {Object} options
 * @param {number} options.analysisInterval - 프레임 분석 간격 (ms), 기본 500
 * @param {number} options.width - 캡처 해상도 너비, 기본 320
 * @param {number} options.height - 캡처 해상도 높이, 기본 240
 * @param {function} options.onFrame - 프레임 분석 결과 콜백 (movement, gestureCount, avgMovement)
 */
export function useCamera(options = {}) {
    const {
        analysisInterval = 500,
        width = 320,
        height = 240,
        onFrame = null,
    } = options

    const [cameraOn, setCameraOn] = useState(false)
    const [error, setError] = useState(null)
    const [metrics, setMetrics] = useState({ movement: 0, gestureCount: 0, avgMovement: 0 })

    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const streamRef = useRef(null)
    const prevFrameRef = useRef(null)
    const timerRef = useRef(null)
    const samplesRef = useRef([])
    const gestureCountRef = useRef(0)
    const lastMovementRef = useRef(0)

    // ── 프레임 분석 (움직임 감지) ──
    const analyzeFrame = useCallback(() => {
        const video = videoRef.current
        const canvas = canvasRef.current
        if (!video || !canvas || video.readyState < 2) return

        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        const captureW = 160, captureH = 120
        canvas.width = captureW
        canvas.height = captureH
        ctx.drawImage(video, 0, 0, captureW, captureH)
        const frame = ctx.getImageData(0, 0, captureW, captureH)
        const data = frame.data

        if (prevFrameRef.current) {
            let diff = 0
            const prev = prevFrameRef.current
            // sample every 4th pixel for performance
            for (let i = 0; i < data.length; i += 16) {
                diff += Math.abs(data[i] - prev[i]) +
                    Math.abs(data[i + 1] - prev[i + 1]) +
                    Math.abs(data[i + 2] - prev[i + 2])
            }
            const movement = Math.round(diff / (data.length / 16) / 3)
            samplesRef.current.push(movement)

            // 급격한 움직임 = 제스처
            if (movement > 25 && lastMovementRef.current < 10) {
                gestureCountRef.current += 1
            }
            lastMovementRef.current = movement

            const avg = samplesRef.current.reduce((a, b) => a + b, 0) / samplesRef.current.length
            const result = {
                movement,
                gestureCount: gestureCountRef.current,
                avgMovement: Math.round(avg),
            }
            setMetrics(result)
            if (onFrame) onFrame(result)
        }
        prevFrameRef.current = new Uint8ClampedArray(data)
    }, [onFrame])

    // ── 카메라 시작 ──
    const startCamera = useCallback(async () => {
        setError(null)
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: width }, height: { ideal: height }, facingMode: 'user' },
                audio: false,
            })
            streamRef.current = stream

            prevFrameRef.current = null
            samplesRef.current = []
            gestureCountRef.current = 0
            lastMovementRef.current = 0

            // videoRef가 렌더링될 때까지 대기 (최대 2초)
            const attachStream = (retries = 20) => {
                const video = videoRef.current
                if (video) {
                    video.srcObject = stream
                    video.muted = true
                    video.playsInline = true
                    video.setAttribute('autoplay', '')
                    // loadedmetadata에서 play 보장
                    video.onloadedmetadata = () => {
                        video.play()
                            .then(() => {
                                console.log('[useCamera] Video playing successfully')
                                setCameraOn(true)
                            })
                            .catch(err => {
                                console.warn('[useCamera] play() failed on metadata:', err)
                                // autoplay policy: muted play 재시도
                                setTimeout(() => {
                                    video.play()
                                        .then(() => setCameraOn(true))
                                        .catch(e2 => {
                                            console.error('[useCamera] play() retry failed:', e2)
                                            setError('영상 재생 실패: ' + e2.message)
                                        })
                                }, 300)
                            })
                    }
                    // 이미 메타데이터 로드된 경우 (readyState >= 1) 바로 play
                    if (video.readyState >= 1) {
                        video.play()
                            .then(() => setCameraOn(true))
                            .catch(() => { })
                    }
                } else if (retries > 0) {
                    setTimeout(() => attachStream(retries - 1), 100)
                } else {
                    console.error('[useCamera] videoRef not available after retries')
                    setError('비디오 요소를 찾을 수 없습니다')
                }
            }
            attachStream()

            timerRef.current = setInterval(() => analyzeFrame(), analysisInterval)
        } catch (e) {
            console.warn('[useCamera] Camera not available:', e.message)
            setError(e.message)
            setCameraOn(false)
        }
    }, [width, height, analysisInterval, analyzeFrame])

    // ── 카메라 종료 ──
    const stopCamera = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current)
            timerRef.current = null
        }
        if (videoRef.current) {
            videoRef.current.onloadedmetadata = null
            videoRef.current.srcObject = null
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop())
            streamRef.current = null
        }
        setCameraOn(false)
    }, [])

    // ── 리셋 ──
    const resetMetrics = useCallback(() => {
        samplesRef.current = []
        gestureCountRef.current = 0
        lastMovementRef.current = 0
        setMetrics({ movement: 0, gestureCount: 0, avgMovement: 0 })
    }, [])

    // ── 클린업 ──
    useEffect(() => {
        return () => stopCamera()
    }, [stopCamera])

    return {
        // refs to attach to DOM elements
        videoRef,
        canvasRef,
        // state
        cameraOn,
        error,
        metrics,
        // actions
        startCamera,
        stopCamera,
        resetMetrics,
    }
}

export default useCamera
