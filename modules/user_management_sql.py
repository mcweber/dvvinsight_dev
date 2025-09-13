# ---------------------------------------------------
# Version: 13.09.2025
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

from datetime import datetime
import os
import hashlib
from dotenv import load_dotenv
import sqlite3

# Define constants ----------------------------------
load_dotenv()

# SQLite database path (relative to project root)
DB_PATH = "db/user_pool.db"

# Helpers -------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with row access by column name.

    A new connection per call avoids cross-thread reuse and fixes
    "SQLite objects created in a thread ..." errors in Streamlit.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Ensure database and schema exist, and apply lightweight migrations."""
    # Make sure folder exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    with get_connection() as conn:
        cur = conn.cursor()
        # Create tables if they don't exist
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                user_password TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action_type TEXT,
                action TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # Migration: ensure users.rolle exists (used by the app)
        cur.execute('PRAGMA table_info(users)')
        cols = [row[1] if not isinstance(row, sqlite3.Row) else row["name"] for row in cur.fetchall()]
        if "rolle" not in cols:
            cur.execute('ALTER TABLE users ADD COLUMN rolle TEXT DEFAULT "user"')
            # Backfill existing rows that may have NULL in the new column
            cur.execute('UPDATE users SET rolle = COALESCE(rolle, "user")')

        conn.commit()


# Initialize database on import
init_db()

# User Hash Functions -----------------------------------------

def hash_string(string: str) -> str:
    """Generates a SHA-256 hash for the given string."""
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def add_user_hash(user_name: str, user_pw: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                '''
                INSERT INTO users (username, user_password)
                VALUES (?, ?)
                ''', (user_name, hash_string(user_pw))
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def check_user_hash(user_name: str, user_pw: str):
    with get_connection() as conn:
        cur = conn.execute(
            '''
            SELECT * FROM users
            WHERE username = ? AND user_password = ?
            ''', (user_name, hash_string(user_pw))
        )
        user = cur.fetchone()
        return user if user else ""


def update_user_hash(user_name: str, new_user_pw: str) -> bool:
    with get_connection() as conn:
        conn.execute(
            '''
            UPDATE users
            SET user_password = ?
            WHERE username = ?
            ''', (hash_string(new_user_pw), user_name)
        )
        conn.commit()
        return True


# User Functions -----------------------------------------

def add_user(user_name: str, user_pw: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                '''
                INSERT INTO users (username, user_password)
                VALUES (?, ?)
                ''', (user_name, user_pw)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def check_user(user_name: str, user_pw: str):
    with get_connection() as conn:
        cur = conn.execute(
            '''
            SELECT * FROM users
            WHERE username = ? AND user_password = ?
            ''', (user_name, user_pw)
        )
        user = cur.fetchone()
        return user if user else ""


def delete_user(user_name: str) -> bool:
    with get_connection() as conn:
        conn.execute(
            '''
            DELETE FROM users
            WHERE username = ?
            ''', (user_name,)
        )
        conn.commit()
        return True


def list_users() -> list:
    with get_connection() as conn:
        cur = conn.execute('SELECT * FROM users')
        users = cur.fetchall()
        return users


# Tracking Functions -----------------------------------------

def save_action(user_name: str, action_type: str = "", action: str = "") -> bool:
    with get_connection() as conn:
        conn.execute(
            '''
            INSERT INTO tracking (username, action_type, action)
            VALUES (?, ?, ?)
            ''', (user_name, action_type, action)
        )
        conn.commit()
        return True
