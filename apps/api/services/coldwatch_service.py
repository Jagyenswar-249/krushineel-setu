import datetime
import io
import csv
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from apps.api.models.coldwatch import ColdRoom, DataSource, SensorReading, Batch, SpoilageScore, Alert
from apps.api.models.notifications import Notification


COMMODITY_SPECS: Dict[str, Dict[str, Any]] = {
    "tomato": {"opt_min_t": 4.0, "opt_max_t": 10.0, "opt_min_rh": 85.0, "opt_max_rh": 95.0, "ref_shelf_life": 14.0},
    "potato": {"opt_min_t": 8.0, "opt_max_t": 12.0, "opt_min_rh": 90.0, "opt_max_rh": 95.0, "ref_shelf_life": 90.0},
    "brinjal": {"opt_min_t": 8.0, "opt_max_t": 12.0, "opt_min_rh": 90.0, "opt_max_rh": 95.0, "ref_shelf_life": 10.0},
    "pointed gourd": {"opt_min_t": 6.0, "opt_max_t": 10.0, "opt_min_rh": 85.0, "opt_max_rh": 90.0, "ref_shelf_life": 12.0},
    "paddy": {"opt_min_t": 15.0, "opt_max_t": 20.0, "opt_min_rh": 60.0, "opt_max_rh": 70.0, "ref_shelf_life": 180.0},
    "onion": {"opt_min_t": 0.0, "opt_max_t": 4.0, "opt_min_rh": 65.0, "opt_max_rh": 75.0, "ref_shelf_life": 120.0},
    "fish": {"opt_min_t": -2.0, "opt_max_t": 2.0, "opt_min_rh": 90.0, "opt_max_rh": 98.0, "ref_shelf_life": 5.0},
}


def get_commodity_spec(commodity_name: str) -> Dict[str, Any]:
    key = commodity_name.lower().strip()
    return COMMODITY_SPECS.get(key, {"opt_min_t": 2.0, "opt_max_t": 8.0, "opt_min_rh": 80.0, "opt_max_rh": 95.0, "ref_shelf_life": 14.0})


def calculate_spoilage_step(
    temp_c: float,
    rh: float,
    hours_elapsed: float,
    spec: Dict[str, Any],
    accumulated_consumed: float
) -> Tuple[float, float, float]:
    """
    Q10 Arrhenius temperature multiplier and humidity penalty calculation.
    Returns (new_accumulated_consumed, remaining_days, risk_pct).
    """
    opt_min_t = spec["opt_min_t"]
    opt_max_t = spec["opt_max_t"]
    ref_shelf_life = spec["ref_shelf_life"]

    if opt_min_t <= temp_c <= opt_max_t:
        multiplier = 1.0
    elif temp_c > opt_max_t:
        multiplier = math.pow(2.5, (temp_c - opt_max_t) / 10.0)
    else:
        # Chilling injury
        multiplier = math.pow(1.5, (opt_min_t - temp_c) / 5.0)

    # Relative humidity penalty (dehydration or mold condensation)
    rh_penalty = 0.0
    if rh < spec["opt_min_rh"]:
        rh_penalty = (spec["opt_min_rh"] - rh) * 0.4
    elif rh > spec["opt_max_rh"]:
        rh_penalty = (rh - spec["opt_max_rh"]) * 0.3

    fraction_consumed = (multiplier * hours_elapsed) / (24.0 * ref_shelf_life)
    total_consumed = min(1.0, accumulated_consumed + fraction_consumed)
    remaining_days = max(0.0, round((1.0 - total_consumed) * ref_shelf_life, 1))
    risk_pct = min(100.0, round(total_consumed * 100.0 + rh_penalty, 1))

    return total_consumed, remaining_days, risk_pct


def update_coldroom_batches(db: Session, cold_room_id: int, current_temp: float, current_rh: float, dt_hours: float = 1.0):
    batches = db.query(Batch).filter(Batch.cold_room_id == cold_room_id, Batch.status == "active").all()
    for batch in batches:
        spec = get_commodity_spec(batch.commodity)
        consumed_prior = 1.0 - (batch.remaining_days / batch.shelf_life_days_ref)
        consumed_prior = max(0.0, min(1.0, consumed_prior))

        new_consumed, rem_days, risk = calculate_spoilage_step(
            current_temp, current_rh, dt_hours, spec, consumed_prior
        )
        batch.remaining_days = rem_days
        batch.current_risk_pct = risk

        status_str = "normal"
        if risk > 70.0 or rem_days < 2.0:
            status_str = "critical"
        elif risk > 40.0:
            status_str = "warning"

        score = SpoilageScore(
            batch_id=batch.id,
            ts=datetime.datetime.utcnow(),
            risk_pct=risk,
            remaining_days=rem_days,
            status=status_str
        )
        db.add(score)
    db.commit()


