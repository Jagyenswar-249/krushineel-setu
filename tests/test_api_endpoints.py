import pytest
import datetime
import uuid
from apps.api.database import SessionLocal, Base, engine
from apps.api.models.user import User
from apps.api.schemas.all import (
    OTPRequest, OTPVerify, ReadingCreate, IngestReadingItem,
    SimulatorScenarioRequest, SMSSimulateRequest
)
from apps.api.routers.auth import request_otp, verify_otp_endpoint, get_me
from apps.api.routers.coldwatch import list_coldrooms, add_manual_reading
from apps.api.routers.ingest import ingest_readings
from apps.api.routers.sagarsuraksha import list_landing_sites, list_boats, list_geofences
from apps.api.services.sagarsuraksha_service import evaluate_risk
from apps.api.routers.mandimitra import list_mandis, list_commodities, get_sell_hold_advice
from apps.api.routers.matsyaconnect import list_catch_listings, list_buyer_requests, list_matches
from apps.api.routers.sms import simulate_sms
from apps.api.routers.admin import get_admin_stats, trigger_simulator_scenario


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def demo_user(db):
    user = db.query(User).filter(User.phone == "9876543210").first()
    if not user:
        user = User(phone="9876543210", name="Demo Farmer", role="farmer", language="or", district="Puri")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def test_auth_router(db):
    req_resp = request_otp(OTPRequest(phone="9876543210"), db)
    assert req_resp["status"] == "success"
    assert req_resp["demo_code"] == "123456"

    verify_resp = verify_otp_endpoint(OTPVerify(phone="9876543210", code="123456", role="farmer"), db)
    assert "access_token" in verify_resp
    assert verify_resp["user"]["phone"] == "9876543210"


def test_coldwatch_router(db, demo_user):
    rooms = list_coldrooms(db)
    assert len(rooms) >= 1
    room = rooms[0]

    # Manual reading
    reading = add_manual_reading(
        room_id=room.id,
        req=ReadingCreate(temp_c=4.1, rh=88.5, is_simulated=False),
        db=db,
        user=demo_user
    )
    assert reading.temp_c == 4.1
    assert reading.cold_room_id == room.id


def test_ingest_router(db):
    unique_key = f"ingest-test-{uuid.uuid4().hex[:8]}"
    items = [
        IngestReadingItem(
            ts=datetime.datetime.utcnow(),
            temp_c=4.4,
            rh=90.0,
            id=unique_key,
            is_simulated=False
        )
    ]
    res = ingest_readings(
        readings=items,
        x_source_token="kns_demo_token_puri_2026",
        db=db
    )
    assert res["status"] == "success"
    assert res["ingested"] == 1


def test_sagarsuraksha_router(db, demo_user):
    sites = list_landing_sites(db)
    assert len(sites) >= 1

    boats = list_boats(db, demo_user)
    assert len(boats) >= 1

    geofences = list_geofences(db)
    assert len(geofences) >= 1

    risk = evaluate_risk(wave_m=1.2, wind_kmh=20.0, gust_kmh=28.0)
    assert risk["risk_level"] == "green"


def test_mandimitra_router(db):
    mandis = list_mandis(db)
    assert len(mandis) >= 1

    commodities = list_commodities(db)
    assert len(commodities) >= 1

    advice = get_sell_hold_advice(mandi_id=mandis[0].id, commodity_id=commodities[0].id, storage_cost=25.0, db=db)
    assert advice["verdict"] in ["HOLD", "SELL"]
    assert len(advice["forecast"]) == 7


def test_matsyaconnect_router(db, demo_user):
    listings = list_catch_listings(None, None, db)
    assert len(listings) >= 1

    requests = list_buyer_requests(db)
    assert len(requests) >= 1

    matches = list_matches(db, demo_user)
    assert isinstance(matches, list)


def test_sms_router(db):
    res = simulate_sms(SMSSimulateRequest(from_phone="9876543210", message="PRICE TOMATO BBSR"), db)
    assert "Tomato" in res.response_sms


def test_admin_router(db):
    stats = get_admin_stats(db)
    assert stats["cold_rooms_count"] >= 1
    assert stats["mandis_tracked"] >= 1

    # Simulator scenario
    res = trigger_simulator_scenario(SimulatorScenarioRequest(cold_room_id=1, scenario="door_open"), db)
    assert res["status"] == "success"
    assert res["badge"] == "SIMULATED"
