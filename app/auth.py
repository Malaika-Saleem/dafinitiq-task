import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from sqlmodel import select
from .models import User
from .db import get_session
import secrets

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_SECRET = os.environ.get("JWT_SECRET", "secret")
JWT_ALGO = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXP = int(os.environ.get("JWT_EXPIRE_SECONDS", "3600"))

def hash_password(password: str) -> str:
    # normalize input to str (handle bytes) and ensure <=72 bytes for bcrypt
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")
    if not isinstance(password, str):
        password = str(password)
    b = password.encode("utf-8")
    if len(b) > 72:
        # truncate bytes and decode ignoring partial multibyte sequences
        password = b[:72].decode("utf-8", errors="ignore")
    # Debug prints requested by developer to inspect problematic values
    try:
        print("Password length:", len(password))
        print("Password:", repr(password))
    except Exception:
        pass
    return pwd_context.hash(password)

def verify_password(plain, hashed) -> bool:
    # Normalize and apply same truncation logic used when hashing
    if isinstance(plain, bytes):
        plain = plain.decode("utf-8", errors="ignore")
    if not isinstance(plain, str):
        plain = str(plain)
    b = plain.encode("utf-8")
    if len(b) > 72:
        plain = b[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(plain, hashed)

def create_access_token(sub: str) -> str:
    to_encode = {"sub": sub, "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP)}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

def send_otp(email: str, otp: str):
    # For assessment/testing we print the OTP to console and optionally show a
    # Windows desktop notification when running on Windows and the
    # SHOW_DESKTOP_OTP env var is enabled.
    msg = f"[OTP] Send to {email}: {otp}"
    print(msg)
    try:
        show_desktop = os.environ.get("SHOW_DESKTOP_OTP", "true").lower() in ("1", "true", "yes")
        if show_desktop and os.name == "nt":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast("Voice Agent OTP", f"{otp} (to {email})", duration=8, threaded=True)
            except Exception:
                # best-effort: if win10toast not available or fails, ignore
                pass
    except Exception:
        pass

def generate_otp() -> str:
    return secrets.token_hex(3)

def create_user(email: str, display_name: str, password: str):
    session = get_session()
    user = User(email=email, display_name=display_name, hashed_password=hash_password(password), is_active=False)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def find_user_by_email(email: str):
    session = get_session()
    q = select(User).where(User.email == email)
    return session.exec(q).first()
