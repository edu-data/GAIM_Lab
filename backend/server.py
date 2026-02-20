"""
GAIM Lab Auth + Analysis API - Cloud Run Standalone Server
PostgreSQL via Cloud SQL Python Connector + Gemini Multimodal Analysis
"""

import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import base64
import uuid
import tempfile
import threading

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ─── Configuration ───
SECRET_KEY = os.getenv("GAIM_SECRET_KEY", "gaim-lab-v71-dev-secret-key")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

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


def _init_analyses_table():
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id VARCHAR(50) PRIMARY KEY,
            username VARCHAR(100),
            video_name VARCHAR(500) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            message VARCHAR(500) DEFAULT '',
            total_score REAL,
            grade VARCHAR(10),
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


_init_db()
_init_analyses_table()

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


# ═══════════════════════════════════════════════════════════
# Analysis Router — Gemini Multimodal Video Analysis
# ═══════════════════════════════════════════════════════════

analysis_router = APIRouter(prefix="/analysis", tags=["분석"])

# In-memory status cache (supplements DB)
_analysis_cache: Dict[str, Dict] = {}

# 7-Dimension Evaluation Prompt for Gemini
EVALUATION_PROMPT = """
당신은 초등학교 교사 임용 2차 수업실연 평가 전문가입니다.
이 수업 시연 영상을 시청하고 7차원으로 평가해주세요.

[평가 기준]
1. 수업 전문성 (20점 만점)
   - 학습목표_명료성 (0-10): 학습 목표가 명확하게 제시되었는가
   - 학습내용_충실성 (0-10): 교육과정에 맞는 내용을 충실히 다루었는가

2. 교수학습 방법 (20점 만점)
   - 교수법_다양성 (0-10): 다양한 교수 방법을 활용하는가
   - 학습활동_효과성 (0-10): 학습 활동이 목표 달성에 효과적인가

3. 판서 및 언어 (15점 만점)
   - 판서_가독성 (0-5): 핵심 내용을 명료하게 정리하는가
   - 언어_명료성 (0-5): 발화가 정확하고 명료한가
   - 발화속도_적절성 (0-5): 학습자 수준에 맞는 속도인가

4. 수업 태도 (15점 만점)
   - 교사_열정 (0-5): 수업에 대한 열정이 느껴지는가
   - 학생_소통 (0-5): 학생과의 상호작용이 자연스러운가
   - 자신감 (0-5): 자신감 있는 태도로 수업하는가

5. 학생 참여 (15점 만점)
   - 질문_기법 (0-7): 효과적인 발문을 사용하는가
   - 피드백_제공 (0-8): 학생 반응에 적절히 피드백하는가

6. 시간 배분 (10점 만점)
   - 시간_균형 (0-10): 도입-전개-정리가 균형 있게 배분되었는가

7. 창의성 (5점 만점)
   - 수업_창의성 (0-5): 독창적인 아이디어와 교수 기법을 사용하는가

[응답 형식]
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{{
  "dimensions": [
    {{"name": "수업 전문성", "score": 0, "max_score": 20, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "교수학습 방법", "score": 0, "max_score": 20, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "판서 및 언어", "score": 0, "max_score": 15, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "수업 태도", "score": 0, "max_score": 15, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "학생 참여", "score": 0, "max_score": 15, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "시간 배분", "score": 0, "max_score": 10, "percentage": 0, "feedback": ["피드백"]}},
    {{"name": "창의성", "score": 0, "max_score": 5, "percentage": 0, "feedback": ["피드백"]}}
  ],
  "total_score": 0,
  "grade": "A+/A/B+/B/C+/C/D+/D/F 중 하나",
  "strengths": ["강점 1", "강점 2", "강점 3"],
  "improvements": ["개선점 1", "개선점 2", "개선점 3"],
  "overall_feedback": "전반적인 수업 시연에 대한 종합 평가 (2-3문장)"
}}
"""


