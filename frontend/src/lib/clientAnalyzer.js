/**
 * GAIM Lab — 클라이언트 사이드 분석기
 * 
 * GitHub Pages 배포 환경에서 백엔드 없이
 * 브라우저에서 직접 Gemini API를 호출하여 수업 영상을 분석합니다.
 * 
 * 파이프라인:
 *   1. 비디오 → 프레임 캡처 (Canvas API)
 *   2. Gemini gemini-2.0-flash 모델에 이미지 + 프롬프트 전송
 *   3. 7차원 수업 평가 결과 반환
 */

import { GoogleGenerativeAI } from '@google/generative-ai'

// 7차원 평가 프롬프트 (백엔드 gemini_evaluator.py와 동일)
const EVALUATION_PROMPT = `당신은 초등학교 교사 임용 2차 수업실연 평가 전문가입니다.
다음 수업 영상의 캡처 이미지들을 분석하여 7차원으로 평가해주세요.

[평가 기준]
1. 수업 전문성 (20점 만점)
   - 학습목표 명료성: 학습 목표가 명확하게 제시되었는가
   - 학습내용 충실성: 교육과정에 맞는 내용을 충실히 다루었는가

2. 교수학습 방법 (20점 만점)
   - 교수법 다양성: 다양한 교수 방법을 활용하는가
   - 학습활동 효과성: 학습 활동이 목표 달성에 효과적인가

3. 판서 및 언어 (15점 만점)
   - 판서 가독성: 핵심 내용을 명료하게 정리하는가
   - 언어 명료성: 발화가 정확하고 명료한가
   - 발화속도 적절성: 학습자 수준에 맞는 속도인가

4. 수업 태도 (15점 만점)
   - 교사 열정: 수업에 대한 열정이 느껴지는가
   - 학생 소통: 학생과의 상호작용이 자연스러운가
   - 자신감: 자신감 있는 태도로 수업하는가

5. 학생 참여 (15점 만점)
   - 질문 기법: 효과적인 발문을 사용하는가
   - 피드백 제공: 학생 반응에 적절히 피드백하는가

6. 시간 배분 (10점 만점)
   - 시간 균형: 도입-전개-정리가 균형 있게 배분되었는가

7. 창의성 (5점 만점)
   - 수업 창의성: 독창적인 아이디어와 교수 기법을 사용하는가

[응답 형식]
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "수업_전문성": {
    "점수": "0-20 사이 정수",
    "학습목표_명료성": "0-10 사이 정수",
    "학습내용_충실성": "0-10 사이 정수",
    "근거": "평가 근거 설명"
  },
  "교수학습_방법": {
    "점수": "0-20 사이 정수",
    "교수법_다양성": "0-10 사이 정수",
    "학습활동_효과성": "0-10 사이 정수",
    "근거": "평가 근거 설명"
  },
  "판서_및_언어": {
    "점수": "0-15 사이 정수",
    "판서_가독성": "0-5 사이 정수",
    "언어_명료성": "0-5 사이 정수",
    "발화속도_적절성": "0-5 사이 정수",
    "근거": "평가 근거 설명"
  },
  "수업_태도": {
    "점수": "0-15 사이 정수",
    "교사_열정": "0-5 사이 정수",
    "학생_소통": "0-5 사이 정수",
    "자신감": "0-5 사이 정수",
    "근거": "평가 근거 설명"
  },
  "학생_참여": {
    "점수": "0-15 사이 정수",
    "질문_기법": "0-7 사이 정수",
    "피드백_제공": "0-8 사이 정수",
    "근거": "평가 근거 설명"
  },
  "시간_배분": {
    "점수": "0-10 사이 정수",
    "시간_균형": "0-10 사이 정수",
    "근거": "평가 근거 설명"
  },
  "창의성": {
    "점수": "0-5 사이 정수",
    "수업_창의성": "0-5 사이 정수",
    "근거": "평가 근거 설명"
  },
  "총점": "0-100 사이 정수",
  "종합_평가": "전반적인 수업 시연에 대한 종합 평가",
  "강점": ["강점 1", "강점 2"],
  "개선점": ["개선점 1", "개선점 2"]
}`


