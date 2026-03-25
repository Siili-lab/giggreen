"""
GigGreen — File Organiser
Moves loose Batch 3 files into their correct project folders.
Run from inside your GigGreen project root:
    python organise_giggreen.py
"""

import os
import shutil
import sys

# ── Map: filename (or relative path) → correct destination ────────────────────
FILE_MAP = {
    # Models
    "gig.py":                  "models/gig.py",
    "impact_score.py":         "models/impact_score.py",

    # Services
    "impact_calculator.py":    "services/impact_calculator.py",
    "matching.py":             "services/matching.py",

    # Routes
    "worker.py":               "routes/worker.py",
    "gigs.py":                 "routes/gigs.py",

    # Worker templates  — note: the analyser showed a stray dashboard.html
    # that belongs to worker, not employer. We map it correctly here.
    "dashboard.html":          "templates/worker/dashboard.html",
    "gig-feed.html":           "templates/worker/gig-feed.html",
    "profile.html":            "templates/worker/profile.html",
    "earnings.html":           "templates/worker/earnings.html",

    # JS
    "impact-score.js":         "static/js/impact-score.js",
    "worker-dashboard.js":     "static/js/worker-dashboard.js",
    "gig-feed.js":             "static/js/gig-feed.js",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def colour(code, text):
    """ANSI colour helper (works on modern Windows terminals too)."""
    return f"\033[{code}m{text}\033[0m"

OK   = lambda t: colour("32", t)   # green
WARN = lambda t: colour("33", t)   # yellow
ERR  = lambda t: colour("31", t)   # red
DIM  = lambda t: colour("2",  t)   # dim


def find_file(root, filename):
    """
    Search *root* for *filename* (case-sensitive, exact basename match).
    Returns the first absolute path found, or None.
    Skips the venv folder to avoid false matches.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip virtual-environment directory entirely
        dirnames[:] = [d for d in dirnames if d not in ("venv", ".git", "__pycache__")]
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def move_file(src, dst):
    """Create destination directory tree and move src → dst."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    root = os.path.abspath(os.path.dirname(__file__))

    print()
    print("=" * 60)
    print("  GigGreen File Organiser")
    print(f"  Root: {root}")
    print("=" * 60)
    print()

    moved   = []
    skipped = []
    missing = []

    for filename, rel_dest in FILE_MAP.items():
        dest_abs = os.path.join(root, rel_dest.replace("/", os.sep))

        # ── Already in the right place ──────────────────────────────────────
        if os.path.exists(dest_abs):
            skipped.append((filename, rel_dest))
            print(f"  {WARN('SKIP')}  {filename:<28} already at {DIM(rel_dest)}")
            continue

        # ── Find the file somewhere in the project ──────────────────────────
        src_abs = find_file(root, filename)

        if src_abs is None:
            missing.append(filename)
            print(f"  {ERR('MISS')}  {filename:<28} not found anywhere in project")
            continue

        # ── Confirm it isn't already the destination (different case, etc.) ─
        if os.path.normcase(src_abs) == os.path.normcase(dest_abs):
            skipped.append((filename, rel_dest))
            print(f"  {WARN('SKIP')}  {filename:<28} same path (case match)")
            continue

        # ── Move ─────────────────────────────────────────────────────────────
        try:
            move_file(src_abs, dest_abs)
            moved.append((filename, rel_dest))
            src_rel = os.path.relpath(src_abs, root)
            print(f"  {OK('MOVE')}  {filename:<28} {DIM(src_rel)} → {OK(rel_dest)}")
        except Exception as exc:
            print(f"  {ERR('ERR ')}  {filename:<28} {ERR(str(exc))}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  {OK('Moved')}  : {len(moved)}")
    print(f"  {WARN('Skipped')}: {len(skipped)}  (already in correct location)")
    print(f"  {ERR('Missing')}: {len(missing)}")

    if missing:
        print()
        print(f"  {ERR('Files not found — create or add them manually:')}")
        for f in missing:
            print(f"    • {f}  →  {FILE_MAP[f]}")

    print()
    if not missing and len(moved) > 0:
        print(f"  {OK('✅  All done! Your project structure is correct.')}")
        print("  Run your Flask app or setup_giggreen.py next.")
    elif not missing and len(moved) == 0:
        print(f"  {OK('✅  Nothing to move — structure was already correct.')}")
    else:
        print(f"  {WARN('⚠️  Some files were missing. Check the list above.')}")
    print()


if __name__ == "__main__":
    # Safety check: make sure we're running from the GigGreen root
    marker = os.path.join(os.path.dirname(__file__), "app.py")
    if not os.path.exists(marker):
        print()
        print(ERR("  ✗  Could not find app.py in this directory."))
        print("  Make sure you run this script from inside your GigGreen project root.")
        print("  e.g.  cd C:\\Users\\muthe\\OneDrive\\Desktop\\GigGreen")
        print("        python organise_giggreen.py")
        print()
        sys.exit(1)

    main()
