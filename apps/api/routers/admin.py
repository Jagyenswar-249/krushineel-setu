from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.coldwatch import ColdRoom, Batch, SensorReading, Alert
from apps.api.models.sagarsuraksha import Boat, Trip
from apps.api.models.mandimitra import Mandi, MandiPrice
from apps.api.models.matsyaconnect import CatchListing, BuyerRequest, Match
from apps.api.schemas.all import SimulatorScenarioRequest
from apps.api.services.coldwatch_service import run_simulator_step

router = APIRouter(prefix="/admin", tags=["Admin & Simulator"])


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    return {
        "cold_rooms_count": db.query(ColdRoom).count(),
        "active_batches_count": db.query(Batch).filter(Batch.status == "active").count(),
        "total_readings_count": db.query(SensorReading).count(),
        "open_alerts_count": db.query(Alert).filter(Alert.resolved_at.is_(None)).count(),
        "registered_boats_count": db.query(Boat).count(),
        "active_trips_count": db.query(Trip).filter(Trip.status.in_(["active", "overdue"])).count(),
        "active_listings_count": db.query(CatchListing).filter(CatchListing.status == "active").count(),
        "buyer_requests_count": db.query(BuyerRequest).filter(BuyerRequest.status == "active").count(),
        "matches_count": db.query(Match).count(),
        "mandis_tracked": db.query(Mandi).count()
    }


@router.post("/simulator/scenario")
def trigger_simulator_scenario(req: SimulatorScenarioRequest, db: Session = Depends(get_db)):
    room = db.query(ColdRoom).filter(ColdRoom.id == req.cold_room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Cold room not found")

    reading = run_simulator_step(db, req.cold_room_id, req.scenario)

    return {
        "status": "success",
        "scenario": req.scenario,
        "cold_room_id": req.cold_room_id,
        "reading": {
            "temp_c": reading.temp_c,
            "rh": reading.rh,
            "ts": reading.ts.isoformat(),
            "is_simulated": reading.is_simulated
        },
        "badge": "SIMULATED"
    }
