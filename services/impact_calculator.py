"""
GigGreen — Impact Calculator Service
Points per green category + level calculation logic.
"""

IMPACT_POINTS = {
    "Solar":               50,   # ~500kg CO2 offset per system installed
    "E-Waste":             20,   # ~10kg diverted from landfill per gig
    "Urban Farming":       15,   # ~50kg local food produced
    "Carbon Scout":        25,   # 1 verified carbon dataset contributed
    "Green Construction":  35,   # Energy-efficient build component
    "Community Educator":  30,   # Direct community climate education
    "Battery Swap":        20,   # EV battery serviced / swapped
    "Climate Data":        25,   # Climate monitoring data collected
}

# (min_score, max_score, level_number, full_label)
LEVELS = [
    (0,    100,         1, "🌱 Green Seed"),
    (101,  300,         2, "🌿 Green Sprout"),
    (301,  600,         3, "🌳 Green Builder"),
    (601,  1000,        4, "⚡ Green Champion"),
    (1001, float("inf"), 5, "🌍 Green Legend"),
]

LEVEL_COLORS = {
    1: "#A8D5B5",   # light green
    2: "#2D9B5A",   # mid green
    3: "#1A6B3A",   # deep green
    4: "#F4A935",   # gold
    5: "#0F1F14",   # near black / prestige
}


def get_points_for_category(category: str) -> int:
    """Return impact points for a given green job category."""
    return IMPACT_POINTS.get(category, 10)


def calculate_level(score: int) -> dict:
    """
    Given an impact score, return full level info dict.
    """
    current_level    = LEVELS[0]
    next_level       = None

    for i, (min_s, max_s, lvl, label) in enumerate(LEVELS):
        if min_s <= score <= max_s:
            current_level = LEVELS[i]
            next_level    = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
            break

    min_s, max_s, lvl_num, label = current_level
    emoji, name = label.split(" ", 1)

    if next_level:
        next_min, _, _, next_label = next_level
        next_emoji, next_name = next_label.split(" ", 1)
        points_to_next = max(0, next_min - score)
        # Progress within current band
        band_size    = next_min - min_s
        band_earned  = score - min_s
        progress_pct = min(100, int((band_earned / band_size) * 100)) if band_size else 100
        next_level_at = next_min
        next_level_name = next_label
    else:
        # Max level
        points_to_next  = 0
        progress_pct    = 100
        next_level_at   = score
        next_level_name = label
        next_emoji      = emoji
        next_name       = name

    return {
        "level":           lvl_num,
        "level_name":      label,        # full e.g. "🌱 Green Seed"
        "level_emoji":     emoji,
        "level_short":     name,
        "level_color":     LEVEL_COLORS.get(lvl_num, "#2D9B5A"),
        "next_level_at":   next_level_at,
        "next_level_name": next_level_name,
        "points_to_next":  points_to_next,
        "progress_pct":    progress_pct,
    }


def co2_offset_kg(category: str, gigs_completed: int = 1) -> int:
    """Estimated CO2 offset in kg for display on ESG dashboard."""
    offsets = {
        "Solar":              500,
        "E-Waste":             10,
        "Urban Farming":        5,
        "Carbon Scout":        15,
        "Green Construction":  40,
        "Community Educator":   8,
        "Battery Swap":        12,
        "Climate Data":         5,
    }
    return offsets.get(category, 5) * gigs_completed


def summarise_worker_impact(db, worker_id: int) -> dict:
    """
    Read completed gigs for a worker and compute impact summary.
    Returns dict with total_co2, gigs_by_category, total_points.
    """
    rows = db.execute(
        """
        SELECT g.category, COUNT(*) AS cnt
        FROM applications a
        JOIN gigs g ON a.gig_id = g.id
        WHERE a.worker_id = ? AND a.status = 'complete'
        GROUP BY g.category
        """,
        (worker_id,),
    ).fetchall()

    total_co2    = 0
    total_points = 0
    by_category  = {}

    for r in rows:
        cat   = r["category"]
        count = r["cnt"]
        pts   = get_points_for_category(cat) * count
        co2   = co2_offset_kg(cat, count)
        total_co2    += co2
        total_points += pts
        by_category[cat] = {"gigs": count, "points": pts, "co2_kg": co2}

    return {
        "total_co2_kg":   total_co2,
        "total_points":   total_points,
        "by_category":    by_category,
        "gigs_completed": sum(r["cnt"] for r in rows),
    }


def summarise_employer_impact(db, employer_id: int) -> dict:
    """
    Compute ESG impact summary for an employer's completed gigs.
    """
    rows = db.execute(
        """
        SELECT g.category, COUNT(DISTINCT a.worker_id) AS workers,
               COUNT(*) AS gigs
        FROM gigs g
        JOIN applications a ON g.id = a.gig_id
        WHERE g.employer_id = ? AND a.status = 'complete'
        GROUP BY g.category
        """,
        (employer_id,),
    ).fetchall()

    total_co2    = 0
    total_workers = 0
    by_category  = {}

    for r in rows:
        cat     = r["category"]
        workers = r["workers"]
        gigs    = r["gigs"]
        co2     = co2_offset_kg(cat, gigs)
        total_co2     += co2
        total_workers += workers
        by_category[cat] = {
            "gigs":     gigs,
            "workers":  workers,
            "co2_kg":   co2,
        }

    return {
        "total_co2_kg":    total_co2,
        "total_workers":   total_workers,
        "by_category":     by_category,
        "categories_used": list(by_category.keys()),
    }
