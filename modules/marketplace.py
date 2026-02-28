"""
Angelopp v2 — Marketplace Room
Buy and sell crops in one place.
Rule 1: This room doesn't know about other rooms.

Flow:
  1. Sell crops -> crop -> quantity -> price -> confirm
  2. Buy crops -> browse -> select -> confirm
"""
from core import db, audit, sms

CROPS = {
    '1': 'Maize',
    '2': 'Beans',
    '3': 'Tomatoes',
    '4': 'Sukuma Wiki (Kale)',
    '5': 'Bananas',
    '6': 'Sweet Potatoes',
    '7': 'Groundnuts',
    '8': 'Other',
}


def handle(session_id, phone, parts):
    """Entry point from router."""
    if not parts:
        return (
            "CON Marketplace\n"
            "1. Sell crops\n"
            "2. Buy crops"
        )

    choice = parts[0]
    rest = parts[1:]

    if choice == '1':
        return sell_crop(session_id, phone, rest)
    elif choice == '2':
        return buy_crop(session_id, phone, rest)
    else:
        return (
            "CON Invalid choice.\n"
            "1. Sell crops\n"
            "2. Buy crops"
        )


def sell_crop(session_id, phone, parts):
    """Sell flow: crop -> [custom name] -> quantity -> price -> confirm."""
    if not parts:
        return "CON What are you selling?\n" + _crop_list()

    crop_key = parts[0]
    crop_name = CROPS.get(crop_key)
    if not crop_name:
        return "CON Invalid crop. Try again.\n" + _crop_list()

    # "Other" needs a custom crop name
    if crop_name == 'Other':
        if len(parts) == 1:
            return "CON Enter crop name:"
        crop_name = parts[1]
        parts = [parts[0]] + parts[2:]  # collapse custom name out

    if len(parts) == 1:
        return f"CON Selling: {crop_name}\nEnter quantity (e.g. 50kg, 2 bags):"

    quantity = parts[1]

    if len(parts) == 2:
        return f"CON {crop_name} - {quantity}\nEnter price in KES:"

    price = parts[2]

    if len(parts) == 3:
        return (
            f"CON Confirm listing:\n"
            f"Crop: {crop_name}\n"
            f"Quantity: {quantity}\n"
            f"Price: KES {price}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    if len(parts) == 4:
        if parts[3] == '1':
            crop_id = db.create_crop(phone, crop_name, quantity, price)
            audit.log_event(phone, session_id, 'crop_listed', {
                'crop_id': crop_id, 'crop': crop_name,
                'quantity': quantity, 'price': price
            })
            sms.send_crop_listed(phone, crop_name, price)
            return (
                f"END Listed! {crop_name}\n"
                f"Quantity: {quantity}\n"
                f"Price: KES {price}\n"
                f"Buyers can now see your listing."
            )
        else:
            return "END Listing cancelled."

    return "END Something went wrong. Please try again."


def buy_crop(session_id, phone, parts):
    """Buy flow: browse -> select -> confirm."""
    crops = db.get_available_crops()

    if not crops:
        return "END No crops available right now. Check back later."

    if not parts:
        lines = ["CON Available crops:"]
        for i, crop in enumerate(crops[:9], 1):
            lines.append(
                f"{i}. {crop['crop_name']} - {crop['quantity']} "
                f"@ KES {crop['price']}"
            )
        return '\n'.join(lines)

    try:
        idx = int(parts[0]) - 1
        if idx < 0 or idx >= len(crops):
            return "CON Invalid selection. Try again."
        selected = crops[idx]
    except (ValueError, IndexError):
        return "CON Invalid selection. Try again."

    if len(parts) == 1:
        return (
            f"CON {selected['crop_name']} - KES {selected['price']}\n"
            f"Add a message for the farmer?\n"
            f"1. Add message\n"
            f"2. Skip"
        )

    # Handle optional message
    message = None
    if parts[1] == '1':
        if len(parts) == 2:
            return "CON Type your message for the farmer:"
        message = parts[2]
        confirm_parts = parts[3:]
    elif parts[1] == '2':
        confirm_parts = parts[2:]
    else:
        confirm_parts = parts[2:]

    if not confirm_parts:
        msg_line = f"Message: {message}\n" if message else ""
        return (
            f"CON Confirm purchase:\n"
            f"Crop: {selected['crop_name']}\n"
            f"Quantity: {selected['quantity']}\n"
            f"Price: KES {selected['price']}\n"
            f"{msg_line}"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    if confirm_parts[0] == '1':
        audit.log_event(phone, session_id, 'crop_purchased', {
            'crop_id': selected['id'],
            'crop': selected['crop_name'],
            'price': selected['price'],
            'seller': selected['phone'],
            'message': message
        })
        sms.send_purchase_to_buyer(
            phone, selected['crop_name'],
            selected['price'], selected['phone']
        )
        sms.send_purchase_to_seller(
            selected['phone'], selected['crop_name'],
            selected['price'], phone, message=message
        )
        return (
            f"END Purchase confirmed!\n"
            f"{selected['crop_name']} - KES {selected['price']}\n"
            f"The farmer will be notified.\n"
            f"You will receive an SMS with contact details."
        )
    else:
        return "END Purchase cancelled."


def _crop_list():
    return '\n'.join(f"{k}. {v}" for k, v in sorted(CROPS.items()))
