"""
Data.gov.in Agmarknet Real-time Daily Ingestion Service.
Fetches daily market prices for major Odisha Mandis from the Government Open Data portal.
"""

import datetime
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from apps.api.config import settings
from apps.api.models.mandimitra import Mandi, Commodity, MandiPrice

# Official resource id for Agmarknet on data.gov.in
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = "https://api.data.gov.in/resource/" + AGMARKNET_RESOURCE_ID


async def sync_odisha_mandi_prices(db: Session, target_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Pulls real daily commodity prices for Odisha from data.gov.in API.
    If no API key is set, returns an informative status with last cached records.
    """
    if not settings.DATAGOV_API_KEY:
        return {
            "status": "skipped",
            "message": "DATAGOV_API_KEY is not set. Using local database historical records.",
            "records_updated": 0
        }

    date_str = (target_date or datetime.date.today()).strftime("%d/%m/%Y")

    params = {
        "api-key": settings.DATAGOV_API_KEY,
        "format": "json",
        "offset": 0,
        "limit": 25,
        "filters[state]": "Odisha"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KrushiNeel/1.0",
        "Accept": "application/json"
    }

    try:
        # data.gov.in database queries take longer due to heavy dataset aggregations
        timeout_config = httpx.Timeout(connect=15.0, read=90.0, write=15.0, pool=15.0)
        async with httpx.AsyncClient(timeout=timeout_config, verify=False, follow_redirects=True) as client:
            resp = await client.get(BASE_URL, params=params, headers=headers)
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"Data.gov.in API returned error: {resp.text[:200]}"
                }

            data = resp.json()
            records = data.get("records", [])

            updated_count = 0
            for item in records:
                market_name = item.get("market", "").strip()
                commodity_name = item.get("commodity", "").strip()
                min_p = float(item.get("min_price", 0) or 0)
                max_p = float(item.get("max_price", 0) or 0)
                modal_p = float(item.get("modal_price", 0) or 0)
                arrivals = float(item.get("arrivals_in_qtl", 0) or 0)
                arrival_date_raw = item.get("arrival_date", "")

                try:
                    record_date = datetime.datetime.strptime(arrival_date_raw, "%d/%m/%Y").date()
                except Exception:
                    record_date = target_date or datetime.date.today()

                if not market_name or not commodity_name or modal_p <= 0:
                    continue

                # Find or create Mandi
                mandi = db.query(Mandi).filter(Mandi.name.ilike(f"%{market_name}%")).first()
                if not mandi:
                    mandi = Mandi(name=market_name, district=item.get("district", "Odisha"), state="Odisha")
                    db.add(mandi)
                    db.flush()

                # Find or create Commodity
                comm = db.query(Commodity).filter(Commodity.name_en.ilike(f"%{commodity_name}%")).first()
                if not comm:
                    comm = Commodity(
                        name_en=commodity_name,
                        name_or=commodity_name,
                        variety=item.get("variety", "General"),
                        shelf_life_days_ambient=4,
                        shelf_life_days_cold=21
                    )
                    db.add(comm)
                    db.flush()

                # Upsert daily price record
                existing = db.query(MandiPrice).filter(
                    MandiPrice.mandi_id == mandi.id,
                    MandiPrice.commodity_id == comm.id,
                    MandiPrice.date == record_date
                ).first()

                if existing:
                    existing.min_price = min_p
                    existing.max_price = max_p
                    existing.modal_price = modal_p
                    existing.arrivals = arrivals
                    existing.source = "data.gov.in"
                else:
                    new_price = MandiPrice(
                        mandi_id=mandi.id,
                        commodity_id=comm.id,
                        date=record_date,
                        min_price=min_p,
                        max_price=max_p,
                        modal_price=modal_p,
                        arrivals=arrivals,
                        source="data.gov.in"
                    )
                    db.add(new_price)

                updated_count += 1

            db.commit()
            return {
                "status": "success",
                "message": f"Successfully synced {updated_count} Odisha mandi price records from data.gov.in",
                "records_updated": updated_count
            }

    except Exception as exc:
        db.rollback()
        import traceback
        return {
            "status": "error",
            "message": f"Failed to ingest from data.gov.in: {type(exc).__name__}: {str(exc)}",
            "trace": traceback.format_exc()[-300:]
        }
