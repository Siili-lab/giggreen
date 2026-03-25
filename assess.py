"""
GigGreen — Deep Assessment Script
Checks every pending file from Batches 4, 5, 6
Reports: DONE / STUB / EMPTY / MISSING for each file
Also checks route function names and placeholder content
"""

import os
import re

BATCH4 = [
    "templates/employer/dashboard.html",
    "templates/employer/blueprint.html",
    "templates/employer/matches.html",
    "templates/employer/impact-report.html",
    "routes/employer.py",
    "static/js/employer-dashboard.js",
]

BATCH5 = [
    "routes/ussd.py",
    "routes/sms.py",
    "routes/payments.py",
    "services/at_ussd.py",
    "services/at_payments.py",
    "services/at_voice.py",
]

BATCH6 = [
    "templates/errors/404.html",
    "templates/errors/500.html",
]

STUB_PHRASES = [
    "TODO", "placeholder", "coming soon", "stub", "pass", "Not implemented",
    "# todo", "<!-- todo", "lorem ipsum",
]

MIN_SIZES = {
    ".py":   500,
    ".html": 500,
    ".js":   200,
}

def assess_file(path):
    if not os.path.exists(path):
        return "MISSING", 0, []

    size = os.path.getsize(path)
    ext = os.path.splitext(path)[1]
    min_size = MIN_SIZES.get(ext, 200)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if size < 60:
        return "EMPTY", size, []

    hits = [p for p in STUB_PHRASES if p.lower() in content.lower()]

    if size < min_size:
        return "STUB", size, hits

    return "DONE", size, hits


def check_routes(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    routes = []
    for line in content.splitlines():
        if re.match(r"\s*@\w+_bp\.route", line) or re.match(r"\s*@\w+\.route", line):
            routes.append(line.strip())
        elif re.match(r"\s*def \w+\(", line):
            routes.append("  -> " + line.strip())
    return routes


def print_section(title, files):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    all_done = True
    for path in files:
        status, size, hits = assess_file(path)
        icon = {"DONE": "✅", "STUB": "⚠️ ", "EMPTY": "❌", "MISSING": "❌"}.get(status, "?")
        print(f"  {icon}  {status:<8} {path}  ({size}B)")
        if hits:
            print(f"           ⚠️  Contains: {', '.join(hits)}")
        if status != "DONE":
            all_done = False

        # Show route map for python files
        if path.endswith(".py") and status == "DONE":
            routes = check_routes(path)
            if routes:
                for r in routes:
                    print(f"           {r}")
    return all_done


print("""
=================================================================
  GigGreen — Batch 4/5/6 Deep Assessment
=================================================================
""")

b4 = print_section("BATCH 4 — Employer Experience", BATCH4)
b5 = print_section("BATCH 5 — AT APIs + USSD + Payments", BATCH5)
b6 = print_section("BATCH 6 — Error Pages + Polish", BATCH6)

print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
print(f"  Batch 4: {'✅ COMPLETE' if b4 else '🔨 INCOMPLETE'}")
print(f"  Batch 5: {'✅ COMPLETE' if b5 else '🔨 INCOMPLETE'}")
print(f"  Batch 6: {'✅ COMPLETE' if b6 else '🔨 INCOMPLETE'}")
print()
