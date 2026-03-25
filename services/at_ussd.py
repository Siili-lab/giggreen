"""
GigGreen — Africa's Talking USSD Service
Stateless AT callback → state tracked in ussd_sessions DB table.

Menu tree:
  Main: 1=View Gigs  2=My Score  3=Earnings  4=Help
"""

import sqlite3
import config


def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def handle(session_id: str, phone: str, text: str) -> str:
    """
    Process USSD input and return CON/END response string.
    `text` is the full input chain e.g. "" / "1" / "1*2"
    """
    parts = text.strip().split("*") if text.strip() else []
    level = len(parts)

    # ── Level 0 — Main menu ───────────────────────────────────────────────────
    if level == 0:
        _save_state(session_id, phone, "main")
        return (
            "CON Welcome to GigGreen 🌱\n"
            "1. View open gigs\n"
            "2. My Impact Score\n"
            "3. My earnings\n"
            "4. Help"
        )

    choice_1 = parts[0]

    # ── Level 1 ───────────────────────────────────────────────────────────────
    if level == 1:
        if choice_1 == "1":
            gigs = _get_open_gigs()
            if not gigs:
                return "END No open gigs in your area right now. We will SMS you when one posts!"
            lines = ["CON Open Gigs Near You:"]
            for i, g in enumerate(gigs[:5], 1):
                lines.append(f"{i}. {g['title']} - KES {g['pay_kes']:,}")
            lines.append("0. Back")
            return "\n".join(lines)

        elif choice_1 == "2":
            worker = _get_worker(phone)
            if not worker:
                return "END Phone not registered. Visit giggreen.co.ke to sign up."
            return (
                f"END Your Green Impact Score: {worker['impact_score']} pts\n"
                f"Level: {worker['level']}\n"
                f"Keep completing gigs to level up!"
            )

        elif choice_1 == "3":
            payments = _get_payments(phone)
            if not payments:
                return "END No earnings yet. Apply for gigs to get started!"
            lines = ["END Recent Earnings:"]
            for p in payments[:3]:
                lines.append(f"KES {p['amount_kes']:,} - {p['status']}")
            return "\n".join(lines)

        elif choice_1 == "4":
            return (
                "END GigGreen Help:\n"
                "SMS JOBS to get gig alerts\n"
                "SMS SCORE for your points\n"
                "Visit giggreen.co.ke\n"
                "Support: 0800 000 000 (free)"
            )
        else:
            return "END Invalid option. Please try again."

    return "END Thank you for using GigGreen. Karibu tena!"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _save_state(session_id: str, phone: str, state: str):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO ussd_sessions (session_id, phone, state)
               VALUES (?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET state=excluded.state""",
            (session_id, phone, state),
        )
        conn.commit()
    finally:
        conn.close()


def _get_worker(phone: str):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM workers WHERE phone = ?", (phone,)
        ).fetchone()
    finally:
        conn.close()


def _get_open_gigs() -> list:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT title, pay_kes FROM gigs WHERE status = 'open' ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _get_payments(phone: str) -> list:
    conn = get_db()
    try:
        worker = conn.execute(
            "SELECT id FROM workers WHERE phone = ?", (phone,)
        ).fetchone()
        if not worker:
            return []
        rows = conn.execute(
            "SELECT amount_kes, status FROM payments WHERE worker_id = ? ORDER BY created_at DESC LIMIT 3",
            (worker["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()