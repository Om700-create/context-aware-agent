"""
Date Extraction Agent.

Converts natural-language date expressions ("tomorrow", "next Monday",
"coming Friday", "in 2 days") into a normalized YYYY-MM-DD value, returning
the original input, parsed date, and a confidence score.
"""
import datetime as dt
import re
import dateparser

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _resolve_weekday_phrase(text: str, base_date: dt.date) -> dt.date | None:
    """Handles 'next Monday', 'coming Friday', 'this Friday', bare 'Friday'."""
    t = text.lower().strip()
    m = re.search(r"(next|coming|this)?\s*(" + "|".join(WEEKDAYS) + r")", t)
    if not m:
        return None
    modifier, day_name = m.group(1), m.group(2)
    target_idx = WEEKDAYS.index(day_name)
    current_idx = base_date.weekday()
    delta = (target_idx - current_idx) % 7

    if modifier in ("next", "coming"):
        # "next/coming X" always means the upcoming occurrence; if today IS that
        # weekday, push to the following week to disambiguate from "today".
        if delta == 0:
            delta = 7
    else:
        # bare weekday name or "this X": nearest occurrence, today counts as 0.
        pass

    return base_date + dt.timedelta(days=delta)


def _resolve_relative_days(text: str, base_date: dt.date) -> dt.date | None:
    t = text.lower().strip()
    if "tomorrow" in t:
        return base_date + dt.timedelta(days=1)
    if "today" in t:
        return base_date
    m = re.search(r"in\s+(\d+)\s+day", t)
    if m:
        return base_date + dt.timedelta(days=int(m.group(1)))
    return None


def run_date_agent(text: str, base_date: dt.date | None = None) -> dict:
    base_date = base_date or dt.date.today()

    parsed_date = _resolve_relative_days(text, base_date) or _resolve_weekday_phrase(text, base_date)

    if parsed_date is None:
        settings_dict = {
            "RELATIVE_BASE": dt.datetime.combine(base_date, dt.time.min),
            "PREFER_DATES_FROM": "future",
        }
        parsed = dateparser.parse(text, settings=settings_dict)
        parsed_date = parsed.date() if parsed else None

    if parsed_date is None:
        return {
            "original_input": text,
            "parsed_date": None,
            "confidence": 0.0,
            "success": False,
            "message": "I couldn't understand that date. Try formats like 'tomorrow', 'next Monday', or '2026-07-01'.",
        }

    confidence = 0.95 if any(k in text.lower() for k in [
        "tomorrow", "today", "next", "coming", "in ", "monday", "tuesday",
        "wednesday", "thursday", "friday", "saturday", "sunday"
    ]) else 0.75

    if parsed_date < dt.date.today():
        return {
            "original_input": text,
            "parsed_date": None,
            "confidence": confidence,
            "success": False,
            "message": f"That date ({parsed_date.isoformat()}) is in the past. Please provide a future date.",
        }

    return {
        "original_input": text,
        "parsed_date": parsed_date.isoformat(),
        "confidence": confidence,
        "success": True,
        "message": None,
    }
