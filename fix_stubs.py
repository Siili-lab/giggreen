"""
GigGreen — Fix Stubs (Final)
Copies real root files over empty stubs, then deletes root duplicates.

Run from your GigGreen project root:
    python fix_stubs.py
"""

import os
import shutil

FILE_MAP = {
    "gig.py":               "models/gig.py",
    "impact_score.py":      "models/impact_score.py",
    "impact_calculator.py": "services/impact_calculator.py",
    "matching.py":          "services/matching.py",
    "worker.py":            "routes/worker.py",
    "gigs.py":              "routes/gigs.py",
    "dashboard.html":       "templates/worker/dashboard.html",
    "gig-feed.html":        "templates/worker/gig-feed.html",
    "profile.html":         "templates/worker/profile.html",
    "earnings.html":        "templates/worker/earnings.html",
    "impact-score.js":      "static/js/impact-score.js",
    "worker-dashboard.js":  "static/js/worker-dashboard.js",
    "gig-feed.js":          "static/js/gig-feed.js",
}

OK   = lambda t: f"\033[32m{t}\033[0m"
ERR  = lambda t: f"\033[31m{t}\033[0m"

root = os.path.abspath(".")

print()
print("=" * 60)
print("  GigGreen Fix Stubs — copying real files over stubs")
print("=" * 60)
print()

copied = []
errors = []

for src_name, rel_dest in FILE_MAP.items():
    src  = os.path.join(root, src_name)
    dest = os.path.join(root, rel_dest.replace("/", os.sep))

    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  {OK('COPY')}  {src_name:<28} → {rel_dest}")
        copied.append(src_name)
    except Exception as e:
        print(f"  {ERR('ERR ')}  {src_name:<28} {e}")
        errors.append(src_name)

print()
print("  Deleting root duplicates...")
print()

for src_name in copied:
    src = os.path.join(root, src_name)
    try:
        os.remove(src)
        print(f"  {OK('DEL ')}  {src_name} removed from root")
    except Exception as e:
        print(f"  {ERR('ERR ')}  Could not delete {src_name}: {e}")

print()
print("=" * 60)
print(f"  Copied  : {len(copied)}")
print(f"  Errors  : {len(errors)}")
print()
if not errors:
    print(f"  {OK('✅  All done! Structure is correct. Run your app next.')}")
else:
    print(f"  {ERR('⚠️  Some files had errors — check above.')}")
print()
