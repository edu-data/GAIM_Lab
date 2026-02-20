"""
GAIM Lab Auth API - Cloud Run Standalone Server
PostgreSQL via Cloud SQL Python Connector
"""

import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional
import base64

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ─── Configuration ───
SECRET_KEY = os.getenv("GAIM_SECRET_KEY", "gaim-lab-v71-dev-secret-key")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ─── Database Configuration ───
DB_USER = os.getenv("DB_USER", "gaim_user")
DB_PASS = os.getenv("DB_PASS", "gaim-user-2024")
DB_NAME = os.getenv("DB_NAME", "gaim_auth")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "gaim-lab-project-2024:asia-northeast3:gaim-lab-db")

# Use Cloud SQL Python Connector for secure connection
from google.cloud.sql.connector import Connector

connector = Connector()


def _get_db():
    """Get a pg8000 connection via Cloud SQL Connector."""
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )
    return conn


def _hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), SECRET_KEY.encode(), 100_000
    ).hex()


def _create_token(data: dict, expires_delta: timedelta = None) -> str:
    payload = data.copy()
    expire = time.time() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).total_seconds()
    payload["exp"] = expire
    payload["iat"] = time.time()
    raw = json.dumps(payload).encode()
    token_data = base64.b64encode(raw).decode()
    sig = hashlib.sha256((token_data + SECRET_KEY).encode()).hexdigest()
    return f"{token_data}.{sig}"


def _decode_token(token: str) -> dict:
    try:
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        token_data, sig = parts
        expected = hashlib.sha256((token_data + SECRET_KEY).encode()).hexdigest()
        if sig != expected:
            return None
        raw = base64.b64decode(token_data)
        payload = json.loads(raw)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# Init DB
def _init_db():
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(200) DEFAULT '',
            email VARCHAR(200) DEFAULT '',
            role VARCHAR(20) DEFAULT 'student',
            is_active BOOLEAN DEFAULT TRUE,
            provider VARCHAR(20) DEFAULT 'local',
            avatar VARCHAR(500) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM users")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (%s, %s, %s, %s)",
            ("admin", _hash_password("admin123"), "관리자", "admin")
        )
        conn.commit()
        print("[AUTH] Default admin created: admin / admin123")
    cur.close()
    conn.close()


_init_db()

# ─── Auth dependency ───
security = HTTPBearer(auto_error=False)


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, role, is_active FROM users WHERE username = %s", (payload["sub"],))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not row[2]:
        raise HTTPException(status_code=401, detail="비활성화된 계정")
    return {"username": row[0], "role": row[1]}


async def require_admin(user=Depends(require_auth)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능")
    return user


# ─── Pydantic Models ───
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
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    new_password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    role: str = "student"
    email: str = ""


# ─── Router ───
router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash, name, role, is_active FROM users WHERE username = %s", (req.username,))
    row = cur.fetchone()
    if not row or row[1] != _hash_password(req.password):
        cur.close(); conn.close()
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다")
    if not row[4]:
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
    cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = %s", (req.username,))
    conn.commit()
    username, _, name, role, _ = row
    cur.close(); conn.close()
    token = _create_token({"sub": username, "role": role})
    return TokenResponse(access_token=token, username=username, name=name, role=role)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if cur.fetchone():
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다")
    role = req.role if req.role in ("student", "teacher") else "student"
    cur.execute(
        "INSERT INTO users (username, password_hash, name, role) VALUES (%s, %s, %s, %s)",
        (req.username, _hash_password(req.password), req.name or req.username, role)
    )
    conn.commit()
    cur.close(); conn.close()
    token = _create_token({"sub": req.username, "role": role})
    return TokenResponse(access_token=token, username=req.username, name=req.name or req.username, role=role)


@router.get("/me")
async def get_me(user=Depends(require_auth)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, name, email, role, is_active, created_at, last_login FROM users WHERE username = %s", (user["username"],))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {
        "username": row[0], "name": row[1], "email": row[2],
        "role": row[3], "is_active": bool(row[4]),
        "created_at": str(row[5]) if row[5] else None,
        "last_login": str(row[6]) if row[6] else None,
    }


@router.put("/me/password")
async def change_my_password(req: PasswordChangeRequest, user=Depends(require_auth)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (user["username"],))
    row = cur.fetchone()
    if not row or row[0] != _hash_password(req.current_password):
        cur.close(); conn.close()
        raise HTTPException(status_code=401, detail="현재 비밀번호가 잘못되었습니다")
    if len(req.new_password) < 4:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="새 비밀번호는 4자 이상이어야 합니다")
    cur.execute("UPDATE users SET password_hash = %s WHERE username = %s",
                (_hash_password(req.new_password), user["username"]))
    conn.commit()
    cur.close(); conn.close()
    return {"message": "비밀번호가 변경되었습니다"}


# ─── Admin ───
@router.get("/users")
async def list_users(user=Depends(require_admin)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, name, email, role, is_active, provider, created_at, last_login FROM users ORDER BY id")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [
        {"id": r[0], "username": r[1], "name": r[2], "email": r[3],
         "role": r[4], "is_active": bool(r[5]), "provider": r[6],
         "created_at": str(r[7]) if r[7] else None, "last_login": str(r[8]) if r[8] else None}
        for r in rows
    ]


@router.post("/users")
async def create_user(req: UserCreateRequest, user=Depends(require_admin)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if cur.fetchone():
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다")
    cur.execute(
        "INSERT INTO users (username, password_hash, name, email, role) VALUES (%s, %s, %s, %s, %s)",
        (req.username, _hash_password(req.password), req.name, req.email, req.role)
    )
    conn.commit()
    cur.close(); conn.close()
    return {"message": f"사용자 '{req.username}'가 생성되었습니다"}


@router.put("/users/{username}")
async def update_user(username: str, req: UserUpdateRequest, user=Depends(require_admin)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if not cur.fetchone():
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if updates:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE users SET {set_clause} WHERE username = %s",
                    (*updates.values(), username))
        conn.commit()
    cur.close(); conn.close()
    return {"message": f"'{username}' 사용자가 수정되었습니다"}


@router.delete("/users/{username}")
async def delete_user(username: str, user=Depends(require_admin)):
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다")
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cur.close(); conn.close()
    return {"message": f"'{username}' 사용자가 삭제되었습니다"}


@router.post("/users/{username}/reset-password")
async def reset_password(username: str, req: PasswordResetRequest, user=Depends(require_admin)):
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if not cur.fetchone():
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    cur.execute("UPDATE users SET password_hash = %s WHERE username = %s",
                (_hash_password(req.new_password), username))
    conn.commit()
    cur.close(); conn.close()
    return {"message": f"'{username}' 비밀번호가 초기화되었습니다"}


# ─── App ───
app = FastAPI(
    title="GAIM Lab Auth API",
    description="GAIM Lab 인증 서비스 (Cloud Run + Cloud SQL)",
    version="7.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

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

app.include_router(router, prefix="/api/v1", tags=["인증"])


@app.get("/")
async def root():
    return {"name": "GAIM Lab Auth API", "version": "7.1.0", "status": "running", "db": "cloud-sql"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
