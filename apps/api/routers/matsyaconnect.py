import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.matsyaconnect import CatchListing, BuyerRequest, Match
from apps.api.models.sagarsuraksha import LandingSite
from apps.api.models.user import User
from apps.api.schemas.all import (
    CatchListingCreate, CatchListingResponse, BuyerRequestCreate, BuyerRequestResponse, MatchResponse
)
from apps.api.services.matsyaconnect_service import run_matching_engine, get_reference_price_band
from apps.api.routers.auth import get_current_user

router = APIRouter(tags=["MatsyaConnect"])


@router.get("/listings", response_model=List[CatchListingResponse])
def list_catch_listings(
    species: Optional[str] = None,
    site_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CatchListing).filter(CatchListing.status == "active")
    if species:
        query = query.filter(CatchListing.species.ilike(f"%{species}%"))
    if site_id:
        query = query.filter(CatchListing.site_id == site_id)
    listings = query.order_by(CatchListing.created_at.desc()).all()

    results = []
    for l in listings:
        ref_band = get_reference_price_band(l.species)
        results.append(
            CatchListingResponse(
                id=l.id,
                fisher_id=l.fisher_id,
                fisher_name=l.fisher.name if l.fisher else f"Fisher #{l.fisher_id}",
                site_id=l.site_id,
                site_name=l.landing_site.name if l.landing_site else None,
                district=l.landing_site.district if l.landing_site else None,
                species=l.species,
                qty_kg=l.qty_kg,
                ask_price=l.ask_price,
                status=l.status,
                created_at=l.created_at,
                expires_at=l.expires_at,
                reference_price_min=ref_band["min"],
                reference_price_max=ref_band["max"]
            )
        )
    return results


@router.post("/listings", response_model=CatchListingResponse)
def create_catch_listing(
    req: CatchListingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    site = db.query(LandingSite).filter(LandingSite.id == req.site_id).first()
    if not site:
        raise HTTPException(status_code=400, detail="Invalid landing site ID")

    now = datetime.datetime.utcnow()
    listing = CatchListing(
        fisher_id=user.id,
        site_id=req.site_id,
        species=req.species.strip().title(),
        qty_kg=req.qty_kg,
        ask_price=req.ask_price,
        status="active",
        created_at=now,
        expires_at=now + datetime.timedelta(hours=req.expires_in_hours or 24)
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    # Run matching engine
    run_matching_engine(db, listing)

    ref_band = get_reference_price_band(listing.species)
    return CatchListingResponse(
        id=listing.id,
        fisher_id=listing.fisher_id,
        fisher_name=user.name,
        site_id=listing.site_id,
        site_name=site.name,
        district=site.district,
        species=listing.species,
        qty_kg=listing.qty_kg,
        ask_price=listing.ask_price,
        status=listing.status,
        created_at=listing.created_at,
        expires_at=listing.expires_at,
        reference_price_min=ref_band["min"],
        reference_price_max=ref_band["max"]
    )


@router.get("/buyer-requests", response_model=List[BuyerRequestResponse])
def list_buyer_requests(db: Session = Depends(get_db)):
    requests = db.query(BuyerRequest).filter(BuyerRequest.status == "active").order_by(BuyerRequest.created_at.desc()).all()
    return [
        BuyerRequestResponse(
            id=r.id,
            buyer_id=r.buyer_id,
            buyer_name=r.buyer.name if r.buyer else f"Buyer #{r.buyer_id}",
            species=r.species,
            qty_kg=r.qty_kg,
            max_price=r.max_price,
            radius_km=r.radius_km,
            status=r.status,
            created_at=r.created_at
        )
        for r in requests
    ]


@router.post("/buyer-requests", response_model=BuyerRequestResponse)
def create_buyer_request(
    req: BuyerRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    buyer_req = BuyerRequest(
        buyer_id=user.id,
        species=req.species.strip().title(),
        qty_kg=req.qty_kg,
        max_price=req.max_price,
        radius_km=req.radius_km,
        preferred_site_id=req.preferred_site_id,
        status="active"
    )
    db.add(buyer_req)
    db.commit()
    db.refresh(buyer_req)

    # Match against existing active listings
    active_listings = db.query(CatchListing).filter(
        CatchListing.species.ilike(f"%{buyer_req.species}%"),
        CatchListing.status == "active"
    ).all()
    for l in active_listings:
        run_matching_engine(db, l)

    return BuyerRequestResponse(
        id=buyer_req.id,
        buyer_id=buyer_req.buyer_id,
        buyer_name=user.name,
        species=buyer_req.species,
        qty_kg=buyer_req.qty_kg,
        max_price=buyer_req.max_price,
        radius_km=buyer_req.radius_km,
        status=buyer_req.status,
        created_at=buyer_req.created_at
    )


@router.get("/matches", response_model=List[MatchResponse])
def list_matches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    matches = db.query(Match).order_by(Match.score.desc()).all()
    results = []
    for m in matches:
        listing = m.listing
        req = m.request
        if not listing or not req:
            continue

        site_name = listing.landing_site.name if listing.landing_site else "Coastal Port"
        buyer_name = req.buyer.name if req.buyer else "Verified Buyer"
        fisher_name = listing.fisher.name if listing.fisher else "Registered Fisher"

        buyer_phone = req.buyer.phone if (m.buyer_contact_revealed or m.status == "accepted") else "***-REVEAL ON ACCEPT"
        fisher_phone = listing.fisher.phone if (m.fisher_contact_revealed or m.status == "accepted") else "***-REVEAL ON ACCEPT"

        results.append(
            MatchResponse(
                id=m.id,
                listing_id=m.listing_id,
                request_id=m.request_id,
                score=m.score,
                status=m.status,
                species=listing.species,
                qty_kg=listing.qty_kg,
                price=listing.ask_price,
                landing_site=site_name,
                buyer_name=buyer_name,
                buyer_phone=buyer_phone,
                fisher_name=fisher_name,
                fisher_phone=fisher_phone,
                proposed_at=m.proposed_at
            )
        )
    return results


@router.post("/matches/{match_id}/accept")
def accept_match(match_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = "accepted"
    match.resolved_at = datetime.datetime.utcnow()
    match.buyer_contact_revealed = True
    match.fisher_contact_revealed = True
    db.commit()

    buyer = match.request.buyer if match.request else None
    fisher = match.listing.fisher if match.listing else None

    return {
        "status": "success",
        "message": "Match accepted! Contact details are now revealed.",
        "buyer_contact": {"name": buyer.name if buyer else "", "phone": buyer.phone if buyer else ""},
        "fisher_contact": {"name": fisher.name if fisher else "", "phone": fisher.phone if fisher else ""}
    }
