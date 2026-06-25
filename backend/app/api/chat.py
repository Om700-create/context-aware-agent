import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.db.session import get_db
from app.db import models
from app.schemas.schemas import ChatRequest, ChatResponse, Citation
from app.agents.supervisor import supervisor_runner
from app.core.logging import logger

router = APIRouter(tags=["chat"])


def _get_or_create_user(db: DBSession, user_id: str | None) -> models.User:
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            return user
    user = models.User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_or_create_session(db: DBSession, session_id: str | None, user: models.User) -> models.Session:
    if session_id:
        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if session:
            return session
    session = models.Session(user_id=user.id, booking_state="IDLE", booking_draft={})
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: DBSession = Depends(get_db)):
    start = time.time()
    user = _get_or_create_user(db, req.user_id)
    session = _get_or_create_session(db, req.session_id, user)

    db.add(models.Message(session_id=session.id, role="user", content=req.message))
    db.commit()

    try:
        result = supervisor_runner(db, session, user, req.message)
    except Exception as e:
        logger.exception(f"Supervisor execution failed: {e}")
        raise HTTPException(status_code=500, detail="Agent execution failed. Check server logs.")

    import datetime as dt
    session.last_active = dt.datetime.utcnow()
    db.add(session)

    msg = models.Message(
        session_id=session.id,
        role="assistant",
        content=result["reply"],
        agent=result["agent"],
        meta={"confidence": result.get("confidence"), "citations": result.get("citations", [])},
    )
    db.add(msg)

    elapsed_ms = (time.time() - start) * 1000
    db.add(models.AnalyticsEvent(
        event_type="chat",
        agent=result["agent"],
        session_id=session.id,
        response_time_ms=elapsed_ms,
        meta={"intent": result["agent"]},
    ))
    db.commit()

    return ChatResponse(
        session_id=session.id,
        user_id=user.id,
        reply=result["reply"],
        agent=result["agent"],
        confidence=result.get("confidence"),
        citations=[Citation(**c) for c in result.get("citations", [])],
        booking_state=result.get("booking_state"),
        meta=result.get("meta", {}),
    )
