import datetime
import secrets
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.coldwatch import ColdRoom, DataSource, SensorReading, Batch, Alert
from apps.api.models.user import User
from apps.api.schemas.all import (
    ColdRoomCreate, ColdRoomResponse, DataSourceCreate, DataSourceResponse,
    ReadingCreate, ReadingResponse, BatchCreate, BatchResponse, AlertResponse, AlertAckRequest
)
from apps.api.services.coldwatch_service import (
    evaluate_coldroom_rules, update_coldroom_batches, parse_and_import_csv,
    check_missed_logs, run_simulator_step
)
from apps.api.routers.auth import get_current_user

router = APIRouter(tags=["ColdWatch"])


@router.get("/coldrooms", response_model=List[ColdRoomResponse])
def list_coldrooms(db: Session = Depends(get_db)):
    rooms = db.query(ColdRoom).all()
    results = []
    for r in rooms:
        last = (
            db.query(SensorReading)
            .filter(SensorReading.cold_room_id == r.id)
            .order_by(SensorReading.ts.desc())
            .first()
        )
        active_alerts = (
            db.query(Alert)
            .filter(Alert.cold_room_id == r.id, Alert.resolved_at.is_(None))
            .count()
        )
        
        status = "optimal"
        if active_alerts > 0:
            status = "warning"
        if last:
            if last.temp_c > r.max_temp or last.temp_c < r.min_temp:
                status = "danger"

        results.append(
            ColdRoomResponse(
                id=r.id,
                name=r.name,
                location=r.location,
                district=r.district,
                capacity_kg=r.capacity_kg,
                min_temp=r.min_temp,
                max_temp=r.max_temp,
                min_rh=r.min_rh,
                max_rh=r.max_rh,
                log_interval_min=r.log_interval_min,
                latest_temp=last.temp_c if last else None,
                latest_rh=last.rh if last else None,
                latest_ts=last.ts if last else None,
                status=status,
                is_simulated=last.is_simulated if last else False,
                active_alerts_count=active_alerts
            )
        )
    return results


