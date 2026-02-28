"""
Angelopp v2 — Farmer Room
List crops for sale in the marketplace.
Rule 1: This room doesn't know about other rooms.

Flow:
  (empty) → Show menu
  1 → List a crop → Name → Quantity → Price → Confirm
  2 → My listings (placeholder)
"""
from core import db, audit


# Common crops in the Bumala area
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
        return menu()

    choice = parts[0]
    rest = parts[1:]

    if choice == '1':
        return list_crop(session_id, phone, rest)
    elif choice == '2':
        return my_listings(phone)
    else:
        return menu_with_error()


def menu():
    return (
        "CON Farmer Menu\n"
        "1. List a crop for sale\n"
        "2. My listings"
    )


def menu_with_error():
    return (
        "CON Invalid choice.\n"
        "1. List a crop for sale\n"
        "2. My listings"
    )


def list_crop(session_id, phone, parts):
    """Step through: crop → quantity → price → confirm."""
    # Step 1: Choose crop
    if not parts:
        lines = [f"{k}. {v}" for k, v in sorted(CROPS.items())]
        return "CON What are you selling?\n" + '\n'.join(lines)

    crop_key = parts[0]
    crop_name = CROPS.get(crop_key)
    if not crop_name:
        return "CON Invalid crop. Try again.\n" + _crop_list()

    # Step 2: Quantity
    if len(parts) == 1:
        return f"CON Selling: {crop_name}\nEnter quantity (e.g. 50kg, 2 bags):"

    quantity = parts[1]

    # Step 3: Price
    if len(parts) == 2:
        return f"CON {crop_name} - {quantity}\nEnter price in KES:"

    price = parts[2]

    # Step 4: Confirm — rule 10: inform, ask, wait
    if len(parts) == 3:
        return (
            f"CON Confirm listing:\n"
            f"Crop: {crop_name}\n"
            f"Quantity: {quantity}\n"
            f"Price: KES {price}\n"
            f"1. Confirm\n"
            f"2. Cancel"
        )

    # Step 5: Execute on consent
    if len(parts) == 4:
        if parts[3] == '1':
            crop_id = db.create_crop(phone, crop_name, quantity, price)
            audit.log_event(phone, session_id, 'crop_listed', {
                'crop_id': crop_id, 'crop': crop_name,
                'quantity': quantity, 'price': price
            })
            return (
                f"END Listed! {crop_name}\n"
                f"Quantity: {quantity}\n"
                f"Price: KES {price}\n"
                f"Buyers can now see your listing."
            )
        else:
            return "END Listing cancelled."

    return "END Something went wrong. Please try again."


def my_listings(phone):
    """Show farmer's listings. Placeholder for pilot."""
    return (
        "END Your listings will appear here.\n"
        "This feature is coming soon."
    )


def _crop_list():
    lines = [f"{k}. {v}" for k, v in sorted(CROPS.items())]
    return '\n'.join(lines)
