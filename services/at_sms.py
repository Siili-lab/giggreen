"""
GigGreen — Africa's Talking SMS Service
Wraps all outbound SMS sends and logs every message to the DB.
"""
import africastalking
from datetime import datetime
from config import AT_API_KEY, AT_USERNAME, AT_SENDER_ID

# Initialise AT SDK once
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS


def _log_sms(db, phone: str, message: str, direction: str, status: str = "sent"):
    """Write an SMS record to sms_log table."""
    try:
        db.execute(
            "INSERT INTO sms_log (phone, message, direction, status) VALUES (?, ?, ?, ?)",
            (phone, message, direction, status),
        )
        db.commit()
    except Exception as e:
        print(f"[SMS LOG ERROR] {e}")


def send_otp(db, phone: str, code: str) -> bool:
    """Send a 6-digit OTP code via AT SMS."""
    message = f"Your GigGreen code is: {code}. It expires in 10 minutes. Do not share it."
    return _send(db, [phone], message)


def send_job_alert(db, phone: str, gig_title: str, location: str, pay_kes: int, gig_id: int) -> bool:
    """Alert a matched worker about a new gig."""
    message = (
        f"GigGreen: New gig near you!\n"
        f"{gig_title} in {location}. Pay: KES {pay_kes:,}.\n"
        f"Reply YES to apply or visit giggreen.app/gigs/{gig_id}"
    )
    return _send(db, [phone], message)


def send_bulk_job_alerts(db, phones: list, gig_title: str, location: str, pay_kes: int, gig_id: int) -> bool:
    """Bulk-send job alerts to top matched workers."""
    message = (
        f"GigGreen: New gig near you!\n"
        f"{gig_title} in {location}. Pay: KES {pay_kes:,}.\n"
        f"Reply YES to apply."
    )
    return _send(db, phones, message)


def send_gig_confirmation(db, phone: str, gig_title: str, date: str, location: str, employer_name: str) -> bool:
    """Confirm a worker has been selected for a gig."""
    message = (
        f"GigGreen: You got the gig!\n"
        f"{gig_title} on {date} at {location}.\n"
        f"Client: {employer_name}. Dial *384*GigGreen# for details."
    )
    return _send(db, [phone], message)


def send_payment_notification(db, phone: str, amount_kes: int, gig_title: str) -> bool:
    """Notify a worker their M-Pesa payment has been sent."""
    message = (
        f"GigGreen: KES {amount_kes:,} sent to your M-Pesa for '{gig_title}'. "
        f"Asante! Keep earning green. giggreen.app"
    )
    return _send(db, [phone], message)


def send_employer_match_notification(db, phone: str, gig_title: str, match_count: int) -> bool:
    """Tell an employer how many workers were matched to their gig."""
    message = (
        f"GigGreen: {match_count} workers matched for '{gig_title}'. "
        f"Log in to review and hire. giggreen.app/employer/matches"
    )
    return _send(db, [phone], message)



def send_application_alert(db, phone: str, gig_title: str, worker_name: str) -> bool:
    """Notify an employer that a worker has applied for their gig."""
    message = (
        f"GigGreen: {worker_name} has applied for '{gig_title}'. "
        f"Log in to review and confirm. giggreen.app/employer/dashboard"
    )
    return _send(db, [phone], message)


def send_completion_alert(db, phone: str, gig_title: str, worker_name: str) -> bool:
    """Notify an employer that a worker has marked a gig as complete."""
    message = (
        f"GigGreen: {worker_name} has marked '{gig_title}' as complete. "
        f"Log in to confirm and release payment. giggreen.app/employer/dashboard"
    )
    return _send(db, [phone], message)

def _send(db, recipients: list, message: str) -> bool:
    """
    Internal send. Tries real AT API, falls back to sandbox simulation.
    Always logs to DB.
    """
    success = False
    status  = "sent"

    try:
        response = sms.send(message, recipients, sender_id=AT_SENDER_ID)
        # AT returns: {"SMSMessageData": {"Message": "...", "Recipients": [...]}}
        recipients_data = response.get("SMSMessageData", {}).get("Recipients", [])
        # Check at least one recipient succeeded
        success = any(r.get("statusCode") == 101 for r in recipients_data)
        status  = "sent" if success else "failed"
        print(f"[AT SMS] Sent to {recipients} | Status: {status}")
    except Exception as e:
        print(f"[AT SMS ERROR] {e}")
        status  = "failed"
        success = False

    # Log each recipient
    for phone in recipients:
        _log_sms(db, phone, message, "outbound", status)

    return success
