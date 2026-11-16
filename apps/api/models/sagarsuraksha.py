import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from apps.api.database import Base


class LandingSite(Base):
    __tablename__ = "landing_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    district = Column(String(50), nullable=False)  # Puri, Ganjam, Kendrapara, Balasore, Jagatsinghpur
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    active_fishers_count = Column(Integer, default=50)

    boats = relationship("Boat", back_populates="landing_site")
    forecasts = relationship("MarineForecast", back_populates="landing_site")
    catches = relationship("CatchListing", back_populates="landing_site")


class Boat(Base):
    __tablename__ = "boats"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reg_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    landing_site_id = Column(Integer, ForeignKey("landing_sites.id"), nullable=False)
    crew_size = Column(Integer, default=4)
    contact_phone = Column(String(20), nullable=False)

    owner = relationship("User", back_populates="boats")
    landing_site = relationship("LandingSite", back_populates="boats")
    trips = relationship("Trip", back_populates="boat", cascade="all, delete-orphan")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    kind = Column(String(20), default="family")  # family, fisheries, coastguard

    user = relationship("User", back_populates="emergency_contacts")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=False)
    departed_at = Column(DateTime, default=datetime.datetime.utcnow)
    expected_return_at = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, overdue, returned, sos
    checkin_interval_min = Column(Integer, default=180)  # 3 hours
    last_checkin_at = Column(DateTime, default=datetime.datetime.utcnow)
    overdue_notified_at = Column(DateTime, nullable=True)
    escalated_notified_at = Column(DateTime, nullable=True)

    boat = relationship("Boat", back_populates="trips")
    checkins = relationship("Checkin", back_populates="trip", cascade="all, delete-orphan")


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    ts = Column(DateTime, default=datetime.datetime.utcnow)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    source = Column(String(20), default="app")  # app, sms
    note = Column(String(255), default="All good")
    is_sos = Column(Boolean, default=False)

    trip = relationship("Trip", back_populates="checkins")


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    name_or = Column(String(150), nullable=False)
    kind = Column(String(50), default="restricted")  # restricted, seasonal_ban, boundary
    polygon_geojson = Column(Text, nullable=False)  # GeoJSON polygon coordinate list
    active_from = Column(DateTime, nullable=True)
    active_to = Column(DateTime, nullable=True)
    alert_message_en = Column(Text, nullable=False)
    alert_message_or = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


class MarineForecast(Base):
    __tablename__ = "marine_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("landing_sites.id"), nullable=False)
    ts = Column(DateTime, default=datetime.datetime.utcnow)
    wave_m = Column(Float, default=1.2)
    wind_kmh = Column(Float, default=18.0)
    gust_kmh = Column(Float, default=25.0)
    risk_level = Column(String(20), default="green")  # green, amber, red
    advice_en = Column(Text, default="Sea condition safe for traditional and motorized crafts.")
    advice_or = Column(Text, default="ସମୁଦ୍ର ଯାତ୍ରା ସୁରକ୍ଷିତ। ସାଧାରଣ ଡଙ୍ଗା ଚଳାଚଳ କରିପାରିବେ।")

    landing_site = relationship("LandingSite", back_populates="forecasts")
