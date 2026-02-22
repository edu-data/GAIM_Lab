"""
GAIM Lab v8.0 — 환경 설정 (Pydantic BaseSettings)

에러 #5, #8 방지: 환경별 자동 감지 + DB 추상화
로컬(.env) / Cloud Run(환경변수) 동일 코드로 동작
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """GAIM Lab 전역 설정 — 환경변수 또는 .env 파일에서 자동 로드"""

    # ─── 환경 ───
    deploy_env: str = "local"          # local | cloud
    debug: bool = False

    # ─── 인증 ───
    jwt_secret: str = "gaim-lab-v8-dev-secret-key"
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # ─── 데이터베이스 ───
    database_url: str = ""             # 비어있으면 SQLite 자동 사용
    # Cloud SQL 전용 (database_url이 비어있고 deploy_env=cloud일 때)
    db_user: str = "gaim_user"
    db_pass: str = ""
    db_name: str = "gaim_auth"
    instance_connection_name: str = ""

    # ─── AI ───
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ─── 경로 ───
    data_dir: str = ""                 # 비어있으면 프로젝트 루트/data 사용
    upload_dir: str = ""               # 비어있으면 프로젝트 루트/uploads 사용

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def project_root(self) -> Path:
        """프로젝트 루트 디렉토리"""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def resolved_data_dir(self) -> Path:
        """데이터 디렉토리 (자동 생성)"""
        p = Path(self.data_dir) if self.data_dir else self.project_root / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def resolved_upload_dir(self) -> Path:
        """업로드 디렉토리 (자동 생성)"""
        p = Path(self.upload_dir) if self.upload_dir else self.project_root / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sqlite_url(self) -> str:
        """SQLite 연결 URL"""
        db_path = self.resolved_data_dir / "gaim_lab.db"
        return f"sqlite:///{db_path}"

    @property
    def is_cloud(self) -> bool:
        return self.deploy_env == "cloud"

    @property
    def is_local(self) -> bool:
        return self.deploy_env == "local"


@lru_cache()
def get_settings() -> Settings:
    """싱글턴 설정 인스턴스 (캐시됨)"""
    return Settings()
