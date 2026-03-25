"""
GigGreen — Impact Score Model
Helpers for reading and updating worker impact scores and levels.
"""
from services.impact_calculator import calculate_level, LEVELS


def get_score(db, worker_id: int) -> int:
    row = db.execute(
        "SELECT impact_score FROM workers WHERE id = ?", (worker_id,)
    ).fetchone()
    return row["impact_score"] if row else 0


def add_points(db, worker_id: int, points: int) -> dict:
    """
    Add points to a worker's impact score.
    Recalculates level automatically.
    Returns updated worker score info dict.
    """
    db.execute(
        "UPDATE workers SET impact_score = impact_score + ? WHERE id = ?",
        (points, worker_id),
    )
    db.commit()
    new_score = get_score(db, worker_id)
    level_info = calculate_level(new_score)
    db.execute(
        "UPDATE workers SET level = ? WHERE id = ?",
        (level_info["level"], worker_id),
    )
    db.commit()
    return {
        "impact_score":    new_score,
        "points_added":    points,
        "level":           level_info["level"],
        "level_name":      level_info["level_name"],
        "level_emoji":     level_info["level_emoji"],
        "next_level_at":   level_info["next_level_at"],
        "points_to_next":  level_info["points_to_next"],
        "progress_pct":    level_info["progress_pct"],
    }


def get_full_score_info(db, worker_id: int) -> dict:
    """Returns full score + level info for a worker."""
    row = db.execute(
        "SELECT impact_score, level FROM workers WHERE id = ?", (worker_id,)
    ).fetchone()
    if not row:
        return {}
    score      = row["impact_score"]
    level_info = calculate_level(score)
    return {
        "impact_score":   score,
        "level":          level_info["level"],
        "level_name":     level_info["level_name"],
        "level_emoji":    level_info["level_emoji"],
        "next_level_at":  level_info["next_level_at"],
        "points_to_next": level_info["points_to_next"],
        "progress_pct":   level_info["progress_pct"],
    }


def recalculate_level(db, worker_id: int) -> dict:
    """Force-recalculate level from current score (use after data imports)."""
    score      = get_score(db, worker_id)
    level_info = calculate_level(score)
    db.execute(
        "UPDATE workers SET level = ? WHERE id = ?",
        (level_info["level"], worker_id),
    )
    db.commit()
    return level_info


def get_leaderboard(db, limit: int = 10) -> list[dict]:
    """Return top workers by impact score."""
    rows = db.execute(
        """
        SELECT id, name, location, impact_score, level
        FROM workers
        ORDER BY impact_score DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    result = []
    for i, r in enumerate(rows, 1):
        info = calculate_level(r["impact_score"])
        result.append({
            "rank":         i,
            "id":           r["id"],
            "name":         r["name"],
            "location":     r["location"],
            "impact_score": r["impact_score"],
            "level":        r["level"],
            "level_name":   info["level_name"],
            "level_emoji":  info["level_emoji"],
        })
    return result
