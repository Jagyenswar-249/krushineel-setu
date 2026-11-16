import hashlib
import datetime
from typing import List
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.coldwatch import DataSource, SensorReading
from apps.api.schemas.all import IngestReadingItem
from apps.api.services.coldwatch_service import evaluate_coldroom_rules, update_coldroom_batches

router = APIRouter(tags=["Ingest"])


@router.post("/ingest/readings")
def ingest_readings(
    readings: List[IngestReadingItem],
    x_source_token: str = Header(..., alias="X-Source-Token"),
    db: Session = Depends(get_db)
):
    if not x_source_token:
        raise HTTPException(status_code=401, detail="Missing X-Source-Token header")

    token_hash = hashlib.sha256(x_source_token.strip().encode()).hexdigest()
    source = db.query(DataSource).filter(DataSource.token_hash == token_hash, DataSource.is_active == True).first()
    if not source:
        raise HTTPException(status_code=403, detail="Invalid or revoked source token")

    source.last_seen_at = datetime.datetime.utcnow()

    ingested_count = 0
    duplicate_count = 0
    last_reading_obj = None

    now = datetime.datetime.utcnow()

    for item in readings:
        # Check idempotency if key provided
        if item.id:
            existing = db.query(SensorReading).filter(SensorReading.idempotency_key == item.id).first()
            if existing:
                duplicate_count += 1
                continue

        # Basic timestamp sanity check (not > 2 hours in future, not > 30 days in past)
        # item.ts might be timezone-aware; strip tz for sqlite/generic naive utc comparison
        naive_ts = item.ts.replace(tzinfo=None) if item.ts.tzinfo else item.ts
        if naive_ts > now + datetime.timedelta(hours=2):
            continue
        if naive_ts < now - datetime.timedelta(days=30):
            continue

        reading = SensorReading(
            cold_room_id=source.cold_room_id,
            source_id=source.id,
            ts=naive_ts,
            temp_c=item.temp_c,
            rh=item.rh,
            entered_by=f"HTTP Ingest API ({source.name})",
            is_simulated=item.is_simulated or False,
            idempotency_key=item.id
        )
        db.add(reading)
        last_reading_obj = reading
        ingested_count += 1

    db.commit()

    if last_reading_obj:
        evaluate_coldroom_rules(db, source.cold_room_id, last_reading_obj)
        update_coldroom_batches(db, source.cold_room_id, last_reading_obj.temp_c, last_reading_obj.rh)

    return {
        "status": "success",
        "ingested": ingested_count,
        "duplicates_skipped": duplicate_count,
        "cold_room_id": source.cold_room_id
    }
