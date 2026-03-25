"""
GigGreen — Employer Routes
GET  /employer/dashboard       → employer home
GET  /employer/blueprint       → Human Blueprint™ form
POST /employer/blueprint       → save new gig + trigger matching
GET  /employer/matches/<id>    → ranked worker matches for a gig
GET  /employer/impact-report   → ESG dashboard
"""

from functools import wraps
from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, jsonify, flash
)

import models.employer        as employer_model
import models.gig             as gig_model
import services.matching      as matching
import config

employer_bp = Blueprint("employer", __name__, url_prefix="/employer")


# ── Auth guard ────────────────────────────────────────────────────────────────

def employer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("employer_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────

@employer_bp.route("/dashboard")
@employer_required
def dashboard():
    employer_id = session["employer_id"]
    employer    = employer_model.get_by_id(employer_id)
    active_gigs = employer_model.get_active_gigs(employer_id)
    return render_template(
        "employer/dashboard.html",
        employer=employer,
        active_gigs=active_gigs,
    )


# ── Human Blueprint™ form ─────────────────────────────────────────────────────

@employer_bp.route("/blueprint", methods=["GET", "POST"])
@employer_required
def blueprint():
    if request.method == "POST":
        data = request.form
        gig_id = gig_model.create(
            employer_id   = session["employer_id"],
            title         = data.get("title", "").strip(),
            category      = data.get("category", "").strip(),
            location      = data.get("location", "").strip(),
            pay_kes       = int(data.get("pay_kes", 0) or 0),
            impact_points = int(data.get("impact_points", 0) or 0),
            description   = data.get("description", "").strip(),
            duration      = data.get("duration", "").strip(),
            workers_needed= int(data.get("workers_needed", 1) or 1),
        )

        # Trigger matching — top 5 workers get SMS
        matched = matching.match_workers_to_gig(gig_id)

        flash(f"Gig posted! {len(matched)} workers notified by SMS.", "success")
        return redirect(url_for("employer.matches", gig_id=gig_id))

    return render_template(
        "employer/blueprint.html",
        categories  = config.GREEN_CATEGORIES,
        counties    = config.KENYA_COUNTIES,
    )


# ── Matches ───────────────────────────────────────────────────────────────────

@employer_bp.route("/matches/<int:gig_id>")
@employer_required
def matches(gig_id):
    gig     = gig_model.get_by_id(gig_id)
    if not gig or gig["employer_id"] != session["employer_id"]:
        return redirect(url_for("employer.dashboard"))

    workers = matching.get_ranked_matches(gig_id)
    return render_template(
        "employer/matches.html",
        gig     = gig,
        workers = workers,
    )


# ── Impact report ─────────────────────────────────────────────────────────────

@employer_bp.route("/impact-report")
@employer_required
def impact_report():
    employer_id = session["employer_id"]
    gigs        = gig_model.get_completed_by_employer(employer_id)

    # Aggregate ESG metrics
    total_co2   = sum(g.get("impact_points", 0) * 10 for g in gigs)   # kg CO2 proxy
    total_gigs  = len(gigs)
    total_paid  = sum(g.get("pay_kes", 0) for g in gigs)

    return render_template(
        "employer/impact-report.html",
        gigs       = gigs,
        total_co2  = total_co2,
        total_gigs = total_gigs,
        total_paid = total_paid,
    )


# ── API: confirm worker ───────────────────────────────────────────────────────

@employer_bp.route("/api/confirm-worker", methods=["POST"])
@employer_required
def confirm_worker():
    data       = request.get_json()
    gig_id     = data.get("gig_id")
    worker_id  = data.get("worker_id")

    if not gig_id or not worker_id:
        return jsonify({"ok": False, "error": "Missing fields"}), 400

    success = gig_model.confirm_worker(gig_id, worker_id)
    return jsonify({"ok": success})
