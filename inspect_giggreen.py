"""
GigGreen Code Inspector
Reads and compares the suspicious duplicate files so you can decide
which ones to keep before running setup_giggreen.py.
Nothing is moved or changed.
"""

import os
import sys

# ── Files to inspect and compare ────────────────────────────────────────────
# (file_a, file_b, label)
# file_a = the small stub  |  file_b = the suspected real version
COMPARISONS = [
    ("auth.py",       "auth (1).py",       "auth.py"),
    ("worker.py",     "worker (1).py",     "worker.py"),
    ("employer.py",   "employer (1).py",   "employer.py"),
    ("__init__.py",   "__init__ (1).py",   "__init__.py (services)"),
    ("__init__.py",   "__init__ (2).py",   "__init__.py (routes/models?)"),
]

# ── Standalone files worth previewing ───────────────────────────────────────
SOLO_INSPECT = [
    ("auth.css",    "Not in spec — may belong in components.css or main.css"),
    ("landing.css", "Not in spec — may belong in main.css"),
    ("env.example", "Should be renamed to .env.example"),
]

PREVIEW_LINES = 30  # how many lines to show per file


def divider(char="─", width=60):
    print(char * width)


def preview(filepath: str, label: str = None):
    label = label or filepath
    if not os.path.exists(filepath):
        print(f"  ⚠️  NOT FOUND: {filepath}")
        return

    size = os.path.getsize(filepath)
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ⚠️  Could not read {filepath}: {e}")
        return

    total_lines = len(lines)
    print(f"\n  📄  {label}")
    print(f"      Size: {size} bytes  |  Lines: {total_lines}")
    divider("·")
    for i, line in enumerate(lines[:PREVIEW_LINES], 1):
        print(f"  {i:>3} │ {line}", end="")
    if total_lines > PREVIEW_LINES:
        remaining = total_lines - PREVIEW_LINES
        print(f"\n  ... ({remaining} more lines — open file to see rest)")
    print()


def is_stub(filepath: str, threshold_bytes: int = 600) -> bool:
    if not os.path.exists(filepath):
        return False
    return os.path.getsize(filepath) <= threshold_bytes


def inspect(scan_dir: str):
    scan_dir = os.path.abspath(scan_dir)
    os.chdir(scan_dir)  # work relative to scan dir

    print(f"\n{'='*60}")
    print(f"  GigGreen Code Inspector")
    print(f"  Directory: {scan_dir}")
    print(f"{'='*60}")

    # ── Section 1: Side-by-side comparisons ─────────────────────────────────
    print(f"\n{'='*60}")
    print("  DUPLICATE FILE COMPARISONS")
    print(f"  (showing first {PREVIEW_LINES} lines of each)")
    print(f"{'='*60}")

    seen_pairs = set()

    for file_a, file_b, label in COMPARISONS:
        pair = (file_a, file_b)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        exists_a = os.path.exists(file_a)
        exists_b = os.path.exists(file_b)

        if not exists_a and not exists_b:
            continue  # neither exists, skip silently

        divider("═")
        print(f"\n  COMPARING: {label}")

        if exists_a and exists_b:
            size_a = os.path.getsize(file_a)
            size_b = os.path.getsize(file_b)

            stub_a = is_stub(file_a)
            stub_b = is_stub(file_b)

            if stub_a and not stub_b:
                print(f"\n  🚨 VERDICT: '{file_a}' looks like a stub ({size_a}B).")
                print(f"             '{file_b}' is larger ({size_b}B) — likely the real file.")
                print(f"             → Rename '{file_b}' to '{file_a}' before running setup.")
            elif stub_b and not stub_a:
                print(f"\n  🚨 VERDICT: '{file_b}' looks like a stub ({size_b}B).")
                print(f"             '{file_a}' is larger ({size_a}B) — likely the real file.")
            elif size_a == size_b:
                print(f"\n  ✅ VERDICT: Both files are the same size ({size_a}B) — likely identical.")
            else:
                print(f"\n  ⚠️  VERDICT: Both files have content. Manual review needed.")
                print(f"             '{file_a}' = {size_a}B  |  '{file_b}' = {size_b}B")

            print()
            preview(file_a, f"[A] {file_a}  ({size_a} bytes)")
            preview(file_b, f"[B] {file_b}  ({size_b} bytes)")

        elif exists_a:
            preview(file_a, f"[ONLY] {file_a}")
        elif exists_b:
            preview(file_b, f"[ONLY] {file_b}")

    # ── Section 2: Standalone unrecognised files ─────────────────────────────
    print(f"\n{'='*60}")
    print("  STANDALONE FILES TO REVIEW")
    print(f"{'='*60}")

    for filename, note in SOLO_INSPECT:
        if not os.path.exists(filename):
            continue
        divider("═")
        print(f"\n  ℹ️  NOTE: {note}")
        preview(filename, filename)

    # ── Section 3: Action checklist ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  ACTION CHECKLIST (do these before running setup_giggreen.py)")
    print(f"{'='*60}\n")

    actions = []

    for file_a, file_b, label in COMPARISONS:
        pair = (file_a, file_b)
        if not os.path.exists(file_a) or not os.path.exists(file_b):
            continue
        if is_stub(file_a) and not is_stub(file_b):
            actions.append(
                f"  🔁  Rename '{file_b}'  →  '{file_a}'  (replace the stub with the real file)"
            )

    if os.path.exists("env.example"):
        actions.append("  📝  Rename 'env.example'  →  '.env.example'")

    if os.path.exists("auth.css"):
        actions.append("  🎨  Decide where 'auth.css' styles belong (components.css? main.css?) then merge")

    if os.path.exists("landing.css"):
        actions.append("  🎨  Decide where 'landing.css' styles belong (main.css?) then merge")

    if actions:
        for a in actions:
            print(a)
    else:
        print("  ✅  No issues found — safe to run setup_giggreen.py")

    print()


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    inspect(folder)
