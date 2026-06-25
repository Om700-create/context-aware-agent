from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from app.db.session import get_db
from app.db import models
from app.schemas.schemas import AnalyticsSummary

router = APIRouter(tags=["analytics"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/analytics", response_model=AnalyticsSummary)
def analytics(db: DBSession = Depends(get_db)):
    total_chats = db.query(models.AnalyticsEvent).filter(models.AnalyticsEvent.event_type == "chat").count()
    total_appointments = db.query(models.Appointment).count()
    total_users = db.query(models.User).count()
    total_documents = db.query(models.Document).count()

    agent_rows = (
        db.query(models.AnalyticsEvent.agent, func.count(models.AnalyticsEvent.id))
        .filter(models.AnalyticsEvent.agent.isnot(None))
        .group_by(models.AnalyticsEvent.agent)
        .all()
    )
    agent_usage = {agent: count for agent, count in agent_rows}

    avg_rt = (
        db.query(func.avg(models.AnalyticsEvent.response_time_ms))
        .filter(models.AnalyticsEvent.response_time_ms.isnot(None))
        .scalar()
    ) or 0.0

    return AnalyticsSummary(
        total_chats=total_chats,
        total_appointments=total_appointments,
        total_users=total_users,
        total_documents=total_documents,
        agent_usage=agent_usage,
        avg_response_time_ms=round(avg_rt, 2),
    )
