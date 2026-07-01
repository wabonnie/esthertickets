"""
database.py  –  MySQL layer for the Ticket Generating System
Tables: users, events, tickets
"""

import mysql.connector
import hashlib
import secrets

# ──────────────────────────────────────────────
# Connection config  
# ──────────────────────────────────────────────

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",           # your MySQL username
    "password": "wanjiru",   # your MySQL password
    "database": "ticket_system",
}


def _connect():
    """Open and return a MySQL connection (auto-creates the DB if missing)."""
    cfg_no_db = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    tmp = mysql.connector.connect(**cfg_no_db)
    cur = tmp.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    tmp.commit()
    cur.close()
    tmp.close()

    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def hash_password(password: str, salt: str = None):
    """Return (hashed, salt). Generates a random salt if none is given."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def _fetchone_dict(cursor):
    cols = [d[0] for d in cursor.description]
    row  = cursor.fetchone()
    return dict(zip(cols, row)) if row else None


def _fetchall_dict(cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


# ──────────────────────────────────────────────
# Schema bootstrap
# ──────────────────────────────────────────────

def init_db():
    conn = _connect()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            username    VARCHAR(80) UNIQUE NOT NULL,
            password    VARCHAR(64) NOT NULL,
            salt        VARCHAR(32) NOT NULL,
            role        VARCHAR(20) NOT NULL DEFAULT 'admin',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(200) NOT NULL,
            event_date  DATE NOT NULL,
            event_time  TIME NOT NULL,
            location    VARCHAR(200) NOT NULL,
            capacity    INT NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            event_id      INT NOT NULL,
            buyer_name    VARCHAR(200) NOT NULL,
            buyer_email   VARCHAR(200) NOT NULL,
            issued_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            status        VARCHAR(20) NOT NULL DEFAULT 'active',
            qr_token      VARCHAR(64) UNIQUE NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)

    # Create a default admin account if no users exist yet
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        hashed, salt = hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password, salt, role) VALUES (%s,%s,%s,%s)",
            ("admin", hashed, salt, "admin")
        )

    conn.commit()
    cur.close()
    conn.close()


# ──────────────────────────────────────────────
# User / Auth
# ──────────────────────────────────────────────

def verify_user(username: str, password: str):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = _fetchone_dict(cur)
    cur.close()
    conn.close()
    if not row:
        return None
    hashed, _ = hash_password(password, row["salt"])
    return row if hashed == row["password"] else None


def change_password(username: str, new_password: str):
    hashed, salt = hash_password(new_password)
    conn = _connect()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE users SET password=%s, salt=%s WHERE username=%s",
        (hashed, salt, username)
    )
    conn.commit()
    cur.close()
    conn.close()


def add_user(username: str, password: str, role: str = "admin"):
    hashed, salt = hash_password(password)
    conn = _connect()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, salt, role) VALUES (%s,%s,%s,%s)",
            (username, hashed, salt, role)
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()


def get_all_users():
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("SELECT id, username, role, created_at FROM users")
    rows = _fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows


# ──────────────────────────────────────────────
# Events
# ──────────────────────────────────────────────

def add_event(title, event_date, event_time, location, capacity):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO events (title, event_date, event_time, location, capacity) "
        "VALUES (%s,%s,%s,%s,%s)",
        (title, event_date, event_time, location, capacity)
    )
    conn.commit()
    eid = cur.lastrowid
    cur.close()
    conn.close()
    return eid


def get_events():
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY event_date")
    rows = _fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows


def get_event(event_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    row = _fetchone_dict(cur)
    cur.close()
    conn.close()
    return row


def delete_event(event_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("DELETE FROM events WHERE id=%s", (event_id,))
    conn.commit()
    cur.close()
    conn.close()


def tickets_sold(event_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM tickets WHERE event_id=%s AND status='active'",
        (event_id,)
    )
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ──────────────────────────────────────────────
# Tickets
# ──────────────────────────────────────────────

def issue_ticket(event_id, buyer_name, buyer_email):
    event = get_event(event_id)
    if not event:
        return None, "Event not found"
    if tickets_sold(event_id) >= event["capacity"]:
        return None, "Event is fully booked"

    qr_token = secrets.token_urlsafe(24)
    conn = _connect()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (event_id, buyer_name, buyer_email, qr_token) "
        "VALUES (%s,%s,%s,%s)",
        (event_id, buyer_name, buyer_email, qr_token)
    )
    conn.commit()
    tid = cur.lastrowid
    cur.close()
    conn.close()
    return tid, qr_token


def get_ticket(ticket_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("""
        SELECT t.*, e.title, e.event_date, e.event_time, e.location
        FROM tickets t JOIN events e ON t.event_id = e.id
        WHERE t.id = %s
    """, (ticket_id,))
    row = _fetchone_dict(cur)
    cur.close()
    conn.close()
    return row


def get_all_tickets(search=None):
    conn = _connect()
    cur  = conn.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("""
            SELECT t.*, e.title, e.event_date, e.event_time, e.location
            FROM tickets t JOIN events e ON t.event_id = e.id
            WHERE t.buyer_name LIKE %s OR t.buyer_email LIKE %s
               OR CAST(t.id AS CHAR) LIKE %s
            ORDER BY t.issued_at DESC
        """, (like, like, like))
    else:
        cur.execute("""
            SELECT t.*, e.title, e.event_date, e.event_time, e.location
            FROM tickets t JOIN events e ON t.event_id = e.id
            ORDER BY t.issued_at DESC
        """)
    rows = _fetchall_dict(cur)
    cur.close()
    conn.close()
    return rows


def cancel_ticket(ticket_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("UPDATE tickets SET status='cancelled' WHERE id=%s", (ticket_id,))
    conn.commit()
    cur.close()
    conn.close()


def reactivate_ticket(ticket_id):
    conn = _connect()
    cur  = conn.cursor()
    cur.execute("UPDATE tickets SET status='active' WHERE id=%s", (ticket_id,))
    conn.commit()
    cur.close()
    conn.close()