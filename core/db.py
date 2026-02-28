"""
Angelopp v2 — Database (The Kernel)
Rule 7: The kernel does not speak. No persona, no tone.
Rule 8: Everything is recorded. No deletion. No mutation on audit.
"""
import sqlite3
import os
from config import DB_PATH


def get_connection():
    """Return a database connection. Caller must close it."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                name TEXT,
                last_role TEXT,
                last_seen DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                session_id TEXT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                role TEXT NOT NULL,
                pickup TEXT,
                destination TEXT,
                order_type TEXT DEFAULT 'delivery',
                description TEXT,
                urgent INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                crop_name TEXT NOT NULL,
                quantity TEXT,
                price TEXT,
                status TEXT DEFAULT 'available',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
            CREATE INDEX IF NOT EXISTS idx_audit_phone ON audit_log(phone);
            CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone);
            CREATE INDEX IF NOT EXISTS idx_crops_phone ON crops(phone);
        """)
        # Migrate existing databases: add new columns safely
        for col, definition in [
            ('order_type', "TEXT DEFAULT 'delivery'"),
            ('description', 'TEXT'),
            ('urgent', 'INTEGER DEFAULT 0'),
        ]:
            try:
                conn.execute(
                    f"ALTER TABLE orders ADD COLUMN {col} {definition}"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()
    finally:
        conn.close()


# --- User operations ---

def get_user(phone):
    """Get user by phone. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE phone = ?", (phone,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_user(phone, name=None):
    """Create a new user. Returns user dict."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (phone, name) VALUES (?, ?)",
            (phone, name)
        )
        conn.commit()
        return get_user(phone)
    finally:
        conn.close()


def update_user_role(phone, role):
    """Remember the user's last chosen role."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET last_role = ?, last_seen = CURRENT_TIMESTAMP "
            "WHERE phone = ?",
            (role, phone)
        )
        conn.commit()
    finally:
        conn.close()


# --- Order operations ---

def create_order(phone, role, pickup, destination,
                 order_type='delivery', description=None, urgent=0):
    """Place a new order. Returns order id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO orders (phone, role, pickup, destination, "
            "order_type, description, urgent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (phone, role, pickup, destination, order_type, description, urgent)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_pending_order_count():
    """Count pending orders for riders."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as count FROM orders WHERE status = 'pending'"
        ).fetchone()
        return row['count'] if row else 0
    finally:
        conn.close()


# --- Crop operations ---

def create_crop(phone, crop_name, quantity, price):
    """List a crop for sale. Returns crop id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO crops (phone, crop_name, quantity, price) "
            "VALUES (?, ?, ?, ?)",
            (phone, crop_name, quantity, price)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_available_crops():
    """Get all available crops for buyers."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM crops WHERE status = 'available' "
            "ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
