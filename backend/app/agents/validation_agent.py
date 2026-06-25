"""
Validation Agent.

Responsible for validating user-supplied profile fields with user-friendly
error messages. Used by the Appointment Agent during the booking state machine.
"""
import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError


def validate_name(name: str) -> tuple[bool, str]:
    name = (name or "").strip()
    if len(name.split()) < 2:
        return False, "Please provide your full name (first and last name)."
    if not re.match(r"^[A-Za-zÀ-ÿ'\-\s\.]+$", name):
        return False, "Name contains invalid characters. Please use letters only."
    return True, name


def validate_email_address(email: str) -> tuple[bool, str]:
    email = (email or "").strip()
    try:
        result = validate_email(email, check_deliverability=False)
        return True, result.normalized
    except EmailNotValidError as e:
        return False, f"That email doesn't look valid: {e}. Please re-enter your email."


def validate_phone(phone: str, default_region: str = "IN") -> tuple[bool, str]:
    phone = (phone or "").strip()
    try:
        parsed = phonenumbers.parse(phone, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return False, "That phone number doesn't look valid. Please include country code if international."
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return True, formatted
    except phonenumbers.NumberParseException:
        return False, "Could not parse that phone number. Please provide it with country code, e.g. +91XXXXXXXXXX."


def run_validation_agent(field: str, value: str) -> dict:
    """Unified entry point used by the Supervisor / Appointment Agent."""
    if field == "name":
        ok, result = validate_name(value)
    elif field == "email":
        ok, result = validate_email_address(value)
    elif field == "phone":
        ok, result = validate_phone(value)
    else:
        ok, result = False, f"Unknown field: {field}"

    return {"field": field, "valid": ok, "value": result if ok else None, "message": None if ok else result}
