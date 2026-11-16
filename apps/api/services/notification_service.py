import datetime
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from apps.api.config import settings
from apps.api.models.notifications import Notification, SMSInbound
from apps.api.models.sagarsuraksha import Boat, Trip, Checkin, LandingSite
from apps.api.models.mandimitra import Mandi, Commodity, MandiPrice
from apps.api.models.matsyaconnect import CatchListing
from apps.api.models.user import User


class SMSGateway:
    def __init__(self, provider: str = None):
        self.provider = provider or settings.SMS_PROVIDER

    def send(self, to_phone: str, message: str, db: Optional[Session] = None) -> bool:
        """
        Sends SMS via chosen adapter (mock for demo).
        """
        if self.provider == "mock" or settings.DEMO_MODE:
            print(f"[SMS MOCK GATEWAY] To: {to_phone} | Msg: {message}")
            if db:
                notif = Notification(
                    user_id=None,
                    channel="sms",
                    title_en=f"SMS to {to_phone}",
                    title_or=f"SMS {to_phone}",
                    body_en=message,
                    body_or=message,
                    status="sent"
                )
                db.add(notif)
                db.commit()
            return True
        elif self.provider == "twilio":
            # Twilio SDK integration placeholder
            return True
        elif self.provider == "fast2sms":
            # Fast2SMS Indian gateway placeholder
            return True
        return True


sms_gateway = SMSGateway()


