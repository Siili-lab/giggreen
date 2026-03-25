"""
GigGreen — Full Stack Connectivity Audit
Checks: Templates → Routes → Services → DB Tables → JS
Reports broken links across the entire stack
"""

import os
import re
import sqlite3

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH       = "giggreen.db"
TEMPLATE_DIRS = ["templates"]
ROUTE_FILES   = [
    "routes/auth.py", "routes/worker.py", "routes/employer.py",
    "routes/gigs.py", "routes/payments.py", "routes/sms.py", "routes/ussd.py",
]
SERVICE_FILES = [
    "services/at_sms.py", "services/at_ussd.py", "services/at_payments.py",
    "services/at_voice.py", "services/matching.py", "services/impact_calculator.py",
]
JS_FILES = [f"static/js/{f}" for f in [
    "main.js", "auth.js", "worker-dashboard.js", "gig-feed.js",
    "impact-score.js", "employer-dashboard.js",
]]

EXPECTED_TABLES = [
    "workers", "employers", "gigs", "applications",
    "payments", "sms_log", "ussd_sessions", "otps",
]

ISSUES  = []
PASSING = []

def ok(msg):   PASSING.append(msg)
def fail(msg): ISSUES.append(msg)

# ── Helpers ───────────────────────────────────────────────────────────────────

