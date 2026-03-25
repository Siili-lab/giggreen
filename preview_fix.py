import os

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

root = os.path.abspath(".")
print()
print(f"{'FILE':<28} {'ROOT SIZE':>10}   {'DEST SIZE':>10}   ACTION")
print("-" * 70)

for src_name, rel_dest in FILE_MAP.items():
    src  = os.path.join(root, src_name)
    dest = os.path.join(root, rel_dest.replace("/", os.sep))

    src_size  = os.path.getsize(src)  if os.path.exists(src)  else None
    dest_size = os.path.getsize(dest) if os.path.exists(dest) else None

    src_str  = f"{src_size}B"  if src_size  is not None else "MISSING"
    dest_str = f"{dest_size}B" if dest_size is not None else "MISSING"

    if src_size is None:
        action = "⚠️  no root file"
    elif dest_size is None:
        action = "✅  will COPY (no dest)"
    elif src_size > dest_size:
        action = f"⚠️  will OVERWRITE stub"
    elif src_size == dest_size:
        action = "🟡  same size — skip?"
    else:
        action = "❌  dest BIGGER than root!"

    print(f"{src_name:<28} {src_str:>10}   {dest_str:>10}   {action}")