"""
GigGreen File Analyser
Run this FIRST before setup_giggreen.py.
It scans your folder and tells you exactly what you have, what's missing,
and what doesn't belong — without moving or changing anything.
"""

import os
import sys

# ── Every file the project expects ──────────────────────────────────────────
PROJECT_FILES = [
    # Root
    "requirements.txt",
    "config.py",
    "app.py",
    ".env.example",

    # Database
    "database/schema.sql",
    "database/seed.sql",

    # Static – CSS
    "static/css/main.css",
    "static/css/components.css",
    "static/css/animations.css",
    "static/css/dashboard.css",

    # Static – JS
    "static/js/main.js",
    "static/js/auth.js",
    "static/js/worker-dashboard.js",
    "static/js/gig-feed.js",
    "static/js/impact-score.js",
    "static/js/employer-dashboard.js",

    # Static – Images
    "static/images/logo.svg",

    # Templates – root
    "templates/base.html",
    "templates/landing.html",

    # Templates – auth
    "templates/auth/login.html",
    "templates/auth/register.html",

    # Templates – worker
    "templates/worker/dashboard.html",
    "templates/worker/gig-feed.html",
    "templates/worker/profile.html",
    "templates/worker/earnings.html",

    # Templates – employer
    "templates/employer/dashboard.html",
    "templates/employer/blueprint.html",
    "templates/employer/matches.html",
    "templates/employer/impact-report.html",

    # Templates – errors
    "templates/errors/404.html",
    "templates/errors/500.html",

    # Routes
    "routes/__init__.py",
    "routes/auth.py",
    "routes/worker.py",
    "routes/employer.py",
    "routes/gigs.py",
    "routes/ussd.py",
    "routes/sms.py",
    "routes/payments.py",

    # Models
    "models/__init__.py",
    "models/worker.py",
    "models/gig.py",
    "models/employer.py",
    "models/impact_score.py",

    # Services
    "services/__init__.py",
    "services/at_sms.py",
    "services/matching.py",
    "services/impact_calculator.py",
    "services/at_ussd.py",
    "services/at_payments.py",
    "services/at_voice.py",
]

EXPECTED_FILENAMES = {os.path.basename(p): p for p in PROJECT_FILES}


def human_size(path):
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    return f"{size/(1024*1024):.1f} MB"


def collect_all_files(root: str):
    """Walk the entire directory tree and collect every file."""
    all_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel  = os.path.relpath(full, root)
            all_files.append((rel, full))
    return all_files


