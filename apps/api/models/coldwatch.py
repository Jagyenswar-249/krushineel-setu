import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from apps.api.database import Base


class ColdRoom(Base):
    __tablename__ = "cold_rooms"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    district = Column(String(50), default="Puri")
    capacity_kg = Column(Float, default=5000.0)
    min_temp = Column(Float, default=2.0)
    max_temp = Column(Float, default=8.0)
    max_rh = Column(Float, default=95.0)
    min_rh = Column(Float, default=80.0)
    log_interval_min = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    org = relationship("Organization", back_populates="cold_rooms")
    data_sources = relationship("DataSource", back_populates="cold_room", cascade="all, delete-orphan")
    readings = relationship("SensorReading", back_populates="cold_room", cascade="all, delete-orphan")
    batches = relationship("Batch", back_populates="cold_room", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="cold_room", cascade="all, delete-orphan")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    cold_room_id = Column(Integer, ForeignKey("cold_rooms.id"), nullable=False)
    name = Column(String(100), default="Primary Logger")
    kind = Column(String(20), default="manual")  # manual, csv, api, simulated
    token_hash = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, nullable=True)

    cold_room = relationship("ColdRoom", back_populates="data_sources")
    readings = relationship("SensorReading", back_populates="source")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    cold_room_id = Column(Integer, ForeignKey("cold_rooms.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    ts = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    temp_c = Column(Float, nullable=False)
    rh = Column(Float, nullable=False)
    entered_by = Column(String(100), default="System")
    is_simulated = Column(Boolean, default=False)
    idempotency_key = Column(String(128), nullable=True, unique=True)

    cold_room = relationship("ColdRoom", back_populates="readings")
    source = relationship("DataSource", back_populates="readings")

    __table_args__ = (
        Index("ix_coldroom_ts", "cold_room_id", "ts"),
    )


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    cold_room_id = Column(Integer, ForeignKey("cold_rooms.id"), nullable=False)
    commodity = Column(String(50), nullable=False)  # e.g. Tomato, Potato, Brinjal
    qty_kg = Column(Float, nullable=False)
    stored_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    shelf_life_days_ref = Column(Float, default=14.0)
    current_risk_pct = Column(Float, default=5.0)
    remaining_days = Column(Float, default=14.0)
    status = Column(String(20), default="active")  # active, discharged, spoiled
    notes = Column(Text, nullable=True)

    cold_room = relationship("ColdRoom", back_populates="batches")
    spoilage_scores = relationship("SpoilageScore", back_populates="batch", cascade="all, delete-orphan")


class SpoilageScore(Base):
    __tablename__ = "spoilage_scores"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    ts = Column(DateTime, default=datetime.datetime.utcnow)
    risk_pct = Column(Float, nullable=False)
    remaining_days = Column(Float, nullable=False)
    status = Column(String(20), default="normal")  # normal, warning, critical

    batch = relationship("Batch", back_populates="spoilage_scores")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    cold_room_id = Column(Integer, ForeignKey("cold_rooms.id"), nullable=False)
    scope = Column(String(50), default="room")
    kind = Column(String(50), nullable=False)  # out_of_range, rapid_rise, missed_log, stale_source
    params_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    cold_room_id = Column(Integer, ForeignKey("cold_rooms.id"), nullable=False, index=True)
    kind = Column(String(50), nullable=False)  # temp_high, temp_low, humidity_high, rapid_rise, missed_log
    severity = Column(String(20), default="warning")  # info, warning, danger
    subject_type = Column(String(50), default="cold_room")
    subject_id = Column(String(50), nullable=True)
    opened_at = Column(DateTime, default=datetime.datetime.utcnow)
    acked_at = Column(DateTime, nullable=True)
    acked_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    message_en = Column(Text, nullable=False)
    message_or = Column(Text, nullable=False)
    payload = Column(Text, default="{}")

    cold_room = relationship("ColdRoom", back_populates="alerts")
