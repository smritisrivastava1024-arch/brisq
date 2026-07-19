import sqlite3
import json
from contextlib import contextmanager

import os

DB_NAME = os.getenv("DB_NAME", "brisq.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def check_health() -> bool:
    """Returns True if the database is readable/writable."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except sqlite3.Error:
        return False

def initialize_database():
    """
    Initializes the database schema.
    This function is completely idempotent and safe to run on every app startup.
    It uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS, ensuring
    it only adds missing structures without dropping existing data.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS abandoned_carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_token TEXT UNIQUE,
            customer_name TEXT,
            email TEXT,
            phone TEXT,
            items TEXT,
            cart_value REAL,
            checkout_url TEXT,
            ai_email TEXT,
            ai_whatsapp TEXT,
            suggested_coupon TEXT,
            approved INTEGER DEFAULT 0,
            sent INTEGER DEFAULT 0,
            recovered INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_type TEXT NOT NULL,
            reference_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            rejected_at TIMESTAMP
        )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_abandoned_carts_status ON abandoned_carts(approved, sent)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        )
        """)
        cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")

        conn.commit()


def create_abandoned_cart(
    cart_token,
    customer_name,
    email,
    phone,
    items,
    cart_value,
    checkout_url
):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO abandoned_carts (
            cart_token,
            customer_name,
            email,
            phone,
            items,
            cart_value,
            checkout_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cart_token,
            customer_name,
            email,
            phone,
            items,
            cart_value,
            checkout_url
        ))

        conn.commit()


def get_pending_abandoned_carts():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM abandoned_carts
        WHERE approved = 0
        AND sent = 0
        ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_abandoned_cart_by_token(cart_token):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM abandoned_carts
        WHERE cart_token = ?
        """, (cart_token,))

        row = cursor.fetchone()
        return dict(row) if row else None


def update_abandoned_cart_ai_messages(
    cart_token,
    ai_email,
    ai_whatsapp,
    suggested_coupon
):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE abandoned_carts
        SET ai_email = ?,
            ai_whatsapp = ?,
            suggested_coupon = ?
        WHERE cart_token = ?
        """, (
            ai_email,
            ai_whatsapp,
            suggested_coupon,
            cart_token
        ))

        conn.commit()


def approve_abandoned_cart(cart_token):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE abandoned_carts
        SET approved = 1
        WHERE cart_token = ?
        """, (cart_token,))

        conn.commit()


def reject_abandoned_cart(cart_token):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE abandoned_carts
        SET approved = 0,
            sent = 0
        WHERE cart_token = ?
        """, (cart_token,))

        conn.commit()


def mark_abandoned_cart_sent(cart_token):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE abandoned_carts
        SET sent = 1
        WHERE cart_token = ?
        """, (cart_token,))

        conn.commit()


def mark_abandoned_cart_recovered(cart_token):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE abandoned_carts
        SET recovered = 1
        WHERE cart_token = ?
        """, (cart_token,))

        conn.commit()


def create_approval(
    approval_type,
    reference_id,
    title,
    description,
    payload
):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO approvals(
            approval_type,
            reference_id,
            title,
            description,
            payload
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            approval_type,
            reference_id,
            title,
            description,
            json.dumps(payload)
        ))

        conn.commit()


def get_pending_approvals():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM approvals
        WHERE status='pending'
        ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_all_approvals():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM approvals
        ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def approve_request(approval_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE approvals
        SET
            status='approved',
            approved_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (approval_id,))

        conn.commit()


def reject_request(approval_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE approvals
        SET
            status='rejected',
            rejected_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (approval_id,))

        conn.commit()