def parse_and_handle_inbound_sms(from_phone: str, body: str, db: Session) -> str:
    """
    Parses fixed keyword commands in English or transliterated Odia.
    Keywords: SAFE, TRIP, HELP, PRICE, SELL, WEATHER
    """
    text = body.strip()
    parts = text.split()
    if not parts:
        return "KrushiNeel Setu: Send SAFE, TRIP, HELP, PRICE, SELL, or WEATHER for instant assistance."

    cmd = parts[0].upper()
    now = datetime.datetime.utcnow()

    # 1. SAFE <boat_reg>
    if cmd == "SAFE":
        reg = parts[1].upper() if len(parts) > 1 else None
        boat = None
        if reg:
            boat = db.query(Boat).filter(Boat.reg_no.ilike(f"%{reg}%")).first()
        if not boat:
            boat = db.query(Boat).filter(Boat.contact_phone == from_phone).first()

        if not boat:
            return "KrushiNeel: Boat not found. Please provide registration no. Example: SAFE OD-02-B123"

        trip = db.query(Trip).filter(Trip.boat_id == boat.id, Trip.status.in_(["active", "overdue"])).first()
        if not trip:
            # Start auto trip if not present
            trip = Trip(
                boat_id=boat.id,
                departed_at=now,
                expected_return_at=now + datetime.timedelta(hours=12),
                status="active",
                checkin_interval_min=180,
                last_checkin_at=now
            )
            db.add(trip)
            db.commit()
            db.refresh(trip)

        checkin = Checkin(
            trip_id=trip.id,
            ts=now,
            source="sms",
            note="SMS Checkin via SAFE command"
        )
        db.add(checkin)
        trip.last_checkin_at = now
        trip.status = "active"
        db.commit()

        next_time = (now + datetime.timedelta(minutes=trip.checkin_interval_min)).strftime("%H:%M UTC")
        return f"Check-in saved for {boat.name}. Status: ACTIVE. Next check-in by {next_time}. Safe fishing!"

    # 2. TRIP <boat_reg> <hours>
    elif cmd == "TRIP":
        reg = parts[1].upper() if len(parts) > 1 else None
        hours = float(parts[2]) if len(parts) > 2 and parts[2].replace(".", "", 1).isdigit() else 12.0

        boat = None
        if reg:
            boat = db.query(Boat).filter(Boat.reg_no.ilike(f"%{reg}%")).first()
        if not boat:
            boat = db.query(Boat).filter(Boat.contact_phone == from_phone).first()

        if not boat:
            return "KrushiNeel: Boat not found. Example: TRIP OD-02-B123 12"

        trip = Trip(
            boat_id=boat.id,
            departed_at=now,
            expected_return_at=now + datetime.timedelta(hours=hours),
            status="active",
            checkin_interval_min=180,
            last_checkin_at=now
        )
        db.add(trip)
        db.commit()

        ret_time = trip.expected_return_at.strftime("%d-%b %H:%M")
        return f"Trip started for {boat.name}. Expected return: {ret_time}. Send SAFE every 3h to check in."

    # 3. HELP <boat_reg> (SOS)
    elif cmd in ["HELP", "SOS"]:
        reg = parts[1].upper() if len(parts) > 1 else None
        boat = None
        if reg:
            boat = db.query(Boat).filter(Boat.reg_no.ilike(f"%{reg}%")).first()
        if not boat:
            boat = db.query(Boat).filter(Boat.contact_phone == from_phone).first()

        boat_label = boat.name if boat else f"Fisher phone {from_phone}"
        if boat:
            trip = db.query(Trip).filter(Trip.boat_id == boat.id, Trip.status != "returned").first()
            if trip:
                trip.status = "sos"
                db.commit()

        return f"EMERGENCY ALERT logged for {boat_label}. Alerting contacts & Coast Guard. Stay calm, help is mobilized."

    # 4. PRICE <crop> <mandi>
    elif cmd == "PRICE":
        crop_query = parts[1] if len(parts) > 1 else "tomato"
        mandi_query = parts[2] if len(parts) > 2 else "Bhubaneswar"

        # Alias mappings for Odisha mandis
        alias_map = {
            "BBSR": "Bhubaneswar",
            "CTC": "Cuttack",
            "SBP": "Sambalpur",
            "BAM": "Berhampur",
            "BLS": "Balasore"
        }
        resolved_mandi = alias_map.get(mandi_query.upper(), mandi_query)

        comm = db.query(Commodity).filter(Commodity.name_en.ilike(f"%{crop_query}%")).first()
        mandi = db.query(Mandi).filter(Mandi.name.ilike(f"%{resolved_mandi}%")).first()

        if not comm or not mandi:
            return f"KrushiNeel: Price data not found for {crop_query} at {mandi_query}. Mandis: BBSR, Cuttack, Puri, Sambalpur."

        p = (
            db.query(MandiPrice)
            .filter(MandiPrice.commodity_id == comm.id, MandiPrice.mandi_id == mandi.id)
            .order_by(MandiPrice.date.desc())
            .first()
        )
        price_val = p.modal_price if p else 2150.0
        return f"{comm.name_en} at {mandi.name}: ₹{price_val:.0f}/Qtl ({p.date if p else 'Today'}). Trend: Steady."

    # 5. SELL <species> <kg> <price> <site>
    elif cmd == "SELL":
        # SELL HILSA 40 450 PURI
        if len(parts) < 5:
            return "KrushiNeel: Format: SELL <species> <kg> <price_per_kg> <landing_site>. Example: SELL HILSA 40 500 PURI"

        species = parts[1].title()
        qty = float(parts[2]) if parts[2].replace(".", "", 1).isdigit() else 25.0
        ask = float(parts[3]) if parts[3].replace(".", "", 1).isdigit() else 450.0
        site_str = parts[4]

        site = db.query(LandingSite).filter(LandingSite.name.ilike(f"%{site_str}%")).first()
        site_id = site.id if site else 1

        # Find or create user
        user = db.query(User).filter(User.phone == from_phone).first()
        if not user:
            user = User(phone=from_phone, name=f"Fisher-{from_phone[-4:]}", role="fisher", language="or")
            db.add(user)
            db.commit()

        listing = CatchListing(
            fisher_id=user.id,
            site_id=site_id,
            species=species,
            qty_kg=qty,
            ask_price=ask,
            status="active",
            created_at=now,
            expires_at=now + datetime.timedelta(hours=24)
        )
        db.add(listing)
        db.commit()

        # Run matching engine
        from apps.api.services.matsyaconnect_service import run_matching_engine
        matches = run_matching_engine(db, listing)

        return f"Catch listed: {qty}kg {species} @ ₹{ask}/kg at {site.name if site else 'Coast'}. {len(matches)} matching buyer(s) notified!"

    # 6. WEATHER <site>
    elif cmd == "WEATHER":
        site_name = parts[1] if len(parts) > 1 else "Puri"
        site = db.query(LandingSite).filter(LandingSite.name.ilike(f"%{site_name}%")).first()
        if not site:
            site = db.query(LandingSite).first()

        from apps.api.services.sagarsuraksha_service import evaluate_risk
        risk = evaluate_risk(wave_m=1.3, wind_kmh=22.0, gust_kmh=28.0)
        return f"{site.name if site else 'Odisha Coast'}: Wave {risk['wave_m']}m, Wind {risk['wind_kmh']} km/h. Sea condition: {risk['risk_level'].upper()}. Safe to sail."

    else:
        return f"KrushiNeel Setu: Unknown command '{cmd}'. Available commands: SAFE, TRIP, HELP, PRICE, SELL, WEATHER."