def _run_gemini_analysis(analysis_id: str, video_bytes: bytes, video_name: str):
    """Background thread: upload video to Gemini and run analysis"""
    import google.generativeai as genai

    try:
        # Update status
        _update_analysis(analysis_id, status="processing", progress=10, message="Gemini API 연결 중...")

        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY가 설정되지 않았습니다")

        genai.configure(api_key=GOOGLE_API_KEY)

        # Save video to temp file for Gemini upload
        _update_analysis(analysis_id, progress=20, message="동영상 업로드 중...")
        suffix = "." + video_name.rsplit(".", 1)[-1] if "." in video_name else ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        # Upload to Gemini File API
        _update_analysis(analysis_id, progress=30, message="Gemini에 동영상 전송 중...")
        video_file = genai.upload_file(path=tmp_path, mime_type=f"video/{suffix[1:]}")

        # Wait for file processing
        _update_analysis(analysis_id, progress=40, message="동영상 처리 대기 중...")
        import time as _time
        while video_file.state.name == "PROCESSING":
            _time.sleep(5)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Gemini 동영상 처리 실패: {video_file.state.name}")

        # Run 7-dimension analysis
        _update_analysis(analysis_id, progress=60, message="AI 수업 분석 중...")
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(
            [video_file, EVALUATION_PROMPT],
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )

        # Parse result
        _update_analysis(analysis_id, progress=80, message="결과 처리 중...")
        result_text = response.text.strip()
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        result = json.loads(result_text)

        # Save to DB
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            """UPDATE analyses SET status=%s, progress=%s, message=%s,
               total_score=%s, grade=%s, result_json=%s, completed_at=CURRENT_TIMESTAMP
               WHERE id=%s""",
            ("completed", 100, "분석 완료",
             result.get("total_score", 0), result.get("grade", ""),
             json.dumps(result, ensure_ascii=False), analysis_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        _analysis_cache[analysis_id] = {
            "status": "completed", "progress": 100, "message": "분석 완료",
            "result": result
        }

        # Cleanup
        try:
            os.unlink(tmp_path)
            genai.delete_file(video_file.name)
        except Exception:
            pass

    except Exception as e:
        _update_analysis(analysis_id, status="failed", progress=0, message=f"분석 실패: {str(e)[:200]}")
        _analysis_cache[analysis_id] = {
            "status": "failed", "progress": 0, "message": f"분석 실패: {str(e)[:200]}"
        }


def _update_analysis(analysis_id: str, **kwargs):
    """Update analysis status in DB and cache"""
    _analysis_cache.setdefault(analysis_id, {}).update(kwargs)
    try:
        conn = _get_db()
        cur = conn.cursor()
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in ("status", "progress", "message"):
                sets.append(f"{k}=%s")
                vals.append(v)
        if sets:
            vals.append(analysis_id)
            cur.execute(f"UPDATE analyses SET {', '.join(sets)} WHERE id=%s", vals)
            conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


@analysis_router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    use_turbo: bool = True,
    use_text: bool = True
):
    """동영상 업로드 및 Gemini 분석 (동기 실행 — Cloud Run 호환)"""
    import google.generativeai as genai

    allowed = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다. 허용: {allowed}")

    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY가 설정되지 않았습니다")

    analysis_id = str(uuid.uuid4())
    video_bytes = await file.read()
    video_name = file.filename

    # Insert into DB
    conn = _get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analyses (id, video_name, status, progress, message) VALUES (%s, %s, %s, %s, %s)",
        (analysis_id, video_name, "processing", 10, "Gemini 분석 시작")
    )
    conn.commit()
    cur.close()
    conn.close()

    try:
        genai.configure(api_key=GOOGLE_API_KEY)

        # Save video to temp file
        suffix = ext or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        # Upload to Gemini File API
        _update_analysis(analysis_id, progress=30, message="Gemini에 동영상 전송 중...")
        video_file = genai.upload_file(path=tmp_path, mime_type=f"video/{suffix[1:]}")

        # Wait for processing
        _update_analysis(analysis_id, progress=40, message="동영상 처리 대기 중...")
        import time as _time
        while video_file.state.name == "PROCESSING":
            _time.sleep(5)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Gemini 동영상 처리 실패: {video_file.state.name}")

        # Run 7-dimension analysis
        _update_analysis(analysis_id, progress=60, message="AI 수업 분석 중...")
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(
            [video_file, EVALUATION_PROMPT],
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )

        # Parse result
        result_text = response.text.strip()
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        result = json.loads(result_text)

        # Save to DB
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            """UPDATE analyses SET status=%s, progress=%s, message=%s,
               total_score=%s, grade=%s, result_json=%s, completed_at=CURRENT_TIMESTAMP
               WHERE id=%s""",
            ("completed", 100, "분석 완료",
             result.get("total_score", 0), result.get("grade", ""),
             json.dumps(result, ensure_ascii=False), analysis_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        _analysis_cache[analysis_id] = {
            "status": "completed", "progress": 100, "message": "분석 완료",
            "result": result
        }

        # Cleanup
        try:
            os.unlink(tmp_path)
            genai.delete_file(video_file.name)
        except Exception:
            pass

        return {
            "id": analysis_id,
            "status": "completed",
            "progress": 100,
            "message": "분석 완료",
            "created_at": datetime.now().isoformat(),
            **result
        }

    except Exception as e:
        _update_analysis(analysis_id, status="failed", progress=0, message=f"분석 실패: {str(e)[:200]}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)[:300]}")


@analysis_router.get("/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """분석 상태 조회"""
    # Check cache first
    if analysis_id in _analysis_cache:
        cache = _analysis_cache[analysis_id]
        return {
            "id": analysis_id,
            "status": cache.get("status", "pending"),
            "progress": cache.get("progress", 0),
            "message": cache.get("message", "")
        }

    # Fall back to DB
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, status, progress, message, created_at, completed_at FROM analyses WHERE id=%s", (analysis_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")

    return {
        "id": row[0], "status": row[1], "progress": row[2], "message": row[3],
        "created_at": str(row[4]) if row[4] else None,
        "completed_at": str(row[5]) if row[5] else None
    }


@analysis_router.get("/{analysis_id}/result")
async def get_analysis_result(analysis_id: str):
    """분석 결과 조회"""
    # Check cache
    if analysis_id in _analysis_cache and "result" in _analysis_cache[analysis_id]:
        result = _analysis_cache[analysis_id]["result"]
        return {
            "id": analysis_id,
            "video_name": "",
            **result
        }

    # Fall back to DB
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT video_name, status, result_json FROM analyses WHERE id=%s", (analysis_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")
    if row[1] != "completed":
        raise HTTPException(status_code=400, detail="분석이 아직 완료되지 않았습니다")

    result = json.loads(row[2]) if row[2] else {}
    return {
        "id": analysis_id,
        "video_name": row[0],
        **result
    }


# ─── App ───
app = FastAPI(
    title="GAIM Lab API",
    description="GAIM Lab 인증 + 수업분석 서비스 (Cloud Run + Cloud SQL + Gemini)",
    version="7.2.0",
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
app.include_router(analysis_router, prefix="/api/v1", tags=["분석"])


@app.get("/")
async def root():
    return {"name": "GAIM Lab API", "version": "7.2.0", "status": "running", "db": "cloud-sql", "analysis": "gemini-2.0-flash"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
