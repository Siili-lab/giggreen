"""
GigGreen Project Structure Setup — v2
Run this from your GigGreen folder after running fix2_giggreen.py.

What's new in v2:
  - Includes static/css/auth.css and static/css/landing.css
  - Handles __init__models.py  → models/__init__.py
  - Handles __init__services.py → services/__init__.py
  - Skips script files from leftover warnings
"""

import os
import shutil
import sys

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
    "static/css/auth.css",
    "static/css/landing.css",

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

# Files renamed by fix_giggreen.py to temp names
# Key = project path  |  Value = current temp filename
TEMP_NAME_MAP = {
    "models/__init__.py":   "__init__models.py",
    "services/__init__.py": "__init__services.py",
}

OWN_SCRIPTS = {
    "setup_giggreen.py", "analyse_giggreen.py",
    "inspect_giggreen.py", "fix_giggreen.py", "fix2_giggreen.py",
}

PLACEHOLDERS = {
    ".py":      "# TODO: implement {filename}\n",
    ".html":    "<!-- TODO: implement {filename} -->\n",
    ".css":     "/* TODO: implement {filename} */\n",
    ".js":      "// TODO: implement {filename}\n",
    ".sql":     "-- TODO: implement {filename}\n",
    ".svg":     "<!-- TODO: implement {filename} -->\n",
    ".txt":     "# TODO: add dependencies\n",
    ".example": (
        "AT_API_KEY=your_africas_talking_api_key\n"
        "AT_USERNAME=sandbox\n"
        "AT_SENDER_ID=GigGreen\n"
        "SECRET_KEY=your-secret-key-here\n"
        "DATABASE_PATH=giggreen.db\n"
        "FLASK_ENV=development\n"
        "FLASK_DEBUG=1\n"
    ),
}


def placeholder_for(filepath):
    name = os.path.basename(filepath)
    ext  = os.path.splitext(name)[1].lower()
    return PLACEHOLDERS.get(ext, "# placeholder\n").replace("{filename}", name)


def setup(project_root, source_dir):
    project_root = os.path.abspath(project_root)
    source_dir   = os.path.abspath(source_dir)

    print(f"\n📁  Project root : {project_root}")
    print(f"🔍  Scanning     : {source_dir}\n")

    # Index every flat file in source_dir
    existing = {}
    for fname in os.listdir(source_dir):
        fpath = os.path.join(source_dir, fname)
        if os.path.isfile(fpath):
            existing[fname] = fpath

    moved   = []
    created = []
    skipped = []

    for rel_path in PROJECT_FILES:
        dest     = os.path.join(project_root, rel_path)
        dest_dir = os.path.dirname(dest)
        filename = os.path.basename(rel_path)

        os.makedirs(dest_dir, exist_ok=True)

        if os.path.exists(dest):
            skipped.append(rel_path)
            continue

        # Check temp name map first
        temp_name = TEMP_NAME_MAP.get(rel_path)
        if temp_name and temp_name in existing:
            shutil.move(existing[temp_name], dest)
            moved.append(f"{temp_name}  →  {rel_path}")
            del existing[temp_name]
            continue

        # Normal match by filename
        if filename in existing:
            shutil.move(existing[filename], dest)
            moved.append(f"{existing[filename]}  →  {rel_path}")
            del existing[filename]
            continue

        # Create placeholder
        with open(dest, "w", encoding="utf-8") as f:
            f.write(placeholder_for(rel_path))
        created.append(rel_path)

    # ── Summary ─────────────────────────────────────────────────────────────
    print("=" * 60)

    if moved:
        print(f"\n✅  MOVED ({len(moved)} files)")
        for m in moved:
            print(f"    {m}")

    if created:
        print(f"\n📄  PLACEHOLDERS created ({len(created)} files)")
        for c in created:
            print(f"    {c}")

    if skipped:
        print(f"\n⏭️   ALREADY IN PLACE ({len(skipped)} files)")
        for s in skipped:
            print(f"    {s}")

    leftover = {k: v for k, v in existing.items() if k not in OWN_SCRIPTS}
    if leftover:
        print(f"\n⚠️   LEFTOVER — not moved, review manually ({len(leftover)} files)")
        for name in leftover:
            print(f"    {name}")

    print("\n✅  Structure ready!\n")
    print("Next steps:")
    print("  1.  python -m venv venv")
    print("  2.  venv\\Scripts\\Activate.ps1")
    print("  3.  pip install -r requirements.txt")
    print("  4.  Copy .env.example → .env and fill in your keys")
    print("  5.  python -c \"from app import init_db; init_db()\"")
    print("  6.  flask run\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        project_root = source_dir = os.getcwd()
    elif len(args) == 1:
        project_root = source_dir = args[0]
    else:
        project_root, source_dir = args[0], args[1]
    setup(project_root, source_dir)
