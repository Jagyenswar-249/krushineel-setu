import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from apps.api.database import Base


class CatchListing(Base):
    __tablename__ = "catch_listings"

    id = Column(Integer, primary_key=True, index=True)
    fisher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("landing_sites.id"), nullable=False)
    species = Column(String(100), nullable=False)  # Hilsa, Pomfret, Prawn, Rohu, Crab
    qty_kg = Column(Float, nullable=False)
    ask_price = Column(Float, nullable=False)  # Rs per kg
    photo_path = Column(String(255), nullable=True)
    status = Column(String(20), default="active")  # active, matched, sold, expired
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    fisher = relationship("User")
    landing_site = relationship("LandingSite", back_populates="catches")
    matches = relationship("Match", back_populates="listing", cascade="all, delete-orphan")


class BuyerRequest(Base):
    __tablename__ = "buyer_requests"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    species = Column(String(100), nullable=False)
    qty_kg = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    radius_km = Column(Float, default=50.0)
    preferred_site_id = Column(Integer, ForeignKey("landing_sites.id"), nullable=True)
    status = Column(String(20), default="active")  # active, fulfilled, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    buyer = relationship("User")
    matches = relationship("Match", back_populates="request", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("catch_listings.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("buyer_requests.id"), nullable=False)
    score = Column(Float, default=0.0)  # 0 to 100
    status = Column(String(20), default="proposed")  # proposed, accepted, declined, expired
    proposed_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    buyer_contact_revealed = Column(Boolean, default=False)
    fisher_contact_revealed = Column(Boolean, default=False)

    listing = relationship("CatchListing", back_populates="matches")
    request = relationship("BuyerRequest", back_populates="matches")