/**
 * 비디오에서 프레임을 캡처합니다.
 * @param {File} videoFile - 비디오 파일
 * @param {number} count - 캡처할 프레임 수
 * @param {Function} onProgress - 진행 콜백
 * @param {number} [knownDuration] - 알려진 비디오 길이 (초), MediaRecorder 녹화시 전달
 * @returns {Promise<string[]>} base64 인코딩된 프레임 배열
 */
async function captureFrames(videoFile, count = 8, onProgress = () => { }, knownDuration = 0) {
    return new Promise((resolve, reject) => {
        const video = document.createElement('video')
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        const frames = []

        video.muted = true
        video.playsInline = true
        video.preload = 'auto'

        const url = URL.createObjectURL(videoFile)
        video.src = url

        video.onloadedmetadata = () => {
            canvas.width = Math.min(video.videoWidth, 1280)
            canvas.height = Math.round(canvas.width * (video.videoHeight / video.videoWidth))

            let duration = video.duration

            // MediaRecorder WebM blobs often report Infinity duration
            if (!isFinite(duration) || duration <= 0) {
                duration = knownDuration > 0 ? knownDuration : 30 // fallback 30초
            }

            const interval = duration / (count + 1)
            let currentFrame = 0

            const captureNext = () => {
                if (currentFrame >= count) {
                    URL.revokeObjectURL(url)
                    video.remove()
                    resolve(frames)
                    return
                }

                const time = Math.min(interval * (currentFrame + 1), duration - 0.1)
                if (!isFinite(time) || time < 0) {
                    // safety: skip if still non-finite
                    currentFrame++
                    captureNext()
                    return
                }
                video.currentTime = time
            }

            video.onseeked = () => {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
                const dataUrl = canvas.toDataURL('image/jpeg', 0.7)
                const base64 = dataUrl.split(',')[1]
                frames.push(base64)
                currentFrame++
                onProgress(Math.round((currentFrame / count) * 20))
                captureNext()
            }

            captureNext()
        }

        video.onerror = (e) => {
            URL.revokeObjectURL(url)
            reject(new Error('비디오를 로드할 수 없습니다.'))
        }
    })
}


/**
 * Gemini API raw 결과를 프론트엔드 dimensions 형식으로 변환
 */
function convertToFrontendFormat(geminiResult) {
    const dimensionMap = [
        { key: '수업_전문성', name: '수업 전문성', maxScore: 20 },
        { key: '교수학습_방법', name: '교수학습 방법', maxScore: 20 },
        { key: '판서_및_언어', name: '판서 및 언어', maxScore: 15 },
        { key: '수업_태도', name: '수업 태도', maxScore: 15 },
        { key: '학생_참여', name: '학생 참여', maxScore: 15 },
        { key: '시간_배분', name: '시간 배분', maxScore: 10 },
        { key: '창의성', name: '창의성', maxScore: 5 },
    ]

    const dimensions = dimensionMap.map(dim => {
        const data = geminiResult[dim.key] || {}
        const score = typeof data.점수 === 'number' ? data.점수 : parseInt(data.점수) || 0
        return {
            name: dim.name,
            dimension: dim.key,
            score,
            max_score: dim.maxScore,
            percentage: Math.round((score / dim.maxScore) * 100),
            feedback: data.근거 || '',
        }
    })

    const totalScore = typeof geminiResult.총점 === 'number'
        ? geminiResult.총점
        : parseInt(geminiResult.총점) || dimensions.reduce((s, d) => s + d.score, 0)

    const grade = totalScore >= 90 ? 'A' :
        totalScore >= 80 ? 'B' :
            totalScore >= 70 ? 'C+' :
                totalScore >= 60 ? 'C' :
                    totalScore >= 50 ? 'D' : 'F'

    return {
        status: 'completed',
        total_score: totalScore,
        grade,
        dimensions,
        strengths: geminiResult.강점 || [],
        improvements: geminiResult.개선점 || [],
        overall_feedback: geminiResult.종합_평가 || '',
    }
}