@router.post("/coldrooms", response_model=ColdRoomResponse)
def create_coldroom(req: ColdRoomCreate, db: Session = Depends(get_db)):
    room = ColdRoom(
        name=req.name,
        location=req.location,
        district=req.district,
        capacity_kg=req.capacity_kg,
        min_temp=req.min_temp,
        max_temp=req.max_temp,
        min_rh=req.min_rh,
        max_rh=req.max_rh,
        log_interval_min=req.log_interval_min
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return ColdRoomResponse(
        id=room.id,
        name=room.name,
        location=room.location,
        district=room.district,
        capacity_kg=room.capacity_kg,
        min_temp=room.min_temp,
        max_temp=room.max_temp,
        min_rh=room.min_rh,
        max_rh=room.max_rh,
        log_interval_min=room.log_interval_min,
        status="optimal",
        is_simulated=False,
        active_alerts_count=0
    )


@router.get("/coldrooms/{room_id}", response_model=ColdRoomResponse)
def get_coldroom(room_id: int, db: Session = Depends(get_db)):
    r = db.query(ColdRoom).filter(ColdRoom.id == room_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Cold room not found")
    last = (
        db.query(SensorReading)
        .filter(SensorReading.cold_room_id == r.id)
        .order_by(SensorReading.ts.desc())
        .first()
    )
    active_alerts = (
        db.query(Alert)
        .filter(Alert.cold_room_id == r.id, Alert.resolved_at.is_(None))
        .count()
    )
    status = "optimal"
    if active_alerts > 0:
        status = "warning"
    if last and (last.temp_c > r.max_temp or last.temp_c < r.min_temp):
        status = "danger"

    return ColdRoomResponse(
        id=r.id,
        name=r.name,
        location=r.location,
        district=r.district,
        capacity_kg=r.capacity_kg,
        min_temp=r.min_temp,
        max_temp=r.max_temp,
        min_rh=r.min_rh,
        max_rh=r.max_rh,
        log_interval_min=r.log_interval_min,
        latest_temp=last.temp_c if last else None,
        latest_rh=last.rh if last else None,
        latest_ts=last.ts if last else None,
        status=status,
        is_simulated=last.is_simulated if last else False,
        active_alerts_count=active_alerts
    )


@router.get("/coldrooms/{room_id}/readings", response_model=List[ReadingResponse])
def get_readings(
    room_id: int,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    since = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    readings = (
        db.query(SensorReading)
        .filter(SensorReading.cold_room_id == room_id, SensorReading.ts >= since)
        .order_by(SensorReading.ts.asc())
        .limit(limit)
        .all()
    )
    return readings


@router.post("/coldrooms/{room_id}/readings", response_model=ReadingResponse)
def add_manual_reading(
    room_id: int,
    req: ReadingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    room = db.query(ColdRoom).filter(ColdRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Cold room not found")

    reading = SensorReading(
        cold_room_id=room_id,
        ts=req.ts or datetime.datetime.utcnow(),
        temp_c=req.temp_c,
        rh=req.rh,
        entered_by=f"Quick-Log ({user.name})",
        is_simulated=req.is_simulated
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Evaluate rules & batch spoilage
    evaluate_coldroom_rules(db, room_id, reading)
    update_coldroom_batches(db, room_id, reading.temp_c, reading.rh, dt_hours=1.0)

    return reading


@router.post("/coldrooms/{room_id}/import")
async def import_csv(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    room = db.query(ColdRoom).filter(ColdRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Cold room not found")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except Exception:
        csv_text = content.decode("latin-1")

    try:
        res = parse_and_import_csv(csv_text, room_id, db, user_name=f"CSV Import by {user.name}")
        return {"status": "success", "message": f"Successfully imported {res['imported_rows']} readings from CSV.", "data": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/coldrooms/{room_id}/sources", response_model=DataSourceResponse)
def create_data_source(
    room_id: int,
    req: DataSourceCreate,
    db: Session = Depends(get_db)
):
    room = db.query(ColdRoom).filter(ColdRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Cold room not found")

    raw_token = f"kns_{secrets.token_urlsafe(24)}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    source = DataSource(
        cold_room_id=room_id,
        name=req.name,
        kind=req.kind,
        token_hash=token_hash,
        is_active=True
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    return DataSourceResponse(
        id=source.id,
        cold_room_id=source.cold_room_id,
        name=source.name,
        kind=source.kind,
        is_active=source.is_active,
        last_seen_at=source.last_seen_at,
        token=raw_token  # Show token ONCE on creation
    )


@router.get("/coldrooms/{room_id}/alerts", response_model=List[AlertResponse])
def get_alerts(room_id: int, db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .filter(Alert.cold_room_id == room_id)
        .order_by(Alert.opened_at.desc())
        .limit(50)
        .all()
    )
    return alerts


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(
    alert_id: int,
    req: AlertAckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acked_at = datetime.datetime.utcnow()
    alert.acked_by = req.acked_by or user.name
    db.commit()
    return {"status": "success", "message": "Alert acknowledged", "acked_at": alert.acked_at}


@router.post("/batches", response_model=BatchResponse)
def add_batch(
    room_id: int = Query(...),
    req: BatchCreate = ...,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    room = db.query(ColdRoom).filter(ColdRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Cold room not found")

    batch = Batch(
        cold_room_id=room_id,
        commodity=req.commodity,
        qty_kg=req.qty_kg,
        shelf_life_days_ref=req.shelf_life_days_ref or 14.0,
        remaining_days=req.shelf_life_days_ref or 14.0,
        current_risk_pct=3.0,
        status="active",
        owner_id=user.id,
        notes=req.notes
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/batches", response_model=List[BatchResponse])
def list_batches(room_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Batch).filter(Batch.status == "active")
    if room_id:
        query = query.filter(Batch.cold_room_id == room_id)
    return query.all()
