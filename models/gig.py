"""
GigGreen — Gig Model
All database read/write operations for gigs and applications tables.
"""
import json
from datetime import datetime


# ── Gig CRUD ────────────────────────────────────────────────────────────────

def get_by_id(db, gig_id: int) -> dict | None:
    row = db.execute("SELECT * FROM gigs WHERE id = ?", (gig_id,)).fetchone()
    return _row_to_dict(row) if row else None


def get_all_open(db) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM gigs WHERE status = 'open' ORDER BY created_at DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_open_by_category(db, category: str) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM gigs WHERE status = 'open' AND category = ? ORDER BY created_at DESC",
        (category,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_open_by_location(db, location: str) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM gigs WHERE status = 'open' AND location = ? ORDER BY created_at DESC",
        (location,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_open_filtered(db, category: str = None, location: str = None,
                      min_pay: int = None, max_pay: int = None) -> list[dict]:
    query  = "SELECT * FROM gigs WHERE status = 'open'"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if location:
        query += " AND location = ?"
        params.append(location)
    if min_pay is not None:
        query += " AND pay_kes >= ?"
        params.append(min_pay)
    if max_pay is not None:
        query += " AND pay_kes <= ?"
        params.append(max_pay)
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_employer(db, employer_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT * FROM gigs WHERE employer_id = ? ORDER BY created_at DESC",
        (employer_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def create(db, employer_id: int, title: str, category: str, location: str,
           pay_kes: int, description: str = "", impact_points: int = None,
           skills_needed: str = "", duration: str = "",
           workers_needed: int = 1) -> dict:
    from services.impact_calculator import get_points_for_category
    if impact_points is None:
        impact_points = get_points_for_category(category)
    db.execute(
        """
        INSERT INTO gigs
          (employer_id, title, category, location, pay_kes, description,
           impact_points, skills_needed, duration, workers_needed, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """,
        (employer_id, title, category, location, pay_kes, description,
         impact_points, skills_needed, duration, workers_needed),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM gigs WHERE employer_id = ? ORDER BY id DESC LIMIT 1",
        (employer_id,),
    ).fetchone()
    return _row_to_dict(row)


def update_status(db, gig_id: int, status: str) -> bool:
    db.execute("UPDATE gigs SET status = ? WHERE id = ?", (status, gig_id))
    db.commit()
    return True


def get_with_employer(db, gig_id: int) -> dict | None:
    """Return gig dict merged with employer company_name."""
    row = db.execute(
        """
        SELECT g.*, e.company_name, e.contact_name, e.phone AS employer_phone
        FROM gigs g
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE g.id = ?
        """,
        (gig_id,),
    ).fetchone()
    return dict(row) if row else None


def get_all_open_with_employer(db) -> list[dict]:
    rows = db.execute(
        """
        SELECT g.*, e.company_name
        FROM gigs g
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE g.status = 'open'
        ORDER BY g.created_at DESC
        """,
    ).fetchall()
    return [dict(r) for r in rows]


# ── Application CRUD ─────────────────────────────────────────────────────────

def get_application(db, worker_id: int, gig_id: int) -> dict | None:
    row = db.execute(
        "SELECT * FROM applications WHERE worker_id = ? AND gig_id = ?",
        (worker_id, gig_id),
    ).fetchone()
    return dict(row) if row else None


def apply(db, worker_id: int, gig_id: int) -> dict | None:
    """Create application. Returns None if already applied."""
    existing = get_application(db, worker_id, gig_id)
    if existing:
        return None
    db.execute(
        "INSERT INTO applications (worker_id, gig_id, status) VALUES (?, ?, 'applied')",
        (worker_id, gig_id),
    )
    db.commit()
    return get_application(db, worker_id, gig_id)


def get_worker_applications(db, worker_id: int) -> list[dict]:
    """Returns applications with gig details joined."""
    rows = db.execute(
        """
        SELECT a.*, g.title, g.category, g.location, g.pay_kes,
               g.impact_points, g.status AS gig_status, e.company_name
        FROM applications a
        JOIN gigs g ON a.gig_id = g.id
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE a.worker_id = ?
        ORDER BY a.applied_at DESC
        """,
        (worker_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_active_application(db, worker_id: int) -> dict | None:
    """Returns the worker's most recent confirmed/in-progress application."""
    row = db.execute(
        """
        SELECT a.*, g.title, g.category, g.location, g.pay_kes,
               g.impact_points, e.company_name
        FROM applications a
        JOIN gigs g ON a.gig_id = g.id
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE a.worker_id = ?
          AND a.status IN ('matched', 'confirmed')
        ORDER BY a.applied_at DESC LIMIT 1
        """,
        (worker_id,),
    ).fetchone()
    return dict(row) if row else None


def get_gig_applicants(db, gig_id: int) -> list[dict]:
    """Returns all workers who applied for a gig, with worker details."""
    rows = db.execute(
        """
        SELECT a.*, w.name, w.phone, w.location AS worker_location,
               w.impact_score, w.level, w.green_categories
        FROM applications a
        JOIN workers w ON a.worker_id = w.id
        WHERE a.gig_id = ?
        ORDER BY a.applied_at ASC
        """,
        (gig_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_application_status(db, worker_id: int, gig_id: int, status: str) -> bool:
    db.execute(
        "UPDATE applications SET status = ? WHERE worker_id = ? AND gig_id = ?",
        (status, worker_id, gig_id),
    )
    db.commit()
    return True


def complete_gig(db, worker_id: int, gig_id: int) -> bool:
    """Mark application complete and update gig status."""
    update_application_status(db, worker_id, gig_id, "complete")
    update_status(db, gig_id, "complete")
    return True


def get_worker_applied_gig_ids(db, worker_id: int) -> set:
    """Returns a set of gig IDs the worker has already applied for."""
    rows = db.execute(
        "SELECT gig_id FROM applications WHERE worker_id = ?", (worker_id,)
    ).fetchall()
    return {r["gig_id"] for r in rows}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    if row is None:
        return None
    d = dict(row)
    return d


CATEGORIES = [
    "Solar",
    "E-Waste",
    "Urban Farming",
    "Carbon Scout",
    "Green Construction",
    "Community Educator",
    "Battery Swap",
    "Climate Data",
]

CATEGORY_COLORS = {
    "Solar":               "#F4A935",
    "E-Waste":             "#2D9B5A",
    "Urban Farming":       "#1A6B3A",
    "Carbon Scout":        "#4A90A4",
    "Green Construction":  "#8B5E3C",
    "Community Educator":  "#9B59B6",
    "Battery Swap":        "#E07B39",
    "Climate Data":        "#27AE60",
}

CATEGORY_ICONS = {
    "Solar":               "☀️",
    "E-Waste":             "♻️",
    "Urban Farming":       "🌱",
    "Carbon Scout":        "🌿",
    "Green Construction":  "🏗️",
    "Community Educator":  "📚",
    "Battery Swap":        "⚡",
    "Climate Data":        "📊",
}
