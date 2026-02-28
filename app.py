"""
Angelopp v2 — Entry Point
This file does three things: logging, database, routes.
Nothing else.
"""
import os
import logging
from flask import Flask, request, send_from_directory
from config import PORT, DEBUG, LOG_DIR
from core.db import init_db
from core.router import handle_ussd

# --- Logging ---
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'angelopp.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('angelopp')

# --- App ---
app = Flask(__name__, static_folder='static')

# --- Database ---
init_db()
logger.info("Database initialized.")


# --- Routes ---

@app.route('/')
def index():
    """Serve the USSD simulator."""
    return send_from_directory('static', 'simulator.html')


@app.route('/ussd', methods=['POST'])
def ussd():
    """
    Africa's Talking USSD callback.
    Receives: sessionId, phoneNumber, text
    Returns: plain text starting with CON or END
    """
    session_id = request.form.get('sessionId', '')
    phone = request.form.get('phoneNumber', '')
    text = request.form.get('text', '')

    logger.info(f"USSD: session={session_id}, phone={phone}, text='{text}'")

    try:
        response = handle_ussd(session_id, phone, text)
    except Exception as e:
        logger.error(f"Error: session={session_id}, phone={phone}, error={e}", exc_info=True)
        response = "END Something went wrong. Please try again later."

    logger.info(f"Response: {response[:100]}")
    return response


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring."""
    return "OK"


# --- Start ---
if __name__ == '__main__':
    logger.info(f"Angelopp v2 starting on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
