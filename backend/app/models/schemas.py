"""
GAIM Lab v8.0 — API 응답 스키마 (Pydantic Models)

에러 #3 방지: 백엔드-프론트엔드 간 API 계약을 코드로 명시
response_model 지정 시 응답 구조 변경 → 유효성 검사 → 즉시 감지
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# 분석 관련 스키마
# ═══════════════════════════════════════════════════════════

class DimensionResult(BaseModel):
    """7차원 개별 결과"""
    name: str
    score: float = 0
    max_score: float = 0
    percentage: float = 0
    grade: str = ""
    feedback: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """분석 요청"""
    use_turbo: bool = True
    use_text: bool = True


class AnalysisStatusResponse(BaseModel):
    """분석 상태 조회 응답"""
    id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = 0
    message: str = ""
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """분석 결과 응답 — 프론트엔드가 기대하는 플랫 구조"""
    id: str
    video_name: str = ""
    status: str = "completed"
    total_score: float = 0
    grade: str = ""
    dimensions: List[DimensionResult] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    overall_feedback: str = ""


class AnalysisUploadResponse(BaseModel):
    """분석 업로드 + 완료 응답 (동기 모드)"""
    id: str
    status: str = "completed"
    progress: int = 100
    message: str = ""
    created_at: str = ""
    total_score: float = 0
    grade: str = ""
    dimensions: List[DimensionResult] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    overall_feedback: str = ""


# ═══════════════════════════════════════════════════════════
# 인증 관련 스키마
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    role: str = "student"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    name: str = ""
    role: str
    expires_in: int = 86400  # 24시간


class UserResponse(BaseModel):
    """사용자 정보"""
    username: str
    name: str = ""
    email: str = ""
    role: str = "student"
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    new_password: str


class UserCreateRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    role: str = "student"
    email: str = ""


# ═══════════════════════════════════════════════════════════
# 성장 분석 관련 스키마
# ═══════════════════════════════════════════════════════════

class GrowthTrend(BaseModel):
    """성장 추세"""
    dimension: str
    trend: Literal["improving", "stable", "declining"]
    slope: float = 0
    recent_avg: float = 0


class GrowthResponse(BaseModel):
    """성장 분석 응답"""
    total_sessions: int = 0
    score_trend: List[float] = Field(default_factory=list)
    dimension_trends: List[GrowthTrend] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    roadmap: dict = Field(default_factory=dict)
