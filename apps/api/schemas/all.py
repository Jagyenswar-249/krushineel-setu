from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import datetime


# --- Auth & User ---
class OTPRequest(BaseModel):
    phone: str = Field(..., description="10-digit mobile number")


class OTPVerify(BaseModel):
    phone: str
    code: str
    name: Optional[str] = None
    role: Optional[str] = "farmer"  # farmer, fisher, buyer, fpo_admin, admin
    language: Optional[str] = "or"
    district: Optional[str] = "Puri"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: int
    phone: str
    name: str
    role: str
    language: str
    district: str

    class Config:
        from_attributes = True


# --- ColdWatch ---
class ColdRoomCreate(BaseModel):
    name: str
    location: str
    district: str = "Puri"
    capacity_kg: float = 5000.0
    min_temp: float = 2.0
    max_temp: float = 8.0
    min_rh: float = 80.0
    max_rh: float = 95.0
    log_interval_min: int = 60


class ColdRoomResponse(BaseModel):
    id: int
    name: str
    location: str
    district: str
    capacity_kg: float
    min_temp: float
    max_temp: float
    min_rh: float
    max_rh: float
    log_interval_min: int
    latest_temp: Optional[float] = None
    latest_rh: Optional[float] = None
    latest_ts: Optional[datetime.datetime] = None
    status: str = "optimal"  # optimal, warning, danger, stale
    is_simulated: bool = False
    active_alerts_count: int = 0

    class Config:
        from_attributes = True


class DataSourceCreate(BaseModel):
    name: str
    kind: str = "api"  # manual, csv, api, simulated


class DataSourceResponse(BaseModel):
    id: int
    cold_room_id: int
    name: str
    kind: str
    is_active: bool
    last_seen_at: Optional[datetime.datetime] = None
    token: Optional[str] = None  # only revealed on creation

    class Config:
        from_attributes = True


class ReadingCreate(BaseModel):
    temp_c: float
    rh: float
    ts: Optional[datetime.datetime] = None
    entered_by: Optional[str] = "Manual Quick-Log"
    is_simulated: bool = False


class IngestReadingItem(BaseModel):
    ts: datetime.datetime
    temp_c: float
    rh: float
    id: Optional[str] = None  # optional idempotency key
    is_simulated: Optional[bool] = False


class ReadingResponse(BaseModel):
    id: int
    cold_room_id: int
    ts: datetime.datetime
    temp_c: float
    rh: float
    entered_by: str
    is_simulated: bool

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    commodity: str
    qty_kg: float
    shelf_life_days_ref: Optional[float] = 14.0
    notes: Optional[str] = None


class BatchResponse(BaseModel):
    id: int
    cold_room_id: int
    commodity: str
    qty_kg: float
    stored_at: datetime.datetime
    shelf_life_days_ref: float
    current_risk_pct: float
    remaining_days: float
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    cold_room_id: int
    kind: str
    severity: str
    opened_at: datetime.datetime
    acked_at: Optional[datetime.datetime] = None
    acked_by: Optional[str] = None
    resolved_at: Optional[datetime.datetime] = None
    message_en: str
    message_or: str
    payload: Optional[str] = None

    class Config:
        from_attributes = True


class AlertAckRequest(BaseModel):
    acked_by: Optional[str] = "Operator"


class SimulatorScenarioRequest(BaseModel):
    scenario: str = "normal"  # normal, door_open, power_cut, recovery
    cold_room_id: int = 1


# --- GradeLens ---
class GradingResponse(BaseModel):
    id: int
    commodity: str
    grade: str
    confidence: float
    color_score: float
    blemish_pct: float
    shape_uniformity: float
    size_est: str
    model_version: str
    needs_review: bool
    reviewed_grade: Optional[str] = None
    certificate_id: str
    qr_code_data: Optional[str] = None
    image_url: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class GradeReviewRequest(BaseModel):
    reviewed_grade: str
    reviewer_notes: Optional[str] = None


# --- SagarSuraksha ---
class BoatCreate(BaseModel):
    reg_no: str
    name: str
    landing_site_id: int
    crew_size: int = 4
    contact_phone: str


class BoatResponse(BaseModel):
    id: int
    reg_no: str
    name: str
    landing_site_id: int
    landing_site_name: Optional[str] = None
    crew_size: int
    contact_phone: str

    class Config:
        from_attributes = True


class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    kind: str = "family"  # family, fisheries, coastguard


class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    kind: str

    class Config:
        from_attributes = True


class TripStartRequest(BaseModel):
    boat_id: int
    expected_duration_hours: float = 12.0
    checkin_interval_min: int = 180


class TripCheckinRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    source: str = "app"
    note: Optional[str] = "All safe"
    is_sos: bool = False


class TripResponse(BaseModel):
    id: int
    boat_id: int
    boat_name: Optional[str] = None
    boat_reg_no: Optional[str] = None
    departed_at: datetime.datetime
    expected_return_at: datetime.datetime
    returned_at: Optional[datetime.datetime] = None
    status: str
    checkin_interval_min: int
    last_checkin_at: Optional[datetime.datetime] = None
    is_overdue: bool = False
    checkins_count: int = 0

    class Config:
        from_attributes = True


class MarineRiskResponse(BaseModel):
    site_id: int
    site_name: str
    district: str
    ts: datetime.datetime
    wave_m: float
    wind_kmh: float
    gust_kmh: float
    risk_level: str  # green, amber, red
    advice_en: str
    advice_or: str


class GeofenceResponse(BaseModel):
    id: int
    name: str
    name_or: str
    kind: str
    polygon: List[List[float]]
    alert_message_en: str
    alert_message_or: str
    is_active: bool


# --- MandiMitra ---
class MandiResponse(BaseModel):
    id: int
    name: str
    name_or: str
    district: str
    lat: float
    lon: float

    class Config:
        from_attributes = True


class CommodityResponse(BaseModel):
    id: int
    name_en: str
    name_or: str
    category: str
    unit: str
    optimal_min_temp: float
    optimal_max_temp: float

    class Config:
        from_attributes = True


class PricePoint(BaseModel):
    date: str
    modal_price: float
    min_price: float
    max_price: float
    arrivals: float


class ForecastPoint(BaseModel):
    date: str
    p10: float
    p50: float
    p90: float


class PriceAdviceResponse(BaseModel):
    commodity: str
    commodity_or: str
    mandi: str
    mandi_or: str
    current_price: float
    forecast_7d_p50: float
    expected_gain_pct: float
    storage_cost_per_day: float
    spoilage_risk_pct: float
    net_storage_profit: float
    verdict: str  # HOLD, SELL
    verdict_or: str
    horizon_days: int
    reason_en: str
    reason_or: str
    historical: List[PricePoint]
    forecast: List[ForecastPoint]


class PriceAlertCreate(BaseModel):
    mandi_id: int
    commodity_id: int
    direction: str = "above"  # above, below
    threshold: float


class PriceAlertResponse(BaseModel):
    id: int
    mandi_id: int
    commodity_id: int
    mandi_name: Optional[str] = None
    commodity_name: Optional[str] = None
    direction: str
    threshold: float
    is_active: bool

    class Config:
        from_attributes = True


# --- MatsyaConnect ---
class CatchListingCreate(BaseModel):
    site_id: int
    species: str
    qty_kg: float
    ask_price: float
    expires_in_hours: Optional[int] = 24


class CatchListingResponse(BaseModel):
    id: int
    fisher_id: int
    fisher_name: Optional[str] = None
    site_id: int
    site_name: Optional[str] = None
    district: Optional[str] = None
    species: str
    qty_kg: float
    ask_price: float
    status: str
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None
    reference_price_min: Optional[float] = None
    reference_price_max: Optional[float] = None

    class Config:
        from_attributes = True


class BuyerRequestCreate(BaseModel):
    species: str
    qty_kg: float
    max_price: float
    radius_km: float = 50.0
    preferred_site_id: Optional[int] = None


class BuyerRequestResponse(BaseModel):
    id: int
    buyer_id: int
    buyer_name: Optional[str] = None
    species: str
    qty_kg: float
    max_price: float
    radius_km: float
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    listing_id: int
    request_id: int
    score: float
    status: str
    species: str
    qty_kg: float
    price: float
    landing_site: str
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    fisher_name: Optional[str] = None
    fisher_phone: Optional[str] = None
    proposed_at: datetime.datetime


# --- Notifications & SMS ---
class NotificationResponse(BaseModel):
    id: int
    channel: str
    title_en: str
    title_or: str
    body_en: str
    body_or: str
    status: str
    sent_at: datetime.datetime

    class Config:
        from_attributes = True


class SMSInboundRequest(BaseModel):
    from_phone: str = Field(..., alias="From")
    body: str = Field(..., alias="Body")

    class Config:
        populate_by_name = True


class SMSSimulateRequest(BaseModel):
    from_phone: str = "9876543210"
    message: str


class SMSSimulateResponse(BaseModel):
    from_phone: str
    incoming_message: str
    parsed_command: str
    response_sms: str
