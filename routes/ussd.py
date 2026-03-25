"""
GigGreen — USSD Routes
POST /ussd/   → Africa's Talking USSD callback
"""

from flask import Blueprint, request
import services.at_ussd as at_ussd

ussd_bp = Blueprint("ussd", __name__, url_prefix="/ussd")


@ussd_bp.route("/", methods=["POST"])
def ussd():
    """
    Handle USSD session from Africa's Talking.
    AT posts: sessionId, phoneNumber, networkCode, serviceCode, text
    We respond with: CON <menu text>  (continue)
                  or END <message>   (end session)
    """
    session_id   = request.form.get("sessionId", "")
    phone        = request.form.get("phoneNumber", "")
    text         = request.form.get("text", "")

    response = at_ussd.handle(
        session_id = session_id,
        phone      = phone,
        text       = text,
    )

    return response, 200, {"Content-Type": "text/plain"}