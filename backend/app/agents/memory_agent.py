"""
Memory Agent.

Owns long-term and session memory: user profile (name/email/phone), past
appointments, and conversation history. Answers introspective questions like
"what email did I provide earlier?" or "what appointment did I book?".
"""
import re
import datetime as dt
from sqlalchemy.orm import Session as DBSession
from app.db import models


MEMORY_PATTERNS = {
    "email": re.compile(r"what.*email|which email|my email", re.I),
    "phone": re.compile(r"what.*phone|which phone|my (phone|number)", re.I),
    "name": re.compile(r"what.*(my )?name|who am i", re.I),
    "appointment": re.compile(
        r"(what|which|when).*(appointment|booking)|appointment.*(did i|i booked|i made)", re.I
    ),
    "last_talk": re.compile(r"last (talk|chat|spoke)|when did we (last )?talk", re.I),
}


def detect_memory_query(text: str) -> str | None:
    for key, pattern in MEMORY_PATTERNS.items():
        if pattern.search(text):
            return key
    return None


def run_memory_agent(db: DBSession, user: models.User, query_type: str) -> str:
    if query_type == "email":
        return f"You provided the email **{user.email}**." if user.email else "I don't have an email on file for you yet."

    if query_type == "phone":
        return f"You provided the phone number **{user.phone}**." if user.phone else "I don't have a phone number on file for you yet."

    if query_type == "name":
        return f"Your name on file is **{user.name}**." if user.name else "I don't have your name on file yet."

    if query_type == "appointment":
        appts = (
            db.query(models.Appointment)
            .filter(models.Appointment.user_id == user.id)
            .order_by(models.Appointment.created_at.desc())
            .all()
        )
        if not appts:
            return "You don't have any appointments booked yet."
        latest = appts[0]
        if len(appts) == 1:
            return f"You booked an appointment for **{latest.appointment_date}** (status: {latest.status})."
        lines = "\n".join(f"- {a.appointment_date} (status: {a.status})" for a in appts)
        return f"You have {len(appts)} appointments:\n{lines}"

    if query_type == "last_talk":
        last_session = (
            db.query(models.Session)
            .filter(models.Session.user_id == user.id)
            .order_by(models.Session.last_active.desc())
            .first()
        )
        if last_session and last_session.last_active:
            delta = dt.datetime.utcnow() - last_session.last_active
            mins = int(delta.total_seconds() // 60)
            return f"We last talked about {mins} minute(s) ago." if mins > 0 else "We're talking right now!"
        return "This looks like our first conversation."

    return "I don't have that information in memory yet."


def get_user_context_summary(user: models.User) -> dict:
    """Returns a compact context block injected into agent prompts for personalization."""
    return {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
    }
