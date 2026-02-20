"""
GAIM Lab v7.1 — JWT 사용자 인증 모듈

기본 JWT 인증 미들웨어:
- /api/v1/auth/login   : 로그인 (토큰 발급)
- /api/v1/auth/register: 사용자 등록
- /api/v1/auth/me      : 현재 사용자 정보
- get_current_user()   : 의존성 주입으로 보호된 라우트 구현

v7.1 Notes:
  - 프로토타입 수준의 인증. 프로덕션에서는 bcrypt, refresh token, DB 통합 필요
  - SECRET_KEY는 환경변수에서 로드 (기본값: 개발용)
"""

import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT 라이브러리 (선택적 — PyJWT 또는 자체 구현)
try:
    import jwt as pyjwt
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

# ─── Configuration ───
SECRET_KEY = os.getenv("GAIM_SECRET_KEY", "gaim-lab-v71-dev-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ─── Simple file-based user store ───
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_USERS_FILE = _DATA_DIR / "users.json"


def _load_users() -> dict:
    if _USERS_FILE.exists():
        return json.loads(_USERS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_users(users: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def _hash_password(password: str) -> str:
    return hashlib.sha256(f"{SECRET_KEY}:{password}".encode()).hexdigest()


# ─── JWT Token Helpers ───
def _create_token(data: dict, expires_delta: timedelta = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = expire.timestamp()
    payload["iat"] = datetime.utcnow().timestamp()

    if HAS_PYJWT:
        return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    else:
        # Fallback: simple base64 token (NOT production-safe)
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
    """
    보호된 라우트에서 사용:

        @router.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            if not user:
                raise HTTPException(401, "로그인 필요")
            return {"user": user["username"]}
    """
    if credentials is None:
        return None

    payload = _decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    users = _load_users()
    if username not in users:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

    return {"username": username, "role": users[username].get("role", "user")}


async def require_auth(user=Depends(get_current_user)):
    """인증 필수 의존성"""
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
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
    role: str
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ─── Router ───
router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """신규 사용자 등록"""
    users = _load_users()
    if req.username in users:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다")

    users[req.username] = {
        "password_hash": _hash_password(req.password),
        "name": req.name,
        "role": req.role,
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_users(users)

    token = _create_token({"sub": req.username, "role": req.role})
    return TokenResponse(access_token=token, username=req.username, role=req.role)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """로그인 (토큰 발급)"""
    users = _load_users()
    user = users.get(req.username)

    if not user or user["password_hash"] != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다")

    role = user.get("role", "user")
    token = _create_token({"sub": req.username, "role": role})
    return TokenResponse(access_token=token, username=req.username, role=role)


@router.get("/me")
async def get_me(user=Depends(require_auth)):
    """현재 로그인 사용자 정보"""
    users = _load_users()
    user_data = users.get(user["username"], {})
    return {
        "username": user["username"],
        "name": user_data.get("name", ""),
        "role": user["role"],
        "created_at": user_data.get("created_at"),
    }


@router.get("/users")
async def list_users(user=Depends(require_auth)):
    """사용자 목록 (관리자 전용)"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근할 수 있습니다")

    users = _load_users()
    return [
        {"username": k, "name": v.get("name", ""), "role": v.get("role", "user")}
        for k, v in users.items()
    ]


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

    # Token exchange
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

        # Get user info
        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google 사용자 정보 조회 실패")

        userinfo = userinfo_res.json()

    # Create or find user
    email = userinfo.get("email", "")
    name = userinfo.get("name", email)
    google_id = userinfo.get("id", "")
    username = f"google_{google_id}"

    users = _load_users()
    if username not in users:
        users[username] = {
            "password_hash": "",  # OAuth 사용자는 비밀번호 없음
            "name": name,
            "email": email,
            "role": "user",
            "provider": "google",
            "google_id": google_id,
            "avatar": userinfo.get("picture", ""),
            "created_at": datetime.utcnow().isoformat(),
        }
        _save_users(users)

    role = users[username].get("role", "user")
    jwt_token = _create_token({"sub": username, "role": role, "name": name, "email": email})

    # Redirect to frontend with token
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"http://localhost:5173/login?token={jwt_token}&username={username}&name={name}"
    )

