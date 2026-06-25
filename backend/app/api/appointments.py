from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.db.session import get_db
from app.db import models
from app.schemas.schemas import AppointmentCreate, AppointmentOut
from app.agents.validation_agent import run_validation_agent
from app.agents.date_agent import run_date_agent

router = APIRouter(tags=["appointments"])


@router.post("/appointments/create", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate, db: DBSession = Depends(get_db)):
    name_check = run_validation_agent("name", payload.full_name)
    if not name_check["valid"]:
        raise HTTPException(status_code=422, detail=name_check["message"])

    email_check = run_validation_agent("email", payload.email)
    if not email_check["valid"]:
        raise HTTPException(status_code=422, detail=email_check["message"])

    phone_check = run_validation_agent("phone", payload.phone)
    if not phone_check["valid"]:
        raise HTTPException(status_code=422, detail=phone_check["message"])

    date_result = run_date_agent(payload.date_text)
    if not date_result["success"]:
        raise HTTPException(status_code=422, detail=date_result["message"])

    if payload.user_id:
        user = db.query(models.User).filter(models.User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
    else:
        user = models.User(name=name_check["value"], email=email_check["value"], phone=phone_check["value"])
        db.add(user)
        db.commit()
        db.refresh(user)

    appt = models.Appointment(
        user_id=user.id,
        full_name=name_check["value"],
        email=email_check["value"],
        phone=phone_check["value"],
        appointment_date=date_result["parsed_date"],
        original_date_text=payload.date_text,
        status="CONFIRMED",
    )
    db.add(appt)
    db.add(models.AnalyticsEvent(event_type="appointment", meta={"appointment_id": appt.id}))
    db.commit()
    db.refresh(appt)
    return appt


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(db: DBSession = Depends(get_db)):
    return db.query(models.Appointment).order_by(models.Appointment.created_at.desc()).all()
