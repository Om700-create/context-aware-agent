"""
Appointment Agent.

Implements the conversational booking state machine:

  IDLE -> WAITING_NAME -> WAITING_EMAIL -> WAITING_PHONE -> WAITING_DATE
       -> CONFIRMATION -> BOOKED

Each transition delegates field validation to the Validation Agent and date
parsing to the Date Agent. The in-progress draft is persisted on the Session
row (booking_draft JSON) so the flow survives context switches to Document Q&A
and back.
"""
from sqlalchemy.orm import Session as DBSession
from app.db import models
from app.agents.validation_agent import run_validation_agent
from app.agents.date_agent import run_date_agent

STATES = [
    "IDLE", "WAITING_NAME", "WAITING_EMAIL", "WAITING_PHONE",
    "WAITING_DATE", "CONFIRMATION", "BOOKED",
]

BOOKING_TRIGGER_WORDS = ["book", "appointment", "schedule", "reservation", "meeting"]


def is_booking_intent(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in BOOKING_TRIGGER_WORDS)


def is_new_booking_request(text: str) -> bool:
    """True for 'book an appointment' style requests (action), as opposed to
    'what appointment did I book?' style questions (memory lookup)."""
    t = text.lower()
    action_words = ["book an appointment", "book appointment", "schedule an appointment",
                     "i want to book", "make an appointment", "set up an appointment", "i'd like to book"]
    return any(w in t for w in action_words)


def _draft(session: models.Session) -> dict:
    return dict(session.booking_draft or {})


def start_booking(session: models.Session, user: models.User) -> dict:
    draft = _draft(session)
    if user.name:
        draft.setdefault("full_name", user.name)
    if user.email:
        draft.setdefault("email", user.email)
    if user.phone:
        draft.setdefault("phone", user.phone)

    session.booking_draft = draft
    next_state, prompt = _next_step(draft)
    session.booking_state = next_state
    return {"reply": prompt, "booking_state": next_state}


def _next_step(draft: dict) -> tuple[str, str]:
    if "full_name" not in draft:
        return "WAITING_NAME", "Let's book your appointment. What's your full name?"
    if "email" not in draft:
        return "WAITING_EMAIL", f"Thanks {draft['full_name']}. What's your email address?"
    if "phone" not in draft:
        return "WAITING_PHONE", "Great. What's your phone number (with country code)?"
    if "appointment_date" not in draft:
        return "WAITING_DATE", "What date would you like to come in? (e.g. 'tomorrow', 'next Monday')"
    return "CONFIRMATION", _confirmation_text(draft)


def _confirmation_text(draft: dict) -> str:
    return (
        "Please confirm your appointment details:\n"
        f"- Name: {draft.get('full_name')}\n"
        f"- Email: {draft.get('email')}\n"
        f"- Phone: {draft.get('phone')}\n"
        f"- Date: {draft.get('appointment_date')} (from: \"{draft.get('original_date_text')}\")\n\n"
        "Reply 'yes' to confirm or 'restart' to start over."
    )


def handle_booking_turn(db: DBSession, session: models.Session, user: models.User, message: str) -> dict:
    state = session.booking_state
    draft = _draft(session)

    if state == "WAITING_NAME":
        result = run_validation_agent("name", message)
        if not result["valid"]:
            return {"reply": result["message"], "booking_state": state}
        draft["full_name"] = result["value"]

    elif state == "WAITING_EMAIL":
        result = run_validation_agent("email", message)
        if not result["valid"]:
            return {"reply": result["message"], "booking_state": state}
        draft["email"] = result["value"]

    elif state == "WAITING_PHONE":
        result = run_validation_agent("phone", message)
        if not result["valid"]:
            return {"reply": result["message"], "booking_state": state}
        draft["phone"] = result["value"]

    elif state == "WAITING_DATE":
        result = run_date_agent(message)
        if not result["success"]:
            return {"reply": result["message"], "booking_state": state}
        draft["appointment_date"] = result["parsed_date"]
        draft["original_date_text"] = message

    elif state == "CONFIRMATION":
        if message.strip().lower() in ("yes", "y", "confirm", "yep", "yeah"):
            appt = models.Appointment(
                user_id=user.id,
                full_name=draft["full_name"],
                email=draft["email"],
                phone=draft["phone"],
                appointment_date=draft["appointment_date"],
                original_date_text=draft.get("original_date_text"),
                status="CONFIRMED",
            )
            db.add(appt)
            user.name = draft["full_name"]
            user.email = draft["email"]
            user.phone = draft["phone"]
            db.commit()

            session.booking_state = "IDLE"
            session.booking_draft = {}
            return {
                "reply": f"Your appointment is booked for {appt.appointment_date}. Confirmation ID: {appt.id[:8]}.",
                "booking_state": "BOOKED",
                "appointment_id": appt.id,
            }
        elif message.strip().lower() in ("restart", "no", "cancel"):
            session.booking_state = "IDLE"
            session.booking_draft = {}
            return {"reply": "No problem, I've cancelled that draft booking. Let me know if you'd like to start again.", "booking_state": "IDLE"}
        else:
            return {"reply": "Please reply 'yes' to confirm or 'restart' to start over.", "booking_state": "CONFIRMATION"}

    session.booking_draft = draft
    next_state, prompt = _next_step(draft)
    session.booking_state = next_state
    return {"reply": prompt, "booking_state": next_state}
