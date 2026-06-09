import sqlite3
import random
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "support_tickets.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id   TEXT PRIMARY KEY,
            customer    TEXT NOT NULL,
            issue       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'unresolved',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            agent       TEXT NOT NULL,
            event       TEXT NOT NULL,
            details     TEXT
        )
    """)
    seed_data = [
        ("123456", "Priya S.",  "Net banking login failure",          "resolved",    "2025-05-01", "2025-05-03"),
        ("650932", "Arjun M.", "Debit card blocked unexpectedly",     "resolved",    "2025-05-10", "2025-05-11"),
        ("999001", "Meena R.", "UPI transfer pending for 3 days",     "in_progress", "2025-06-01", "2025-06-02"),
        ("784521", "Ravi K.",  "Home loan statement not received",    "unresolved",  "2025-06-05", "2025-06-05"),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO support_tickets
        (ticket_id, customer, issue, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, seed_data)
    conn.commit()
    conn.close()


def generate_ticket_id():
    conn = get_connection()
    cursor = conn.cursor()
    while True:
        tid = str(random.randint(100000, 999999))
        cursor.execute("SELECT 1 FROM support_tickets WHERE ticket_id = ?", (tid,))
        if not cursor.fetchone():
            conn.close()
            return tid


def insert_ticket(ticket_id: str, customer: str, issue: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute("""
        INSERT INTO support_tickets (ticket_id, customer, issue, status, created_at, updated_at)
        VALUES (?, ?, ?, 'unresolved', ?, ?)
    """, (ticket_id, customer, issue, now, now))
    conn.commit()
    conn.close()
    return {"ticket_id": ticket_id, "customer": customer, "issue": issue, "status": "unresolved", "created_at": now}


def get_ticket(ticket_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM support_tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_tickets() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM support_tickets ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_event(agent: str, event: str, details: str = ""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute(
        "INSERT INTO agent_logs (timestamp, agent, event, details) VALUES (?, ?, ?, ?)",
        (now, agent, event, details)
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
