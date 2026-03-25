"""
GigGreen — Worker Routes
GET  /worker/dashboard   → worker home
GET  /worker/profile     → view/edit profile
POST /worker/profile     → save profile changes
GET  /worker/gigs        → gig feed (personalised)
GET  /worker/earnings    → payment history
GET  /worker/api/score   → JSON: current score + level info
"""
import json
from functools import wraps
from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, jsonify, current_app
)

worker_bp = Blueprint("worker", __name__, url_prefix="/worker")


# ── Auth guard ───────────────────────────────────────────────────────────────

def worker_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("worker_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def get_db():
    return current_app.get_db()


# ── Routes ───────────────────────────────────────────────────────────────────

@worker_bp.route("/dashboard")
@worker_required
def dashboard():
    import models.worker       as worker_model
    import models.gig          as gig_model
    import models.impact_score as score_model
    from services.matching     import get_gigs_for_worker

    db        = get_db()
    worker_id = session["worker_id"]

    worker     = worker_model.get_by_id(db, worker_id)
    score_info = score_model.get_full_score_info(db, worker_id)
    active_app = gig_model.get_active_application(db, worker_id)
    all_apps   = gig_model.get_worker_applications(db, worker_id)

    # Top 3 matched gigs (not yet applied for)
    applied_ids  = gig_model.get_worker_applied_gig_ids(db, worker_id)
    matched_gigs = [
        g for g in get_gigs_for_worker(db, worker)
        if g["id"] not in applied_ids
    ][:3]

    # Recent SMS alerts
    sms_alerts = db.execute(
        "SELECT * FROM sms_log WHERE phone = ? ORDER BY sent_at DESC LIMIT 5",
        (worker["phone"],),
    ).fetchall()

    # Recent payments
    payments = db.execute(
        """
        SELECT p.*, g.title AS gig_title
        FROM payments p
        JOIN gigs g ON p.gig_id = g.id
        WHERE p.worker_id = ?
        ORDER BY p.created_at DESC LIMIT 3
        """,
        (worker_id,),
    ).fetchall()

    return render_template(
        "worker/dashboard.html",
        worker=worker,
        score_info=score_info,
        active_app=active_app,
        matched_gigs=matched_gigs,
        sms_alerts=[dict(s) for s in sms_alerts],
        payments=[dict(p) for p in payments],
        applications=all_apps,
    )


@worker_bp.route("/profile", methods=["GET", "POST"])
@worker_required
def profile():
    import models.worker as worker_model
    import models.gig    as gig_model

    db        = get_db()
    worker_id = session["worker_id"]
    worker    = worker_model.get_by_id(db, worker_id)

    if request.method == "POST":
        data  = request.get_json(silent=True) or {}
        name  = (data.get("name") or "").strip()
        loc   = (data.get("location") or "").strip()
        bio   = (data.get("bio") or "").strip()
        avail = (data.get("availability") or "full-time").strip()
        cats  = data.get("green_categories", [])

        if not name:
            return jsonify({"message": "Name is required."}), 400
        if not loc:
            return jsonify({"message": "Location is required."}), 400
        if not cats:
            return jsonify({"message": "Select at least one green job category."}), 400

        updated = worker_model.update(
            db, worker_id,
            name=name, location=loc, bio=bio,
            availability=avail, green_categories=cats,
        )
        # Refresh session name
        session["user_name"] = updated["name"]
        return jsonify({"ok": True, "message": "Profile updated!"})

    return render_template(
        "worker/profile.html",
        worker=worker,
        categories=gig_model.CATEGORIES,
    )


@worker_bp.route("/gigs")
@worker_required
def gig_feed():
    import models.worker as worker_model
    import models.gig    as gig_model
    from services.matching import get_gigs_for_worker

    db        = get_db()
    worker_id = session["worker_id"]
    worker    = worker_model.get_by_id(db, worker_id)

    # Query params for filtering
    category = request.args.get("category", "")
    location = request.args.get("location", "")
    min_pay  = request.args.get("min_pay", type=int)
    max_pay  = request.args.get("max_pay", type=int)

    if any([category, location, min_pay, max_pay]):
        gigs = gig_model.get_open_filtered(
            db, category=category or None,
            location=location or None,
            min_pay=min_pay, max_pay=max_pay
        )
        # Join company name manually
        for g in gigs:
            emp = db.execute(
                "SELECT company_name FROM employers WHERE id = ?",
                (g.get("employer_id"),)
            ).fetchone()
            g["company_name"] = emp["company_name"] if emp else "Unknown"
    else:
        gigs = get_gigs_for_worker(db, worker)

    applied_ids = gig_model.get_worker_applied_gig_ids(db, worker_id)

    # Attach applied flag
    for g in gigs:
        g["already_applied"] = g["id"] in applied_ids

    # Get all unique locations for filter dropdown
    locations = [r["location"] for r in db.execute(
        "SELECT DISTINCT location FROM gigs WHERE status='open'"
    ).fetchall()]

    return render_template(
        "worker/gig-feed.html",
        gigs=gigs,
        worker=worker,
        categories=gig_model.CATEGORIES,
        category_colors=gig_model.CATEGORY_COLORS,
        category_icons=gig_model.CATEGORY_ICONS,
        locations=locations,
        selected_category=category,
        selected_location=location,
        selected_min_pay=min_pay or "",
        selected_max_pay=max_pay or "",
    )


@worker_bp.route("/earnings")
@worker_required
def earnings():
    import models.worker as worker_model

    db        = get_db()
    worker_id = session["worker_id"]
    worker    = worker_model.get_by_id(db, worker_id)

    payments = db.execute(
        """
        SELECT p.*, g.title AS gig_title, g.category,
               e.company_name
        FROM payments p
        JOIN gigs g ON p.gig_id = g.id
        LEFT JOIN employers e ON p.employer_id = e.id
        WHERE p.worker_id = ?
        ORDER BY p.created_at DESC
        """,
        (worker_id,),
    ).fetchall()

    # Stats
    total_earned  = sum(p["amount_kes"] for p in payments if p["status"] == "released")
    total_pending = sum(p["amount_kes"] for p in payments if p["status"] == "held")
    gigs_done     = len([p for p in payments if p["status"] == "released"])

    return render_template(
        "worker/earnings.html",
        worker=worker,
        payments=[dict(p) for p in payments],
        total_earned=total_earned,
        total_pending=total_pending,
        gigs_done=gigs_done,
    )


@worker_bp.route("/api/score")
@worker_required
def api_score():
    import models.impact_score as score_model
    db        = get_db()
    worker_id = session["worker_id"]
    info      = score_model.get_full_score_info(db, worker_id)
    return jsonify(info)
