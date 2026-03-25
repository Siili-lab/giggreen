import os
from dotenv import load_dotenv

load_dotenv()

# ── Africa's Talking ────────────────────────────────────────────────────────
AT_API_KEY   = os.getenv("AT_API_KEY", "sandbox_key_replace_me")
AT_USERNAME  = os.getenv("AT_USERNAME", "sandbox")
AT_SENDER_ID = os.getenv("AT_SENDER_ID", "GigGreen")

# ── Flask ───────────────────────────────────────────────────────────────────
SECRET_KEY  = os.getenv("SECRET_KEY", "gg-dev-secret-change-in-prod-2026")
FLASK_ENV   = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

# ── Database ────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "giggreen.db"))
SCHEMA_PATH   = os.path.join(BASE_DIR, "database", "schema.sql")
SEED_PATH     = os.path.join(BASE_DIR, "database", "seed.sql")

# ── OTP ─────────────────────────────────────────────────────────────────────
OTP_EXPIRY_MINUTES = 10

# ── Impact Score Levels ──────────────────────────────────────────────────────
LEVELS = [
    (0,    100,         1, "Green Seed"),
    (101,  300,         2, "Green Sprout"),
    (301,  600,         3, "Green Builder"),
    (601,  1000,        4, "Green Champion"),
    (1001, float("inf"), 5, "Green Legend"),
]

# ── Green Categories ─────────────────────────────────────────────────────────
GREEN_CATEGORIES = [
    "Solar",
    "E-Waste",
    "Urban Farming",
    "Carbon Scout",
    "Green Construction",
    "Community Educator",
    "Battery Swap",
    "Climate Data",
]

# ── Kenya Counties ────────────────────────────────────────────────────────────
KENYA_COUNTIES = [
    "Baringo","Bomet","Bungoma","Busia","Elgeyo-Marakwet","Embu","Garissa",
    "Homa Bay","Isiolo","Kajiado","Kakamega","Kericho","Kiambu","Kilifi",
    "Kirinyaga","Kisii","Kisumu","Kitui","Kwale","Laikipia","Lamu","Machakos",
    "Makueni","Mandera","Marsabit","Meru","Migori","Mombasa","Murang'a",
    "Nairobi","Nakuru","Nandi","Narok","Nyamira","Nyandarua","Nyeri",
    "Samburu","Siaya","Taita-Taveta","Tana River","Tharaka-Nithi","Trans Nzoia",
    "Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot",
]
