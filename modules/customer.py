"""
Angelopp v2 — Customer Room
Request rides and deliveries between landmarks.
Rule 1: This room doesn't know about other rooms.
Rule 10: Inform, ask, wait, execute on consent.

Flow:
  (empty) → Show menu
  1 → New delivery → Pick pickup → Pick destination → Confirm
  2 → My orders (placeholder)
"""
from core import db, audit
from config import format_landmarks, get_landmark_name


def handle(session_id, phone, parts):
    """
    Entry point. Called by router with remaining path parts.
    parts = [] means customer just selected this role.
    """
    if not parts:
        return menu()

    choice = parts[0]
    rest = parts[1:]

    if choice == '1':
        return new_delivery(session_id, phone, rest)
    elif choice == '2':
        return my_orders(phone)
    else:
        return menu_with_error()


def menu():
    return (
        "CON Customer Menu\n"
        "1. New delivery\n"
        "2. My orders"
    )


def menu_with_error():
    return (
        "CON Invalid choice.\n"
        "1. New delivery\n"
        "2. My orders"
    )


def new_delivery(session_id, phone, parts):
    """
    Step through: pickup → destination → confirm
    parts[0] = pickup landmark number
    parts[1] = destination landmark number
    parts[2] = confirmation (1=yes)
    """
    # Step 1: Ask pickup location
    if not parts:
        return (
            "CON Where do you want pickup?\n"
            + format_landmarks()
        )

    pickup_num = parts[0]
    pickup = get_landmark_name(pickup_num)
    if not pickup:
        return (
            "CON Invalid location. Try again.\n"
            + format_landmarks()
        )

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
            "Invalid destination. Try again.\n"
            + format_landmarks()
        )

    # Same location check
    if pickup_num == dest_num:
        return (
            "CON Pickup and destination cannot be the same.\n"
            "Choose a different destination.\n"
            + format_landmarks()
        )

    # Step 3: Confirm — rule 10: the system asks, the user decides
    if len(parts) == 2:
        return (
            f"CON Confirm your delivery:\n"
            f"From: {pickup}\n"
            f"To: {destination}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 4: Execute on consent
    if len(parts) == 3:
        if parts[2] == '1':
            order_id = db.create_order(phone, 'customer', pickup, destination)
            audit.log_event(phone, session_id, 'order_placed', {
                'order_id': order_id, 'pickup': pickup, 'destination': destination
            })
            return (
                f"END Order #{order_id} confirmed!\n"
                f"From: {pickup}\n"
                f"To: {destination}\n"
                f"You will receive an SMS when a rider accepts."
            )
        else:
            audit.log_event(phone, session_id, 'order_cancelled', {
                'pickup': pickup, 'destination': destination
            })
            return "END Order cancelled. Dial again when ready."

    return "END Something went wrong. Please try again."


def my_orders(phone):
    """Show recent orders. Placeholder — kept simple for pilot."""
    return (
        "END Your recent orders will appear here.\n"
        "This feature is coming soon."
    )
