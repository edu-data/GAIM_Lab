"""
GAIM Lab v7.1 — JWT 사용자 인증 모듈 (SQLite DB)

엔드포인트:
- POST /auth/login       : 로그인 (토큰 발급)
- POST /auth/register    : 사용자 등록
- GET  /auth/me          : 현재 사용자 정보
- GET  /auth/users       : 사용자 목록 (관리자)
- PUT  /auth/users/{uid} : 사용자 수정 (관리자)
- DELETE /auth/users/{uid}: 사용자 삭제 (관리자)
- POST /auth/users/{uid}/reset-password : 비밀번호 초기화 (관리자)

v7.1: SQLite users.db + PBKDF2 해싱 + 관리자 CRUD
"""

import os
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT 라이브러리 (선택적)
try:
    import jwt as pyjwt
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

# ─── Configuration ───
SECRET_KEY = os.getenv("GAIM_SECRET_KEY", "gaim-lab-v71-dev-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ─── SQLite User Database ───
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_DB_PATH = _DATA_DIR / "users.db"


def _get_db() -> sqlite3.Connection:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Password Hashing (PBKDF2) ───
def _hash_password(password: str) -> str:
    """PBKDF2-SHA256 with salt derived from SECRET_KEY"""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), SECRET_KEY.encode(), 100_000
    ).hex()


def _init_db():
    """테이블 생성 및 기본 admin 계정 seed"""
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

    # Seed default admin if no users exist
    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if row["cnt"] == 0:
        conn.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("admin", _hash_password("admin123"), "관리자", "admin")
        )
        conn.commit()
        print("[AUTH] 기본 관리자 계정 생성: admin / admin123")

    conn.close()


# Initialize on module load
_init_db()


