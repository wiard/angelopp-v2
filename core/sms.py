"""
Angelopp v2 — SMS Service (The Telephone Room)
Rule 4: The outside world is locked. Only through here, only with consent.
"""
import logging
from config import AT_USERNAME, AT_API_KEY, AT_SENDER_ID

logger = logging.getLogger('angelopp.sms')


def send_sms(to, message):
    """Send a single SMS via Africa's Talking."""
    if not AT_API_KEY:
        logger.warning(f"SMS not sent (no API key): to={to}, msg={message[:50]}")
        return False

    try:
        import africastalking
        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        sms = africastalking.SMS
        response = sms.send(message, [to], sender_id=AT_SENDER_ID)
        logger.info(f"SMS sent: to={to}, status={response}")
        return True
    except Exception as e:
        logger.error(f"SMS failed: to={to}, error={e}")
        return False


def send_delivery_confirmation(to, order_id, pickup, destination, description):
    """Send delivery confirmation SMS."""
    message = (
        f"Angelopp: Delivery #{order_id} confirmed.\n"
        f"From: {pickup}\n"
        f"To: {destination}\n"
        f"Item: {description}\n"
        f"A rider will pick it up soon."
    )
    return send_sms(to, message)


def send_ride_confirmation(to, order_id, pickup, destination):
    """Send ride confirmation SMS."""
    message = (
        f"Angelopp: Ride #{order_id} confirmed.\n"
        f"From: {pickup}\n"
        f"To: {destination}\n"
        f"A rider will contact you soon."
    )
    return send_sms(to, message)


def send_medical_confirmation(to, order_id, pickup, emergency=None):
    """Send urgent medical transport confirmation SMS."""
    emg_line = f"Emergency: {emergency}\n" if emergency else ""
    message = (
        f"Angelopp URGENT: Medical transport #{order_id}.\n"
        f"Pickup: {pickup}\n"
        f"To: Bumala Health Center\n"
        f"{emg_line}"
        f"A rider will be notified immediately."
    )
    return send_sms(to, message)


def send_crop_listed(to, crop_name, price):
    """Notify farmer their crop is listed."""
    message = (
        f"Angelopp: Your listing for {crop_name} at KES {price} is live.\n"
        f"Buyers can see it in the marketplace."
    )
    return send_sms(to, message)


def send_purchase_to_buyer(to, crop_name, price, seller_phone):
    """Notify buyer their purchase is confirmed with seller contact."""
    message = (
        f"Angelopp: You bought {crop_name} for KES {price}.\n"
        f"Contact the farmer: {seller_phone}"
    )
    return send_sms(to, message)


def send_purchase_to_seller(to, crop_name, price, buyer_phone,
                            message=None):
    """Notify farmer their crop was purchased with buyer contact."""
    msg_line = f"Message: {message}\n" if message else ""
    body = (
        f"Angelopp: Your {crop_name} (KES {price}) has been purchased!\n"
        f"{msg_line}"
        f"Contact the buyer: {buyer_phone}"
    )
    return send_sms(to, body)


def broadcast(phones, message):
    """Send same message to multiple numbers. Use sparingly."""
    results = []
    for phone in phones:
        results.append(send_sms(phone, message))
    return results
