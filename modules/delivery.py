"""
Angelopp v2 — Delivery Room
Send packages, food, or medicine between landmarks.
Rule 1: This room doesn't know about other rooms.

Flow: Pickup -> Destination -> What are you sending? -> Confirm
"""
from core import db, audit, sms
from config import format_landmarks, get_landmark_name


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        return "CON Where is the pickup?\n" + format_landmarks()

    pickup_num = parts[0]
    pickup = get_landmark_name(pickup_num)
    if not pickup:
        return "CON Invalid location. Try again.\n" + format_landmarks()

    # Step 2: Ask destination
    if len(parts) == 1:
        return (
            f"CON Pickup: {pickup}\n"
            "Where should we deliver?\n"
            + format_landmarks()
        )

    dest_num = parts[1]
    destination = get_landmark_name(dest_num)
    if not destination:
        return (
            f"CON Pickup: {pickup}\n"
            "Invalid location. Try again.\n"
            + format_landmarks()
        )

    if pickup_num == dest_num:
        return (
            "CON Pickup and destination cannot be the same.\n"
            "Choose a different destination.\n"
            + format_landmarks()
        )

    # Step 3: Ask what they're sending
    if len(parts) == 2:
        return (
            f"CON From: {pickup}\n"
            f"To: {destination}\n"
            f"What are you sending?"
        )

    description = parts[2]

    # Step 4: Confirm
    if len(parts) == 3:
        return (
            f"CON Confirm delivery:\n"
            f"From: {pickup}\n"
            f"To: {destination}\n"
            f"Item: {description}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 5: Execute on consent
    if len(parts) == 4:
        if parts[3] == '1':
            order_id = db.create_order(
                phone, 'delivery', pickup, destination,
                order_type='delivery', description=description
            )
            audit.log_event(phone, session_id, 'order_placed', {
                'order_id': order_id, 'pickup': pickup,
                'destination': destination, 'description': description
            })
            sms.send_delivery_confirmation(
                phone, order_id, pickup, destination, description
            )
            return (
                f"END Delivery #{order_id} confirmed!\n"
                f"From: {pickup}\n"
                f"To: {destination}\n"
                f"Item: {description}\n"
                f"You'll get an SMS when a rider picks it up."
            )
        else:
            audit.log_event(phone, session_id, 'order_cancelled', {})
            return "END Delivery cancelled. Dial again when ready."

    return "END Something went wrong. Please try again."
