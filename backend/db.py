import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

DATABASE = Path(__file__).with_name("lost_found.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            report_type TEXT NOT NULL CHECK(report_type IN ('lost', 'found')),
            image TEXT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            claimant_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (claimant_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            recipient_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );
        CREATE TABLE IF NOT EXISTS login_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'login',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    login_columns = {row[1] for row in connection.execute("PRAGMA table_info(login_events)").fetchall()}
    if "is_read" not in login_columns:
        connection.execute("ALTER TABLE login_events ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0")
    if "event_type" not in login_columns:
        connection.execute("ALTER TABLE login_events ADD COLUMN event_type TEXT NOT NULL DEFAULT 'login'")
    notification_columns = {row[1] for row in connection.execute("PRAGMA table_info(notifications)").fetchall()}
    if "recipient_id" not in notification_columns:
        connection.execute("ALTER TABLE notifications ADD COLUMN recipient_id INTEGER")
    existing = connection.execute("SELECT id FROM users WHERE email = ?", ("admin@campus.edu",)).fetchone()
    if not existing:
        connection.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'admin')",
            ("Campus Admin", "admin@campus.edu", generate_password_hash("admin123")),
        )
    connection.commit()
    connection.close()
