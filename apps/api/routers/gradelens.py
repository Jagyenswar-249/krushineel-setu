import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.gradelens import GradingRequest, GradingResult
from apps.api.models.user import User
from apps.api.schemas.all import GradingResponse, GradeReviewRequest
from apps.api.services.gradelens_service import process_grading_request
from apps.api.routers.auth import get_current_user

router = APIRouter(tags=["GradeLens"])


def format_grading_response(res: GradingResult, req: GradingRequest) -> GradingResponse:
    filename = os.path.basename(req.image_path)
    image_url = f"/api/v1/grading/{res.id}/image"
    return GradingResponse(
        id=res.id,
        commodity=req.commodity,
        grade=res.reviewed_grade or res.grade,
        confidence=res.confidence,
        color_score=res.color_score,
        blemish_pct=res.blemish_pct,
        shape_uniformity=res.shape_uniformity,
        size_est=res.size_est,
        model_version=res.model_version,
        needs_review=res.needs_review,
        reviewed_grade=res.reviewed_grade,
        certificate_id=res.certificate_id,
        qr_code_data=res.qr_code_data,
        image_url=image_url,
        created_at=res.created_at
    )


@router.post("/grading", response_model=GradingResponse)
async def grade_produce(
    file: UploadFile = File(...),
    commodity: str = Form("Tomato"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG)")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit")

    req, res = process_grading_request(
        db=db,
        image_bytes=image_bytes,
        commodity=commodity,
        user_id=user.id,
        notes=notes
    )

    return format_grading_response(res, req)


@router.get("/grading", response_model=List[GradingResponse])
def list_gradings(db: Session = Depends(get_db)):
    results = (
        db.query(GradingResult, GradingRequest)
        .join(GradingRequest, GradingResult.request_id == GradingRequest.id)
        .order_by(GradingResult.created_at.desc())
        .limit(50)
        .all()
    )
    return [format_grading_response(res, req) for res, req in results]


@router.get("/grading/{grading_id}", response_model=GradingResponse)
def get_grading(grading_id: int, db: Session = Depends(get_db)):
    res = db.query(GradingResult).filter(GradingResult.id == grading_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Grading record not found")
    req = db.query(GradingRequest).filter(GradingRequest.id == res.request_id).first()
    return format_grading_response(res, req)


@router.get("/grading/{grading_id}/certificate")
def get_certificate(grading_id: int, db: Session = Depends(get_db)):
    res = db.query(GradingResult).filter(GradingResult.id == grading_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Grading record not found")
    req = db.query(GradingRequest).filter(GradingRequest.id == res.request_id).first()
    
    return {
        "certificate_id": res.certificate_id,
        "issued_at": res.created_at.isoformat(),
        "commodity": req.commodity,
        "grade": res.reviewed_grade or res.grade,
        "confidence": f"{int(res.confidence * 100)}%",
        "color_maturity": f"{res.color_score}%",
        "blemish_defect_pct": f"{res.blemish_pct}%",
        "shape_uniformity": f"{res.shape_uniformity}",
        "size_grade": res.size_est,
        "model_version": res.model_version,
        "verification_url": res.qr_code_data,
        "disclaimer_en": "This digital certificate provides decision-support grade assessment based on optical analysis and does not replace official statutory certification.",
        "disclaimer_or": "ଏହି ଡିଜିଟାଲ୍ ସାର୍ଟିଫିକେଟ୍ ଅପ୍ଟିକାଲ୍ ବିଶ୍ଳେଷଣ ଉପରେ ଆଧାରିତ ଏକ ନିଷ୍ପତ୍ତି ସହାୟକ ମାନ ଏବଂ ସରକାରୀ ବିଧିବଦ୍ଧ ପ୍ରମାଣପତ୍ରକୁ ବଦଳାଇ ପାରିବ ନାହିଁ।"
    }


@router.get("/grading/{grading_id}/image")
def get_grading_image(grading_id: int, db: Session = Depends(get_db)):
    res = db.query(GradingResult).filter(GradingResult.id == grading_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Grading record not found")
    req = db.query(GradingRequest).filter(GradingRequest.id == res.request_id).first()
    if not req or not os.path.exists(req.image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server")
    return FileResponse(req.image_path, media_type="image/jpeg")


@router.post("/grading/{grading_id}/review", response_model=GradingResponse)
def review_grading(
    grading_id: int,
    req_body: GradeReviewRequest,
    db: Session = Depends(get_db)
):
    res = db.query(GradingResult).filter(GradingResult.id == grading_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Grading record not found")
    req = db.query(GradingRequest).filter(GradingRequest.id == res.request_id).first()

    res.reviewed_grade = req_body.reviewed_grade.strip().upper()
    res.reviewer_notes = req_body.reviewer_notes
    res.needs_review = False
    db.commit()
    db.refresh(res)

    return format_grading_response(res, req)
