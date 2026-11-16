import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from apps.api.models.matsyaconnect import CatchListing, BuyerRequest, Match
from apps.api.models.user import User
from apps.api.models.sagarsuraksha import LandingSite
from apps.api.models.notifications import Notification


SPECIES_REFERENCE_BANDS: Dict[str, Dict[str, float]] = {
    "hilsa": {"min": 450.0, "max": 800.0, "modal": 600.0},
    "tiger prawn": {"min": 550.0, "max": 950.0, "modal": 750.0},
    "pomfret": {"min": 380.0, "max": 600.0, "modal": 480.0},
    "rohu": {"min": 160.0, "max": 230.0, "modal": 190.0},
    "mud crab": {"min": 420.0, "max": 700.0, "modal": 540.0},
    "catla": {"min": 170.0, "max": 240.0, "modal": 200.0},
    "default": {"min": 200.0, "max": 400.0, "modal": 300.0}
}


def get_reference_price_band(species: str) -> Dict[str, float]:
    return SPECIES_REFERENCE_BANDS.get(species.lower().strip(), SPECIES_REFERENCE_BANDS["default"])


def run_matching_engine(db: Session, listing: CatchListing) -> List[Match]:
    """
    Finds buyer requests matching species and calculates multi-factor score.
    """
    species_clean = listing.species.lower().strip()
    requests = (
        db.query(BuyerRequest)
        .filter(BuyerRequest.status == "active")
        .all()
    )

    matches_created = []
    now = datetime.datetime.utcnow()
    hours_since_landing = (now - listing.created_at).total_seconds() / 3600.0

    for req in requests:
        if req.species.lower().strip() != species_clean:
            continue

        # 1. Price Score
        if listing.ask_price <= req.max_price:
            price_score = 100.0
        else:
            pct_diff = (listing.ask_price - req.max_price) / req.max_price
            price_score = max(0.0, 100.0 - (pct_diff * 150.0))

        # 2. Quantity Score
        min_q = min(listing.qty_kg, req.qty_kg)
        max_q = max(listing.qty_kg, req.qty_kg)
        qty_score = (min_q / max_q) * 100.0

        # 3. Freshness Score
        freshness_score = max(20.0, 100.0 - (hours_since_landing * 2.5))

        composite_score = round(0.45 * price_score + 0.35 * qty_score + 0.20 * freshness_score, 1)

        if composite_score >= 45.0:
            existing = (
                db.query(Match)
                .filter(Match.listing_id == listing.id, Match.request_id == req.id)
                .first()
            )
            if not existing:
                match = Match(
                    listing_id=listing.id,
                    request_id=req.id,
                    score=composite_score,
                    status="proposed",
                    proposed_at=now
                )
                db.add(match)
                matches_created.append(match)

                # Send notifications to both buyer and fisher
                buyer = db.query(User).filter(User.id == req.buyer_id).first()
                fisher = db.query(User).filter(User.id == listing.fisher_id).first()

                if buyer:
                    notif = Notification(
                        user_id=buyer.id,
                        channel="in_app",
                        title_en=f"New Catch Match: {listing.qty_kg}kg {listing.species}",
                        title_or=f"ନୂଆ ମାଛ ମ୍ୟାଚ୍: {listing.qty_kg} କେଜି {listing.species}",
                        body_en=f"Matched with catch at {listing.landing_site.name if listing.landing_site else 'Site'} @ ₹{listing.ask_price}/kg. Score: {composite_score}%.",
                        body_or=f"ଉପଲବ୍ଧ: {listing.landing_site.name if listing.landing_site else 'ଘାଟ'} ରେ ₹{listing.ask_price}/କେଜି ଦରରେ। ମ୍ୟାଚ୍ ସ୍କୋର୍: {composite_score}%।"
                    )
                    db.add(notif)

    db.commit()
    return matches_created
