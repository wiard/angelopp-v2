"""
Angelopp v2 — Audit Log
Rule 8: Everything is recorded. Append-only. No deletion. No mutation.
What happened, happened.
"""
import json
from core.db import get_connection


def log_event(phone, session_id, event_type, event_data=None):
    """
    Record an event. This is the only write function.
    There is no delete. There is no update. By design.
    
    Event types:
        session_start, session_end, session_timeout
        role_select, menu_select
        order_placed, order_cancelled
        crop_listed, crop_purchased
        sms_sent
        error
    """
    data_str = json.dumps(event_data) if event_data else None
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_log (phone, session_id, event_type, event_data) "
            "VALUES (?, ?, ?, ?)",
            (phone, session_id, event_type, data_str)
        )
        conn.commit()
    finally:
        conn.close()


def get_events(phone=None, event_type=None, limit=50):
    """Read events. For analysis only. Never for modifying state."""
    conn = get_connection()
    try:
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if phone:
            query += " AND phone = ?"
            params.append(phone)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
