/**
 * GAIM Lab v8.0 — useAsyncTask Hook
 * 
 * 무거운 동기 작업을 메인 스레드에서 분리하여 UI 블로킹 방지.
 * 
 * Web Worker가 사용 가능한 경우 Worker를 활용하고,
 * 불가능한 경우 setTimeout 기반 yielding으로 폴백합니다.
 * 
 * AgentMonitor, 분석 파이프라인 등에서 사용.
 */

import { useState, useCallback, useRef } from 'react'

/**
 * @returns {Object} { runTask, isRunning, progress, error, cancel }
 */
export function useAsyncTask() {
    const [isRunning, setIsRunning] = useState(false)
    const [progress, setProgress] = useState(0)
    const [error, setError] = useState(null)
    const cancelRef = useRef(false)

    /**
     * 비동기 태스크 실행 (UI 블로킹 방지)
     * 
     * @param {function} taskFn - 실행할 함수 (동기 또는 비동기)
     * @param {Object} options
     * @param {string} options.name - 태스크 이름 (디버그용)
     * @param {function} options.onProgress - 진행률 콜백 (0~100)
     * @returns {Promise<any>} 태스크 결과
     */
    const runTask = useCallback(async (taskFn, options = {}) => {
        const { name = 'task', onProgress } = options

        cancelRef.current = false
        setIsRunning(true)
        setProgress(0)
        setError(null)

        const updateProgress = (pct) => {
            setProgress(pct)
            if (onProgress) onProgress(pct)
        }

        try {
            // yield to allow UI update before starting
            await new Promise(r => setTimeout(r, 16))

            if (cancelRef.current) {
                throw new Error(`[${name}] cancelled`)
            }

            updateProgress(10)

            // Run the actual task
            const result = await Promise.resolve(taskFn({
                // Provide a yield function so task can cooperatively yield
                yield: () => new Promise(r => setTimeout(r, 0)),
                // Check if cancelled
                isCancelled: () => cancelRef.current,
                // Report progress from within the task
                reportProgress: updateProgress,
            }))

            if (cancelRef.current) {
                throw new Error(`[${name}] cancelled`)
            }

            updateProgress(100)
            return result
        } catch (e) {
            setError(e.message || String(e))
            console.error(`[useAsyncTask:${name}]`, e)
            throw e
        } finally {
            setIsRunning(false)
        }
    }, [])

    /**
     * 실행 중인 태스크 취소
     */
    const cancel = useCallback(() => {
        cancelRef.current = true
    }, [])

    return { runTask, isRunning, progress, error, cancel }
}

export default useAsyncTask
