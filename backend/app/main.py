"""
GAIM Lab - FastAPI 메인 애플리케이션
GINUE AI Microteaching Lab 백엔드 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# v8.0: 동적 버전 참조 (pyproject.toml 단일 소스)
try:
    from importlib.metadata import version as pkg_version
    APP_VERSION = pkg_version("gaim-lab")
except Exception:
    APP_VERSION = "8.0.0"

from app.api import auth

# ML-dependent routers: gracefully skip if packages not installed (Cloud Run lightweight mode)
try:
    from app.api import analysis, portfolio, badges, mentoring, realtime, agents, history
    from app.api import live_coaching, cohort, rubric_experiment
    _ML_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"[WARN] ML modules not available, running in auth-only mode: {e}")
    _ML_AVAILABLE = False

# 앱 초기화
app = FastAPI(
    title="GAIM Lab API",
    description="GINUE AI Microteaching Lab - 예비교원 수업역량 강화 시스템",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://edu-data.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 — v7.0: 상대 경로 기반
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = _PROJECT_ROOT / "uploads"
OUTPUT_DIR = _PROJECT_ROOT / "output"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# 라우터 등록 — 인증은 항상 등록
app.include_router(auth.router, prefix="/api/v1", tags=["인증"])

# ML 라우터는 사용 가능할 때만 등록
if _ML_AVAILABLE:
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["분석"])
    app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["포트폴리오"])
    app.include_router(badges.router, prefix="/api/v1/badges", tags=["디지털 배지"])
    app.include_router(mentoring.router, prefix="/api/v1/mentoring", tags=["멘토링"])
    app.include_router(realtime.router, prefix="/api/v1", tags=["실시간"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["에이전트"])
    app.include_router(history.router, prefix="/api/v1", tags=["이력/성장"])
    app.include_router(live_coaching.router, prefix="/api/v1", tags=["실시간 코칭"])
    app.include_router(cohort.router, prefix="/api/v1/cohort", tags=["코호트 비교"])
    app.include_router(rubric_experiment.router, prefix="/api/v1/experiment", tags=["A/B 루브릭"])


@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "name": "GAIM Lab API",
        "version": APP_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/api/docs",
            "analysis": "/api/v1/analysis",
            "portfolio": "/api/v1/portfolio",
            "badges": "/api/v1/badges",
            "mentoring": "/api/v1/mentoring"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
