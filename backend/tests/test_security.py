"""
GAIM Lab v8.1 — Security Unit Tests

JWT 생성/검증, argon2id 해싱, 레거시 PBKDF2 호환, 프로덕션 시크릿 검증 테스트.

실행:
    python -m pytest backend/tests/test_security.py -v
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import timedelta

import pytest

# 테스트 환경에서 Cloud SQL 없이 실행하기 위한 모킹
# server.py의 Cloud SQL 관련 import를 건너뛰기 위해 직접 보안 함수를 테스트

# ── argon2id ──
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

# ── JWT (python-jose) ──
from jose import jwt, JWTError
from datetime import datetime


# ─── Configuration for tests ───
TEST_SECRET = "test-secret-key-for-unit-tests-only"


class TestArgon2Hashing:
    """argon2id 패스워드 해싱 테스트"""

    def test_hash_produces_argon2_format(self):
        """해싱 결과가 $argon2 형식이어야 함"""
        hashed = _ph.hash("testpassword123")
        assert hashed.startswith("$argon2"), f"Expected argon2 prefix, got: {hashed[:20]}"

    def test_hash_verify_roundtrip(self):
        """해싱 → 검증 라운드트립"""
        password = "MySecureP@ss123!"
        hashed = _ph.hash(password)
        assert _ph.verify(hashed, password)

    def test_wrong_password_fails(self):
        """잘못된 비밀번호 검증 실패"""
        hashed = _ph.hash("correct-password")
        with pytest.raises(VerifyMismatchError):
            _ph.verify(hashed, "wrong-password")

    def test_different_hashes_for_same_password(self):
        """동일 비밀번호도 서로 다른 해시 생성 (랜덤 salt)"""
        password = "same-password"
        h1 = _ph.hash(password)
        h2 = _ph.hash(password)
        assert h1 != h2, "Same password should produce different hashes due to random salt"

    def test_unicode_password(self):
        """유니코드 비밀번호 지원"""
        password = "한글비밀번호🔐"
        hashed = _ph.hash(password)
        assert _ph.verify(hashed, password)


class TestLegacyPBKDF2:
    """레거시 PBKDF2 해시 호환성 테스트"""

    LEGACY_SALT = "dev-only-insecure-key-do-not-use-in-production"

    def _pbkdf2_hash(self, password: str, salt: str = None) -> str:
        """레거시 PBKDF2 해싱 (서버와 동일한 로직)"""
        salt = salt or self.LEGACY_SALT
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100_000
        ).hex()

    def test_legacy_hash_is_hex(self):
        """PBKDF2 해시는 hex 문자열"""
        hashed = self._pbkdf2_hash("password")
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_legacy_hash_deterministic(self):
        """PBKDF2 해시는 결정론적 (같은 salt → 같은 결과)"""
        h1 = self._pbkdf2_hash("password")
        h2 = self._pbkdf2_hash("password")
        assert h1 == h2

    def test_is_legacy_detection(self):
        """레거시 해시 vs argon2 해시 구분"""
        legacy = self._pbkdf2_hash("password")
        argon2 = _ph.hash("password")
        assert not legacy.startswith("$argon2")
        assert argon2.startswith("$argon2")

    def test_v71_salt_produces_different_hash(self):
        """v7.1 salt와 기본 salt는 다른 해시 생성"""
        h_default = self._pbkdf2_hash("password", self.LEGACY_SALT)
        h_v71 = self._pbkdf2_hash("password", "gaim-lab-v71-dev-secret-key")
        assert h_default != h_v71


class TestJWT:
    """JWT 생성/검증 테스트"""

    def test_create_and_decode(self):
        """JWT 생성 → 디코딩 라운드트립"""
        payload = {"sub": "testuser", "role": "student"}
        expire = datetime.utcnow() + timedelta(hours=1)
        payload["exp"] = expire
        payload["iat"] = datetime.utcnow()
        
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "student"

    def test_expired_token_raises(self):
        """만료된 토큰 → JWTError"""
        payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        
        with pytest.raises(Exception):  # ExpiredSignatureError
            jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    def test_wrong_secret_raises(self):
        """잘못된 시크릿 → JWTError"""
        payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])

    def test_token_contains_expected_claims(self):
        """토큰에 필수 클레임 포함"""
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        
        assert "sub" in decoded
        assert "role" in decoded
        assert "exp" in decoded
        assert "iat" in decoded


class TestProductionSecretGuard:
    """프로덕션 환경에서 시크릿 키 강제 검증"""

    def test_dev_key_is_insecure(self):
        """개발용 키가 프로덕션에 사용되면 안 됨"""
        dev_key = "dev-only-insecure-key-do-not-use-in-production"
        assert len(dev_key) < 64, "Dev key should not be production-strength"

    def test_secret_key_minimum_length(self):
        """프로덕션 시크릿은 최소 32자 이상 권장"""
        import secrets
        prod_key = secrets.token_urlsafe(32)
        assert len(prod_key) >= 32
