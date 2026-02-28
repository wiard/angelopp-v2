"""
Angelopp v2 — USSD Router (The Butler)
Rule 2: The butler asks. No action without consent.
Rule 3: The butler does not remember. Sessions expire.
Rule 5: Internal first. Then reflection. Then route. Then respond.
Rule 6: Numbers are shortcuts, not menus.
"""
import logging
from core import db, audit
from modules import customer, provider, farmer, buyer
from config import LANDMARKS, format_landmarks, get_landmark_name

logger = logging.getLogger('angelopp.router')

# Role mapping — the four rooms
ROLES = {
    '1': ('customer', 'Customer (Request delivery)', customer),
    '2': ('provider', 'Provider (Offer transport)', provider),
    '3': ('farmer', 'Farmer (Sell crops)', farmer),
    '4': ('buyer', 'Buyer (Buy crops)', buyer),
}


def handle_ussd(session_id, phone, text):
    """
    Main USSD entry point. Called by app.py on every request.
    
    Flow:
    1. Internal: get/create user (rule 5: internal first)
    2. Reflect: parse input, handle back navigation
    3. Route: send to correct room
    4. Respond: return CON or END text
    """
    # Step 1: Internal — ensure user exists
    user = db.get_user(phone)
    if not user:
        user = db.create_user(phone)
        audit.log_event(phone, session_id, 'session_start', {'new_user': True})
    else:
        audit.log_event(phone, session_id, 'session_start', {'returning': True})

    # Step 2: Reflect — parse the input path
    parts = [p for p in text.split('*') if p] if text else []

    # Back navigation: 0 = go back one step (for real phones)
    parts = _process_back(parts)

    # Empty input (or backed all the way out) = start of session
    if not parts:
        return welcome_screen(user, phone)

    # Step 3: Route based on first input (role selection or shortcut)
    first = parts[0]
    rest = parts[1:] if len(parts) > 1 else []

    # Handle "continue as last role" for returning users
    if user.get('last_role') and first == '1' and not _was_at_role_select(parts, user):
        # User said "Yes" to "Continue as [role]?"
        role_key = _role_name_to_key(user['last_role'])
        if role_key and role_key in ROLES:
            role_name, _, module = ROLES[role_key]
            audit.log_event(phone, session_id, 'role_select', {'role': role_name, 'shortcut': True})
            return module.handle(session_id, phone, rest)

    # "2" on welcome-back screen = show role selection
    if user.get('last_role') and first == '2' and len(parts) == 1:
        return role_select_screen()

    # Direct role selection
    if first in ROLES:
        role_name, _, module = ROLES[first]
        db.update_user_role(phone, role_name)
        audit.log_event(phone, session_id, 'role_select', {'role': role_name})
        return module.handle(session_id, phone, rest)

    # If we get here with a returning user who picked "2" (other role)
    # then selected a role, the path is "2*[role]*..."
    if first == '2' and rest:
        role_pick = rest[0]
        role_rest = rest[1:] if len(rest) > 1 else []
        if role_pick in ROLES:
            role_name, _, module = ROLES[role_pick]
            db.update_user_role(phone, role_name)
            audit.log_event(phone, session_id, 'role_select', {'role': role_name})
            return module.handle(session_id, phone, role_rest)

    # Unknown input
    audit.log_event(phone, session_id, 'error', {'input': text, 'reason': 'unknown_path'})
    return "END Invalid input. Please try again."


def welcome_screen(user, phone):
    """
    First screen. Returning users get a shortcut (rule 6).
    New users get role selection.
    """
    if user.get('last_role'):
        return (
            f"CON Welcome back to Angelopp!\n"
            f"Continue as {user['last_role']}?\n"
            f"1. Yes\n"
            f"2. Choose different role"
        )
    return role_select_screen()


def role_select_screen():
    """Show the four rooms. This is the only menu."""
    return (
        "CON Welcome to Angelopp!\n"
        "Choose your role:\n"
        "1. Customer (Request delivery)\n"
        "2. Provider (Offer transport)\n"
        "3. Farmer (Sell crops)\n"
        "4. Buyer (Buy crops)"
    )


def _role_name_to_key(role_name):
    """Convert role name back to selection key."""
    for key, (name, _, _) in ROLES.items():
        if name.lower() == role_name.lower():
            return key
    return None


def _process_back(parts):
    """Process '0' as back navigation. Each 0 removes the previous step."""
    result = []
    for part in parts:
        if part == '0':
            if result:
                result.pop()
        else:
            result.append(part)
    return result


def _was_at_role_select(parts, user):
    """Check if user is at role selection (picked '2' then a role number)."""
    # If first input is a role number and user has no last_role, they're selecting directly
    return not user.get('last_role')
