"""
실시간 피드백 WebSocket 모듈
분석 진행 상황을 실시간으로 클라이언트에 전송
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # analysis_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, analysis_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = set()
        self.active_connections[analysis_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, analysis_id: str):
        """클라이언트 연결 해제"""
        if analysis_id in self.active_connections:
            self.active_connections[analysis_id].discard(websocket)
            if not self.active_connections[analysis_id]:
                del self.active_connections[analysis_id]
    
    async def send_progress(self, analysis_id: str, data: dict):
        """특정 분석에 연결된 모든 클라이언트에 진행 상황 전송"""
        if analysis_id in self.active_connections:
            message = json.dumps(data, ensure_ascii=False)
            disconnected = set()
            for connection in self.active_connections[analysis_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.add(connection)
            # 연결 해제된 소켓 정리
            for conn in disconnected:
                self.active_connections[analysis_id].discard(conn)
    
    async def broadcast_all(self, data: dict):
        """모든 클라이언트에 메시지 전송"""
        message = json.dumps(data, ensure_ascii=False)
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass


# 전역 연결 관리자
manager = ConnectionManager()


class AnalysisProgressTracker:
    """분석 진행 상황 추적기"""
    
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.stages = [
            {"id": "upload", "name": "영상 업로드", "weight": 5},
            {"id": "audio_extract", "name": "오디오 추출", "weight": 10},
            {"id": "stt", "name": "음성 인식 (STT)", "weight": 20},
            {"id": "vision", "name": "비전 분석", "weight": 25},
            {"id": "vibe", "name": "오디오 분석", "weight": 15},
            {"id": "text", "name": "텍스트 분석", "weight": 10},
            {"id": "evaluation", "name": "7차원 평가", "weight": 10},
            {"id": "report", "name": "리포트 생성", "weight": 5},
        ]
        self.current_stage_idx = 0
        self.current_stage_progress = 0
        self.timeline_events = []
        self.start_time = datetime.now()
    
    def get_overall_progress(self) -> float:
        """전체 진행률 계산"""
        total = 0
        for i, stage in enumerate(self.stages):
            if i < self.current_stage_idx:
                total += stage["weight"]
            elif i == self.current_stage_idx:
                total += stage["weight"] * (self.current_stage_progress / 100)
        return round(total, 1)
    
    async def update_stage(self, stage_id: str, progress: float, message: str = None):
        """단계 진행 상황 업데이트"""
        # 현재 단계 찾기
        for i, stage in enumerate(self.stages):
            if stage["id"] == stage_id:
                self.current_stage_idx = i
                self.current_stage_progress = min(100, max(0, progress))
                break
        
        # 타임라인 이벤트 추가
        if message:
            self.timeline_events.append({
                "timestamp": datetime.now().isoformat(),
                "stage": stage_id,
                "message": message
            })
        
        # WebSocket으로 진행 상황 전송
        await self._send_update()
    
    async def add_timeline_event(self, event_type: str, message: str, data: dict = None):
        """타임라인 이벤트 추가"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        self.timeline_events.append(event)
        await self._send_update()
    
    async def complete(self, result: dict = None):
        """분석 완료"""
        self.current_stage_idx = len(self.stages)
        self.current_stage_progress = 100
        
        await manager.send_progress(self.analysis_id, {
            "type": "complete",
            "analysis_id": self.analysis_id,
            "progress": 100,
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "timeline": self.timeline_events[-10:],  # 최근 10개 이벤트
            "result": result
        })
    
    async def error(self, error_message: str):
        """분석 오류"""
        await manager.send_progress(self.analysis_id, {
            "type": "error",
            "analysis_id": self.analysis_id,
            "message": error_message,
            "progress": self.get_overall_progress(),
            "stage": self.stages[self.current_stage_idx]["name"]
        })
    
    def get_status(self) -> dict:
        """v7.1: 현재 상태를 동기적으로 반환 (SSE용)"""
        current_stage = self.stages[self.current_stage_idx] if self.current_stage_idx < len(self.stages) else None
        return {
            "type": "progress",
            "analysis_id": self.analysis_id,
            "overall_progress": self.get_overall_progress(),
            "current_stage": {
                "id": current_stage["id"] if current_stage else "complete",
                "name": current_stage["name"] if current_stage else "완료",
                "progress": self.current_stage_progress
            },
            "stages": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "status": "completed" if i < self.current_stage_idx
                              else ("in_progress" if i == self.current_stage_idx else "pending")
                }
                for i, s in enumerate(self.stages)
            ],
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "timeline": self.timeline_events[-5:]
        }

    async def _send_update(self):
        """진행 상황 업데이트 전송"""
        current_stage = self.stages[self.current_stage_idx] if self.current_stage_idx < len(self.stages) else None
        
        await manager.send_progress(self.analysis_id, {
            "type": "progress",
            "analysis_id": self.analysis_id,
            "overall_progress": self.get_overall_progress(),
            "current_stage": {
                "id": current_stage["id"] if current_stage else "complete",
                "name": current_stage["name"] if current_stage else "완료",
                "progress": self.current_stage_progress
            },
            "stages": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "status": "completed" if i < self.current_stage_idx 
                              else ("in_progress" if i == self.current_stage_idx else "pending")
                }
                for i, s in enumerate(self.stages)
            ],
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "timeline": self.timeline_events[-5:]  # 최근 5개 이벤트
        })


# 진행 상황 추적기 저장소
progress_trackers: Dict[str, AnalysisProgressTracker] = {}


def get_tracker(analysis_id: str) -> AnalysisProgressTracker:
    """분석 ID에 해당하는 추적기 반환 또는 생성"""
    if analysis_id not in progress_trackers:
        progress_trackers[analysis_id] = AnalysisProgressTracker(analysis_id)
    return progress_trackers[analysis_id]


def cleanup_tracker(analysis_id: str):
    """추적기 정리"""
    if analysis_id in progress_trackers:
        del progress_trackers[analysis_id]
