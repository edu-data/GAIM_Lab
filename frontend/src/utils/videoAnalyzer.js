/**
 * 클라이언트 사이드 비디오 분석 엔진
 * Canvas + Web Audio API를 활용한 실제 비디오 분석
 */

// ── Extractor: 비디오에서 프레임 + 오디오 추출 ──
export async function extractResources(videoFile, onProgress) {
    const url = URL.createObjectURL(videoFile)

    // 비디오 로드 (먼저!)
    const video = document.createElement('video')
    video.muted = true
    video.playsInline = true
    video.preload = 'auto'
    video.src = url

    await new Promise((resolve, reject) => {
        const done = () => { video.onloadeddata = null; video.onerror = null; resolve() }
        video.onloadeddata = done
        video.onerror = () => { video.onloadeddata = null; reject(new Error('비디오 로드 실패')) }
        setTimeout(() => { video.onloadeddata = null; reject(new Error('비디오 로드 시간 초과 (30초)')) }, 30000)
    })

    const duration = video.duration
    if (!duration || !isFinite(duration) || duration <= 0) {
        URL.revokeObjectURL(url)
        throw new Error('비디오 길이를 읽을 수 없습니다')
    }

    if (onProgress) onProgress(5)

    const width = Math.min(video.videoWidth || 320, 320)
    const height = Math.round((video.videoHeight || 240) * (width / (video.videoWidth || 320)))
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d', { willReadFrequently: true })

    // 동적 샘플링: 최대 60프레임까지만
    const maxFrames = 60
    const interval = Math.max(1, Math.floor(duration / maxFrames))
    const totalFrames = Math.min(Math.floor(duration / interval), maxFrames)
    const frames = []

    for (let i = 0; i < totalFrames; i++) {
        const time = i * interval
        try {
            // seek
            await new Promise((resolve) => {
                const handler = () => { video.removeEventListener('seeked', handler); resolve() }
                video.addEventListener('seeked', handler)
                video.currentTime = time
                setTimeout(() => { video.removeEventListener('seeked', handler); resolve() }, 2000)
            })
            // UI 스레드에 양보 (검정 화면 방지)
            await new Promise(r => setTimeout(r, 0))
            ctx.drawImage(video, 0, 0, width, height)
            const imageData = ctx.getImageData(0, 0, width, height)
            frames.push({ time, imageData, width, height })
        } catch (e) {
            console.warn(`Frame ${i} skip:`, e.message)
        }
        if (onProgress) onProgress(5 + Math.round((i / totalFrames) * 75))
    }

    // 오디오: 50MB 미만일 때만 추출 (메모리 보호)
    let audioData = null
    if (videoFile.size < 50 * 1024 * 1024) {
        try {
            if (onProgress) onProgress(85)
            const ab = await videoFile.arrayBuffer()
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
            audioData = await audioCtx.decodeAudioData(ab)
            audioCtx.close()
        } catch (e) {
            console.warn('Audio decode skipped:', e.message)
        }
    } else {
        console.log('Audio skipped: file too large (' + (videoFile.size / 1024 / 1024).toFixed(0) + 'MB)')
    }

    URL.revokeObjectURL(url)
    if (onProgress) onProgress(100)

    if (frames.length === 0) {
        throw new Error('프레임을 추출할 수 없습니다. 지원되는 비디오 형식인지 확인하세요.')
    }

    return {
        frames,
        audioData,
        duration,
        width,
        height,
        totalFrames: frames.length,
        fps: 1 / interval,
        videoWidth: video.videoWidth || width,
        videoHeight: video.videoHeight || height,
    }
}

// ── Vision Agent: 움직임 + 제스처 분석 ──
export function analyzeVision(frames, onProgress) {
    const movements = []
    let totalMovement = 0
    let highMovementCount = 0
    let lowMovementCount = 0

    for (let i = 1; i < frames.length; i++) {
        const prev = frames[i - 1].imageData.data
        const curr = frames[i].imageData.data
        let diff = 0
        const pixelCount = prev.length / 4

        for (let p = 0; p < prev.length; p += 16) { // 샘플링 (4px 간격)
            diff += Math.abs(prev[p] - curr[p])       // R
            diff += Math.abs(prev[p + 1] - curr[p + 1]) // G
            diff += Math.abs(prev[p + 2] - curr[p + 2]) // B
        }

        const normalizedDiff = diff / (pixelCount / 4 * 3) // 0-255 스케일
        const movementPercent = Math.min(100, (normalizedDiff / 30) * 100)
        movements.push({ time: frames[i].time, movement: movementPercent })
        totalMovement += movementPercent

        if (movementPercent > 40) highMovementCount++
        else if (movementPercent < 10) lowMovementCount++

        if (onProgress) onProgress(Math.round((i / frames.length) * 100))
    }

    const avgMovement = totalMovement / Math.max(1, movements.length)
    const gestureActivity = (highMovementCount / Math.max(1, movements.length)) * 100

    return {
        movements,
        avgMovement: +avgMovement.toFixed(1),
        gestureActivity: +gestureActivity.toFixed(1),
        highMovementFrames: highMovementCount,
        lowMovementFrames: lowMovementCount,
        totalFrames: frames.length,
        desc: `제스처 활성 ${gestureActivity.toFixed(1)}%, 평균 움직임 ${avgMovement.toFixed(1)}%`,
    }
}

