"""
GAIM Lab Auth API - Cloud Run Standalone Server
Single-file server with zero cross-module imports
"""

import os
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import base64

# ─── Configuration ───
SECRET_KEY = os.getenv("GAIM_SECRET_KEY", "gaim-lab-v71-dev-secret-key")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ─── SQLite ───
_DATA_DIR = Path(os.getenv("GAIM_DATA_DIR", "/tmp/data"))
_DB_PATH = _DATA_DIR / "users.db"


def _get_db():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            role TEXT DEFAULT 'student',
            is_active INTEGER DEFAULT 1,
            provider TEXT DEFAULT 'local',
            avatar TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        )
    """)
    conn.commit()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if row["cnt"] == 0:
        conn.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("admin", _hash_password("admin123"), "관리자", "admin")
        )
        conn.commit()
        print("[AUTH] Default admin created: admin / admin123")
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
    row = conn.execute("SELECT * FROM users WHERE username = ?", (payload["sub"],)).fetchone()
    conn.close()
    if not row or not row["is_active"]:
        raise HTTPException(status_code=401, detail="비활성화된 계정")
    return {"username": row["username"], "role": row["role"]}


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
    row = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    if not row or row["password_hash"] != _hash_password(req.password):
        conn.close()
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다")
    if not row["is_active"]:
        conn.close()
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
    conn.execute("UPDATE users SET last_login = datetime('now') WHERE username = ?", (req.username,))
    conn.commit()
    role, name = row["role"], row["name"]
    conn.close()
    token = _create_token({"sub": req.username, "role": role})
    return TokenResponse(access_token=token, username=req.username, name=name, role=role)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    conn = _get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다")
    role = req.role if req.role in ("student", "teacher") else "student"
    conn.execute(
        "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
        (req.username, _hash_password(req.password), req.name or req.username, role)
    )
    conn.commit()
    conn.close()
    token = _create_token({"sub": req.username, "role": role})
    return TokenResponse(access_token=token, username=req.username, name=req.name or req.username, role=role)


@router.get("/me")
async def get_me(user=Depends(require_auth)):
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (user["username"],)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {
        "username": row["username"], "name": row["name"], "email": row["email"],
        "role": row["role"], "is_active": bool(row["is_active"]),
        "created_at": row["created_at"], "last_login": row["last_login"],
    }


@router.put("/me/password")
async def change_my_password(req: PasswordChangeRequest, user=Depends(require_auth)):
    conn = _get_db()
    row = conn.execute("SELECT password_hash FROM users WHERE username = ?", (user["username"],)).fetchone()
    if not row or row["password_hash"] != _hash_password(req.current_password):
        conn.close()
        raise HTTPException(status_code=401, detail="현재 비밀번호가 잘못되었습니다")
    if len(req.new_password) < 4:
        conn.close()
        raise HTTPException(status_code=400, detail="새 비밀번호는 4자 이상이어야 합니다")
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                 (_hash_password(req.new_password), user["username"]))
    conn.commit()
    conn.close()
    return {"message": "비밀번호가 변경되었습니다"}


# ─── Admin ───
@router.get("/users")
async def list_users(user=Depends(require_admin)):
    conn = _get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return [
        {"id": r["id"], "username": r["username"], "name": r["name"], "email": r["email"],
         "role": r["role"], "is_active": bool(r["is_active"]), "provider": r["provider"],
         "created_at": r["created_at"], "last_login": r["last_login"]}
        for r in rows
    ]


@router.post("/users")
async def create_user(req: UserCreateRequest, user=Depends(require_admin)):
    conn = _get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다")
    conn.execute(
        "INSERT INTO users (username, password_hash, name, email, role) VALUES (?, ?, ?, ?, ?)",
        (req.username, _hash_password(req.password), req.name, req.email, req.role)
    )
    conn.commit()
    conn.close()
    return {"message": f"사용자 '{req.username}'가 생성되었습니다"}


@router.put("/users/{username}")
async def update_user(username: str, req: UserUpdateRequest, user=Depends(require_admin)):
    conn = _get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if "is_active" in updates:
        updates["is_active"] = 1 if updates["is_active"] else 0
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE users SET {set_clause} WHERE username = ?",
                     (*updates.values(), username))
        conn.commit()
    conn.close()
    return {"message": f"'{username}' 사용자가 수정되었습니다"}


@router.delete("/users/{username}")
async def delete_user(username: str, user=Depends(require_admin)):
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다")
    conn = _get_db()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return {"message": f"'{username}' 사용자가 삭제되었습니다"}


@router.post("/users/{username}/reset-password")
async def reset_password(username: str, req: PasswordResetRequest, user=Depends(require_admin)):
    conn = _get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                 (_hash_password(req.new_password), username))
    conn.commit()
    conn.close()
    return {"message": f"'{username}' 비밀번호가 초기화되었습니다"}


# ─── App ───
app = FastAPI(
    title="GAIM Lab Auth API",
    description="GAIM Lab 인증 서비스 (Cloud Run)",
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
    return {"name": "GAIM Lab Auth API", "version": "7.1.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