def evaluate_coldroom_rules(db: Session, cold_room_id: int, reading: SensorReading):
    room = db.query(ColdRoom).filter(ColdRoom.id == cold_room_id).first()
    if not room:
        return

    # 1. Out of range check
    if reading.temp_c > room.max_temp:
        open_alert = db.query(Alert).filter(
            Alert.cold_room_id == cold_room_id,
            Alert.kind == "temp_high",
            Alert.resolved_at.is_(None)
        ).first()
        if not open_alert:
            alert = Alert(
                cold_room_id=cold_room_id,
                kind="temp_high",
                severity="danger",
                message_en=f"Move produce or check cooling. {room.name} temperature is {reading.temp_c:.1f}°C (exceeds limit {room.max_temp}°C).",
                message_or=f"ସତର୍କତା: {room.name} ତାପମାତ୍ରା {reading.temp_c:.1f}°C ପହଞ୍ଚିଛି (ସର୍ବୋଚ୍ଚ ସୀମା {room.max_temp}°C)। ଶୀଘ୍ର ଯାଞ୍ଚ କରନ୍ତୁ।",
                payload=f'{{"temp_c": {reading.temp_c}, "max_temp": {room.max_temp}, "is_simulated": {str(reading.is_simulated).lower()}}}'
            )
            db.add(alert)

            # Create notification
            notif = Notification(
                user_id=None,
                channel="in_app",
                title_en=f"ColdWatch Alert: High Temp in {room.name}",
                title_or=f"କୋଲ୍ଡଓ୍ବାଚ୍ ସତର୍କତା: {room.name} ରେ ଉଚ୍ଚ ତାପମାତ୍ରା",
                body_en=alert.message_en,
                body_or=alert.message_or
            )
            db.add(notif)
            db.commit()

    elif reading.temp_c < room.min_temp:
        open_alert = db.query(Alert).filter(
            Alert.cold_room_id == cold_room_id,
            Alert.kind == "temp_low",
            Alert.resolved_at.is_(None)
        ).first()
        if not open_alert:
            alert = Alert(
                cold_room_id=cold_room_id,
                kind="temp_low",
                severity="warning",
                message_en=f"Chilling risk: {room.name} temperature is {reading.temp_c:.1f}°C (below min {room.min_temp}°C).",
                message_or=f"{room.name} ରେ ତାପମାତ୍ରା {reading.temp_c:.1f}°C କୁ ହ୍ରାସ ପାଇଛି (ସର୍ବନିମ୍ନ ସୀମା {room.min_temp}°C)।",
                payload=f'{{"temp_c": {reading.temp_c}, "min_temp": {room.min_temp}}}'
            )
            db.add(alert)
            db.commit()

    # 2. Check for rapid rise (> 2.0°C in last hour)
    one_hour_ago = reading.ts - datetime.timedelta(hours=1.2)
    past_reading = (
        db.query(SensorReading)
        .filter(SensorReading.cold_room_id == cold_room_id, SensorReading.ts >= one_hour_ago, SensorReading.ts < reading.ts)
        .order_by(SensorReading.ts.asc())
        .first()
    )
    if past_reading and (reading.temp_c - past_reading.temp_c) >= 2.0:
        open_alert = db.query(Alert).filter(
            Alert.cold_room_id == cold_room_id,
            Alert.kind == "rapid_rise",
            Alert.resolved_at.is_(None)
        ).first()
        if not open_alert:
            rise_val = reading.temp_c - past_reading.temp_c
            alert = Alert(
                cold_room_id=cold_room_id,
                kind="rapid_rise",
                severity="danger",
                message_en=f"Rapid warming detected: {room.name} rose by {rise_val:.1f}°C in under an hour. Check door or power supply.",
                message_or=f"ଦ୍ରୁତ ତାପମାତ୍ରା ବୃଦ୍ଧି: {room.name} ରେ ୧ ଘଣ୍ଟା ମଧ୍ୟରେ {rise_val:.1f}°C ବୃଦ୍ଧି ପାଇଛି। କବାଟ ବନ୍ଦ ଅଛି କି ନାହିଁ ଦେଖନ୍ତୁ।",
                payload=f'{{"rise": {rise_val:.1f}}}'
            )
            db.add(alert)
            db.commit()


def check_missed_logs(db: Session):
    """Watchdog for missed logs across all active cold rooms."""
    rooms = db.query(ColdRoom).all()
    now = datetime.datetime.utcnow()
    for room in rooms:
        last_reading = (
            db.query(SensorReading)
            .filter(SensorReading.cold_room_id == room.id)
            .order_by(SensorReading.ts.desc())
            .first()
        )
        if last_reading:
            elapsed_min = (now - last_reading.ts).total_seconds() / 60.0
            grace_min = 30
            if elapsed_min > (room.log_interval_min + grace_min):
                open_alert = db.query(Alert).filter(
                    Alert.cold_room_id == room.id,
                    Alert.kind == "missed_log",
                    Alert.resolved_at.is_(None)
                ).first()
                if not open_alert:
                    alert = Alert(
                        cold_room_id=room.id,
                        kind="missed_log",
                        severity="warning",
                        message_en=f"Missed log reminder: {room.name} has not had a temperature reading for {int(elapsed_min)} minutes.",
                        message_or=f"ଲଗ୍ ସ୍ମାରକୀ: {room.name} ପାଇଁ ଗତ {int(elapsed_min)} ମିନିଟ୍ ଧରି କୌଣସି ତାପମାତ୍ରା ରେକର୍ଡ ହୋଇନାହିଁ।",
                        payload=f'{{"elapsed_min": {int(elapsed_min)}}}'
                    )
                    db.add(alert)
                    db.commit()