// ── Content Agent: 슬라이드 변화 감지 ──
export function analyzeContent(frames, onProgress) {
    const slideChanges = []
    let currentSlideStart = 0
    const SLIDE_THRESHOLD = 25 // 슬라이드 전환 감지 임계값

    // 화면 상단 70%만 분석 (슬라이드 영역)
    for (let i = 1; i < frames.length; i++) {
        const prev = frames[i - 1].imageData
        const curr = frames[i].imageData
        const w = prev.width
        const h = Math.floor(prev.height * 0.7)
        let diff = 0
        let count = 0

        for (let y = 0; y < h; y += 4) {
            for (let x = 0; x < w; x += 4) {
                const idx = (y * w + x) * 4
                const dr = Math.abs(prev.data[idx] - curr.data[idx])
                const dg = Math.abs(prev.data[idx + 1] - curr.data[idx + 1])
                const db = Math.abs(prev.data[idx + 2] - curr.data[idx + 2])
                diff += (dr + dg + db) / 3
                count++
            }
        }

        const avgDiff = diff / Math.max(1, count)
        if (avgDiff > SLIDE_THRESHOLD) {
            slideChanges.push({
                from: currentSlideStart,
                to: frames[i].time,
                duration: frames[i].time - currentSlideStart,
            })
            currentSlideStart = frames[i].time
        }

        if (onProgress) onProgress(Math.round((i / frames.length) * 100))
    }

    // 마지막 슬라이드
    const lastTime = frames[frames.length - 1]?.time || 0
    if (lastTime > currentSlideStart) {
        slideChanges.push({
            from: currentSlideStart,
            to: lastTime,
            duration: lastTime - currentSlideStart,
        })
    }

    // 프레임 밝기 분석 (텍스트 밀도 추정)
    let totalBrightness = 0
    for (const frame of frames) {
        const d = frame.imageData.data
        let brightness = 0
        for (let i = 0; i < d.length; i += 16) {
            brightness += (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114)
        }
        totalBrightness += brightness / (d.length / 16)
    }
    const avgBrightness = totalBrightness / frames.length
    const textDensity = Math.min(100, Math.round(avgBrightness / 2.55))

    return {
        slideChanges,
        slideCount: slideChanges.length,
        avgBrightness: +avgBrightness.toFixed(1),
        textDensity,
        desc: `슬라이드 ${slideChanges.length}장 감지, 텍스트 밀도 ${textDensity}`,
    }
}

// ── STT Agent (시뮬레이션): 오디오 기반 음성 활동 감지 ──
export function analyzeSTT(audioData, onProgress) {
    if (!audioData) {
        if (onProgress) onProgress(100)
        return {
            speechActivity: 0,
            silenceRatio: 100,
            estimatedWords: 0,
            segments: [],
            desc: '오디오 데이터 없음',
        }
    }

    const channelData = audioData.getChannelData(0)
    const sampleRate = audioData.sampleRate
    const segmentSize = Math.floor(sampleRate * 0.5) // 0.5초 세그먼트
    const segments = []
    let speechFrames = 0
    let silenceFrames = 0
    const totalSegments = Math.floor(channelData.length / segmentSize)

    for (let i = 0; i < totalSegments; i++) {
        const start = i * segmentSize
        const end = Math.min(start + segmentSize, channelData.length)
        let rms = 0
        for (let j = start; j < end; j++) {
            rms += channelData[j] * channelData[j]
        }
        rms = Math.sqrt(rms / (end - start))

        const isSpeech = rms > 0.02
        if (isSpeech) speechFrames++
        else silenceFrames++

        segments.push({
            time: +(i * 0.5).toFixed(1),
            rms: +rms.toFixed(4),
            isSpeech,
        })

        if (onProgress) onProgress(Math.round((i / totalSegments) * 100))
    }

    const total = speechFrames + silenceFrames
    const speechRatio = total > 0 ? (speechFrames / total) * 100 : 0
    const silenceRatio = 100 - speechRatio
    // 추정 어절: 음성 활성 시간 × 분당 약 200어절 / 60초 × 0.5초 세그먼트
    const estimatedWords = Math.round(speechFrames * 0.5 * (200 / 60))

    return {
        speechActivity: +speechRatio.toFixed(1),
        silenceRatio: +silenceRatio.toFixed(1),
        estimatedWords,
        segments,
        desc: `음성 활성 ${speechRatio.toFixed(1)}%, 추정 ${estimatedWords}어절`,
    }
}

