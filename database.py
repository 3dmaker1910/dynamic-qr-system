import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "qrcodes.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                target_url TEXT NOT NULL,
                clicks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def create_qr(slug: str, target_url: str) -> dict:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO qr_codes (slug, target_url) VALUES (?, ?)",
            (slug, target_url),
        )
        row = conn.execute(
            "SELECT * FROM qr_codes WHERE slug = ?", (slug,)
        ).fetchone()
        return dict(row)


def update_qr(slug: str, target_url: str) -> dict | None:
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE qr_codes SET target_url = ?, updated_at = CURRENT_TIMESTAMP WHERE slug = ?",
            (target_url, slug),
        )
        if cursor.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT * FROM qr_codes WHERE slug = ?", (slug,)
        ).fetchone()
        return dict(row)


def get_qr(slug: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM qr_codes WHERE slug = ?", (slug,)
        ).fetchone()
        return dict(row) if row else None


def list_qrs() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM qr_codes ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def increment_clicks(slug: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE qr_codes SET clicks = clicks + 1 WHERE slug = ?", (slug,)
        )


def delete_qr(slug: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM qr_codes WHERE slug = ?", (slug,))
        return cursor.rowcount > 0
