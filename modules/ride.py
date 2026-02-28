"""
Angelopp v2 — Ride Room
Personal transport between landmarks.
Rule 1: This room doesn't know about other rooms.

Flow: Where are you? -> Where to? -> Confirm
"""
from core import db, audit, sms
from config import format_landmarks, get_landmark_name


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        return "CON Where are you now?\n" + format_landmarks()

    pickup_num = parts[0]
    pickup = get_landmark_name(pickup_num)
    if not pickup:
        return "CON Invalid location. Try again.\n" + format_landmarks()

    # Step 2: Ask destination
    if len(parts) == 1:
        return (
            f"CON You're at: {pickup}\n"
            f"Where do you need to go?\n"
            + format_landmarks()
        )

    dest_num = parts[1]
    destination = get_landmark_name(dest_num)
    if not destination:
        return (
            f"CON You're at: {pickup}\n"
            "Invalid location. Try again.\n"
            + format_landmarks()
        )

    if pickup_num == dest_num:
        return (
            "CON Pickup and destination cannot be the same.\n"
            "Choose a different destination.\n"
            + format_landmarks()
        )

    # Step 3: Confirm
    if len(parts) == 2:
        return (
            f"CON Confirm your ride:\n"
            f"From: {pickup}\n"
            f"To: {destination}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 4: Execute on consent
    if len(parts) == 3:
        if parts[2] == '1':
            order_id = db.create_order(
                phone, 'ride', pickup, destination, order_type='ride'
            )
            audit.log_event(phone, session_id, 'order_placed', {
                'order_id': order_id, 'pickup': pickup,
                'destination': destination, 'type': 'ride'
            })
            sms.send_ride_confirmation(phone, order_id, pickup, destination)
            return (
                f"END Ride #{order_id} confirmed!\n"
                f"From: {pickup}\n"
                f"To: {destination}\n"
                f"A rider will contact you soon."
            )
        else:
            audit.log_event(phone, session_id, 'order_cancelled', {})
            return "END Ride cancelled. Dial again when ready."

    return "END Something went wrong. Please try again."
