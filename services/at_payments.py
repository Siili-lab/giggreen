"""
GigGreen — Africa's Talking Payments Service
Escrow simulation for hackathon demo.
Real AT Payments API call is wrapped but status-flagged in DB.
"""

import sqlite3
import config


def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initiate_escrow(gig_id: int, worker_id: int,
                    employer_id: int, amount_kes: int) -> dict:
    """
    Simulate holding funds in escrow.
    Inserts a payment record with status 'held'.
    """
    conn = get_db()
    try:
        # Check if payment already exists for this gig
        existing = conn.execute(
            "SELECT id FROM payments WHERE gig_id = ?", (gig_id,)
        ).fetchone()

        if existing:
            return {"ok": False, "error": "Payment already initiated for this gig"}

        cur = conn.execute(
            """INSERT INTO payments
               (gig_id, worker_id, employer_id, amount_kes, status)
               VALUES (?, ?, ?, ?, 'held')""",
            (gig_id, worker_id, employer_id, amount_kes),
        )
        conn.commit()

        # In production: call AT Payments API here
        # at.initiate_wallet_payment(...)

        return {
            "ok":         True,
            "payment_id": cur.lastrowid,
            "status":     "held",
            "amount_kes": amount_kes,
            "message":    f"KES {amount_kes:,} held in escrow. Will release on job completion.",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def release_funds(gig_id: int, worker_id: int) -> dict:
    """
    Release escrowed funds to worker.
    Updates payment status to 'released' and gig status to 'complete'.
    """
    conn = get_db()
    try:
        payment = conn.execute(
            "SELECT * FROM payments WHERE gig_id = ? AND worker_id = ? AND status = 'held'",
            (gig_id, worker_id),
        ).fetchone()

        if not payment:
            return {"ok": False, "error": "No held payment found for this gig/worker"}

        # Get worker phone for SMS confirmation
        worker = conn.execute(
            "SELECT phone, name FROM workers WHERE id = ?", (worker_id,)
        ).fetchone()

        conn.execute(
            "UPDATE payments SET status = 'released' WHERE id = ?",
            (payment["id"],),
        )
        conn.execute(
            "UPDATE gigs SET status = 'complete' WHERE id = ?",
            (gig_id,),
        )
        conn.commit()

        # In production: trigger real AT mobile money transfer here
        # at.send_mobile_checkout(phone, amount)

        # Log confirmation SMS
        if worker:
            msg = (
                f"GigGreen: KES {payment['amount_kes']:,} has been sent to your M-Pesa. "
                f"Congrats on completing the job! Check your GigGreen score — it just went up."
            )
            conn.execute(
                "INSERT INTO sms_log (phone, message, direction) VALUES (?, ?, 'outbound')",
                (worker["phone"], msg),
            )
            conn.commit()

        return {
            "ok":         True,
            "status":     "released",
            "amount_kes": payment["amount_kes"],
            "message":    f"KES {payment['amount_kes']:,} released to worker via M-Pesa.",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_payment_status(gig_id: int) -> dict:
    conn = get_db()
    try:
        payment = conn.execute(
            "SELECT * FROM payments WHERE gig_id = ?", (gig_id,)
        ).fetchone()

        if not payment:
            return {"ok": True, "status": "none", "message": "No payment initiated yet"}

        return {
            "ok":         True,
            "payment_id": payment["id"],
            "status":     payment["status"],
            "amount_kes": payment["amount_kes"],
        }
    finally:
        conn.close()