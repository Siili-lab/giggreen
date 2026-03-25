"""
GigGreen — Quick Rename Fix
Finishes the 3 renames that failed because Windows won't overwrite with os.rename().
Uses os.replace() which does allow overwriting.
Run from your GigGreen folder.
"""
import os, sys

folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
os.chdir(folder)

FIXES = [
    ("auth (1).py",     "auth.py",     "Full auth routes (193 lines)"),
    ("worker (1).py",   "worker.py",   "Full worker model (185 lines)"),
    ("employer (1).py", "employer.py", "Full employer model (58 lines)"),
]

print()
for src, dst, note in FIXES:
    if not os.path.exists(src):
        print(f"  ⚠️  NOT FOUND : {src} — skipping")
        continue
    try:
        os.replace(src, dst)   # overwrites dst on Windows without complaint
        print(f"  ✅  REPLACED  : {src}  →  {dst}  ({note})")
    except Exception as e:
        print(f"  ❌  ERROR     : {src} → {dst} : {e}")

# Clean up the .bak stubs — they're the tiny placeholder files, safe to delete
for bak in ["auth.py.bak", "worker.py.bak", "employer.py.bak"]:
    if os.path.exists(bak):
        size = os.path.getsize(bak)
        os.remove(bak)
        print(f"  🗑️  DELETED   : {bak} ({size}B stub — no longer needed)")

print("\n  ✅  Done. Now copy setup_giggreen.py into this folder and run it.\n")
