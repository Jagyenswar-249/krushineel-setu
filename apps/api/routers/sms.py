from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from apps.api.database import get_db
from apps.api.models.notifications import SMSInbound
from apps.api.schemas.all import SMSSimulateRequest, SMSSimulateResponse
from apps.api.services.notification_service import parse_and_handle_inbound_sms

router = APIRouter(tags=["SMS"])


@router.post("/sms/inbound")
def inbound_sms_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):
    reply_text = parse_and_handle_inbound_sms(From, Body, db)

    # Save to inbound log
    log = SMSInbound(
        from_phone=From,
        body=Body,
        parsed_command=Body.split()[0].upper() if Body.split() else "EMPTY",
        response_text=reply_text
    )
    db.add(log)
    db.commit()

    # Twilio-compatible XML TwiML or plain text response
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_text}</Message></Response>'
    return Response(content=twiml, media_type="application/xml")


@router.post("/sms/simulate", response_model=SMSSimulateResponse)
def simulate_sms(req: SMSSimulateRequest, db: Session = Depends(get_db)):
    reply = parse_and_handle_inbound_sms(req.from_phone, req.message, db)

    cmd = req.message.split()[0].upper() if req.message.split() else "EMPTY"
    log = SMSInbound(
        from_phone=req.from_phone,
        body=req.message,
        parsed_command=cmd,
        response_text=reply
    )
    db.add(log)
    db.commit()

    return SMSSimulateResponse(
        from_phone=req.from_phone,
        incoming_message=req.message,
        parsed_command=cmd,
        response_sms=reply
    )


@router.get("/sms/logs")
def list_sms_logs(db: Session = Depends(get_db)):
    logs = db.query(SMSInbound).order_by(SMSInbound.handled_at.desc()).limit(50).all()
    return logs
