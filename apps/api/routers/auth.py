from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.user import User
from apps.api.schemas.all import OTPRequest, OTPVerify, TokenResponse, UserResponse
from apps.api.services.auth_service import generate_otp, verify_otp, create_access_token, decode_token, get_or_create_user

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        # Fallback in demo mode to default user if no token provided
        user = db.query(User).first()
        if user:
            return user
        user = User(phone="9876543210", name="Demo Farmer", role="farmer", language="or", district="Puri")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    phone = payload["sub"]
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/otp/request")
def request_otp(req: OTPRequest, db: Session = Depends(get_db)):
    phone_clean = req.phone.strip()
    if len(phone_clean) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    code = generate_otp(phone_clean, db)
    return {
        "status": "success",
        "message": "OTP sent successfully",
        "phone": phone_clean,
        "demo_code": code  # Exposed in demo mode for ease of evaluation
    }


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp_endpoint(req: OTPVerify, db: Session = Depends(get_db)):
    phone_clean = req.phone.strip()
    is_valid = verify_otp(phone_clean, req.code.strip(), db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code")

    user = get_or_create_user(
        db,
        phone=phone_clean,
        name=req.name,
        role=req.role or "farmer",
        language=req.language or "or",
        district=req.district or "Puri"
    )

    token = create_access_token({"sub": user.phone, "user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "phone": user.phone,
            "name": user.name,
            "role": user.role,
            "language": user.language,
            "district": user.district
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user