/**
 * 클라이언트 사이드에서 비디오를 Gemini API로 분석합니다.
 * 
 * @param {File} videoFile - 분석할 비디오 파일
 * @param {string} apiKey - Google API Key
 * @param {Function} onProgress - 진행 콜백 (0~100, message)
 * @param {Object} [transcriptData] - 실시간 코칭 전사 데이터 (선택)
 * @param {string} [transcriptData.text] - 전사 텍스트
 * @param {number} [transcriptData.durationSec] - 세션 시간 (초)
 * @param {number} [transcriptData.avgWpm] - 평균 WPM
 * @param {number} [transcriptData.fillerCount] - 필러 단어 수
 * @param {number} [transcriptData.silenceRatio] - 침묵 비율
 * @returns {Promise<Object>} 프론트엔드 형식의 분석 결과
 */
export async function analyzeVideoClient(videoFile, apiKey, onProgress = () => { }, transcriptData = null) {
    if (!apiKey) throw new Error('Google API Key가 필요합니다.')

    onProgress(5, '📤 비디오 프레임 추출 중...')

    // 1. 프레임 캡처 (MediaRecorder 녹화의 경우 knownDuration 전달)
    const knownDuration = transcriptData?.durationSec || 0
    const frames = await captureFrames(videoFile, 8, (p) => {
        onProgress(5 + p, '🎞️ 비디오 프레임 추출 중...')
    }, knownDuration)

    onProgress(30, '🚀 Gemini API에 전송 중...')

    // 2. Gemini API 호출
    const genAI = new GoogleGenerativeAI(apiKey)
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })

    const imageParts = frames.map(base64 => ({
        inlineData: {
            data: base64,
            mimeType: 'image/jpeg',
        }
    }))

    onProgress(50, '🤖 AI가 수업을 분석하고 있어요...')

    // 프롬프트 구성: 기본 평가 + 전사 텍스트 보강
    const promptParts = [EVALUATION_PROMPT]
    if (transcriptData?.text && transcriptData.text.length > 10) {
        promptParts.push(`\n\n[추가 데이터 — 실시간 전사 텍스트]\n아래는 이 수업의 음성 전사 텍스트입니다. 영상 프레임과 함께 종합적으로 평가하세요.\n\n전사 텍스트: "${transcriptData.text}"\n세션 시간: ${Math.round(transcriptData.durationSec || 0)}초\n평균 말하기 속도: ${Math.round(transcriptData.avgWpm || 0)} WPM\n필러 단어 수: ${transcriptData.fillerCount || 0}\n침묵 비율: ${Math.round((transcriptData.silenceRatio || 0) * 100)}%`)
    }

    const result = await model.generateContent([
        ...promptParts,
        ...imageParts,
    ])

    onProgress(80, '📊 평가 결과 정리 중...')

    // 3. 결과 파싱
    let responseText = result.response.text().trim()

    // JSON 블록 추출
    if (responseText.includes('```json')) {
        responseText = responseText.split('```json')[1].split('```')[0]
    } else if (responseText.includes('```')) {
        responseText = responseText.split('```')[1].split('```')[0]
    }

    let geminiResult
    try {
        geminiResult = JSON.parse(responseText)
    } catch (e) {
        throw new Error('AI 응답을 해석할 수 없습니다. 다시 시도해 주세요.')
    }

    onProgress(95, '✅ 분석 완료!')

    // 4. 프론트엔드 형식으로 변환
    const formatted = convertToFrontendFormat(geminiResult)
    formatted.id = `client_${Date.now()}`
    formatted.video_name = videoFile.name

    onProgress(100, '✅ 완료')

    return formatted
}


/**
 * API Key 유효성 간단 검증
 */
export function validateApiKey(key) {
    if (!key || typeof key !== 'string') return false
    return key.trim().length >= 30 && key.trim().startsWith('AIza')
}


/**
 * localStorage에서 API Key 가져오기
 */
export function getStoredApiKey() {
    try {
        return localStorage.getItem('gaim_google_api_key') || ''
    } catch {
        return ''
    }
}


/**
 * localStorage에 API Key 저장
 */
export function setStoredApiKey(key) {
    try {
        localStorage.setItem('gaim_google_api_key', key)
    } catch { /* ignore */ }
}


/**
 * 현재 환경이 GitHub Pages인지 확인
 */
export function isGitHubPages() {
    return typeof window !== 'undefined' &&
        window.location.hostname !== 'localhost' &&
        window.location.hostname !== '127.0.0.1'
}


