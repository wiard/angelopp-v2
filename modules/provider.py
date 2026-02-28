"""
Angelopp v2 — Provider Room
Offer transport and delivery services.
Rule 1: This room doesn't know about other rooms.

Flow:
  (empty) → Show menu
  1 → Set available (at which landmark)
  2 → View incoming orders (placeholder)
"""
from core import db, audit
from config import format_landmarks, get_landmark_name


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        return menu()

    choice = parts[0]
    rest = parts[1:]

    if choice == '1':
        return set_available(session_id, phone, rest)
    elif choice == '2':
        return view_orders(phone)
    else:
        return menu_with_error()


def menu():
    return (
        "CON Provider Menu\n"
        "1. I'm available for rides\n"
        "2. View incoming orders"
    )


def menu_with_error():
    return (
        "CON Invalid choice.\n"
        "1. I'm available for rides\n"
        "2. View incoming orders"
    )


def set_available(session_id, phone, parts):
    """Set provider as available at a specific landmark."""
    if not parts:
        return (
            "CON Where are you now?\n"
            + format_landmarks()
        )

    location = get_landmark_name(parts[0])
    if not location:
        return (
            "CON Invalid location. Try again.\n"
            + format_landmarks()
        )

    # Confirm availability — rule 2: butler asks
    if len(parts) == 1:
        return (
            f"CON Set yourself available at:\n"
            f"{location}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    if len(parts) == 2:
        if parts[1] == '1':
            audit.log_event(phone, session_id, 'provider_available', {
                'location': location
            })
            return (
                f"END You are now available at {location}.\n"
                f"You will receive an SMS when a customer needs a ride."
            )
        else:
            return "END Cancelled. Dial again when ready."

    return "END Something went wrong. Please try again."


def view_orders(phone):
    """Show incoming orders. Placeholder for pilot."""
    return (
        "END Incoming orders will appear here.\n"
        "This feature is coming soon."
    )
