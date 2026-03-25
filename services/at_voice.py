"""
GigGreen — Africa's Talking Voice Service
Triggered when a worker is matched to a gig.
AT calls the worker's number and reads gig details aloud.
Worker presses 1 to confirm interest, 2 to decline.
"""

import sqlite3
import config


def call_worker_with_briefing(phone: str, gig: dict) -> dict:
    """
    Initiate an outbound call to a worker with a gig briefing.
    In production: uses AT Voice API. For hackathon: logged only.
    """
    try:
        import africastalking
        africastalking.initialize(config.AT_USERNAME, config.AT_API_KEY)
        voice = africastalking.Voice()
        response = voice.call(
            callFrom=getattr(config, 'AT_SENDER_ID', '+254711082436'),
            callTo=[phone],
        )
        return {"ok": True, "phone": phone, "at_response": str(response)}
    except Exception as e:
        return {"ok": False, "error": str(e), "phone": phone}


def handle_voice_callback(session_id: str, phone: str,
                           dtmf_digits: str, gig_id: int) -> str:
    """Handle AT voice callback. Returns TTS XML response string."""
    if dtmf_digits == "1":
        _confirm_interest(phone, gig_id)
        return (
            '<?xml version="1.0"?>'
            '<Response>'
            '<Say>Great! We have noted your interest. '
            'The employer will contact you shortly. Good luck!</Say>'
            '</Response>'
        )
    return (
        '<?xml version="1.0"?>'
        '<Response>'
        '<Say>No problem. We will keep looking for gigs that suit you. Goodbye!</Say>'
        '</Response>'
    )


def _confirm_interest(phone: str, gig_id: int):
    """Mark application as confirmed after voice response."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        worker = conn.execute(
            "SELECT id FROM workers WHERE phone = ?", (phone,)
        ).fetchone()
        if worker:
            conn.execute(
                "UPDATE applications SET status = 'confirmed' "
                "WHERE worker_id = ? AND gig_id = ?",
                (worker["id"], gig_id),
            )
            conn.commit()
    finally:
        conn.close()