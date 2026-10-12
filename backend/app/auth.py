"""Phone OTP authentication (MVP).

Flow: POST /auth/request {phone} -> 6-digit code (10-min expiry, 5 attempts).
POST /auth/verify {phone, code} -> JWT + profile on success.

Dev mode (AUTH_DEV_MODE=1, default): the code is returned in the response so
local testing works without an SMS provider. Set AUTH_DEV_MODE=0 and plug an
SMS sender into send_sms() for production (Termii / Africa's Talking).
Tokens are HS256 JWTs signed with AUTH_SECRET (stdlib only, no new deps).
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy import select
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()

NG_PHONE = re.compile(r"^0[789][01]\d{8}$")
CODE_TTL_SECS = 600
MAX_ATTEMPTS = 5


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), index=True)
    code = Column(String(8))
    consumed = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime)


def dev_mode() -> bool:
    return os.getenv("AUTH_DEV_MODE", "1") == "1"


def secret() -> str:
    return os.getenv("AUTH_SECRET", "dev-insecure-secret-change-me")


def send_sms(phone: str, code: str):
    """Production hook: send `code` via SMS provider. MVP logs only."""
    print(f"[auth] OTP for {phone}: {code}")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_token(user_id: int, phone: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": user_id, "phone": phone}).encode())
    sig = _b64url(hmac.new(secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def check_token(token: str):
    try:
        header, payload, sig = token.split(".")
        expect = _b64url(hmac.new(secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expect, sig):
            return None
        pad = "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload + pad))
    except Exception:
        return None


def request_code(db: Session, phone: str) -> dict:
    phone = (phone or "").strip().replace(" ", "")
    if not NG_PHONE.match(phone):
        raise ValueError("Enter a valid 11-digit Nigerian phone number, e.g. 0803...")
    code = f"{secrets.randbelow(1000000):06d}"
    now = _utcnow()
    db.add(OtpCode(phone=phone, code=code, expires_at=datetime.fromtimestamp(now.timestamp() + CODE_TTL_SECS)))
    db.commit()
    if not dev_mode():
        send_sms(phone, code)
        return {"sent": True, "expires_in": CODE_TTL_SECS}
    send_sms(phone, code)
    return {"sent": True, "expires_in": CODE_TTL_SECS, "dev_code": code}


def verify_code(db: Session, phone: str, code: str):
    from .models import User
    phone = (phone or "").strip().replace(" ", "")
    row = db.execute(select(OtpCode).where(
        OtpCode.phone == phone, OtpCode.consumed == False  # noqa: E712
    ).order_by(OtpCode.id.desc())).scalars().first()
    if row is None:
        raise ValueError("No code requested for this number. Request one first.")
    if row.expires_at < _utcnow():
        raise ValueError("Code expired. Request a new one.")
    if row.attempts >= MAX_ATTEMPTS:
        raise ValueError("Too many attempts. Request a new code.")
    if row.code != (code or "").strip():
        row.attempts += 1
        db.commit()
        raise ValueError("Wrong code. Check and try again.")
    row.consumed = True
    user = db.execute(select(User).where(User.phone == phone)).scalars().first()
    if user is None:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        db.commit()
    return {"token": make_token(user.id, phone),
            "profile": {"id": user.id, "phone": user.phone, "name": user.full_name or ""}}
