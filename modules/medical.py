"""
Angelopp v2 — Medical Transport Room
Urgent transport to Bumala Health Center. Fewest possible steps.
Rule 1: This room doesn't know about other rooms.

Flow: Where are you? -> Confirm (destination is always Health Center)
"""
from core import db, audit, sms
from config import format_landmarks, get_landmark_name

DESTINATION = 'Bumala Health Center'


def handle(session_id, phone, parts):
    """Entry point from router. Two steps only."""
    if not parts:
        return (
            "CON MEDICAL TRANSPORT\n"
            "Where are you now?\n"
            + format_landmarks()
        )

    pickup_num = parts[0]
    pickup = get_landmark_name(pickup_num)
    if not pickup:
        return "CON Invalid location. Try again.\n" + format_landmarks()

    # Step 2: Confirm — one step to go
    if len(parts) == 1:
        return (
            f"CON Urgent transport:\n"
            f"From: {pickup}\n"
            f"To: {DESTINATION}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 3: Execute
    if len(parts) == 2:
        if parts[1] == '1':
            order_id = db.create_order(
                phone, 'medical', pickup, DESTINATION,
                order_type='medical', urgent=1
            )
            audit.log_event(phone, session_id, 'order_placed', {
                'order_id': order_id, 'pickup': pickup,
                'destination': DESTINATION, 'type': 'medical', 'urgent': True
            })
            sms.send_medical_confirmation(phone, order_id, pickup)
            return (
                f"END Medical transport #{order_id} confirmed!\n"
                f"From: {pickup}\n"
                f"To: {DESTINATION}\n"
                f"A rider will be notified immediately."
            )
        else:
            return "END Cancelled. Dial again if you need help."

    return "END Something went wrong. Please try again."