def parse_and_import_csv(csv_text: str, cold_room_id: int, db: Session, user_name: str = "CSV Import") -> Dict[str, Any]:
    f = io.StringIO(csv_text.strip())
    reader = csv.reader(f)
    rows = list(reader)
    if not rows:
        raise ValueError("CSV file is completely empty")

    header = [col.strip().lower() for col in rows[0]]
    # Match columns
    ts_idx = -1
    temp_idx = -1
    rh_idx = -1

    for idx, col in enumerate(header):
        if col in ["ts", "timestamp", "date", "datetime", "time", "logged_at"]:
            ts_idx = idx
        elif col in ["temp", "temperature", "temp_c", "t_c", "celsius", "temperature_c"]:
            temp_idx = idx
        elif col in ["rh", "humidity", "rh_pct", "rh_%", "rel_humidity"]:
            rh_idx = idx

    if temp_idx == -1:
        raise ValueError("Could not find a temperature column in CSV (expected 'temp', 'temperature', 'temp_c')")
    if rh_idx == -1:
        # Default RH if absent
        pass

    imported_count = 0
    readings = []

    for row_num, row in enumerate(rows[1:], start=2):
        if not row or all(c.strip() == "" for c in row):
            continue
        try:
            temp_val = float(row[temp_idx].strip())
            rh_val = float(row[rh_idx].strip()) if rh_idx != -1 and len(row) > rh_idx else 85.0
            
            ts_val = datetime.datetime.utcnow()
            if ts_idx != -1 and len(row) > ts_idx and row[ts_idx].strip():
                raw_ts = row[ts_idx].strip()
                try:
                    ts_val = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except Exception:
                    try:
                        ts_val = datetime.datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

            reading = SensorReading(
                cold_room_id=cold_room_id,
                ts=ts_val,
                temp_c=temp_val,
                rh=rh_val,
                entered_by=user_name,
                is_simulated=False
            )
            db.add(reading)
            readings.append(reading)
            imported_count += 1
        except Exception as e:
            continue

    db.commit()

    if readings:
        last = readings[-1]
        evaluate_coldroom_rules(db, cold_room_id, last)
        update_coldroom_batches(db, cold_room_id, last.temp_c, last.rh)

    return {"imported_rows": imported_count, "cold_room_id": cold_room_id}


def run_simulator_step(db: Session, cold_room_id: int, scenario: str) -> SensorReading:
    """
    Generates a simulated reading based on scenario.
    Marked clearly as `is_simulated=True`.
    """
    now = datetime.datetime.utcnow()
    last_reading = (
        db.query(SensorReading)
        .filter(SensorReading.cold_room_id == cold_room_id)
        .order_by(SensorReading.ts.desc())
        .first()
    )

    base_temp = last_reading.temp_c if last_reading else 4.2
    base_rh = last_reading.rh if last_reading else 90.0

    if scenario == "door_open":
        # Rapid spike
        new_temp = round(min(16.5, base_temp + 2.8), 1)
        new_rh = round(max(68.0, base_rh - 4.5), 1)
    elif scenario == "power_cut":
        # Gradual warm up towards ambient 28°C
        new_temp = round(min(27.0, base_temp + 1.2), 1)
        new_rh = round(max(65.0, base_rh - 2.0), 1)
    elif scenario == "recovery":
        # Cooling down
        new_temp = round(max(3.8, base_temp - 2.0), 1)
        new_rh = round(min(92.0, base_rh + 3.0), 1)
    else:  # normal
        # Small oscillation around 4.0°C
        import random
        delta = random.choice([-0.2, -0.1, 0.0, 0.1, 0.2])
        new_temp = round(max(3.0, min(5.5, base_temp + delta)), 1)
        new_rh = round(max(85.0, min(94.0, base_rh + delta * 2)), 1)

    reading = SensorReading(
        cold_room_id=cold_room_id,
        ts=now,
        temp_c=new_temp,
        rh=new_rh,
        entered_by="Demo Simulator (Scenario: " + scenario + ")",
        is_simulated=True
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Evaluate rules & update spoilage
    evaluate_coldroom_rules(db, cold_room_id, reading)
    update_coldroom_batches(db, cold_room_id, reading.temp_c, reading.rh, dt_hours=0.5)

    return reading
