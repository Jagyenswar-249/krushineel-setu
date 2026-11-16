import datetime
import hashlib
import secrets
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from apps.api.config import settings
from apps.api.models.user import User, OTPCode, AuditLog


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_otp(phone: str, db: Session) -> str:
    # In DEMO_MODE or for testing, '123456' is default OTP, but generate random for realism
    code = "123456" if settings.DEMO_MODE else f"{secrets.randbelow(900000) + 100000}"
    code_hash = hash_token(code)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

    # Save OTP to DB
    otp_record = OTPCode(
        phone=phone,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0
    )
    db.add(otp_record)
    db.commit()
    return code


def verify_otp(phone: str, code: str, db: Session) -> bool:
    if settings.DEMO_MODE and code in ["123456", "999999"]:
        return True

    now = datetime.datetime.utcnow()
    record = (
        db.query(OTPCode)
        .filter(OTPCode.phone == phone, OTPCode.expires_at > now)
        .order_by(OTPCode.id.desc())
        .first()
    )

    if not record:
        return False

    if record.attempts >= 5:
        return False

    record.attempts += 1
    db.commit()

    if hash_token(code) == record.code_hash:
        return True
    return False


def get_or_create_user(
    db: Session,
    phone: str,
    name: Optional[str] = None,
    role: Optional[str] = "farmer",
    language: Optional[str] = "or",
    district: Optional[str] = "Puri"
) -> User:
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(
            phone=phone,
            name=name or f"User-{phone[-4:]}",
            role=role or "farmer",
            language=language or "or",
            district=district or "Puri"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="USER_REGISTERED",
            entity="User",
            entity_id=str(user.id),
            details_json=f'{{"role": "{user.role}", "phone": "{user.phone}"}}'
        )
        db.add(audit)
        db.commit()
    return user
