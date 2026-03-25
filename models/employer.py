"""
GigGreen — Employer Model
Full CRUD for employers table
"""

import sqlite3
import config


def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_by_id(employer_id: int):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM employers WHERE id = ?", (employer_id,)
        ).fetchone()
    finally:
        conn.close()


def get_by_phone(phone: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM employers WHERE phone = ?", (phone,)
        ).fetchone()
    finally:
        conn.close()


def create(phone: str, company_name: str, contact_name: str,
           location: str, company_size: str = "") -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO employers
               (phone, company_name, contact_name, location, company_size)
               VALUES (?, ?, ?, ?, ?)""",
            (phone, company_name, contact_name, location, company_size),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_profile(employer_id: int, company_name: str,
                   contact_name: str, location: str, company_size: str) -> bool:
    conn = get_db()
    try:
        conn.execute(
            """UPDATE employers
               SET company_name=?, contact_name=?, location=?, company_size=?
               WHERE id=?""",
            (company_name, contact_name, location, company_size, employer_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_active_gigs(employer_id: int) -> list:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT * FROM gigs
               WHERE employer_id = ? AND status != 'complete'
               ORDER BY created_at DESC""",
            (employer_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all() -> list:
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM employers").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