// ── Vibe Agent: 오디오 프로소디(운율) 분석 ──
export function analyzeVibe(audioData, onProgress) {
    if (!audioData) {
        if (onProgress) onProgress(100)
        return {
            avgVolume: 0,
            volumeVariation: 0,
            silenceRatio: 0,
            energyTimeline: [],
            desc: '오디오 데이터 없음',
        }
    }

    const channelData = audioData.getChannelData(0)
    const sampleRate = audioData.sampleRate
    const windowSize = Math.floor(sampleRate * 1.0) // 1초 윈도우
    const totalWindows = Math.floor(channelData.length / windowSize)
    const energyTimeline = []
    let totalRms = 0
    let silentWindows = 0

    for (let i = 0; i < totalWindows; i++) {
        const start = i * windowSize
        const end = Math.min(start + windowSize, channelData.length)
        let rms = 0
        for (let j = start; j < end; j++) {
            rms += channelData[j] * channelData[j]
        }
        rms = Math.sqrt(rms / (end - start))
        const dbLevel = rms > 0 ? 20 * Math.log10(rms) : -100

        energyTimeline.push({ time: i, rms: +rms.toFixed(4), db: +dbLevel.toFixed(1) })
        totalRms += rms
        if (rms < 0.015) silentWindows++

        if (onProgress) onProgress(Math.round((i / totalWindows) * 100))
    }

    const avgRms = totalRms / Math.max(1, totalWindows)
    let variation = 0
    for (const e of energyTimeline) {
        variation += Math.pow(e.rms - avgRms, 2)
    }
    variation = Math.sqrt(variation / Math.max(1, totalWindows))

    const avgVolume = +(avgRms * 1000).toFixed(1)
    const volumeVariation = +(variation * 1000).toFixed(2)
    const silenceRatio = +((silentWindows / Math.max(1, totalWindows)) * 100).toFixed(1)

    return {
        avgVolume,
        volumeVariation,
        silenceRatio,
        energyTimeline,
        desc: `볼륨 변동 ${volumeVariation}, 침묵 비율 ${silenceRatio}%`,
    }
}

// ── Pedagogy Agent: 7차원 교육학 평가 ──
export function evaluatePedagogy(visionResult, contentResult, sttResult, vibeResult, onProgress) {
    if (onProgress) onProgress(10)

    // 1. 교수 전달력 (음성 기반)
    const deliveryScore = Math.min(20, Math.round(
        (sttResult.speechActivity > 60 ? 12 : sttResult.speechActivity > 40 ? 8 : 4) +
        (vibeResult.volumeVariation > 2 ? 5 : vibeResult.volumeVariation > 1 ? 3 : 1) +
        (vibeResult.silenceRatio < 30 ? 3 : vibeResult.silenceRatio < 50 ? 1 : 0)
    ))
    if (onProgress) onProgress(25)

    // 2. 비언어적 소통 (제스처/움직임)
    const nonverbalScore = Math.min(15, Math.round(
        (visionResult.gestureActivity > 30 ? 10 : visionResult.gestureActivity > 15 ? 7 : 3) +
        (visionResult.avgMovement > 20 ? 5 : visionResult.avgMovement > 10 ? 3 : 1)
    ))
    if (onProgress) onProgress(40)

    // 3. 수업 구성 (슬라이드 변화)
    const structureScore = Math.min(15, Math.round(
        (contentResult.slideCount > 5 ? 10 : contentResult.slideCount > 2 ? 7 : 4) +
        (contentResult.textDensity > 50 ? 5 : contentResult.textDensity > 30 ? 3 : 1)
    ))
    if (onProgress) onProgress(55)

    // 4. 학습 자료 활용
    const materialScore = Math.min(10, Math.round(
        (contentResult.slideCount > 3 ? 7 : contentResult.slideCount > 1 ? 5 : 2) +
        (contentResult.avgBrightness > 100 ? 3 : 1)
    ))
    if (onProgress) onProgress(70)

    // 5. 시간 관리
    const timeScore = Math.min(10, Math.round(
        vibeResult.silenceRatio < 20 ? 8 :
            vibeResult.silenceRatio < 40 ? 6 :
                vibeResult.silenceRatio < 60 ? 4 : 2
    ))
    if (onProgress) onProgress(80)

    // 6. 학습자 상호작용 (추론)
    const interactionScore = Math.min(15, Math.round(
        (sttResult.speechActivity > 70 ? 5 : 3) +
        (visionResult.highMovementFrames > 10 ? 5 : 3) +
        (vibeResult.volumeVariation > 1.5 ? 5 : 3)
    ))
    if (onProgress) onProgress(90)

    // 7. 전문성
    const expertiseScore = Math.min(15, Math.round(
        (sttResult.estimatedWords > 500 ? 8 : sttResult.estimatedWords > 200 ? 5 : 3) +
        (contentResult.slideCount > 3 ? 4 : 2) +
        (visionResult.gestureActivity > 20 ? 3 : 1)
    ))
    if (onProgress) onProgress(100)

    const dimensions = [
        { name: '교수 전달력', score: deliveryScore, max: 20 },
        { name: '비언어적 소통', score: nonverbalScore, max: 15 },
        { name: '수업 구성', score: structureScore, max: 15 },
        { name: '학습 자료 활용', score: materialScore, max: 10 },
        { name: '시간 관리', score: timeScore, max: 10 },
        { name: '학습자 상호작용', score: interactionScore, max: 15 },
        { name: '전문성', score: expertiseScore, max: 15 },
    ]

    const totalScore = dimensions.reduce((sum, d) => sum + d.score, 0)
    const grade = totalScore >= 90 ? 'A+' : totalScore >= 80 ? 'A' : totalScore >= 70 ? 'B+' :
        totalScore >= 60 ? 'B' : totalScore >= 50 ? 'C+' : totalScore >= 40 ? 'C' : 'D'

    return {
        dimensions,
        totalScore,
        grade,
        desc: `7차원 평가: ${totalScore}/100 (${grade})`,
    }
}

