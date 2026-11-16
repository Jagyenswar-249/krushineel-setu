from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.mandimitra import Mandi, Commodity, MandiPrice, PriceAlert
from apps.api.models.user import User
from apps.api.schemas.all import (
    MandiResponse, CommodityResponse, PriceAdviceResponse, PriceAlertCreate, PriceAlertResponse
)
from apps.api.services.mandimitra_service import calculate_price_forecast_and_advice
from apps.api.services.agmarknet_ingest import sync_odisha_mandi_prices
from apps.api.routers.auth import get_current_user

router = APIRouter(tags=["MandiMitra"])


@router.post("/mandimitra/sync-live")
async def trigger_live_mandi_sync(db: Session = Depends(get_db)):
    """
    Triggers on-demand synchronization of Odisha mandi prices from data.gov.in Agmarknet API.
    """
    result = await sync_odisha_mandi_prices(db)
    return result


@router.get("/mandis", response_model=List[MandiResponse])
def list_mandis(db: Session = Depends(get_db)):
    return db.query(Mandi).all()


@router.get("/commodities", response_model=List[CommodityResponse])
def list_commodities(db: Session = Depends(get_db)):
    return db.query(Commodity).all()


@router.get("/advice/sell-hold", response_model=PriceAdviceResponse)
def get_sell_hold_advice(
    mandi_id: int = Query(...),
    commodity_id: int = Query(...),
    storage_cost: float = Query(25.0, description="Cost in Rs per Qtl per day"),
    db: Session = Depends(get_db)
):
    try:
        return calculate_price_forecast_and_advice(
            db=db,
            mandi_id=mandi_id,
            commodity_id=commodity_id,
            storage_cost_per_day_per_qtl=storage_cost
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prices")
def get_prices(
    mandi_id: Optional[int] = None,
    commodity_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(MandiPrice)
    if mandi_id:
        query = query.filter(MandiPrice.mandi_id == mandi_id)
    if commodity_id:
        query = query.filter(MandiPrice.commodity_id == commodity_id)
    prices = query.order_by(MandiPrice.date.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "mandi_id": p.mandi_id,
            "mandi_name": p.mandi.name if p.mandi else None,
            "commodity_id": p.commodity_id,
            "commodity_name": p.commodity.name_en if p.commodity else None,
            "date": p.date.strftime("%Y-%m-%d"),
            "min_price": p.min_price,
            "max_price": p.max_price,
            "modal_price": p.modal_price,
            "arrivals": p.arrivals
        }
        for p in prices
    ]


@router.get("/price-alerts", response_model=List[PriceAlertResponse])
def get_user_price_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alerts = db.query(PriceAlert).filter(PriceAlert.user_id == user.id).all()
    results = []
    for a in alerts:
        results.append(
            PriceAlertResponse(
                id=a.id,
                mandi_id=a.mandi_id,
                commodity_id=a.commodity_id,
                mandi_name=a.mandi.name if a.mandi else None,
                commodity_name=a.commodity.name_en if a.commodity else None,
                direction=a.direction,
                threshold=a.threshold,
                is_active=a.is_active
            )
        )
    return results


@router.post("/price-alerts", response_model=PriceAlertResponse)
def create_price_alert(
    req: PriceAlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    alert = PriceAlert(
        user_id=user.id,
        mandi_id=req.mandi_id,
        commodity_id=req.commodity_id,
        direction=req.direction,
        threshold=req.threshold,
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return PriceAlertResponse(
        id=alert.id,
        mandi_id=alert.mandi_id,
        commodity_id=alert.commodity_id,
        mandi_name=alert.mandi.name if alert.mandi else None,
        commodity_name=alert.commodity.name_en if alert.commodity else None,
        direction=alert.direction,
        threshold=alert.threshold,
        is_active=alert.is_active
    )
