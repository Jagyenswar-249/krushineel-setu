import os
import sys
import datetime
import random
import hashlib
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.database import SessionLocal, Base, engine
from apps.api.models.user import User, Organization, Membership, AuditLog
from apps.api.models.coldwatch import ColdRoom, DataSource, SensorReading, Batch, SpoilageScore, AlertRule, Alert
from apps.api.models.gradelens import GradingRequest, GradingResult
from apps.api.models.sagarsuraksha import LandingSite, Boat, EmergencyContact, Trip, Checkin, Geofence, MarineForecast
from apps.api.models.mandimitra import Mandi, Commodity, MandiPrice, PriceForecast
from apps.api.models.matsyaconnect import CatchListing, BuyerRequest, Match
from apps.api.models.notifications import Notification


def seed(force_reset: bool = False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0 and not force_reset:
            print("Database already seeded. Skipping re-seed.")
            return

        if force_reset:
            print("Force reset requested. Clearing existing records...")
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()

        print("Seeding Users & Organizations...")
        # Users
        u_farmer = User(phone="9876543210", name="Ramesh Sahoo", role="farmer", language="or", district="Puri")
        u_fisher = User(phone="9876543211", name="Sanatan Behera", role="fisher", language="or", district="Puri")
        u_buyer = User(phone="9876543212", name="Rajesh Mohanty", role="buyer", language="en", district="Bhubaneswar")
        u_fpo = User(phone="9876543213", name="Priya Pattnaik", role="fpo_admin", language="en", district="Puri")
        u_admin = User(phone="9999999999", name="KrushiNeel Admin", role="admin", language="en", district="Bhubaneswar")
        db.add_all([u_farmer, u_fisher, u_buyer, u_fpo, u_admin])
        db.commit()

        # Organizations
        fpo = Organization(name="Jagannath Krushak Producer Co.", type="fpo", district="Puri")
        coop = Organization(name="Chilika Matsyajibi Cooperative", type="coop", district="Puri")
        db.add_all([fpo, coop])
        db.commit()

        # Memberships
        db.add(Membership(user_id=u_farmer.id, org_id=fpo.id, role="member"))
        db.add(Membership(user_id=u_fpo.id, org_id=fpo.id, role="manager"))
        db.add(Membership(user_id=u_fisher.id, org_id=coop.id, role="member"))
        db.commit()

        print("Seeding ColdWatch Cold Rooms & Readings...")
        room1 = ColdRoom(
            org_id=fpo.id,
            name="Konark Solar Micro Cold Room #1",
            location="Konark Agri Cluster, Gop Block",
            district="Puri",
            capacity_kg=5000.0,
            min_temp=2.0,
            max_temp=8.0,
            min_rh=80.0,
            max_rh=95.0,
            log_interval_min=60
        )
        room2 = ColdRoom(
            org_id=fpo.id,
            name="Nimapada Storage Unit #2",
            location="Nimapada Cold Hub",
            district="Puri",
            capacity_kg=10000.0,
            min_temp=6.0,
            max_temp=12.0,
            min_rh=85.0,
            max_rh=95.0,
            log_interval_min=60
        )
        db.add_all([room1, room2])
        db.commit()

        # Data sources with known demo token
        demo_token = "kns_demo_token_puri_2026"
        token_hash = hashlib.sha256(demo_token.encode()).hexdigest()
        source1 = DataSource(cold_room_id=room1.id, name="Solar IoT Gateway", kind="api", token_hash=token_hash, is_active=True)
        source2 = DataSource(cold_room_id=room1.id, name="Daily Staff Log", kind="manual", is_active=True)
        db.add_all([source1, source2])
        db.commit()

        # Past 24h readings
        now = datetime.datetime.utcnow()
        for i in range(24, 0, -1):
            ts = now - datetime.timedelta(hours=i)
            # Normal oscillation around 4.1°C
            temp = round(4.0 + 0.4 * math.sin(i / 2.0), 1)
            rh = round(89.0 + 2.0 * math.cos(i / 3.0), 1)
            db.add(SensorReading(
                cold_room_id=room1.id,
                source_id=source1.id,
                ts=ts,
                temp_c=temp,
                rh=rh,
                entered_by="Demo Logger",
                is_simulated=False
            ))
        db.commit()

        # Batches
        batch1 = Batch(
            cold_room_id=room1.id,
            commodity="Tomato",
            qty_kg=1200.0,
            stored_at=now - datetime.timedelta(days=2.5),
            owner_id=u_farmer.id,
            shelf_life_days_ref=14.0,
            remaining_days=11.5,
            current_risk_pct=8.5,
            status="active",
            notes="Lot #T-882 from Gop farmer cluster"
        )
        batch2 = Batch(
            cold_room_id=room1.id,
            commodity="Pointed Gourd",
            qty_kg=650.0,
            stored_at=now - datetime.timedelta(days=3.0),
            owner_id=u_farmer.id,
            shelf_life_days_ref=12.0,
            remaining_days=9.0,
            current_risk_pct=14.2,
            status="active",
            notes="Potala harvest, washed & crates packed"
        )
        batch3 = Batch(
            cold_room_id=room1.id,
            commodity="Potato",
            qty_kg=2500.0,
            stored_at=now - datetime.timedelta(days=6.0),
            owner_id=u_farmer.id,
            shelf_life_days_ref=90.0,
            remaining_days=84.0,
            current_risk_pct=4.1,
            status="active",
            notes="Kufri Jyoti seed potatoes"
        )
        db.add_all([batch1, batch2, batch3])
        db.commit()

        print("Seeding Landing Sites & SagarSuraksha Data...")
        landing_sites = [
            LandingSite(name="Puri Blue Flag Beach", district="Puri", lat=19.7983, lon=85.8249, active_fishers_count=120),
            LandingSite(name="Paradip Fish Harbour", district="Jagatsinghpur", lat=20.3012, lon=86.6021, active_fishers_count=350),
            LandingSite(name="Gopalpur Port", district="Ganjam", lat=19.2608, lon=84.9089, active_fishers_count=90),
            LandingSite(name="Chandipur Coast", district="Balasore", lat=21.4697, lon=87.0135, active_fishers_count=140),
            LandingSite(name="Arakhakuda Chilika Mouth", district="Puri", lat=19.6890, lon=85.4520, active_fishers_count=180),
            LandingSite(name="Dhamra Port", district="Bhadrak", lat=20.8038, lon=86.9744, active_fishers_count=85)
        ]
        db.add_all(landing_sites)
        db.commit()

        boat1 = Boat(
            owner_id=u_fisher.id,
            reg_no="OD-02-MM-104",
            name="Maa Mangala",
            landing_site_id=landing_sites[0].id,
            crew_size=4,
            contact_phone="9876543211"
        )
        boat2 = Boat(
            owner_id=u_fisher.id,
            reg_no="OD-04-SK-208",
            name="Sagar Kanya",
            landing_site_id=landing_sites[1].id,
            crew_size=5,
            contact_phone="9876543214"
        )
        db.add_all([boat1, boat2])
        db.commit()

        # Emergency Contacts
        c1 = EmergencyContact(user_id=u_fisher.id, name="Subhadra Behera (Spouse)", phone="9876500001", kind="family")
        c2 = EmergencyContact(user_id=u_fisher.id, name="Puri Fisheries Officer", phone="06752222345", kind="fisheries")
        c3 = EmergencyContact(user_id=u_fisher.id, name="Paradip Coast Guard Station", phone="1554", kind="coastguard")
        db.add_all([c1, c2, c3])
        db.commit()

        # Active Trip for Boat 1
        trip1 = Trip(
            boat_id=boat1.id,
            departed_at=now - datetime.timedelta(hours=4.5),
            expected_return_at=now + datetime.timedelta(hours=7.5),
            status="active",
            checkin_interval_min=180,
            last_checkin_at=now - datetime.timedelta(minutes=45)
        )
        db.add(trip1)
        db.commit()

        # Checkin for trip
        db.add(Checkin(
            trip_id=trip1.id,
            ts=now - datetime.timedelta(minutes=45),
            lat=19.7420,
            lon=85.8950,
            source="app",
            note="Good catch so far, sea calm, all 4 crew safe"
        ))
        db.commit()

        # Geofences
        gf1 = Geofence(
            name="Gahirmatha Marine Sanctuary",
            name_or="ଗହିରମଥା ସାମୁଦ୍ରିକ ଅଭୟାରଣ୍ୟ (ଅଲିଭ୍ ରିଡଲେ ସଂରକ୍ଷଣ)",
            kind="restricted",
            polygon_geojson=json.dumps([
                [20.5500, 86.8500],
                [20.8500, 87.0500],
                [20.6500, 87.2500],
                [20.4000, 87.0000]
            ]),
            alert_message_en="WARNING: Gahirmatha Olive Ridley Sanctuary! Mechanized fishing is prohibited by law.",
            alert_message_or="ସତର୍କତା: ଆପଣ ଗହିରମଥା କଇଁଛ ସଂରକ୍ଷିତ ଅଞ୍ଚଳ ନିକଟରେ ଅଛନ୍ତି! ମେସିନ୍ ଡଙ୍ଗାରେ ମାଛ ଧରିବା ନିଷେଧ।"
        )
        gf2 = Geofence(
            name="Rushikulya Rookery Offshore Buffer",
            name_or="ଋଷିକୁଲ୍ୟା ମୁହାଁଣ ସଂରକ୍ଷିତ ମତ୍ସ୍ୟ ନିଷିଦ୍ଧ ଅଞ୍ଚଳ",
            kind="seasonal_ban",
            polygon_geojson=json.dumps([
                [19.2500, 85.0000],
                [19.4500, 85.1500],
                [19.3500, 85.3000],
                [19.1500, 85.1000]
            ]),
            alert_message_en="CAUTION: Rushikulya seasonal turtle conservation zone (Nov 1 to May 31).",
            alert_message_or="ସୂଚନା: ଋଷିକୁଲ୍ୟା ମୁହାଁଣରେ କଇଁଛ ଅଣ୍ଡାଦାନ ଋତୁ ପାଇଁ ମାଛ ଧରିବା ଉପରେ କଟକଣା ରହିଛି।"
        )
        db.add_all([gf1, gf2])
        db.commit()

        print("Seeding Mandis, Commodities & Agmarknet Prices...")
        mandis = [
            Mandi(name="Bhubaneswar (Unit 1)", name_or="ଭୁବନେଶ୍ୱର (ୟୁନିଟ୍ ୧ ମଣ୍ଡି)", district="Khordha", lat=20.2700, lon=85.8300),
            Mandi(name="Cuttack (Malgodown)", name_or="କଟକ (ମାଲଗୋଦାମ)", district="Cuttack", lat=20.4625, lon=85.8828),
            Mandi(name="Puri (Badasankha)", name_or="ପୁରୀ (ବଡ଼ଶଙ୍ଖ ମଣ୍ଡି)", district="Puri", lat=19.8135, lon=85.8312),
            Mandi(name="Sambalpur (Khetrajpur)", name_or="ସମ୍ବଲପୁର (କ୍ଷେତରାଜପୁର ମଣ୍ଡି)", district="Sambalpur", lat=21.4885, lon=83.9780),
            Mandi(name="Balasore (Bada Mandi)", name_or="ବାଲେଶ୍ୱର (ବଡ଼ ମଣ୍ଡି)", district="Balasore", lat=21.4934, lon=86.9135),
            Mandi(name="Berhampur (Ganjam)", name_or="ବ୍ରହ୍ମପୁର ମଣ୍ଡି", district="Ganjam", lat=19.3150, lon=84.7941),
        ]
        db.add_all(mandis)
        db.commit()

        commodities = [
            Commodity(name_en="Tomato", name_or="ଟମାଟୋ", category="veg", unit="Quintal", optimal_min_temp=4.0, optimal_max_temp=10.0),
            Commodity(name_en="Potato", name_or="ଆଳୁ", category="veg", unit="Quintal", optimal_min_temp=8.0, optimal_max_temp=12.0),
            Commodity(name_en="Brinjal", name_or="ବାଇଗଣ", category="veg", unit="Quintal", optimal_min_temp=8.0, optimal_max_temp=12.0),
            Commodity(name_en="Pointed Gourd", name_or="ପୋଟଳ", category="veg", unit="Quintal", optimal_min_temp=6.0, optimal_max_temp=10.0),
            Commodity(name_en="Paddy (Dhan)", name_or="ଧାନ", category="paddy", unit="Quintal", optimal_min_temp=15.0, optimal_max_temp=20.0),
            Commodity(name_en="Onion", name_or="ପିଆଜ", category="veg", unit="Quintal", optimal_min_temp=0.0, optimal_max_temp=4.0)
        ]
        db.add_all(commodities)
        db.commit()

        # Seed 25 days of realistic price history
        base_prices = {
            "Tomato": 2100.0,
            "Potato": 1550.0,
            "Brinjal": 2400.0,
            "Pointed Gourd": 3200.0,
            "Paddy (Dhan)": 2183.0,
            "Onion": 2600.0
        }

        today = datetime.date.today()
        for comm in commodities:
            b_price = base_prices.get(comm.name_en, 2000.0)
            for m in mandis:
                # Add location baseline offset
                loc_offset = (m.id % 3) * 40.0 - 40.0
                curr = b_price + loc_offset

                for day_offset in range(25, 0, -1):
                    p_date = today - datetime.timedelta(days=day_offset)
                    # Simulated random walk with slight upward drift for tomato
                    drift = 12.0 if comm.name_en == "Tomato" else 3.0
                    shock = random.uniform(-40.0, 45.0)
                    curr = max(800.0, curr + drift + shock)

                    modal = round(curr, 0)
                    min_p = round(curr * 0.92, 0)
                    max_p = round(curr * 1.08, 0)
                    arrivals = round(random.uniform(30.0, 180.0), 1)

                    db.add(MandiPrice(
                        mandi_id=m.id,
                        commodity_id=comm.id,
                        date=p_date,
                        min_price=min_p,
                        max_price=max_p,
                        modal_price=modal,
                        arrivals=arrivals,
                        source="agmarknet"
                    ))
        db.commit()

        print("Seeding MatsyaConnect Listings, Buyer Demands & Matches...")
        cl1 = CatchListing(
            fisher_id=u_fisher.id,
            site_id=landing_sites[0].id,
            species="Hilsa (Ilish)",
            qty_kg=45.0,
            ask_price=580.0,
            status="active",
            created_at=now - datetime.timedelta(hours=2.0),
            expires_at=now + datetime.timedelta(hours=22.0)
        )
        cl2 = CatchListing(
            fisher_id=u_fisher.id,
            site_id=landing_sites[1].id,
            species="Tiger Prawn",
            qty_kg=35.0,
            ask_price=720.0,
            status="active",
            created_at=now - datetime.timedelta(hours=3.5),
            expires_at=now + datetime.timedelta(hours=20.5)
        )
        cl3 = CatchListing(
            fisher_id=u_fisher.id,
            site_id=landing_sites[2].id,
            species="Pomfret",
            qty_kg=28.0,
            ask_price=460.0,
            status="active",
            created_at=now - datetime.timedelta(hours=1.0),
            expires_at=now + datetime.timedelta(hours=23.0)
        )
        db.add_all([cl1, cl2, cl3])
        db.commit()

        br1 = BuyerRequest(
            buyer_id=u_buyer.id,
            species="Hilsa (Ilish)",
            qty_kg=50.0,
            max_price=620.0,
            radius_km=60.0,
            preferred_site_id=landing_sites[0].id,
            status="active"
        )
        br2 = BuyerRequest(
            buyer_id=u_buyer.id,
            species="Tiger Prawn",
            qty_kg=40.0,
            max_price=750.0,
            radius_km=80.0,
            preferred_site_id=landing_sites[1].id,
            status="active"
        )
        db.add_all([br1, br2])
        db.commit()

        # Seed Match
        match1 = Match(
            listing_id=cl1.id,
            request_id=br1.id,
            score=91.5,
            status="proposed",
            proposed_at=now - datetime.timedelta(minutes=30),
            buyer_contact_revealed=False,
            fisher_contact_revealed=False
        )
        db.add(match1)
        db.commit()

        # Initial System Notifications
        n1 = Notification(
            user_id=u_farmer.id,
            channel="in_app",
            title_en="Welcome to KrushiNeel Setu",
            title_or="କୃଷିନୀଳ ସେତୁକୁ ସ୍ୱାଗତ",
            body_en="Explore MandiMitra price forecasts and ColdWatch shelf-life monitoring for your produce.",
            body_or="ଆପଣଙ୍କ ଫସଲ ପାଇଁ ମଣ୍ଡିମିତ୍ର ଦର ପୂର୍ବାନୁମାନ ଏବଂ କୋଲ୍ଡଓ୍ବାଚ୍ ସଂରକ୍ଷଣ ସୁବିଧା ଦେଖନ୍ତୁ।"
        )
        n2 = Notification(
            user_id=u_fisher.id,
            channel="in_app",
            title_en="SagarSuraksha Sea Safety Active",
            title_or="ସାଗରସୁରକ୍ଷା ସକ୍ରିୟ ଅଛି",
            body_en="Puri coast sea status is GREEN today. Remember to send SAFE via SMS or tap the Safe button.",
            body_or="ଆଜି ପୁରୀ ଉପକୂଳ ସମୁଦ୍ର ଶାନ୍ତ ଅଛି। ସୁରକ୍ଷିତ ଚେକ୍-ଇନ୍ ପାଇଁ 'SAFE' ବଟନ୍ ବ୍ୟବହାର କରନ୍ତୁ।"
        )
        db.add_all([n1, n2])
        db.commit()

        print("Demo database successfully seeded!")
        print(f"-> Demo Users: Farmer (9876543210), Fisher (9876543211), Buyer (9876543212), FPO (9876543213), Admin (9999999999)")
        print(f"-> Demo OTP: 123456")
        print(f"-> Demo Ingest Source Token: {demo_token}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import math
    seed(force_reset=True)