// ── Feedback Agent: 피드백 생성 ──
export function generateFeedback(pedagogyResult, visionResult, vibeResult, onProgress) {
    if (onProgress) onProgress(20)

    const strengths = []
    const improvements = []

    for (const dim of pedagogyResult.dimensions) {
        const ratio = dim.score / dim.max
        if (ratio >= 0.7) {
            strengths.push({ dimension: dim.name, score: dim.score, max: dim.max, message: `${dim.name}이(가) 우수합니다 (${dim.score}/${dim.max})` })
        } else if (ratio < 0.5) {
            improvements.push({ dimension: dim.name, score: dim.score, max: dim.max, message: `${dim.name} 개선이 필요합니다 (${dim.score}/${dim.max})` })
        }
    }

    if (onProgress) onProgress(50)

    // 구체적 피드백
    const tips = []
    if (visionResult.gestureActivity < 20) tips.push('💡 제스처를 더 적극적으로 활용해보세요.')
    if (visionResult.avgMovement < 10) tips.push('💡 교실 내 이동을 늘려 학생과의 거리감을 줄여보세요.')
    if (vibeResult.silenceRatio > 40) tips.push('💡 침묵 구간이 길어요. 학생 참여를 유도하는 질문을 추가해보세요.')
    if (vibeResult.volumeVariation < 1) tips.push('💡 목소리에 억양 변화를 주면 학생들의 집중도가 높아집니다.')

    if (onProgress) onProgress(100)

    return {
        strengths,
        improvements,
        tips,
        totalFeedback: strengths.length + improvements.length + tips.length,
        desc: `강점 ${strengths.length}건, 개선점 ${improvements.length}건, 팁 ${tips.length}건`,
    }
}

// ── Master Agent: 종합 리포트 생성 ──
export function generateReport(extractResult, visionResult, contentResult, sttResult, vibeResult, pedagogyResult, feedbackResult, onProgress) {
    if (onProgress) onProgress(30)

    const report = {
        summary: {
            duration: extractResult.duration,
            totalFrames: extractResult.totalFrames,
            resolution: `${extractResult.videoWidth}×${extractResult.videoHeight}`,
            totalScore: pedagogyResult.totalScore,
            grade: pedagogyResult.grade,
        },
        dimensions: pedagogyResult.dimensions,
        metrics: {
            gestureActivity: visionResult.gestureActivity,
            avgMovement: visionResult.avgMovement,
            slideCount: contentResult.slideCount,
            speechActivity: sttResult.speechActivity,
            estimatedWords: sttResult.estimatedWords,
            silenceRatio: vibeResult.silenceRatio,
            volumeVariation: vibeResult.volumeVariation,
        },
        feedback: feedbackResult,
        timestamp: new Date().toISOString(),
    }

    if (onProgress) onProgress(100)

    return {
        report,
        desc: `종합 리포트: ${pedagogyResult.totalScore}점 (${pedagogyResult.grade})`,
    }
}
