"""
GigGreen — Full Project Health Check
Checks: file existence, file size (stubs), encoding (null bytes), import errors
Run: python health_check.py
"""

import os
import sys
import importlib.util

# ── Expected files and minimum acceptable sizes ───────────────────────────────
EXPECTED = {
    # Core
    "app.py":                              500,
    "config.py":                           200,
    "requirements.txt":                     50,

    # Database
    "database/schema.sql":                 500,
    "database/seed.sql":                   200,

    # Models
    "models/__init__.py":                    0,
    "models/worker.py":                    500,
    "models/employer.py":                  300,
    "models/gig.py":                       500,
    "models/impact_score.py":              200,

    # Routes
    "routes/__init__.py":                    0,
    "routes/auth.py":                      500,
    "routes/worker.py":                    500,
    "routes/employer.py":                  500,
    "routes/gigs.py":                      500,
    "routes/payments.py":                  300,
    "routes/sms.py":                       200,
    "routes/ussd.py":                      200,

    # Services
    "services/__init__.py":                  0,
    "services/at_sms.py":                  300,
    "services/at_ussd.py":                 300,
    "services/at_payments.py":             300,
    "services/at_voice.py":                300,
    "services/matching.py":                500,
    "services/impact_calculator.py":       500,

    # Static JS
    "static/js/main.js":                   500,
    "static/js/auth.js":                   500,
    "static/js/worker-dashboard.js":       200,
    "static/js/gig-feed.js":              200,
    "static/js/impact-score.js":          200,
    "static/js/employer-dashboard.js":    200,

    # Templates
    "templates/base.html":                 500,
    "templates/landing.html":             500,
    "templates/auth/login.html":           500,
    "templates/auth/register.html":        500,
    "templates/worker/dashboard.html":     500,
    "templates/worker/profile.html":       500,
    "templates/worker/gig-feed.html":      500,
    "templates/worker/earnings.html":      500,
    "templates/employer/dashboard.html":   500,
    "templates/employer/blueprint.html":   500,
    "templates/employer/matches.html":     500,
    "templates/employer/impact-report.html": 500,
    "templates/errors/404.html":           200,
    "templates/errors/500.html":           200,
}

# ── Python files to import-check ──────────────────────────────────────────────
PY_IMPORTS = [
    "config",
    "models.worker",
    "models.employer",
    "models.gig",
    "models.impact_score",
    "routes.auth",
    "routes.worker",
    "routes.employer",
    "routes.gigs",
    "routes.payments",
    "routes.sms",
    "routes.ussd",
    "services.at_sms",
    "services.at_ussd",
    "services.at_payments",
    "services.at_voice",
    "services.matching",
    "services.impact_calculator",
]

OK   = lambda t: f"\033[32m{t}\033[0m"
WARN = lambda t: f"\033[33m{t}\033[0m"
ERR  = lambda t: f"\033[31m{t}\033[0m"
BOLD = lambda t: f"\033[1m{t}\033[0m"

issues = []

print()
print("=" * 65)
print(BOLD("  GigGreen — Full Project Health Check"))
print("=" * 65)

# ── 1. File existence + size + encoding ───────────────────────────────────────
print()
print(BOLD("  [1] FILE CHECK"))
print()

for rel_path, min_size in EXPECTED.items():
    abs_path = rel_path.replace("/", os.sep)

    if not os.path.exists(abs_path):
        print(f"  {ERR('MISSING')}  {rel_path}")
        issues.append(f"MISSING: {rel_path}")
        continue

    size = os.path.getsize(abs_path)

    if min_size > 0 and size < min_size:
        print(f"  {WARN('STUB   ')}  {rel_path}  ({size}B — expected >{min_size}B)")
        issues.append(f"STUB: {rel_path} ({size}B)")
        continue

    if rel_path.endswith(('.py', '.html', '.js', '.css', '.sql')):
        try:
            open(abs_path, 'r', encoding='utf-8').read()
        except UnicodeDecodeError:
            print(f"  {ERR('CORRUPT')}  {rel_path}  (null bytes / bad encoding)")
            issues.append(f"CORRUPT: {rel_path}")
            continue
        except Exception as e:
            print(f"  {ERR('ERROR  ')}  {rel_path}  {e}")
            issues.append(f"ERROR: {rel_path}")
            continue

    print(f"  {OK('OK     ')}  {rel_path}  ({size}B)")

# ── 2. Python import check ────────────────────────────────────────────────────
print()
print(BOLD("  [2] IMPORT CHECK"))
print()

sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("FLASK_APP", "app")

for module in PY_IMPORTS:
    try:
        importlib.import_module(module)
        print(f"  {OK('OK     ')}  import {module}")
    except Exception as e:
        short = str(e).split("\n")[0]
        print(f"  {ERR('FAIL   ')}  import {module}  — {short}")
        issues.append(f"IMPORT FAIL: {module} — {short}")

# ── 3. Summary ────────────────────────────────────────────────────────────────
print()
print("=" * 65)
print(BOLD("  SUMMARY"))
print("=" * 65)
print()

if not issues:
    print(f"  {OK('✅  All checks passed! Run: python app.py')}")
else:
    print(f"  {ERR(f'❌  {len(issues)} issue(s) found:')}")
    print()
    for i, issue in enumerate(issues, 1):
        print(f"  {i:>2}. {issue}")

print()
