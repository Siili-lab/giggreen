"""
GigGreen — SMS Routes
POST /sms/incoming   → Africa's Talking incoming SMS callback
"""

from flask import Blueprint, request
import services.at_sms as at_sms

sms_bp = Blueprint("sms", __name__, url_prefix="/sms")


@sms_bp.route("/incoming", methods=["POST"])
def incoming():
    """Handle inbound SMS from Africa's Talking callback."""
    phone   = request.form.get("from", "")
    message = request.form.get("text", "").strip().upper()

    # Log the incoming SMS
    at_sms.log_sms(phone=phone, message=message, direction="inbound")

    # Simple keyword responses
    if message in ("HELP", "MSAADA"):
        at_sms.send(
            phone,
            "GigGreen: Reply JOBS to see open gigs, SCORE for your impact score, "
            "STOP to unsubscribe. Maswali? 0800 000 000"
        )
    elif message in ("JOBS", "KAZI"):
        at_sms.send(
            phone,
            "GigGreen: New gigs available! Login at giggreen.co.ke to apply, "
            "or we will SMS you when a match is found."
        )
    elif message in ("SCORE", "POINTI"):
        at_sms.send(
            phone,
            "GigGreen: Login at giggreen.co.ke to see your Green Impact Score and level."
        )
    elif message in ("STOP", "ACHA"):
        at_sms.send(
            phone,
            "GigGreen: You have been unsubscribed from SMS alerts. "
            "Reply START to resubscribe anytime."
        )

    # AT expects empty 200 response
    return "", 200