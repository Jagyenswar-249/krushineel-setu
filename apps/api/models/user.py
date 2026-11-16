import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from apps.api.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), default="farmer")  # farmer, fisher, buyer, fpo_admin, admin
    language = Column(String(10), default="or")  # 'or' for Odia, 'en' for English
    district = Column(String(50), default="Puri")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memberships = relationship("Membership", back_populates="user")
    boats = relationship("Boat", back_populates="owner")
    emergency_contacts = relationship("EmergencyContact", back_populates="user")
    price_alerts = relationship("PriceAlert", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    type = Column(String(50), default="fpo")  # fpo, coop, buyer_firm
    district = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memberships = relationship("Membership", back_populates="org")
    cold_rooms = relationship("ColdRoom", back_populates="org")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String(50), default="member")  # manager, staff, member

    user = relationship("User", back_populates="memberships")
    org = relationship("Organization", back_populates="memberships")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=True)
    ts = Column(DateTime, default=datetime.datetime.utcnow)
