import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from apps.api.database import Base


class GradingRequest(Base):
    __tablename__ = "grading_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    commodity = Column(String(50), default="Tomato")  # Tomato, Brinjal, Potato
    image_path = Column(String(255), nullable=False)
    image_sha256 = Column(String(64), nullable=False)
    sample_count = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    result = relationship("GradingResult", back_populates="request", uselist=False, cascade="all, delete-orphan")


class GradingResult(Base):
    __tablename__ = "grading_results"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("grading_requests.id"), nullable=False, unique=True)
    grade = Column(String(10), nullable=False)  # A, B, C, Reject
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    color_score = Column(Float, default=0.0)
    blemish_pct = Column(Float, default=0.0)
    shape_uniformity = Column(Float, default=0.0)
    size_est = Column(String(20), default="Medium")
    model_version = Column(String(50), default="MobileNetV2-OdishaAgri-v1.0")
    needs_review = Column(Boolean, default=False)
    reviewed_grade = Column(String(10), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    certificate_id = Column(String(64), unique=True, index=True)
    qr_code_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    request = relationship("GradingRequest", back_populates="result")
