"""
database.py -- MySQL persistence layer for the Ticket Generating System.

Defines the Database class, which encapsulates the connection to MySQL
and every data-access operation on the three tables managed by the
application: users, events and tickets.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Tuple, Any

import mysql.connector
import hashlib
import secrets

# Default connection parameters. Can be overridden by passing a custom
# 'config' dict to Database(config=...) instead of editing this constant.
DB_CONFIG: Dict[str, Any] = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "wanjiru",
    "database": "ticket_system",
}


class Database:
    """Encapsulates all MySQL access for the ticket system.

    Every public method opens its own short-lived connection, performs
    one operation, commits if needed, and closes the connection again.
    This keeps each method self-contained and avoids holding a MySQL
    connection open for the whole lifetime of the GUI application.

    Attributes:
        config: dict of connection parameters passed to
            mysql.connector.connect() (host, port, user, password,
            database).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the Database wrapper.

        Args:
            config: optional dict overriding the default DB_CONFIG
                connection parameters. If omitted, DB_CONFIG is used.
        """
        self.config: Dict[str, Any] = config if config is not None else DB_CONFIG

    # ── Connection ──────────────────────────────────────────────

    def _connect(self) -> mysql.connector.MySQLConnection:
        """Open and return a new MySQL connection.

        Creates the target database on the server if it does not
        already exist, then connects to it with autocommit disabled
        (callers are responsible for calling conn.commit() after any
        write operation).

        Returns:
            An open mysql.connector connection to self.config['database'].
        """
        cfg_no_db = {k: v for k, v in self.config.items() if k != "database"}
        tmp = mysql.connector.connect(**cfg_no_db)
        cur = tmp.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{self.config['database']}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        tmp.commit()
        cur.close()
        tmp.close()

        conn = mysql.connector.connect(**self.config)
        conn.autocommit = False
        return conn

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password with a random or given salt.

        Args:
            password: the plain-text password to hash.
            salt: an existing hex salt to reuse (e.g. when verifying a
                login). If None, a new random salt is generated.

        Returns:
            A (hashed, salt) tuple, where hashed is the SHA-256 hex
            digest of (salt + password) and salt is the hex string used.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return hashed, salt

    @staticmethod
    def _fetchone_dict(cursor: mysql.connector.cursor.MySQLCursor) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a cursor as a dict keyed by column name.

        Args:
            cursor: a MySQL cursor that has just executed a SELECT.

        Returns:
            A dict mapping column name to value, or None if there was
            no row to fetch.
        """
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        return dict(zip(cols, row)) if row else None

    @staticmethod
    def _fetchall_dict(cursor: mysql.connector.cursor.MySQLCursor) -> List[Dict[str, Any]]:
        """Fetch all rows from a cursor as a list of dicts.

        Args:
            cursor: a MySQL cursor that has just executed a SELECT.

        Returns:
            A list of dicts, one per row, each mapping column name to
            value. Empty list if there were no rows.
        """
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    # ── Schema bootstrap ────────────────────────────────────────

    def init_db(self) -> None:
        """Create the users/events/tickets tables if they don't exist yet.

        Also creates a default administrator account (username "admin",
        password "admin123") the first time the database is initialized,
        i.e. only if the users table is currently empty.
        """
        conn = self._connect()
        cur = conn.cursor()

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

        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            hashed, salt = self.hash_password("admin123")
            cur.execute(
                "INSERT INTO users (username, password, salt, role) VALUES (%s,%s,%s,%s)",
                ("admin", hashed, salt, "admin")
            )

        conn.commit()
        cur.close()
        conn.close()

    # ── User / Auth ─────────────────────────────────────────────

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Check a username/password pair against the users table.

        Args:
            username: the username to look up.
            password: the plain-text password to verify.

        Returns:
            The matching user row as a dict if the credentials are
            correct, otherwise None.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = self._fetchone_dict(cur)
        cur.close()
        conn.close()
        if not row:
            return None
        hashed, _ = self.hash_password(password, row["salt"])
        return row if hashed == row["password"] else None

    def change_password(self, username: str, new_password: str) -> None:
        """Set a new password (with a freshly generated salt) for a user.

        Args:
            username: the account to update.
            new_password: the new plain-text password.
        """
        hashed, salt = self.hash_password(new_password)
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=%s, salt=%s WHERE username=%s",
            (hashed, salt, username)
        )
        conn.commit()
        cur.close()
        conn.close()

    def add_user(self, username: str, password: str, role: str = "admin") -> bool:
        """Create a new user account.

        Args:
            username: desired username (must be unique).
            password: plain-text password to hash and store.
            role: role label to assign (default "admin").

        Returns:
            True if the account was created, False if the username was
            already taken (UNIQUE constraint violation).
        """
        hashed, salt = self.hash_password(password)
        conn = self._connect()
        cur = conn.cursor()
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

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Return every user account (without password/salt columns).

        Returns:
            A list of dicts, each with id, username, role, created_at.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, created_at FROM users")
        rows = self._fetchall_dict(cur)
        cur.close()
        conn.close()
        return rows

    # ── Events ──────────────────────────────────────────────────

    def add_event(self, title: str, event_date: str, event_time: str,
                  location: str, capacity: int) -> int:
        """Insert a new event.

        Args:
            title: event name.
            event_date: date string in "YYYY-MM-DD" format.
            event_time: time string in "HH:MM" format.
            location: venue name/address.
            capacity: maximum number of tickets that can be issued.

        Returns:
            The auto-generated id of the newly created event.
        """
        conn = self._connect()
        cur = conn.cursor()
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

    def get_events(self) -> List[Dict[str, Any]]:
        """Return every event, ordered by date.

        Returns:
            A list of event dicts.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events ORDER BY event_date")
        rows = self._fetchall_dict(cur)
        cur.close()
        conn.close()
        return rows

    def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Look up a single event by id.

        Args:
            event_id: the event's database id.

        Returns:
            The event as a dict, or None if no such event exists.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE id=%s", (event_id,))
        row = self._fetchone_dict(cur)
        cur.close()
        conn.close()
        return row

    def delete_event(self, event_id: int) -> None:
        """Delete an event and (via ON DELETE CASCADE) all its tickets.

        Args:
            event_id: the event's database id.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM events WHERE id=%s", (event_id,))
        conn.commit()
        cur.close()
        conn.close()

    def tickets_sold(self, event_id: int) -> int:
        """Count how many active (non-cancelled) tickets exist for an event.

        Args:
            event_id: the event's database id.

        Returns:
            The number of active tickets issued for that event.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM tickets WHERE event_id=%s AND status='active'",
            (event_id,)
        )
        n = cur.fetchone()[0]
        cur.close()
        conn.close()
        return n

    # ── Tickets ─────────────────────────────────────────────────

    def issue_ticket(self, event_id: int, buyer_name: str,
                      buyer_email: str) -> Tuple[Optional[int], str]:
        """Issue a new ticket for an event, if capacity allows.

        Args:
            event_id: the event to issue a ticket for.
            buyer_name: full name of the attendee.
            buyer_email: email address of the attendee.

        Returns:
            A (ticket_id, qr_token) tuple on success, or
            (None, error_message) if the event does not exist or is
            fully booked.
        """
        event = self.get_event(event_id)
        if not event:
            return None, "Event not found"
        if self.tickets_sold(event_id) >= event["capacity"]:
            return None, "Event is fully booked"

        qr_token = secrets.token_urlsafe(24)
        conn = self._connect()
        cur = conn.cursor()
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

    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Look up a single ticket, joined with its event's details.

        Args:
            ticket_id: the ticket's database id.

        Returns:
            A dict with the ticket's own columns plus title, event_date,
            event_time and location from the related event, or None if
            no such ticket exists.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, e.title, e.event_date, e.event_time, e.location
            FROM tickets t JOIN events e ON t.event_id = e.id
            WHERE t.id = %s
        """, (ticket_id,))
        row = self._fetchone_dict(cur)
        cur.close()
        conn.close()
        return row

    def get_all_tickets(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return every ticket, optionally filtered by a search string.

        Args:
            search: if given, only tickets whose buyer name, buyer
                email, or numeric id contain this substring (case
                insensitive) are returned. If None, all tickets are
                returned.

        Returns:
            A list of ticket dicts (each joined with its event's
            details), most recently issued first.
        """
        conn = self._connect()
        cur = conn.cursor()
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
        rows = self._fetchall_dict(cur)
        cur.close()
        conn.close()
        return rows

    def cancel_ticket(self, ticket_id: int) -> None:
        """Mark a ticket as cancelled (soft delete, kept for records).

        Args:
            ticket_id: the ticket's database id.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE tickets SET status='cancelled' WHERE id=%s", (ticket_id,))
        conn.commit()
        cur.close()
        conn.close()

    def reactivate_ticket(self, ticket_id: int) -> None:
        """Mark a previously cancelled ticket as active again.

        Args:
            ticket_id: the ticket's database id.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE tickets SET status='active' WHERE id=%s", (ticket_id,))
        conn.commit()
        cur.close()
        conn.close()