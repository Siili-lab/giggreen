"""
GigGreen — Payments Routes
POST /payments/initiate   → employer holds funds in escrow
POST /payments/release    → employer releases funds to worker
GET  /payments/status     → check payment status
"""

from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for
import services.at_payments as at_payments
import models.gig           as gig_model

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


# ── Auth guard ────────────────────────────────────────────────────────────────

def employer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("employer_id"):
            return jsonify({"ok": False, "error": "Unauthorised"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Initiate escrow ───────────────────────────────────────────────────────────

@payments_bp.route("/initiate", methods=["POST"])
@employer_required
def initiate():
    data       = request.get_json() or {}
    gig_id     = data.get("gig_id")
    worker_id  = data.get("worker_id")
    amount_kes = data.get("amount_kes")

    if not all([gig_id, worker_id, amount_kes]):
        return jsonify({"ok": False, "error": "Missing fields"}), 400

    result = at_payments.initiate_escrow(
        gig_id     = gig_id,
        worker_id  = worker_id,
        employer_id= session["employer_id"],
        amount_kes = amount_kes,
    )
    return jsonify(result)


# ── Release payment ───────────────────────────────────────────────────────────

@payments_bp.route("/release", methods=["POST"])
@employer_required
def release():
    data      = request.get_json() or {}
    gig_id    = data.get("gig_id")
    worker_id = data.get("worker_id")

    if not all([gig_id, worker_id]):
        return jsonify({"ok": False, "error": "Missing fields"}), 400

    result = at_payments.release_funds(
        gig_id    = gig_id,
        worker_id = worker_id,
    )
    return jsonify(result)


# ── Status check ──────────────────────────────────────────────────────────────

@payments_bp.route("/status", methods=["GET"])
@employer_required
def status():
    gig_id = request.args.get("gig_id")
    if not gig_id:
        return jsonify({"ok": False, "error": "Missing gig_id"}), 400

    result = at_payments.get_payment_status(gig_id=gig_id)
    return jsonify(result)