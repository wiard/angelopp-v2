"""
Angelopp v2 — USSD Router (The Butler)
Rule 2: The butler asks. No action without consent.
Rule 3: The butler does not remember. Sessions expire.
Rule 5: Internal first. Then reflection. Then route. Then respond.
Rule 6: Numbers are shortcuts, not menus.
"""
import logging
from core import db, audit
from modules import delivery, ride, medical, marketplace, rider

logger = logging.getLogger('angelopp.router')

# Role mapping — the five rooms
ROLES = {
    '1': ('delivery', 'Send something', delivery),
    '2': ('ride', 'I need a ride', ride),
    '3': ('medical', 'Medical transport', medical),
    '4': ('marketplace', 'Buy or sell crops', marketplace),
    '5': ('rider', "I'm a rider", rider),
}

# Human-readable role descriptions for returning users
ROLE_DISPLAY = {
    'delivery': 'sending deliveries',
    'ride': 'booking rides',
    'medical': 'medical transport',
    'marketplace': 'the marketplace',
    'rider': 'finding rides',
}


def handle_ussd(session_id, phone, text):
    """
    Main USSD entry point. Called by app.py on every request.

    Flow:
    1. Internal: get/create user
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
    parts = _process_back(parts)

    if not parts:
        return welcome_screen(user)

    # Name registration — new user without a name
    if not user.get('name'):
        name = parts[0]
        db.update_user_name(phone, name)
        audit.log_event(phone, session_id, 'name_set', {'name': name})
        user['name'] = name
        rest_after_name = parts[1:]
        if not rest_after_name:
            return role_select_screen()
        parts = rest_after_name
    elif parts[0] == user['name']:
        # Name already set — skip the name prefix from USSD path
        parts = parts[1:]
        if not parts:
            return welcome_screen(user)

    # Step 3: Route
    first = parts[0]
    rest = parts[1:] if len(parts) > 1 else []

    # Returning user: 1=continue with last role, 2=choose different
    if user.get('last_role'):
        if first == '1':
            role_key = _role_name_to_key(user['last_role'])
            if role_key and role_key in ROLES:
                role_name, _, module = ROLES[role_key]
                audit.log_event(phone, session_id, 'role_select', {
                    'role': role_name, 'shortcut': True
                })
                return module.handle(session_id, phone, rest)

        if first == '2':
            # "Choose different" — always intercept for returning users
            if not rest:
                return role_select_screen()
            role_pick = rest[0]
            role_rest = rest[1:]
            if role_pick in ROLES:
                role_name, _, module = ROLES[role_pick]
                db.update_user_role(phone, role_name)
                audit.log_event(phone, session_id, 'role_select', {
                    'role': role_name
                })
                return module.handle(session_id, phone, role_rest)
            audit.log_event(phone, session_id, 'error', {
                'input': text, 'reason': 'invalid_role'
            })
            return "END Invalid choice. Dial again."

    # Direct role selection (new users, or returning users typing 3-5)
    if first in ROLES:
        role_name, _, module = ROLES[first]
        db.update_user_role(phone, role_name)
        audit.log_event(phone, session_id, 'role_select', {'role': role_name})
        return module.handle(session_id, phone, rest)

    audit.log_event(phone, session_id, 'error', {
        'input': text, 'reason': 'unknown_path'
    })
    return "END Invalid input. Please try again."


def welcome_screen(user):
    """First screen. New users without name get asked. Returning get shortcut."""
    # New user without a name — ask first
    if not user.get('name'):
        return "CON Welcome to Angelopp!\nWhat is your name?"

    if user.get('last_role'):
        display = ROLE_DISPLAY.get(user['last_role'], user['last_role'])
        return (
            f"CON Welcome back, {user['name']}!\n"
            f"Continue with {display}?\n"
            f"1. Yes\n"
            f"2. Choose different"
        )
    return role_select_screen()


def role_select_screen():
    """Show the five rooms."""
    return (
        "CON Angelopp Bumala\n"
        "What do you need?\n"
        "1. Send something\n"
        "2. I need a ride\n"
        "3. Medical transport\n"
        "4. Buy or sell crops\n"
        "5. I'm a rider"
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
