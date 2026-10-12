"""OTP auth tests: request/verify, wrong/expired codes, attempt limits, tokens."""
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import app, engine
from backend.app.auth import OtpCode, check_token
c = TestClient(app)
PHONE = "08031234567"


def _request(phone=PHONE):
    return c.post("/auth/request", json={"phone": phone}).json()


def test_request_returns_dev_code():
    r = _request()
    assert r["sent"] is True and len(r["dev_code"]) == 6


def test_request_rejects_bad_phone():
    assert "error" in c.post("/auth/request", json={"phone": "123"}).json()


def test_verify_happy_path_and_token():
    code = _request()["dev_code"]
    r = c.post("/auth/verify", json={"phone": PHONE, "code": code, "name": "Test"}).json()
    assert "token" in r and r["profile"]["phone"] == PHONE
    claims = check_token(r["token"])
    assert claims and claims["phone"] == PHONE
    assert check_token("bogus.token.here") is None


def test_verify_wrong_code_counts_attempts():
    code = _request()["dev_code"]
    wrong = "000000" if code != "000000" else "111111"
    r = c.post("/auth/verify", json={"phone": PHONE, "code": wrong}).json()
    assert "Wrong code" in r["error"]
    with Session(engine) as s:
        row = s.execute(select(OtpCode).where(OtpCode.phone == PHONE).order_by(OtpCode.id.desc())).scalars().first()
        assert row.attempts >= 1 and not row.consumed


def test_verify_expired_code():
    from datetime import datetime, timedelta
    code = _request()["dev_code"]
    with Session(engine) as s:
        row = s.execute(select(OtpCode).where(OtpCode.phone == PHONE).order_by(OtpCode.id.desc())).scalars().first()
        row.expires_at = datetime.now() - timedelta(seconds=1)
        s.commit()
    assert "expired" in c.post("/auth/verify", json={"phone": PHONE, "code": code}).json()["error"]


def test_verify_max_attempts_locks():
    _request()
    for _ in range(6):
        r = c.post("/auth/verify", json={"phone": PHONE, "code": "999999"}).json()
    assert "Too many attempts" in r["error"]


def test_reused_code_rejected():
    code = _request()["dev_code"]
    assert "token" in c.post("/auth/verify", json={"phone": PHONE, "code": code}).json()
    assert "error" in c.post("/auth/verify", json={"phone": PHONE, "code": code}).json()


def test_simple_login_no_otp():
    r = c.post("/auth/login", json={"phone": "08055556666", "name": "NoOtp"}).json()
    assert "token" in r and r["profile"]["phone"] == "08055556666" and r["profile"]["name"] == "NoOtp"
    claims = check_token(r["token"])
    assert claims and claims["phone"] == "08055556666"
    h = {"Authorization": f"Bearer {r['token']}"}
    assert c.get("/syllabus", headers=h).status_code == 200
    assert "error" in c.post("/auth/login", json={"phone": "bad"}).json()
    r2 = c.post("/auth/login", json={"phone": "08055556666"}).json()
    assert r2["profile"]["name"] == "NoOtp"  # name kept, same account