# ─── JWT Token Helpers ───
def _create_token(data: dict, expires_delta: timedelta = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = expire.timestamp()
    payload["iat"] = datetime.utcnow().timestamp()

    if HAS_PYJWT:
        return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    else:
        import base64
        token_data = json.dumps(payload).encode()
        sig = hashlib.sha256(f"{SECRET_KEY}:{token_data.decode()}".encode()).hexdigest()[:16]
        return base64.urlsafe_b64encode(token_data).decode() + "." + sig


def _decode_token(token: str) -> dict:
    if HAS_PYJWT:
        try:
            return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
        except pyjwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
    else:
        import base64
        try:
            parts = token.rsplit(".", 1)
            token_data = base64.urlsafe_b64decode(parts[0]).decode()
            payload = json.loads(token_data)
            if payload.get("exp", 0) < time.time():
                raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
            return payload
        except Exception:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


# ─── FastAPI Security ───
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    if credentials is None:
        return None

    payload = _decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

    return {"username": username, "role": row["role"], "name": row["name"]}


async def require_auth(user=Depends(get_current_user)):
    """인증 필수 의존성"""
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return user


async def require_admin(user=Depends(require_auth)):
    """관리자 전용 의존성"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근할 수 있습니다")
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


class UserCreateRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    role: str = "student"
    email: str = ""


# ─── Router ───
router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """신규 사용자 등록"""
    conn = _get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다")

    conn.execute(
        "INSERT INTO users (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
        (req.username, _hash_password(req.password), req.name, req.role)
    )
    conn.commit()
    conn.close()

    token = _create_token({"sub": req.username, "role": req.role})
    return TokenResponse(access_token=token, username=req.username, name=req.name, role=req.role)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """로그인 (토큰 발급)"""
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()

    if not row or row["password_hash"] != _hash_password(req.password):
        conn.close()
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다")

    if not row["is_active"]:
        conn.close()
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의하세요")

    # Update last_login
    conn.execute(
        "UPDATE users SET last_login = datetime('now') WHERE username = ?",
        (req.username,)
    )
    conn.commit()

    role = row["role"]
    name = row["name"]
    conn.close()

    token = _create_token({"sub": req.username, "role": role})
    return TokenResponse(access_token=token, username=req.username, name=name, role=role)


@router.get("/me")
async def get_me(user=Depends(require_auth)):
    """현재 로그인 사용자 정보"""
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (user["username"],)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return {
        "username": row["username"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


# ─── Admin: User Management ───

@router.get("/users")
async def list_users(user=Depends(require_admin)):
    """사용자 목록 (관리자 전용)"""
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, username, name, email, role, is_active, provider, created_at, last_login FROM users ORDER BY id"
    ).fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "username": r["username"],
            "name": r["name"],
            "email": r["email"],
            "role": r["role"],
            "is_active": bool(r["is_active"]),
            "provider": r["provider"],
            "created_at": r["created_at"],
            "last_login": r["last_login"],
        }
        for r in rows
    ]


@router.post("/users", response_model=dict)
async def admin_create_user(req: UserCreateRequest, user=Depends(require_admin)):
    """관리자: 새 사용자 생성"""
    conn = _get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다")

    conn.execute(
        "INSERT INTO users (username, password_hash, name, email, role) VALUES (?, ?, ?, ?, ?)",
        (req.username, _hash_password(req.password), req.name, req.email, req.role)
    )
    conn.commit()
    conn.close()
    return {"message": f"사용자 '{req.username}' 생성 완료", "username": req.username}


@router.put("/users/{username}")
async def update_user(username: str, req: UserUpdateRequest, user=Depends(require_admin)):
    """관리자: 사용자 정보 수정"""
    conn = _get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    updates = []
    params = []
    if req.name is not None:
        updates.append("name = ?")
        params.append(req.name)
    if req.role is not None:
        if req.role not in ("student", "teacher", "admin"):
            conn.close()
            raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다 (student/teacher/admin)")
        updates.append("role = ?")
        params.append(req.role)
    if req.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if req.is_active else 0)
    if req.email is not None:
        updates.append("email = ?")
        params.append(req.email)

    if not updates:
        conn.close()
        return {"message": "수정할 내용이 없습니다"}

    params.append(username)
    conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE username = ?", params)
    conn.commit()
    conn.close()
    return {"message": f"사용자 '{username}' 정보 수정 완료"}


@router.delete("/users/{username}")
async def delete_user(username: str, user=Depends(require_admin)):
    """관리자: 사용자 삭제"""
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다")

    conn = _get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return {"message": f"사용자 '{username}' 삭제 완료"}


@router.post("/users/{username}/reset-password")
async def reset_password(username: str, req: PasswordResetRequest, user=Depends(require_admin)):
    """관리자: 비밀번호 초기화"""
    conn = _get_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (_hash_password(req.new_password), username)
    )
    conn.commit()
    conn.close()
    return {"message": f"사용자 '{username}' 비밀번호 초기화 완료"}


# ─── Google OAuth 2.0 (v7.1) ───
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google/login")
async def google_login():
    """Google OAuth 로그인 리디렉트"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=501,
            detail="Google OAuth 미설정 — GOOGLE_CLIENT_ID 환경변수를 설정하세요"
        )

    from urllib.parse import urlencode
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    })
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None):
    """Google OAuth 콜백 — 토큰 교환 + JWT 발급"""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code가 없습니다")

    try:
        import httpx
    except ImportError:
        raise HTTPException(status_code=501, detail="httpx 패키지가 필요합니다 (pip install httpx)")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })

        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google 토큰 교환 실패")

        tokens = token_res.json()
        access_token = tokens.get("access_token")

        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google 사용자 정보 조회 실패")

        userinfo = userinfo_res.json()

    email = userinfo.get("email", "")
    name = userinfo.get("name", email)
    google_id = userinfo.get("id", "")
    username = f"google_{google_id}"

    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO users (username, password_hash, name, email, role, provider, avatar) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, "", name, email, "student", "google", userinfo.get("picture", ""))
        )
        conn.commit()

    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    role = row["role"]
    conn.execute("UPDATE users SET last_login = datetime('now') WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    jwt_token = _create_token({"sub": username, "role": role, "name": name, "email": email})

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"http://localhost:5173/#/login?token={jwt_token}&username={username}&name={name}"
    )