def read(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def find_all_templates():
    templates = []
    for root, _, files in os.walk("templates"):
        for f in files:
            if f.endswith(".html"):
                templates.append(os.path.join(root, f).replace("\\", "/"))
    return templates

def extract_url_fors(content):
    return re.findall(r"url_for\(['\"]([^'\"]+)['\"]", content)

def extract_fetch_urls(content):
    return re.findall(r'(?:fetch|apiFetch)\s*\(\s*["\']([^"\']+)["\']', content)

def extract_defined_endpoints(content):
    """Returns set of blueprint.function endpoint names from a route file."""
    bp_name = None
    match = re.search(r"(\w+)\s*=\s*Blueprint\s*\(\s*['\"](\w+)['\"]", content)
    if match:
        bp_name = match.group(2)

    endpoints = set()
    funcs = re.findall(r"@\w+_bp\.route\([^)]+\)\s*(?:@[^\n]+\n)*def (\w+)\(", content)
    if bp_name:
        for f in funcs:
            endpoints.add(f"{bp_name}.{f}")
    return endpoints

def extract_db_tables(content):
    return set(re.findall(r'(?:FROM|JOIN|INTO|UPDATE)\s+"?(\w+)"?', content, re.IGNORECASE))

def extract_service_functions(content):
    return set(re.findall(r"^def (\w+)\(", content, re.MULTILINE))

# ── 1. File existence ─────────────────────────────────────────────────────────

print("\n" + "="*65)
print("  GigGreen — Full Stack Connectivity Audit")
print("="*65)

print("\n[1] FILE EXISTENCE")
all_files = ROUTE_FILES + SERVICE_FILES + JS_FILES
for path in all_files:
    if os.path.exists(path):
        size = os.path.getsize(path)
        if size < 60:
            fail(f"EMPTY: {path} ({size}B)")
            print(f"  ❌  EMPTY    {path} ({size}B)")
        else:
            ok(f"EXISTS: {path}")
            print(f"  ✅  OK       {path} ({size}B)")
    else:
        fail(f"MISSING: {path}")
        print(f"  ❌  MISSING  {path}")

# ── 2. Collect all defined endpoints ─────────────────────────────────────────

print("\n[2] DEFINED ENDPOINTS")
all_endpoints = set()
all_endpoints.add("index")  # app.py root
all_endpoints.add("static")  # Flask built-in

for path in ROUTE_FILES:
    content = read(path)
    if content:
        eps = extract_defined_endpoints(content)
        for ep in sorted(eps):
            print(f"  ✅  {ep}")
        all_endpoints.update(eps)

# ── 3. Template → url_for checks ─────────────────────────────────────────────

print("\n[3] TEMPLATE url_for CHECKS")
templates = find_all_templates()
for tpl in sorted(templates):
    content = read(tpl)
    if not content:
        continue
    refs = extract_url_fors(content)
    for ref in refs:
        if ref == "static":
            continue
        if ref in all_endpoints:
            ok(f"{tpl} → {ref}")
        else:
            fail(f"BROKEN url_for: '{ref}' in {tpl}")
            print(f"  ❌  BROKEN   url_for('{ref}') in {tpl}")

broken_tpl = [i for i in ISSUES if "BROKEN url_for" in i]
if not broken_tpl:
    print("  ✅  All url_for references resolve correctly")

# ── 4. JS fetch → route checks ────────────────────────────────────────────────

print("\n[4] JS FETCH → ROUTE CHECKS")

# Build URL map from routes
url_map = {}
for path in ROUTE_FILES:
    content = read(path)
    if not content:
        continue
    bp_match = re.search(r"Blueprint\s*\(\s*['\"](\w+)['\"].*url_prefix\s*=\s*['\"]([^'\"]+)['\"]", content)
    bp_prefix = ""
    if bp_match:
        bp_prefix = bp_match.group(2).rstrip("/")
    routes = re.findall(r'@\w+_bp\.route\s*\(\s*["\']([^"\']+)["\']', content)
    for r in routes:
        full = bp_prefix + r
        url_map[full] = path

for js_path in JS_FILES:
    content = read(js_path)
    if not content:
        continue
    urls = extract_fetch_urls(content)
    for url in urls:
        matched = any(
            re.fullmatch(re.sub(r"<[^>]+>", "[^/]+", k), url)
            for k in url_map
        )
        if matched:
            ok(f"{js_path} → {url}")
            print(f"  ✅  OK       {js_path} → {url}")
        else:
            fail(f"UNMATCHED fetch: '{url}' in {js_path}")
            print(f"  ❌  UNMATCHED fetch('{url}') in {js_path}")

# ── 5. DB table checks ────────────────────────────────────────────────────────

print("\n[5] DATABASE TABLE CHECKS")
if not os.path.exists(DB_PATH):
    fail(f"DB not found: {DB_PATH}")
    print(f"  ❌  DB not found: {DB_PATH}")
else:
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {r[0] for r in cursor.fetchall()}
    conn.close()

    for table in EXPECTED_TABLES:
        if table in existing_tables:
            ok(f"TABLE: {table}")
            print(f"  ✅  {table}")
        else:
            fail(f"MISSING TABLE: {table}")
            print(f"  ❌  MISSING TABLE: {table}")

    # Check which tables routes actually query
    print("\n  Tables referenced in routes:")
    for path in ROUTE_FILES + SERVICE_FILES:
        content = read(path)
        if not content:
            continue
        tables = extract_db_tables(content)
        for t in sorted(tables):
            if t not in existing_tables and t not in ("VALUES", "SET"):
                fail(f"QUERY on missing table '{t}' in {path}")
                print(f"  ❌  '{t}' queried in {path} but not in DB")
            elif t in existing_tables:
                print(f"  ✅  '{t}' in {path}")

# ── 6. Service function checks ────────────────────────────────────────────────

print("\n[6] SERVICE → ROUTE IMPORT CHECKS")
service_funcs = {}
for path in SERVICE_FILES:
    content = read(path)
    if content:
        module = path.replace("/", ".").replace(".py", "")
        service_funcs[module] = extract_service_functions(content)

for path in ROUTE_FILES:
    content = read(path)
    if not content:
        continue
    imports = re.findall(r"from (services\.\w+) import (.+)", content)
    for module, names in imports:
        imported = [n.strip() for n in names.split(",")]
        available = service_funcs.get(module, set())
        for name in imported:
            if name in available:
                ok(f"{path} imports {module}.{name}")
                print(f"  ✅  {path} ← {module}.{name}()")
            else:
                fail(f"BROKEN IMPORT: {name} from {module} in {path}")
                print(f"  ❌  BROKEN: '{name}' not found in {module} (used in {path})")

# ── Summary ───────────────────────────────────────────────────────────────────

print("\n" + "="*65)
print("  SUMMARY")
print("="*65)
print(f"  ✅  {len(PASSING)} checks passed")
print(f"  ❌  {len(ISSUES)} issue(s) found\n")
for i, issue in enumerate(ISSUES, 1):
    print(f"  {i:2}. {issue}")
print()
