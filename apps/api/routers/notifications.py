from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.notifications import Notification
from apps.api.schemas.all import NotificationResponse

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db)):
    notifs = db.query(Notification).order_by(Notification.sent_at.desc()).limit(50).all()
    return notifs


@router.post("/push/subscribe")
def push_subscribe(sub: Dict[str, Any]):
    # Store web push subscription
    return {"status": "subscribed", "endpoint": sub.get("endpoint", "")[:30] + "..."}
