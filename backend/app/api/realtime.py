"""
실시간 피드백 WebSocket API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.realtime_feedback import manager, get_tracker

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/analysis/{analysis_id}")
async def websocket_analysis_progress(websocket: WebSocket, analysis_id: str):
    """
    분석 진행 상황 실시간 스트리밍
    
    클라이언트는 이 WebSocket에 연결하여 분석 진행 상황을 실시간으로 수신합니다.
    
    메시지 형식:
    {
        "type": "progress" | "complete" | "error",
        "analysis_id": "...",
        "overall_progress": 0-100,
        "current_stage": {...},
        "stages": [...],
        "timeline": [...]
    }
    """
    await manager.connect(websocket, analysis_id)
    
    try:
        # 현재 상태 전송
        tracker = get_tracker(analysis_id)
        await tracker._send_update()
        
        # 연결 유지 및 클라이언트 메시지 수신
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터의 ping 처리
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, analysis_id)
    except Exception:
        manager.disconnect(websocket, analysis_id)


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket):
    """
    전역 알림 WebSocket
    
    모든 분석 완료 알림 등을 수신합니다.
    """
    await websocket.accept()
    
    # 임시 분석 ID로 연결 (전역 알림용)
    notification_id = "__notifications__"
    if notification_id not in manager.active_connections:
        manager.active_connections[notification_id] = set()
    manager.active_connections[notification_id].add(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.active_connections[notification_id].discard(websocket)
    except Exception:
        manager.active_connections[notification_id].discard(websocket)


# ─── v7.1: SSE (Server-Sent Events) endpoint ───
# Easier to use from frontend than WebSocket (works with EventSource API)

from fastapi import Request
from fastapi.responses import StreamingResponse
import asyncio
import json


@router.get("/sse/analysis/{analysis_id}")
async def sse_analysis_progress(analysis_id: str, request: Request):
    """
    v7.1: SSE 기반 분석 진행 상황 스트리밍

    클라이언트 사용법:
        const es = new EventSource('/api/v1/ws/sse/analysis/abc123')
        es.onmessage = (e) => console.log(JSON.parse(e.data))
    """
    async def event_stream():
        tracker = get_tracker(analysis_id)
        last_progress = -1

        while True:
            if await request.is_disconnected():
                break

            current = tracker.get_status()
            progress = current.get("overall_progress", 0)

            if progress != last_progress:
                data = json.dumps(current, ensure_ascii=False, default=str)
                yield f"data: {data}\n\n"
                last_progress = progress

                if current.get("type") in ("complete", "error"):
                    break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/status")
async def get_realtime_status():
    """v7.1: 현재 활성 분석 세션 상태 조회"""
    active = {
        aid: len(sockets)
        for aid, sockets in manager.active_connections.items()
        if aid != "__notifications__" and sockets
    }
    return {
        "active_sessions": len(active),
        "connections": active,
    }

