"""
Angelopp v2 — Rider Room
Boda-boda riders looking for work.
Rule 1: This room doesn't know about other rooms.

Flow: Where are you? -> Confirm -> Available
"""
from core import db, audit
from config import format_landmarks, get_landmark_name


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        pending = db.get_pending_order_count()
        if pending > 0:
            header = f"CON Rider — {pending} orders waiting\n"
        else:
            header = "CON Rider\n"
        return header + "Where are you now?\n" + format_landmarks()

    location_num = parts[0]
    location = get_landmark_name(location_num)
    if not location:
        return "CON Invalid location. Try again.\n" + format_landmarks()

    # Step 2: Confirm
    if len(parts) == 1:
        return (
            f"CON Set yourself available at:\n"
            f"{location}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 3: Execute
    if len(parts) == 2:
        if parts[1] == '1':
            audit.log_event(phone, session_id, 'provider_available', {
                'location': location
            })
            return (
                f"END You are available at {location}.\n"
                f"You will get an SMS when someone needs a ride."
            )
        else:
            return "END Cancelled. Dial again when ready."

    return "END Something went wrong. Please try again."