/**
 * 실시간 코칭 전사 텍스트 + 메트릭을 Gemini API로 7차원 평가합니다.
 * 
 * @param {Object} params
 * @param {string} params.transcript - 전체 전사 텍스트
 * @param {number} params.durationSec - 세션 시간 (초)
 * @param {number} params.avgWpm - 평균 WPM
 * @param {number} params.totalWords - 총 단어 수
 * @param {number} params.silenceRatio - 침묵 비율 (0~1)
 * @param {number} params.fillerCount - 필러 횟수
 * @param {number} params.uniqueWords - 고유 단어 수
 * @param {Object} params.videoMetrics - 영상 메트릭 {avgMovement, gestureCount}
 * @param {string} apiKey - Google API Key
 * @returns {Promise<Object>} 7차원 평가 결과
 */
export async function analyzeTranscript({ transcript, durationSec, avgWpm, totalWords, silenceRatio, fillerCount, uniqueWords, videoMetrics }, apiKey) {
    if (!apiKey) throw new Error('Google API Key가 필요합니다.')

    const mins = (durationSec / 60).toFixed(1)
    const silencePct = (silenceRatio * 100).toFixed(0)
    const vm = videoMetrics || {}

    const prompt = `당신은 초등학교 교사 임용 2차 수업실연 평가 전문가입니다.
아래 실시간 코칭 세션의 전사 텍스트와 발화 데이터를 바탕으로 7차원 수업 평가를 진행해주세요.

[세션 정보]
- 수업 시간: ${mins}분 (${Math.round(durationSec)}초)
- 평균 말 속도: ${Math.round(avgWpm)} WPM
- 총 발화량: ${totalWords}어절
- 침묵 비율: ${silencePct}%
- 필러(음, 어, 그 등) 횟수: ${fillerCount}회
- 고유 어휘 수: ${uniqueWords}개
- 제스처/움직임 횟수: ${vm.gestureCount || 0}회
- 평균 움직임 강도: ${vm.avgMovement || 0}

[전사 텍스트]
${transcript || '(전사 내용 없음)'}

[평가 기준]
1. 수업 전문성 (20점 만점) - 학습목표 명료성, 학습내용 충실성
2. 교수학습 방법 (20점 만점) - 교수법 다양성, 학습활동 효과성
3. 판서 및 언어 (15점 만점) - 언어 명료성, 발화속도 적절성, 어휘 사용
4. 수업 태도 (15점 만점) - 교사 열정, 학생 소통, 자신감
5. 학생 참여 (15점 만점) - 질문 기법, 피드백 제공
6. 시간 배분 (10점 만점) - 수업 단계별 시간 균형
7. 창의성 (5점 만점) - 독창적인 교수 기법

※ 참고: 이 데이터는 실시간 코칭 세션에서 수집된 것으로, 실제 교실 수업의 일부만 반영될 수 있습니다.
  전사 텍스트의 내용과 발화 데이터를 종합적으로 고려하여 평가해주세요.

[응답 형식]
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "수업_전문성": { "점수": "0-20", "근거": "..." },
  "교수학습_방법": { "점수": "0-20", "근거": "..." },
  "판서_및_언어": { "점수": "0-15", "근거": "..." },
  "수업_태도": { "점수": "0-15", "근거": "..." },
  "학생_참여": { "점수": "0-15", "근거": "..." },
  "시간_배분": { "점수": "0-10", "근거": "..." },
  "창의성": { "점수": "0-5", "근거": "..." },
  "총점": "0-100",
  "종합_평가": "전반적인 평가",
  "강점": ["강점 1", "강점 2"],
  "개선점": ["개선점 1", "개선점 2"]
}`

    const genAI = new GoogleGenerativeAI(apiKey)
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })

    const result = await model.generateContent([prompt])
    let responseText = result.response.text().trim()

    // JSON 블록 추출
    if (responseText.includes('```json')) {
        responseText = responseText.split('```json')[1].split('```')[0]
    } else if (responseText.includes('```')) {
        responseText = responseText.split('```')[1].split('```')[0]
    }

    let geminiResult
    try {
        geminiResult = JSON.parse(responseText)
    } catch (e) {
        console.error('[analyzeTranscript] Parse error:', responseText)
        throw new Error('AI 응답을 해석할 수 없습니다.')
    }

    return convertToFrontendFormat(geminiResult)
}
