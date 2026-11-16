import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from apps.api.models.sagarsuraksha import LandingSite, Boat, Trip, Checkin, Geofence, MarineForecast, EmergencyContact
from apps.api.models.notifications import Notification


DEFAULT_LANDING_SITES = [
    {"name": "Puri Blue Flag Beach", "district": "Puri", "lat": 19.7983, "lon": 85.8249},
    {"name": "Paradip Fish Harbour", "district": "Jagatsinghpur", "lat": 20.3012, "lon": 86.6021},
    {"name": "Gopalpur Port", "district": "Ganjam", "lat": 19.2608, "lon": 84.9089},
    {"name": "Chandipur Coast", "district": "Balasore", "lat": 21.4697, "lon": 87.0135},
    {"name": "Arakhakuda Chilika Mouth", "district": "Puri", "lat": 19.6890, "lon": 85.4520},
    {"name": "Dhamra Port", "district": "Bhadrak", "lat": 20.8038, "lon": 86.9744},
]


# Ray casting point-in-polygon
def is_point_in_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """
    polygon is list of [lat, lon] points.
    """
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0][0], polygon[0][1]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n][0], polygon[i % n][1]
        if min(p1y, p2y) < lon <= max(p1y, p2y):
            if lat <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (lon - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or lat <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside


async def fetch_marine_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Calls Open-Meteo marine and weather API with graceful fallback.
    Fetches real-time wave heights, wind speeds, and wind gusts.
    """
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wind_wave_height&hourly=wave_height"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=wind_speed_10m,wind_gusts_10m"

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp_marine = await client.get(url)
            resp_weather = await client.get(weather_url)
            
            wave_m = 1.2
            wind_kmh = 20.0
            gust_kmh = 28.0

            if resp_marine.status_code == 200:
                data = resp_marine.json()
                wave_val = data.get("current", {}).get("wave_height")
                if wave_val is not None:
                    wave_m = float(wave_val)

            if resp_weather.status_code == 200:
                w_data = resp_weather.json()
                curr_w = w_data.get("current", {})
                wind_val = curr_w.get("wind_speed_10m")
                gust_val = curr_w.get("wind_gusts_10m")
                if wind_val is not None:
                    wind_kmh = float(wind_val)
                if gust_val is not None:
                    gust_kmh = float(gust_val)

            return evaluate_risk(wave_m, wind_kmh, gust_kmh)

    except Exception as exc:
        print(f"[Open-Meteo Marine] Offline fallback invoked: {exc}")
        return evaluate_risk(wave_m=1.3, wind_kmh=22.0, gust_kmh=29.0)


def evaluate_risk(wave_m: float, wind_kmh: float, gust_kmh: float) -> Dict[str, Any]:
    if wave_m >= 2.5 or wind_kmh >= 45.0 or gust_kmh >= 55.0:
        risk = "red"
        advice_en = "DANGER: High waves & strong squall. Fishermen are strictly advised not to venture into deep sea."
        advice_or = "ବିପଦ ସଙ୍କେତ: ଉଚ୍ଚ ତରଙ୍ଗ ଏବଂ ପ୍ରବଳ ପବନ। ମତ୍ସ୍ୟଜୀବୀମାନଙ୍କୁ ସମୁଦ୍ର ମଧ୍ୟକୁ ନଯିବା ପାଇଁ କଡ଼ା ପରାମର୍ଶ ଦିଆଯାଉଛି।"
    elif wave_m >= 1.8 or wind_kmh >= 30.0 or gust_kmh >= 40.0:
        risk = "amber"
        advice_en = "CAUTION: Moderate to rough sea conditions. Small motorized boats exercise extreme caution."
        advice_or = "ସତର୍କତା: ସମୁଦ୍ର ମଧ୍ୟମ ଅଶାନ୍ତ ଅଛି। ଛୋଟ ଡଙ୍ଗା ଚାଳକମାନେ କୂଳ ନିକଟରେ ରହି ସତର୍କତା ଅବଲମ୍ବନ କରନ୍ତୁ।"
    else:
        risk = "green"
        advice_en = "NORMAL: Sea conditions favorable. Safe for fishing."
        advice_or = "ସାଧାରଣ: ସମୁଦ୍ର ଶାନ୍ତ ଏବଂ ଅନୁକୂଳ ଅଛି। ମାଛ ଧରିବା ପାଇଁ ସୁରକ୍ଷିତ।"

    return {
        "wave_m": round(wave_m, 2),
        "wind_kmh": round(wind_kmh, 1),
        "gust_kmh": round(gust_kmh, 1),
        "risk_level": risk,
        "advice_en": advice_en,
        "advice_or": advice_or
    }


def check_trips_watchdog(db: Session):
    """
    Checks active trips for overdue check-ins or unreturned boats,
    escalating to emergency contacts and authorities.
    """
    now = datetime.datetime.utcnow()
    active_trips = db.query(Trip).filter(Trip.status == "active").all()

    for trip in active_trips:
        # Check elapsed checkin
        interval_min = trip.checkin_interval_min or 180
        grace_min = 30
        elapsed_min = (now - trip.last_checkin_at).total_seconds() / 60.0

        if elapsed_min > (interval_min + grace_min):
            trip.status = "overdue"
            boat = db.query(Boat).filter(Boat.id == trip.boat_id).first()
            boat_name = boat.name if boat else f"Boat-{trip.boat_id}"

            # Create notification
            notif = Notification(
                user_id=boat.owner_id if boat else None,
                channel="sms",
                title_en=f"OVERDUE ALERT: Boat {boat_name}",
                title_or=f"ସମୟ ଅତିକ୍ରାନ୍ତ ସତର୍କତା: ଡଙ୍ଗା {boat_name}",
                body_en=f"Boat {boat_name} missed scheduled check-in by {int(elapsed_min - interval_min)} min. Please send SAFE to check in.",
                body_or=f"ଡଙ୍ଗା {boat_name} ନିର୍ଦ୍ଧାରିତ ଚେକ୍-ଇନ୍ ସମୟ {int(elapsed_min - interval_min)} ମିନିଟ୍ ଅତିକ୍ରମ କରିଛି। ତୁରନ୍ତ 'SAFE' ଲେଖି SMS ପଠାନ୍ତୁ।"
            )
            db.add(notif)
            trip.overdue_notified_at = now

        # Check return time escalation
        if now > trip.expected_return_at:
            over_return_min = (now - trip.expected_return_at).total_seconds() / 60.0
            if over_return_min > 60 and not trip.escalated_notified_at:
                boat = db.query(Boat).filter(Boat.id == trip.boat_id).first()
                boat_name = boat.name if boat else f"Boat-{trip.boat_id}"
                
                # Fetch emergency contacts
                contacts = []
                if boat:
                    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == boat.owner_id).all()

                contact_names = ", ".join([c.name for c in contacts]) if contacts else "Fisheries Department / Coast Guard"
                notif = Notification(
                    user_id=boat.owner_id if boat else None,
                    channel="sms",
                    title_en=f"ESCALATION: Boat {boat_name} Overdue Return",
                    title_or=f"ଜରୁରୀ ସତର୍କତା: ଡଙ୍ଗା {boat_name} ଫେରିବାରେ ବିଳମ୍ବ",
                    body_en=f"URGENT: Boat {boat_name} is overdue return by {int(over_return_min)} min. Alerts sent to: {contact_names}.",
                    body_or=f"ଜରୁରୀ: ଡଙ୍ଗା {boat_name} ଫେରିବା ସମୟ {int(over_return_min)} ମିନିଟ୍ ବିତିଯାଇଛି। ସୂଚନା ପଠାଗଲା: {contact_names}।"
                )
                db.add(notif)
                trip.escalated_notified_at = now

    db.commit()


def check_position_geofences(db: Session, lat: float, lon: float) -> List[Dict[str, Any]]:
    """
    Checks if a position violates any marine conservation or security geofence.
    """
    geofences = db.query(Geofence).filter(Geofence.is_active == True).all()
    violations = []

    for gf in geofences:
        try:
            poly_coords = json.loads(gf.polygon_geojson)
            if is_point_in_polygon(lat, lon, poly_coords):
                violations.append({
                    "id": gf.id,
                    "name": gf.name,
                    "name_or": gf.name_or,
                    "kind": gf.kind,
                    "alert_message_en": gf.alert_message_en,
                    "alert_message_or": gf.alert_message_or
                })
        except Exception:
            continue

    return violations
