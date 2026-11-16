import datetime
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.sagarsuraksha import LandingSite, Boat, Trip, Checkin, Geofence, EmergencyContact
from apps.api.models.user import User
from apps.api.schemas.all import (
    BoatCreate, BoatResponse, TripStartRequest, TripCheckinRequest, TripResponse,
    MarineRiskResponse, GeofenceResponse, EmergencyContactCreate, EmergencyContactResponse
)
from apps.api.services.sagarsuraksha_service import (
    fetch_marine_forecast, check_trips_watchdog, check_position_geofences
)
from apps.api.routers.auth import get_current_user

router = APIRouter(tags=["SagarSuraksha"])


@router.get("/sites")
def list_landing_sites(db: Session = Depends(get_db)):
    return db.query(LandingSite).all()


@router.get("/sites/{site_id}/marine-risk", response_model=MarineRiskResponse)
async def get_marine_risk(site_id: int, db: Session = Depends(get_db)):
    site = db.query(LandingSite).filter(LandingSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Landing site not found")

    forecast = await fetch_marine_forecast(site.lat, site.lon)
    return MarineRiskResponse(
        site_id=site.id,
        site_name=site.name,
        district=site.district,
        ts=datetime.datetime.utcnow(),
        wave_m=forecast["wave_m"],
        wind_kmh=forecast["wind_kmh"],
        gust_kmh=forecast["gust_kmh"],
        risk_level=forecast["risk_level"],
        advice_en=forecast["advice_en"],
        advice_or=forecast["advice_or"]
    )


@router.post("/boats", response_model=BoatResponse)
def register_boat(
    req: BoatCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    site = db.query(LandingSite).filter(LandingSite.id == req.landing_site_id).first()
    if not site:
        raise HTTPException(status_code=400, detail="Invalid landing site ID")

    existing = db.query(Boat).filter(Boat.reg_no == req.reg_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Boat with this registration number already registered")

    boat = Boat(
        owner_id=user.id,
        reg_no=req.reg_no.upper().strip(),
        name=req.name,
        landing_site_id=req.landing_site_id,
        crew_size=req.crew_size,
        contact_phone=req.contact_phone
    )
    db.add(boat)
    db.commit()
    db.refresh(boat)

    return BoatResponse(
        id=boat.id,
        reg_no=boat.reg_no,
        name=boat.name,
        landing_site_id=boat.landing_site_id,
        landing_site_name=site.name,
        crew_size=boat.crew_size,
        contact_phone=boat.contact_phone
    )


@router.get("/boats", response_model=List[BoatResponse])
def list_boats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    boats = db.query(Boat).all()
    results = []
    for b in boats:
        site = db.query(LandingSite).filter(LandingSite.id == b.landing_site_id).first()
        results.append(
            BoatResponse(
                id=b.id,
                reg_no=b.reg_no,
                name=b.name,
                landing_site_id=b.landing_site_id,
                landing_site_name=site.name if site else None,
                crew_size=b.crew_size,
                contact_phone=b.contact_phone
            )
        )
    return results


@router.post("/trips", response_model=TripResponse)
def start_trip(
    req: TripStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    boat = db.query(Boat).filter(Boat.id == req.boat_id).first()
    if not boat:
        raise HTTPException(status_code=404, detail="Boat not found")

    now = datetime.datetime.utcnow()
    expected_return = now + datetime.timedelta(hours=req.expected_duration_hours)

    trip = Trip(
        boat_id=boat.id,
        departed_at=now,
        expected_return_at=expected_return,
        status="active",
        checkin_interval_min=req.checkin_interval_min,
        last_checkin_at=now
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return TripResponse(
        id=trip.id,
        boat_id=trip.boat_id,
        boat_name=boat.name,
        boat_reg_no=boat.reg_no,
        departed_at=trip.departed_at,
        expected_return_at=trip.expected_return_at,
        returned_at=trip.returned_at,
        status=trip.status,
        checkin_interval_min=trip.checkin_interval_min,
        last_checkin_at=trip.last_checkin_at,
        is_overdue=False,
        checkins_count=0
    )


@router.get("/trips/active", response_model=List[TripResponse])
def get_active_trips(db: Session = Depends(get_db)):
    check_trips_watchdog(db)
    trips = db.query(Trip).filter(Trip.status.in_(["active", "overdue", "sos"])).all()
    now = datetime.datetime.utcnow()

    res = []
    for t in trips:
        boat = db.query(Boat).filter(Boat.id == t.boat_id).first()
        is_overdue = t.status == "overdue" or (t.last_checkin_at and (now - t.last_checkin_at).total_seconds() > (t.checkin_interval_min * 60 + 1800))
        cnt = db.query(Checkin).filter(Checkin.trip_id == t.id).count()
        res.append(
            TripResponse(
                id=t.id,
                boat_id=t.boat_id,
                boat_name=boat.name if boat else f"Boat-{t.boat_id}",
                boat_reg_no=boat.reg_no if boat else "",
                departed_at=t.departed_at,
                expected_return_at=t.expected_return_at,
                returned_at=t.returned_at,
                status=t.status,
                checkin_interval_min=t.checkin_interval_min,
                last_checkin_at=t.last_checkin_at,
                is_overdue=is_overdue,
                checkins_count=cnt
            )
        )
    return res


@router.post("/trips/{trip_id}/checkin")
def trip_checkin(
    trip_id: int,
    req: TripCheckinRequest,
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now = datetime.datetime.utcnow()
    checkin = Checkin(
        trip_id=trip.id,
        ts=now,
        lat=req.lat,
        lon=req.lon,
        source=req.source,
        note=req.note or "Check-in received",
        is_sos=req.is_sos
    )
    db.add(checkin)
    
    trip.last_checkin_at = now
    if req.is_sos:
        trip.status = "sos"
    elif trip.status == "overdue":
        trip.status = "active"

    # Geofence check if GPS provided
    geofence_alerts = []
    if req.lat and req.lon:
        geofence_alerts = check_position_geofences(db, req.lat, req.lon)

    db.commit()

    return {
        "status": "success",
        "message": "Check-in recorded",
        "trip_status": trip.status,
        "next_checkin_due_in_min": trip.checkin_interval_min,
        "geofence_alerts": geofence_alerts
    }


@router.post("/trips/{trip_id}/end")
def end_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.status = "returned"
    trip.returned_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Trip marked as safely returned"}


@router.get("/geofences", response_model=List[GeofenceResponse])
def list_geofences(db: Session = Depends(get_db)):
    geofences = db.query(Geofence).filter(Geofence.is_active == True).all()
    results = []
    for gf in geofences:
        try:
            poly = json.loads(gf.polygon_geojson)
        except Exception:
            poly = []
        results.append(
            GeofenceResponse(
                id=gf.id,
                name=gf.name,
                name_or=gf.name_or,
                kind=gf.kind,
                polygon=poly,
                alert_message_en=gf.alert_message_en,
                alert_message_or=gf.alert_message_or,
                is_active=gf.is_active
            )
        )
    return results


@router.get("/contacts", response_model=List[EmergencyContactResponse])
def get_contacts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(EmergencyContact).filter(EmergencyContact.user_id == user.id).all()


@router.post("/contacts", response_model=EmergencyContactResponse)
def add_contact(
    req: EmergencyContactCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    c = EmergencyContact(
        user_id=user.id,
        name=req.name,
        phone=req.phone,
        kind=req.kind
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
