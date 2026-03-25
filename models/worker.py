"""
GigGreen — Worker Model
Full CRUD + level calculation
"""

import json
import sqlite3
import config

LEVELS = [
    (0,    100,  1, "🌱 Green Seed"),
    (101,  300,  2, "🌿 Green Sprout"),
    (301,  600,  3, "🌳 Green Builder"),
    (601,  1000, 4, "⚡ Green Champion"),
    (1001, float("inf"), 5, "🌍 Green Legend"),
]


def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Level helpers ─────────────────────────────────────────────────────────────

def get_level_info(score: int) -> dict:
    """Return level number, name, min, max, and points to next level."""
    for min_pts, max_pts, level_num, level_name in LEVELS:
        if min_pts <= score <= max_pts:
            next_threshold = max_pts + 1 if max_pts != float("inf") else None
            points_to_next = (next_threshold - score) if next_threshold else 0
            return {
                "level":          level_num,
                "level_name":     level_name,
                "min":            min_pts,
                "max":            max_pts,
                "points_to_next": points_to_next,
            }
    # Fallback — should never hit
    return {"level": 1, "level_name": "🌱 Green Seed", "min": 0, "max": 100, "points_to_next": 100}


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_by_phone(phone: str) -> sqlite3.Row | None:
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM workers WHERE phone = ?", (phone,)
        ).fetchone()
    finally:
        conn.close()


def get_by_id(worker_id: int) -> sqlite3.Row | None:
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()
    finally:
        conn.close()


def create(phone: str, name: str, location: str,
           green_categories: list, bio: str = "", availability: str = "full-time") -> int:
    """Insert a new worker and return their new ID."""
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO workers
               (phone, name, location, green_categories, bio, availability, impact_score, level)
               VALUES (?, ?, ?, ?, ?, ?, 0, 1)""",
            (phone, name, location, json.dumps(green_categories), bio, availability),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_profile(worker_id: int, name: str, location: str,
                   green_categories: list, bio: str, availability: str) -> bool:
    conn = get_db()
    try:
        conn.execute(
            """UPDATE workers
               SET name=?, location=?, green_categories=?, bio=?, availability=?
               WHERE id=?""",
            (name, location, json.dumps(green_categories), bio, availability, worker_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_score(worker_id: int, points_to_add: int) -> dict:
    """Add points to a worker's impact score, recalculate level, return new info."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT impact_score FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()
        if not row:
            return {}
        new_score = row["impact_score"] + points_to_add
        level_info = get_level_info(new_score)
        conn.execute(
            "UPDATE workers SET impact_score=?, level=? WHERE id=?",
            (new_score, level_info["level"], worker_id),
        )
        conn.commit()
        return {"new_score": new_score, **level_info}
    finally:
        conn.close()


def get_full_profile(worker_id: int) -> dict | None:
    """Return worker row as dict with parsed categories and level info."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["green_categories"] = json.loads(data.get("green_categories") or "[]")
        except (json.JSONDecodeError, TypeError):
            data["green_categories"] = []
        data.update(get_level_info(data["impact_score"]))
        return data
    finally:
        conn.close()


def get_all_active() -> list:
    """Return all workers (for matching engine)."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM workers").fetchall()
        workers = []
        for row in rows:
            w = dict(row)
            try:
                w["green_categories"] = json.loads(w.get("green_categories") or "[]")
            except (json.JSONDecodeError, TypeError):
                w["green_categories"] = []
            workers.append(w)
        return workers
    finally:
        conn.close()


def get_recent_sms(worker_id: int, limit: int = 5) -> list:
    """Return recent SMS log entries for a worker."""
    conn = get_db()
    try:
        worker = conn.execute(
            "SELECT phone FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()
        if not worker:
            return []
        rows = conn.execute(
            """SELECT message, direction, sent_at FROM sms_log
               WHERE phone = ?
               ORDER BY sent_at DESC LIMIT ?""",
            (worker["phone"], limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()