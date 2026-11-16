import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from apps.api.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    channel = Column(String(20), default="in_app")  # in_app, sms, push
    title_en = Column(String(150), nullable=False)
    title_or = Column(String(200), nullable=False)
    body_en = Column(Text, nullable=False)
    body_or = Column(Text, nullable=False)
    status = Column(String(20), default="sent")  # sent, failed, pending
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    error = Column(Text, nullable=True)

    user = relationship("User", back_populates="notifications")


class SMSInbound(Base):
    __tablename__ = "sms_inbound"

    id = Column(Integer, primary_key=True, index=True)
    from_phone = Column(String(20), nullable=False, index=True)
    body = Column(Text, nullable=False)
    parsed_command = Column(String(50), nullable=True)
    response_text = Column(Text, nullable=True)
    handled_at = Column(DateTime, default=datetime.datetime.utcnow)
