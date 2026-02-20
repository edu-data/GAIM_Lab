"""
GAIM Lab - Cloud Run 전용 메인 (인증 API만 포함)
ML 의존성 없이 경량 실행
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api import auth

app = FastAPI(
    title="GAIM Lab Auth API",
    description="GAIM Lab 인증 서비스 (Cloud Run)",
    version="7.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
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

# 인증 라우터만 등록
app.include_router(auth.router, prefix="/api/v1", tags=["인증"])


@app.get("/")
async def root():
    return {
        "name": "GAIM Lab Auth API",
        "version": "7.1.0",
        "mode": "cloud-run-auth-only",
        "status": "running",
        "endpoints": {
            "docs": "/api/docs",
            "auth": "/api/v1/auth",
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
