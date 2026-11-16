import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from apps.api.models.mandimitra import Mandi, Commodity, MandiPrice, PriceForecast, PriceAlert
from apps.api.models.notifications import Notification


def calculate_price_forecast_and_advice(
    db: Session,
    mandi_id: int,
    commodity_id: int,
    storage_cost_per_day_per_qtl: float = 25.0,  # ~ ₹0.25/kg per day in cold room
    spoilage_rate_pct_7d: float = 2.5
) -> Dict[str, Any]:
    mandi = db.query(Mandi).filter(Mandi.id == mandi_id).first()
    commodity = db.query(Commodity).filter(Commodity.id == commodity_id).first()

    if not mandi or not commodity:
        raise ValueError("Invalid Mandi or Commodity ID")

    # Fetch last 30 days of prices
    prices = (
        db.query(MandiPrice)
        .filter(MandiPrice.mandi_id == mandi_id, MandiPrice.commodity_id == commodity_id)
        .order_by(MandiPrice.date.asc())
        .limit(30)
        .all()
    )

    if not prices:
        # Fallback baseline price if no records
        latest_price = 2200.0
        historical = []
    else:
        latest_price = prices[-1].modal_price
        historical = [
            {
                "date": p.date.strftime("%Y-%m-%d"),
                "modal_price": p.modal_price,
                "min_price": p.min_price,
                "max_price": p.max_price,
                "arrivals": p.arrivals
            }
            for p in prices
        ]

    # Generate or query 7-day forecast
    forecast_points = []
    today = datetime.date.today()

    # Heuristic trend projection
    recent_trend = 0.0
    if len(prices) >= 5:
        recent_trend = (prices[-1].modal_price - prices[-5].modal_price) / 5.0

    # Damped drift
    drift = max(-30.0, min(40.0, recent_trend * 0.85))
    volatility = max(35.0, latest_price * 0.035)

    p50_final = latest_price
    for day in range(1, 8):
        f_date = today + datetime.timedelta(days=day)
        p50 = round(latest_price + (drift * day), 1)
        spread = volatility * (day ** 0.5)
        p10 = round(p50 - spread * 1.2, 1)
        p90 = round(p50 + spread * 1.2, 1)
        if day == 7:
            p50_final = p50

        forecast_points.append({
            "date": f_date.strftime("%Y-%m-%d"),
            "p10": p10,
            "p50": p50,
            "p90": p90
        })

    # Net-of-storage analysis
    days_held = 5 if drift > 0 else 0
    total_storage_cost = storage_cost_per_day_per_qtl * days_held
    spoilage_cost = (spoilage_rate_pct_7d / 100.0) * latest_price * (days_held / 7.0)
    
    price_diff = p50_final - latest_price
    net_storage_profit = price_diff - total_storage_cost - spoilage_cost
    gain_pct = round((price_diff / latest_price) * 100.0, 1)

    if net_storage_profit > 120.0 and gain_pct > 5.0:
        verdict = "HOLD"
        verdict_or = "ରଖନ୍ତୁ (HOLD)"
        horizon_days = 5
        reason_en = (
            f"Prices expected to rise by ~{gain_pct}% over the next 5-7 days. "
            f"Net gain after cold storage cost (₹{total_storage_cost:.0f}) and spoilage buffer is +₹{net_storage_profit:.0f}/Qtl."
        )
        reason_or = (
            f"ଆଗାମୀ ୫ ଦିନ ମଧ୍ୟରେ ଦର ପ୍ରାୟ {gain_pct}% ବଢ଼ିବାର ସମ୍ଭାବନା ଅଛି। "
            f"କୋଲ୍ଡ ଷ୍ଟୋରେଜ୍ ଖର୍ଚ୍ଚ (₹{total_storage_cost:.0f}) ବାଦ ଦେଇ ଆପଣଙ୍କର କୁଇଣ୍ଟାଲ ପିଛା ପ୍ରାୟ +₹{net_storage_profit:.0f} ଲାଭ ହେବ।"
        )
    else:
        verdict = "SELL"
        verdict_or = "ବିକ୍ରୟ କରନ୍ତୁ (SELL)"
        horizon_days = 0
        reason_en = (
            f"Prices are plateauing or expected storage cost (₹{total_storage_cost:.0f}) outweighs price gains. "
            f"Selling today locks in ₹{latest_price:.0f}/Qtl without storage risks."
        )
        reason_or = (
            f"ବଜାର ଦର ସ୍ଥିର ରହିଛି କିମ୍ବା କୋଲ୍ଡ ଷ୍ଟୋରେଜ୍ ଖର୍ଚ୍ଚ ଲାଭଠାରୁ ଅଧିକ ହେବ। "
            f"ଆଜି ହିଁ ₹{latest_price:.0f} ଦରରେ ବିକ୍ରୟ କରିବା ସବୁଠାରୁ ଲାଭଜନକ।"
        )

    return {
        "commodity": commodity.name_en,
        "commodity_or": commodity.name_or,
        "mandi": mandi.name,
        "mandi_or": mandi.name_or,
        "current_price": latest_price,
        "forecast_7d_p50": p50_final,
        "expected_gain_pct": gain_pct,
        "storage_cost_per_day": storage_cost_per_day_per_qtl,
        "spoilage_risk_pct": spoilage_rate_pct_7d,
        "net_storage_profit": round(net_storage_profit, 1),
        "verdict": verdict,
        "verdict_or": verdict_or,
        "horizon_days": horizon_days,
        "reason_en": reason_en,
        "reason_or": reason_or,
        "historical": historical,
        "forecast": forecast_points
    }
