"""
Angelopp v2 — Buyer Room
Browse available crops and place orders.
Rule 1: This room doesn't know about other rooms.

Flow:
  (empty) → Show menu
  1 → Browse crops → Select → Confirm purchase
  2 → My purchases (placeholder)
"""
from core import db, audit, sms


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        return menu()

    choice = parts[0]
    rest = parts[1:]

    if choice == '1':
        return browse_crops(session_id, phone, rest)
    elif choice == '2':
        return my_purchases(phone)
    else:
        return menu_with_error()


def menu():
    return (
        "CON Buyer Menu\n"
        "1. Browse available crops\n"
        "2. My purchases"
    )


def menu_with_error():
    return (
        "CON Invalid choice.\n"
        "1. Browse available crops\n"
        "2. My purchases"
    )


def browse_crops(session_id, phone, parts):
    """Show available crops and let buyer select."""
    crops = db.get_available_crops()

    if not crops:
        return "END No crops available right now. Check back later."

    # Step 1: Show available crops
    if not parts:
        lines = ["CON Available crops:"]
        for i, crop in enumerate(crops[:9], 1):  # Max 9 on USSD screen
            lines.append(f"{i}. {crop['crop_name']} - {crop['quantity']} @ KES {crop['price']}")
        return '\n'.join(lines)

    # Step 2: Select a crop
    try:
        idx = int(parts[0]) - 1
        if idx < 0 or idx >= len(crops):
            return "CON Invalid selection. Please try again."
        selected = crops[idx]
    except (ValueError, IndexError):
        return "CON Invalid selection. Please try again."

    # Step 3: Confirm purchase
    if len(parts) == 1:
        return (
            f"CON Buy this crop?\n"
            f"Crop: {selected['crop_name']}\n"
            f"Quantity: {selected['quantity']}\n"
            f"Price: KES {selected['price']}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 4: Execute on consent
    if len(parts) == 2:
        if parts[1] == '1':
            audit.log_event(phone, session_id, 'crop_purchased', {
                'crop_id': selected['id'],
                'crop': selected['crop_name'],
                'price': selected['price'],
                'seller': selected['phone']
            })
            sms.send_purchase_to_buyer(phone, selected['crop_name'], selected['price'], selected['phone'])
            sms.send_purchase_to_seller(selected['phone'], selected['crop_name'], selected['price'], phone)
            return (
                f"END Purchase confirmed!\n"
                f"{selected['crop_name']} - KES {selected['price']}\n"
                f"The farmer will be notified.\n"
                f"You will receive an SMS with contact details."
            )
        else:
            return "END Purchase cancelled."

    return "END Something went wrong. Please try again."


def my_purchases(phone):
    """Show buyer's purchases. Placeholder for pilot."""
    return (
        "END Your purchases will appear here.\n"
        "This feature is coming soon."
    )
