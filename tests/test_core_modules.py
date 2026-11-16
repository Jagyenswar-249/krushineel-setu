import pytest
import datetime
from apps.api.database import SessionLocal, Base, engine
from apps.api.models.coldwatch import ColdRoom, DataSource, SensorReading
from apps.api.models.sagarsuraksha import Boat, Trip
from apps.api.models.matsyaconnect import CatchListing, BuyerRequest
from apps.api.services.coldwatch_service import (
    calculate_spoilage_step, get_commodity_spec, parse_and_import_csv, run_simulator_step
)
from apps.api.services.sagarsuraksha_service import (
    is_point_in_polygon, evaluate_risk
)
from apps.api.services.mandimitra_service import calculate_price_forecast_and_advice
from apps.api.services.matsyaconnect_service import run_matching_engine, get_reference_price_band
from apps.api.services.notification_service import parse_and_handle_inbound_sms
from apps.api.services.gradelens_service import analyze_produce_image
from PIL import Image
import os


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_spoilage_step_calculation():
    spec = get_commodity_spec("Tomato")
    assert spec["opt_min_t"] == 4.0
    assert spec["opt_max_t"] == 10.0

    # At optimal temperature 6°C
    cons_0, rem_0, risk_0 = calculate_spoilage_step(temp_c=6.0, rh=90.0, hours_elapsed=24.0, spec=spec, accumulated_consumed=0.0)
    assert rem_0 < spec["ref_shelf_life"]
    assert risk_0 > 0.0

    # At elevated temperature 18°C (spoilage accelerates due to Q10 factor)
    cons_high, rem_high, risk_high = calculate_spoilage_step(temp_c=18.0, rh=90.0, hours_elapsed=24.0, spec=spec, accumulated_consumed=0.0)
    assert cons_high > cons_0
    assert rem_high < rem_0
    assert risk_high > risk_0


def test_csv_parser(db):
    csv_content = """timestamp,temperature,humidity
2026-11-14T01:00:00Z,4.2,90.5
2026-11-14T02:00:00Z,4.4,89.8
2026-11-14T03:00:00Z,4.6,88.2
"""
    room = db.query(ColdRoom).first()
    res = parse_and_import_csv(csv_content, room.id, db, user_name="Test CSV")
    assert res["imported_rows"] == 3


def test_simulator_scenarios(db):
    room = db.query(ColdRoom).first()
    
    # Door open scenario triggers spike
    reading_door = run_simulator_step(db, room.id, "door_open")
    assert reading_door.is_simulated is True
    assert reading_door.temp_c > 6.0

    # Power cut scenario
    reading_power = run_simulator_step(db, room.id, "power_cut")
    assert reading_power.is_simulated is True


def test_point_in_polygon_geofence():
    # Square around lat 20-21, lon 86-87
    poly = [[20.0, 86.0], [21.0, 86.0], [21.0, 87.0], [20.0, 87.0]]
    
    # Inside point
    assert is_point_in_polygon(20.5, 86.5, poly) is True
    # Outside point
    assert is_point_in_polygon(19.0, 85.0, poly) is False


def test_marine_risk_thresholds():
    risk_safe = evaluate_risk(wave_m=1.1, wind_kmh=18.0, gust_kmh=24.0)
    assert risk_safe["risk_level"] == "green"

    risk_caution = evaluate_risk(wave_m=2.0, wind_kmh=35.0, gust_kmh=42.0)
    assert risk_caution["risk_level"] == "amber"

    risk_danger = evaluate_risk(wave_m=3.2, wind_kmh=52.0, gust_kmh=65.0)
    assert risk_danger["risk_level"] == "red"


def test_mandi_forecast_and_advice(db):
    res = calculate_price_forecast_and_advice(db, mandi_id=1, commodity_id=1)
    assert res["commodity"] == "Tomato"
    assert "verdict" in res
    assert res["verdict"] in ["HOLD", "SELL"]
    assert len(res["forecast"]) == 7
    assert len(res["historical"]) > 0


def test_matsyaconnect_matching(db):
    listing = db.query(CatchListing).filter(CatchListing.status == "active").first()
    matches = run_matching_engine(db, listing)
    assert isinstance(matches, list)

    ref = get_reference_price_band("Hilsa (Ilish)")
    assert ref["min"] > 0
    assert ref["max"] > ref["min"]


def test_sms_keyword_parser(db):
    # Test SAFE command
    boat = db.query(Boat).first()
    reply_safe = parse_and_handle_inbound_sms(boat.contact_phone, f"SAFE {boat.reg_no}", db)
    assert "Check-in saved" in reply_safe

    # Test PRICE command
    reply_price = parse_and_handle_inbound_sms("9876543210", "PRICE TOMATO BBSR", db)
    assert "Tomato" in reply_price
    assert "₹" in reply_price

    # Test WEATHER command
    reply_weather = parse_and_handle_inbound_sms("9876543210", "WEATHER PURI", db)
    assert "Wave" in reply_weather


def test_gradelens_image_analysis(tmp_path):
    # Generate test image
    test_img_path = str(tmp_path / "test_tomato.jpg")
    img = Image.new("RGB", (224, 224), color=(200, 30, 25))
    img.save(test_img_path)

    metrics = analyze_produce_image(test_img_path, "Tomato")
    assert metrics["grade"] in ["A", "B", "C", "Reject"]
    assert metrics["confidence"] > 0.5
    assert metrics["color_score"] > 50.0
