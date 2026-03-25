import os
import sqlite3
from flask import Flask, g, session, redirect, url_for
from config import (
    SECRET_KEY, FLASK_DEBUG, DATABASE_PATH, SCHEMA_PATH, SEED_PATH
)

# ── App factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["DATABASE"] = DATABASE_PATH


# ── Database helpers ─────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables from schema.sql, then load seed data if DB is empty."""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r") as f:
        db.executescript(f.read())

    # Only seed if workers table is empty
    row = db.execute("SELECT COUNT(*) as cnt FROM workers").fetchone()
    if row["cnt"] == 0:
        with open(SEED_PATH, "r") as f:
            db.executescript(f.read())

    db.commit()
    db.close()
    print("✅  Database initialised at", DATABASE_PATH)


app.teardown_appcontext(close_db)

# Make get_db available to routes via app context
app.get_db = get_db


# ── Register blueprints ──────────────────────────────────────────────────────
from routes.auth     import auth_bp
from routes.worker   import worker_bp
from routes.employer import employer_bp
from routes.gigs     import gigs_bp
from routes.payments import payments_bp
from routes.ussd     import ussd_bp
from routes.sms      import sms_bp

app.register_blueprint(auth_bp)
app.register_blueprint(worker_bp,   url_prefix="/worker")
app.register_blueprint(employer_bp, url_prefix="/employer")
app.register_blueprint(gigs_bp,     url_prefix="/gigs")
app.register_blueprint(payments_bp, url_prefix="/payments")
app.register_blueprint(ussd_bp,     url_prefix="/ussd")
app.register_blueprint(sms_bp,      url_prefix="/sms")


# ── Root redirect ────────────────────────────────────────────────────────────
from flask import render_template

@app.route("/")
def index():
    return render_template("landing.html")


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ── Context processor — inject session worker data into all templates ─────────
@app.context_processor
def inject_session_user():
    worker_id   = session.get("worker_id")
    employer_id = session.get("employer_id")
    user_name   = session.get("user_name", "")
    impact_score = session.get("impact_score", 0)
    user_level  = session.get("user_level", 1)
    user_level_name = session.get("user_level_name", "Green Seed")
    return dict(
        session_worker_id=worker_id,
        session_employer_id=employer_id,
        session_user_name=user_name,
        session_impact_score=impact_score,
        session_user_level=user_level,
        session_user_level_name=user_level_name,
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(DATABASE_PATH):
        init_db()
    app.run(debug=FLASK_DEBUG, host="0.0.0.0", port=5000)
