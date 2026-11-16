import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from apps.api.database import Base


class Mandi(Base):
    __tablename__ = "mandis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    name_or = Column(String(150), nullable=False)
    district = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    prices = relationship("MandiPrice", back_populates="mandi")
    forecasts = relationship("PriceForecast", back_populates="mandi")
    alerts = relationship("PriceAlert", back_populates="mandi")


class Commodity(Base):
    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), nullable=False, unique=True)
    name_or = Column(String(150), nullable=False)
    category = Column(String(50), default="veg")  # veg, paddy, fish
    unit = Column(String(20), default="Quintal")  # Quintal, Kg
    default_shelf_life_days = Column(Float, default=14.0)
    optimal_min_temp = Column(Float, default=2.0)
    optimal_max_temp = Column(Float, default=8.0)
    optimal_min_rh = Column(Float, default=85.0)
    optimal_max_rh = Column(Float, default=95.0)

    prices = relationship("MandiPrice", back_populates="commodity")
    forecasts = relationship("PriceForecast", back_populates="commodity")
    alerts = relationship("PriceAlert", back_populates="commodity")


class MandiPrice(Base):
    __tablename__ = "mandi_prices"

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False, index=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    modal_price = Column(Float, nullable=False)
    arrivals = Column(Float, default=0.0)
    source = Column(String(50), default="agmarknet")

    mandi = relationship("Mandi", back_populates="prices")
    commodity = relationship("Commodity", back_populates="prices")

    __table_args__ = (
        Index("ix_mandi_commodity_date", "mandi_id", "commodity_id", "date"),
    )


class PriceForecast(Base):
    __tablename__ = "price_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    made_on = Column(Date, default=datetime.date.today)
    horizon_days = Column(Integer, nullable=False)  # 1 to 7
    p10 = Column(Float, nullable=False)
    p50 = Column(Float, nullable=False)
    p90 = Column(Float, nullable=False)
    model_version = Column(String(50), default="LightGBM-OdishaAgri-v1.2")

    mandi = relationship("Mandi", back_populates="forecasts")
    commodity = relationship("Commodity", back_populates="forecasts")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    direction = Column(String(10), default="above")  # above, below
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="price_alerts")
    mandi = relationship("Mandi", back_populates="alerts")
    commodity = relationship("Commodity", back_populates="alerts")
