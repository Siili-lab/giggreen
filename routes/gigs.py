"""
GigGreen — Gigs Routes
GET  /gigs/             → all open gigs (JSON)
GET  /gigs/<id>         → single gig detail (JSON)
POST /gigs/<id>/apply   → worker applies for a gig
POST /gigs/<id>/complete → mark gig complete (employer confirms)
POST /gigs/create       → employer creates a gig
"""
from functools import wraps
from flask import (
    Blueprint, request, jsonify, session,
    current_app, redirect, url_for
)

gigs_bp = Blueprint("gigs", __name__, url_prefix="/gigs")


def get_db():
    return current_app.get_db()


def worker_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("worker_id"):
            return jsonify({"message": "Login required."}), 401
        return f(*args, **kwargs)
    return decorated


def employer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("employer_id"):
            return jsonify({"message": "Employer login required."}), 401
        return f(*args, **kwargs)
    return decorated


# ── Routes ───────────────────────────────────────────────────────────────────

@gigs_bp.route("/")
def list_gigs():
    import models.gig as gig_model
    db   = get_db()
    gigs = gig_model.get_all_open_with_employer(db)
    return jsonify(gigs)


@gigs_bp.route("/<int:gig_id>")
def get_gig(gig_id):
    import models.gig as gig_model
    db  = get_db()
    gig = gig_model.get_with_employer(db, gig_id)
    if not gig:
        return jsonify({"message": "Gig not found."}), 404
    return jsonify(gig)


@gigs_bp.route("/<int:gig_id>/apply", methods=["POST"])
@worker_required
def apply(gig_id):
    import models.gig    as gig_model
    import models.worker as worker_model

    db        = get_db()
    worker_id = session["worker_id"]
    worker    = worker_model.get_by_id(db, worker_id)
    gig       = gig_model.get_with_employer(db, gig_id)

    if not gig:
        return jsonify({"message": "Gig not found."}), 404
    if gig["status"] != "open":
        return jsonify({"message": "This gig is no longer accepting applications."}), 400

    application = gig_model.apply(db, worker_id, gig_id)
    if not application:
        return jsonify({"message": "You have already applied for this gig."}), 409

    # Notify employer via SMS
    try:
        from services.at_sms import send_application_alert
        employer = db.execute(
            "SELECT phone FROM employers WHERE id = ?", (gig["employer_id"],)
        ).fetchone()
        if employer:
            send_application_alert(db, employer["phone"], worker, gig)
    except Exception as e:
        print(f"[GIGS] Employer SMS error: {e}")

    return jsonify({
        "ok":      True,
        "message": f"Applied! The employer will contact you by SMS to {worker['phone']}.",
    })


@gigs_bp.route("/<int:gig_id>/complete", methods=["POST"])
def complete(gig_id):
    import models.gig          as gig_model
    import models.impact_score as score_model

    db = get_db()

    # Either employer or worker can mark complete
    worker_id   = session.get("worker_id")
    employer_id = session.get("employer_id")

    if not worker_id and not employer_id:
        return jsonify({"message": "Login required."}), 401

    data      = request.get_json(silent=True) or {}
    target_worker_id = data.get("worker_id") or worker_id

    if not target_worker_id:
        return jsonify({"message": "worker_id required."}), 400

    gig = gig_model.get_by_id(db, gig_id)
    if not gig:
        return jsonify({"message": "Gig not found."}), 404

    # Employer auth check
    if employer_id and gig["employer_id"] != employer_id:
        return jsonify({"message": "Not your gig."}), 403

    gig_model.complete_gig(db, target_worker_id, gig_id)

    # Award impact points
    points = gig.get("impact_points", 10)
    score_info = score_model.add_points(db, target_worker_id, points)

    # Notify worker
    try:
        from services.at_sms import send_completion_alert
        worker = db.execute(
            "SELECT phone, name FROM workers WHERE id = ?", (target_worker_id,)
        ).fetchone()
        if worker:
            send_completion_alert(db, worker["phone"], gig, score_info)
    except Exception as e:
        print(f"[GIGS] Completion SMS error: {e}")

    return jsonify({
        "ok":          True,
        "message":     "Gig marked complete. Impact points added!",
        "points_added": points,
        "new_score":   score_info["impact_score"],
        "level_name":  score_info["level_name"],
    })


@gigs_bp.route("/create", methods=["POST"])
@employer_required
def create_gig():
    import models.gig as gig_model
    from services.matching import match_workers_to_gig

    db          = get_db()
    employer_id = session["employer_id"]
    data        = request.get_json(silent=True) or {}

    title    = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()
    location = (data.get("location") or "").strip()
    pay_kes  = data.get("pay_kes")
    desc     = (data.get("description") or "").strip()
    skills   = (data.get("skills_needed") or "").strip()
    duration = (data.get("duration") or "").strip()
    workers_needed = int(data.get("workers_needed") or 1)

    # Validate
    if not title:
        return jsonify({"message": "Job title is required."}), 400
    if not category:
        return jsonify({"message": "Green category is required."}), 400
    if not location:
        return jsonify({"message": "Location is required."}), 400
    if not pay_kes:
        return jsonify({"message": "Pay rate is required."}), 400

    try:
        pay_kes = int(pay_kes)
    except (ValueError, TypeError):
        return jsonify({"message": "Pay must be a number."}), 400

    gig = gig_model.create(
        db,
        employer_id=employer_id,
        title=title,
        category=category,
        location=location,
        pay_kes=pay_kes,
        description=desc,
        skills_needed=skills,
        duration=duration,
        workers_needed=workers_needed,
    )

    # Trigger matching + SMS (background-safe — errors logged not raised)
    try:
        match_workers_to_gig(db, gig, notify=True)
    except Exception as e:
        print(f"[GIGS] Matching error: {e}")

    return jsonify({
        "ok":     True,
        "gig_id": gig["id"],
        "message": f"Gig posted! We're already finding matched workers.",
    })
