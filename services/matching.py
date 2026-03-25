"""
GigGreen — Matching Service
Matches workers to gigs by category + location, scores each match,
and triggers bulk SMS to the top 5.
"""
import json
from services.impact_calculator import calculate_level


def match_workers_to_gig(db, gig: dict, notify: bool = True) -> list[dict]:
    """
    Main matching function.
    1. Filter workers whose green_categories include gig.category
    2. Score each match
    3. Return sorted top 10
    4. Trigger SMS to top 5 if notify=True

    Returns list of match dicts (worker info + match_score).
    """
    category = gig["category"]
    location = gig.get("location", "")

    # Pull all workers
    workers = db.execute(
        "SELECT * FROM workers WHERE green_categories IS NOT NULL"
    ).fetchall()

    scored = []
    for w in workers:
        worker = dict(w)
        cats   = _parse_categories(worker.get("green_categories", "[]"))

        if category not in cats:
            continue   # must have the right category

        score = _score_match(worker, gig, cats, category, location)
        scored.append({**worker, "match_score": score})

    # Sort descending by match score
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top_10 = scored[:10]

    # Notify top 5
    if notify and top_10:
        _notify_top_workers(db, top_10[:5], gig)

    return top_10


def _score_match(worker: dict, gig: dict, worker_cats: list,
                 category: str, gig_location: str) -> int:
    score = 0

    # Location match
    if worker.get("location", "").lower() == gig_location.lower():
        score += 30
    elif gig_location.lower() in (worker.get("location") or "").lower():
        score += 15   # partial match e.g. "Nairobi CBD" ↔ "Nairobi"

    # Category match (primary = first listed)
    if worker_cats and worker_cats[0] == category:
        score += 20   # primary category — strongest signal
    elif category in worker_cats:
        score += 12   # secondary category

    # Impact score bonus
    impact = worker.get("impact_score", 0)
    score += (impact // 100) * 10   # +10 per 100 impact points

    # Level bonus
    level = worker.get("level", 1)
    if level >= 2:
        score += 15
    if level >= 3:
        score += 10
    if level >= 4:
        score += 10

    return score


def _parse_categories(raw: str) -> list:
    try:
        cats = json.loads(raw)
        return cats if isinstance(cats, list) else []
    except Exception:
        return []


def _notify_top_workers(db, workers: list, gig: dict):
    """Send SMS alerts to the top matched workers."""
    try:
        from services.at_sms import send_gig_alert
        phones = [w["phone"] for w in workers if w.get("phone")]
        if phones:
            send_gig_alert(db, phones, gig)
    except Exception as e:
        print(f"[MATCHING] SMS notify error: {e}")


def get_matches_for_gig(db, gig_id: int) -> list[dict]:
    """
    Re-run matching for an existing gig by ID.
    Useful for employer matches page.
    """
    from models.gig import get_by_id
    gig = get_by_id(db, gig_id)
    if not gig:
        return []
    return match_workers_to_gig(db, gig, notify=False)


def get_gigs_for_worker(db, worker: dict) -> list[dict]:
    """
    Return open gigs that match a specific worker's categories and location.
    Used for the worker gig feed personalisation.
    """
    cats = _parse_categories(worker.get("green_categories", "[]"))
    if not cats:
        # No categories set — return all open gigs
        from models.gig import get_all_open_with_employer
        return get_all_open_with_employer(db)

    placeholders = ",".join("?" for _ in cats)
    rows = db.execute(
        f"""
        SELECT g.*, e.company_name
        FROM gigs g
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE g.status = 'open'
          AND g.category IN ({placeholders})
        ORDER BY g.created_at DESC
        """,
        cats,
    ).fetchall()

    # Also get non-matching gigs for discovery (appended at end)
    matched_ids = {r["id"] for r in rows}
    all_rows = db.execute(
        """
        SELECT g.*, e.company_name
        FROM gigs g
        LEFT JOIN employers e ON g.employer_id = e.id
        WHERE g.status = 'open'
        ORDER BY g.created_at DESC
        """
    ).fetchall()

    result   = [dict(r) for r in rows]
    discover = [dict(r) for r in all_rows if r["id"] not in matched_ids]
    return result + discover
