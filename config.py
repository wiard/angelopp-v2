"""
Angelopp v2 — Configuration
All settings in one place. Nothing hidden.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server
PORT = 5003
DEBUG = os.environ.get('ANGELOPP_DEBUG', 'true').lower() == 'true'

# Database
DB_PATH = os.path.join(BASE_DIR, 'data', 'angelopp.db')

# Logging
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Africa's Talking
AT_USERNAME = os.environ.get('AT_USERNAME', 'sandbox')
AT_API_KEY = os.environ.get('AT_API_KEY', '')
AT_SENDER_ID = os.environ.get('AT_SENDER_ID', 'ANGELOPP')

# Landmarks — the organic places people know in Bumala
LANDMARKS = {
    1: 'Bumala Town Center',
    2: 'Murende College',
    3: 'Bumala Market',
    4: 'Bumala Health Center',
    5: 'Shell Petrol Station',
    6: 'Bumala Bus Park',
    7: 'St. Mary\'s Church',
    8: 'Lwanya Junction',
}

# Session timeout (seconds)
SESSION_TIMEOUT = 180  # 3 minutes, per USSD standard


# --- Landmark helpers ---

def format_landmarks():
    """Format landmarks as numbered list for USSD display."""
    lines = []
    for num, name in sorted(LANDMARKS.items()):
        lines.append(f"{num}. {name}")
    return '\n'.join(lines)


def get_landmark_name(number):
    """Get landmark name by number. Returns None if invalid."""
    try:
        return LANDMARKS.get(int(number))
    except (ValueError, TypeError):
        return None
