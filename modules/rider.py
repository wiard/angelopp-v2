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

    # Step 2: Optional vehicle type
    if len(parts) == 1:
        return (
            f"CON Location: {location}\n"
            f"Add your vehicle type?\n"
            f"1. Add vehicle\n"
            f"2. Skip"
        )

    # Handle optional vehicle
    vehicle = None
    if parts[1] == '1':
        if len(parts) == 2:
            return "CON Enter vehicle type (e.g. Boda, Tuk-tuk):"
        vehicle = parts[2]
        confirm_parts = parts[3:]
    elif parts[1] == '2':
        confirm_parts = parts[2:]
    else:
        confirm_parts = parts[2:]

    # Step 3: Confirm
    if not confirm_parts:
        veh_line = f"Vehicle: {vehicle}\n" if vehicle else ""
        return (
            f"CON Set yourself available at:\n"
            f"{location}\n"
            f"{veh_line}"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 4: Execute
    if confirm_parts[0] == '1':
        audit.log_event(phone, session_id, 'provider_available', {
            'location': location, 'vehicle': vehicle
        })
        veh_msg = f" ({vehicle})" if vehicle else ""
        return (
            f"END You are available at {location}{veh_msg}.\n"
            f"You will get an SMS when someone needs a ride."
        )
    else:
        return "END Cancelled. Dial again when ready."