def analyse(scan_dir: str):
    scan_dir = os.path.abspath(scan_dir)
    print(f"\n{'='*60}")
    print(f"  GigGreen File Analyser")
    print(f"  Scanning: {scan_dir}")
    print(f"{'='*60}\n")

    all_files = collect_all_files(scan_dir)

    # ── Bucket 1: already in the correct relative path ──────────────────────
    correct_path   = []  # (rel_path, size)
    wrong_location = []  # (rel_path, expected_rel, size) — right name, wrong folder
    unrecognised   = []  # (rel_path, size) — not in project spec at all

    found_filenames = {}  # basename → (rel_path, full_path)

    for rel, full in all_files:
        fname = os.path.basename(rel)
        size  = human_size(full)

        if rel in PROJECT_FILES:
            correct_path.append((rel, size))
        elif fname in EXPECTED_FILENAMES:
            wrong_location.append((rel, EXPECTED_FILENAMES[fname], size))
        else:
            unrecognised.append((rel, size))

        found_filenames[fname] = rel

    # ── Bucket 2: missing entirely ───────────────────────────────────────────
    missing = []
    for expected in PROJECT_FILES:
        fname = os.path.basename(expected)
        if fname not in found_filenames:
            missing.append(expected)

    # ── Batch completion summary (from build tracker) ────────────────────────
    batches = {
        "Batch 1 — Foundation Layer": [
            "requirements.txt", "config.py", "app.py",
            "database/schema.sql", "database/seed.sql",
            "static/css/main.css", "static/css/components.css",
            "static/css/animations.css", "static/css/dashboard.css",
            "static/js/main.js", "templates/base.html", "static/images/logo.svg",
        ],
        "Batch 2 — Auth + Landing": [
            "templates/landing.html", "templates/auth/login.html",
            "templates/auth/register.html", "routes/auth.py",
            "models/worker.py", "services/at_sms.py", "static/js/auth.js",
        ],
        "Batch 3 — Worker Experience": [
            "templates/worker/dashboard.html", "templates/worker/gig-feed.html",
            "templates/worker/profile.html", "templates/worker/earnings.html",
            "routes/worker.py", "models/gig.py", "services/matching.py",
            "services/impact_calculator.py", "models/impact_score.py",
            "static/js/worker-dashboard.js", "static/js/gig-feed.js",
            "static/js/impact-score.js",
        ],
        "Batch 4 — Employer Experience": [
            "templates/employer/dashboard.html", "templates/employer/blueprint.html",
            "templates/employer/matches.html", "templates/employer/impact-report.html",
            "routes/employer.py", "models/employer.py",
            "static/js/employer-dashboard.js", "routes/gigs.py",
        ],
        "Batch 5 — AT APIs + USSD + Payments": [
            "routes/ussd.py", "routes/sms.py", "services/at_ussd.py",
            "services/at_payments.py", "services/at_voice.py", "routes/payments.py",
        ],
        "Batch 6 — Error Pages + Polish": [
            "templates/errors/404.html", "templates/errors/500.html",
        ],
    }

    # ── Print results ────────────────────────────────────────────────────────

    if correct_path:
        print(f"✅  ALREADY IN CORRECT LOCATION ({len(correct_path)} files)")
        for rel, size in sorted(correct_path):
            print(f"    {rel:<45} {size}")

    print()

    if wrong_location:
        print(f"📂  FOUND BUT IN WRONG FOLDER ({len(wrong_location)} files)")
        print(f"    {'Current path':<40} {'Should be':<45} Size")
        print(f"    {'-'*40} {'-'*45} ----")
        for rel, expected, size in wrong_location:
            print(f"    {rel:<40} {expected:<45} {size}")

    print()

    if missing:
        print(f"❌  MISSING ENTIRELY ({len(missing)} files)")
        for m in missing:
            print(f"    {m}")

    print()

    if unrecognised:
        print(f"⚠️   UNRECOGNISED FILES ({len(unrecognised)}) — not in project spec")
        for rel, size in unrecognised:
            print(f"    {rel:<45} {size}")

    print()

    # ── Per-batch progress ───────────────────────────────────────────────────
    print(f"{'='*60}")
    print("  BATCH PROGRESS")
    print(f"{'='*60}")
    for batch_name, batch_files in batches.items():
        found_count = sum(
            1 for f in batch_files
            if os.path.basename(f) in found_filenames
        )
        total = len(batch_files)
        bar_filled = int((found_count / total) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        pct = int((found_count / total) * 100)
        status = "✅" if found_count == total else "⏳"
        print(f"  {status}  {batch_name}")
        print(f"      [{bar}] {found_count}/{total} ({pct}%)")
    print()

    # ── Quick action summary ─────────────────────────────────────────────────
    print(f"{'='*60}")
    print("  WHAT TO DO NEXT")
    print(f"{'='*60}")
    if wrong_location:
        print(f"  → Run setup_giggreen.py to move {len(wrong_location)} misplaced file(s) into place.")
    if missing:
        print(f"  → {len(missing)} file(s) are missing. setup_giggreen.py will create placeholders for them.")
    if not wrong_location and not missing:
        print("  → All files accounted for! Run setup_giggreen.py to finalise the structure.")
    if unrecognised:
        print(f"  → Review the {len(unrecognised)} unrecognised file(s) — they won't be touched by setup_giggreen.py.")
    print()


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    """
    Usage:
        python analyse_giggreen.py           # scans current directory
        python analyse_giggreen.py /path/to/folder
    """
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    analyse(folder)
