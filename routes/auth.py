"""
GigGreen — Auth Routes
POST /auth/send-otp      → generate + send OTP via AT SMS
POST /auth/verify-otp    → check OTP, create session
POST /auth/register      → create worker or employer account
GET  /auth/login         → login page
GET  /auth/register      → register page
GET  /auth/logout        → clear session
"""
import random
import string
import json
from datetime import datetime, timedelta
from flask import (
    Blueprint, request, jsonify, session,
    render_template, redirect, url_for, current_app
)
from config import OTP_EXPIRY_MINUTES
import models.worker   as worker_model
import models.employer as employer_model

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_db():
    return current_app.get_db()


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _save_otp(db, phone: str, code: str):
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    db.execute("UPDATE otps SET used = 1 WHERE phone = ? AND used = 0", (phone,))
    db.execute(
        "INSERT INTO otps (phone, code, expires_at) VALUES (?, ?, ?)",
        (phone, code, expires_at),
    )
    db.commit()


def _verify_otp(db, phone: str, code: str) -> bool:
    row = db.execute(
        """
        SELECT id FROM otps
        WHERE phone = ? AND code = ? AND used = 0
          AND expires_at > CURRENT_TIMESTAMP
        ORDER BY created_at DESC LIMIT 1
        """,
        (phone, code),
    ).fetchone()
    if row:
        db.execute("UPDATE otps SET used = 1 WHERE id = ?", (row["id"],))
        db.commit()
        return True
    return False


def _set_worker_session(worker: dict):
    session["worker_id"]       = worker["id"]
    session["user_name"]       = worker["name"] or ""
    session["impact_score"]    = worker["impact_score"]
    session["user_level"]      = worker["level"]
    session["user_level_name"] = worker["level_name"]
    session["user_type"]       = "worker"


def _set_employer_session(employer: dict):
    session["employer_id"]  = employer["id"]
    session["user_name"]    = employer["company_name"] or employer.get("contact_name") or ""
    session["user_type"]    = "employer"


@auth_bp.route("/login")
def login():
    if session.get("worker_id") or session.get("employer_id"):
        return _post_login_redirect()
    return render_template("auth/login.html")


@auth_bp.route("/register")
def register():
    if session.get("worker_id") or session.get("employer_id"):
        return _post_login_redirect()
    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone or not phone.startswith("+254"):
        return jsonify({"message": "Enter a valid Kenyan number starting with +254."}), 400
    db   = get_db()
    code = _generate_otp()
    _save_otp(db, phone, code)
    try:
        from services.at_sms import send_otp as at_send_otp
        at_send_otp(db, phone, code)
    except Exception as e:
        print(f"[AUTH] AT SMS error: {e}")
        print(f"[AUTH][DEV] OTP for {phone}: {code}")
    return jsonify({"ok": True, "message": "Code sent!"})


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data        = request.get_json(silent=True) or {}
    phone       = (data.get("phone") or "").strip()
    code        = (data.get("code") or "").strip()
    is_register = data.get("is_register", False)
    if not phone or not code:
        return jsonify({"message": "Phone and code are required."}), 400
    db = get_db()
    if not _verify_otp(db, phone, code):
        return jsonify({"message": "Incorrect or expired code. Try again."}), 400
    session["verified_phone"] = phone
    session["verified_for_register"] = is_register
    if is_register:
        return jsonify({"ok": True, "message": "Phone verified."})
    worker = worker_model.get_by_phone(db, phone)
    if worker:
        _set_worker_session(worker)
        return jsonify({"ok": True, "redirect": url_for("worker.dashboard")})
    employer = employer_model.get_by_phone(db, phone)
    if employer:
        _set_employer_session(employer)
        return jsonify({"ok": True, "redirect": url_for("employer.dashboard")})
    return jsonify({"message": "This number isn't registered yet. Please create an account."}), 404


@auth_bp.route("/register", methods=["POST"])
def do_register():
    data      = request.get_json(silent=True) or {}
    phone     = (data.get("phone") or session.get("verified_phone") or "").strip()
    user_type = (data.get("user_type") or "worker").strip()
    if session.get("verified_phone") != phone:
        return jsonify({"message": "Phone not verified. Please start again."}), 400
    db = get_db()
    if user_type == "employer":
        company_name = (data.get("company_name") or "").strip()
        contact_name = (data.get("name") or "").strip()
        location     = (data.get("location") or "").strip()
        sector       = (data.get("sector") or "").strip()
        if not company_name:
            return jsonify({"message": "Company name is required."}), 400
        if employer_model.get_by_phone(db, phone):
            return jsonify({"message": "This number is already registered as an employer."}), 409
        employer = employer_model.create(
            db, phone=phone, company_name=company_name,
            contact_name=contact_name, location=location, sector=sector,
        )
        _set_employer_session(employer)
        session.pop("verified_phone", None)
        return jsonify({"ok": True, "redirect_employer": url_for("employer.dashboard")})
    else:
        name         = (data.get("name") or "").strip()
        location     = (data.get("location") or "").strip()
        bio          = (data.get("bio") or "").strip()
        availability = (data.get("availability") or "full-time").strip()
        green_raw    = data.get("green_categories", "[]")
        if not name:
            return jsonify({"message": "Your name is required."}), 400
        if not location:
            return jsonify({"message": "Please select your county."}), 400
        try:
            green_categories = json.loads(green_raw) if isinstance(green_raw, str) else green_raw
        except json.JSONDecodeError:
            green_categories = []
        if not green_categories:
            return jsonify({"message": "Select at least one green job category."}), 400
        if worker_model.get_by_phone(db, phone):
            return jsonify({"message": "This number is already registered. Please sign in."}), 409
        worker = worker_model.create(
            db, phone=phone, name=name, location=location,
            bio=bio, availability=availability, green_categories=green_categories,
        )
        _set_worker_session(worker)
        session.pop("verified_phone", None)
        return jsonify({"ok": True, "redirect": url_for("worker.dashboard")})


def _post_login_redirect():
    if session.get("employer_id"):
        return redirect(url_for("employer.dashboard"))
    return redirect(url_for("worker.dashboard"))
