"""
GAIM Lab v7.1 — Live Coaching (실시간 코칭 라이트)

WebSocket 기반 실시간 분석:
- 브라우저 마이크 → 오디오 청크 수신
- Whisper STT (tiny) → 텍스트 변환
- 간이 피드백: 필러 카운트, 말 속도(WPM), 침묵 비율, 즉시 팁
"""

import asyncio
import json
import time
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# ── 필러 패턴 (한국어 + 영어) ──
FILLER_PATTERNS = re.compile(
    r'\b(음|어|그|저|이제|뭐|아|에|그러니까|있잖아|'
    r'um|uh|like|you know|so|well|basically|actually)\b',
    re.IGNORECASE
)

# ── 침묵 감지 임계값 ──
SILENCE_THRESHOLD_SEC = 3.0

# ── 피드백 규칙 ──
def _generate_tips(filler_count: int, wpm: float, silence_ratio: float) -> list:
    """실시간 피드백 팁 생성"""
    tips = []
    if filler_count > 5:
        tips.append("💬 필러 사용이 많습니다. '음', '어' 대신 잠시 멈추세요.")
    if wpm > 180:
        tips.append("⚡ 말이 빠릅니다. 핵심 내용에서 속도를 줄여보세요.")
    elif wpm < 80 and wpm > 0:
        tips.append("🐌 말이 느립니다. 에너지를 높여 학생 집중도를 유지하세요.")
    if silence_ratio > 0.4:
        tips.append("🔇 침묵이 길어지고 있습니다. 발문이나 활동을 시작하세요.")
    elif silence_ratio < 0.05 and wpm > 0:
        tips.append("💡 학생에게 생각할 시간을 주세요 (3초 대기).")
    if not tips:
        tips.append("✅ 현재 좋은 페이스를 유지하고 있습니다!")
    return tips


class LiveCoachingSession:
    """단일 WebSocket 세션의 분석 상태"""

    def __init__(self):
        self.start_time = time.time()
        self.total_words = 0
        self.filler_count = 0
        self.silence_segments = 0
        self.total_segments = 0
        self.transcript_chunks = []

    def process_text(self, text: str) -> dict:
        """텍스트 청크를 분석하고 피드백 반환"""
        self.total_segments += 1

        if not text.strip():
            self.silence_segments += 1
        else:
            words = text.split()
            self.total_words += len(words)
            fillers = FILLER_PATTERNS.findall(text)
            self.filler_count += len(fillers)
            self.transcript_chunks.append(text)

        elapsed = max(time.time() - self.start_time, 1)
        wpm = (self.total_words / elapsed) * 60
        silence_ratio = (self.silence_segments / max(self.total_segments, 1))

        tips = _generate_tips(self.filler_count, wpm, silence_ratio)

        return {
            "type": "feedback",
            "elapsed_sec": round(elapsed, 1),
            "total_words": self.total_words,
            "filler_count": self.filler_count,
            "wpm": round(wpm, 1),
            "silence_ratio": round(silence_ratio, 3),
            "tips": tips,
            "latest_text": text.strip() or "(침묵)",
        }

    def get_summary(self) -> dict:
        """세션 종료 시 요약"""
        elapsed = max(time.time() - self.start_time, 1)
        return {
            "type": "summary",
            "duration_sec": round(elapsed, 1),
            "total_words": self.total_words,
            "filler_count": self.filler_count,
            "avg_wpm": round((self.total_words / elapsed) * 60, 1),
            "silence_ratio": round(self.silence_segments / max(self.total_segments, 1), 3),
            "transcript": " ".join(self.transcript_chunks),
        }


@router.websocket("/ws/live-coaching")
async def live_coaching_ws(websocket: WebSocket):
    """
    WebSocket 실시간 코칭 엔드포인트

    클라이언트 메시지 형식:
    - {"type": "text", "content": "인식된 텍스트"}  (브라우저 Web Speech API 결과)
    - {"type": "stop"}  (세션 종료)
    """
    await websocket.accept()
    session = LiveCoachingSession()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                # 텍스트 그대로 처리
                msg = {"type": "text", "content": raw}

            if msg.get("type") == "stop":
                summary = session.get_summary()
                await websocket.send_json(summary)
                break
            elif msg.get("type") == "text":
                feedback = session.process_text(msg.get("content", ""))
                await websocket.send_json(feedback)
            else:
                await websocket.send_json({"type": "error", "message": "Unknown message type"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
