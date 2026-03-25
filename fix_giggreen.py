"""
GigGreen Pre-Setup Fixer
Renames all the duplicate/misnamed files to their correct names
so that setup_giggreen.py can then move everything into the right folders.

Run this BEFORE setup_giggreen.py.
Nothing is moved to subfolders here — just renames in the current directory.
"""

import os
import sys
import shutil


# ── Renames to perform ───────────────────────────────────────────────────────
# (source, destination, reason)
RENAMES = [
    # Replace stubs with real files
    ("auth (1).py",     "auth.py",      "Replace stub with full auth routes (193 lines)"),
    ("worker (1).py",   "worker.py",    "Replace stub with full worker model (185 lines)"),
    ("employer (1).py", "employer.py",  "Replace stub with full employer model (58 lines)"),

    # __init__.py files — each goes to a different package
    # Current __init__.py says "# routes package" — keep as-is (correct name)
    # Rename the (1) and (2) variants to temp names first, then setup will sort folders
    ("__init__ (1).py", "__init__models.py",   "models package init — will be placed in models/"),
    ("__init__ (2).py", "__init__services.py", "services package init — will be placed in services/"),

    # env file
    ("env.example",     ".env.example", "Correct the missing dot prefix"),

    # CSS files — keep as separate files in static/css/ (not merged)
    ("auth.css",        "auth.css",     "Keep as-is — will be added to static/css/"),
    ("landing.css",     "landing.css",  "Keep as-is — will be added to static/css/"),
]

# ── Files setup_giggreen.py needs to know about ──────────────────────────────
# We'll also patch setup to handle the temp-named __init__ files and extra CSS.
EXTRA_MOVES = {
    "__init__models.py":   "models/__init__.py",
    "__init__services.py": "services/__init__.py",
    "auth.css":            "static/css/auth.css",
    "landing.css":         "static/css/landing.css",
}


def fix(scan_dir: str):
    scan_dir = os.path.abspath(scan_dir)
    os.chdir(scan_dir)

    print(f"\n{'='*60}")
    print(f"  GigGreen Pre-Setup Fixer")
    print(f"  Directory: {scan_dir}")
    print(f"{'='*60}\n")

    done    = []
    skipped = []
    errors  = []

    for src, dst, reason in RENAMES:
        if src == dst:
            # No rename needed — just confirm file exists
            if os.path.exists(src):
                print(f"  ✅  KEPT     {src:<30} ({reason})")
            else:
                print(f"  ⚠️  MISSING  {src:<30} (not found, skipping)")
            continue

        src_exists = os.path.exists(src)
        dst_exists = os.path.exists(dst)

        if not src_exists:
            skipped.append((src, "source not found"))
            print(f"  ⚠️  SKIP     {src:<30} → not found")
            continue

        if dst_exists:
            # Destination already exists — back it up before overwriting
            backup = dst + ".bak"
            shutil.copy2(dst, backup)
            print(f"  📦  BACKUP   {dst} → {backup}")

        try:
            os.rename(src, dst)
            done.append((src, dst))
            print(f"  🔁  RENAMED  {src:<30} → {dst}")
            print(f"              ({reason})")
        except Exception as e:
            errors.append((src, str(e)))
            print(f"  ❌  ERROR    {src}: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  ✅  Renamed  : {len(done)}")
    print(f"  ⚠️  Skipped  : {len(skipped)}")
    print(f"  ❌  Errors   : {len(errors)}")

    # ── Patch setup_giggreen.py to handle extra files ────────────────────────
    patch_setup(scan_dir)

    print(f"\n{'='*60}")
    print("  WHAT TO DO NEXT")
    print(f"{'='*60}")
    print("  1. python setup_giggreen.py   ← moves everything into correct folders")
    print()


def patch_setup(scan_dir: str):
    """
    Adds the extra files (renamed __init__ files, auth.css, landing.css)
    into setup_giggreen.py's PROJECT_FILES list so they get moved correctly.
    """
    setup_path = os.path.join(scan_dir, "setup_giggreen.py")
    if not os.path.exists(setup_path):
        print(f"\n  ℹ️  setup_giggreen.py not found — skipping auto-patch.")
        print(f"     Add these entries manually to PROJECT_FILES in setup_giggreen.py:")
        for src, dest in EXTRA_MOVES.items():
            print(f"       '{dest}',  # from {src}")
        return

    with open(setup_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Lines to inject into PROJECT_FILES
    inject_lines = []
    for src_temp, dest_path in EXTRA_MOVES.items():
        marker = f'"{dest_path}"'
        if marker not in content:
            inject_lines.append(f'    "{dest_path}",  # renamed from {src_temp}')

    if not inject_lines:
        print(f"\n  ✅  setup_giggreen.py already has all extra entries — no patch needed.")
        return

    # Also need to teach setup about the temp filenames
    # We do this by adding a FILENAME_OVERRIDES dict and logic, but
    # the simplest safe approach: just add to PROJECT_FILES so dirs are created,
    # and add a custom mapping so the mover finds them.

    # Inject after the last entry in PROJECT_FILES
    insert_after = '"services/at_voice.py",'
    if insert_after in content:
        injection = "\n" + "\n".join(inject_lines)
        content = content.replace(insert_after, insert_after + injection)

    # Also add EXTRA_FILENAME_MAP before the setup() function
    map_entries = "\n".join(
        f'    "{os.path.basename(dest)}": "{src}",'
        for src, dest in EXTRA_MOVES.items()
    )
    extra_map = f"""
# ── Extra filename mappings (temp names → project names) ────────────────────
# These handle files that were renamed by fix_giggreen.py
EXTRA_FILENAME_MAP = {{
{map_entries}
}}

"""
    # Inject before def setup(
    content = content.replace("def setup(", extra_map + "def setup(", 1)

    # Patch the move logic to check EXTRA_FILENAME_MAP
    old_move_logic = '        # 3. If a matching filename exists in the source dir, move it\n        if filename in existing:'
    new_move_logic = (
        '        # 3. If a matching filename exists in the source dir, move it\n'
        '        #    Check EXTRA_FILENAME_MAP for files with temp names\n'
        '        alt_name = EXTRA_FILENAME_MAP.get(filename)\n'
        '        if alt_name and alt_name in existing:\n'
        '            shutil.move(existing[alt_name], dest)\n'
        '            moved.append(f"{existing[alt_name]}  →  {rel_path}")\n'
        '            del existing[alt_name]\n'
        '            continue\n'
        '        if filename in existing:'
    )
    content = content.replace(old_move_logic, new_move_logic)

    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  🔧  PATCHED  setup_giggreen.py with {len(inject_lines)} extra file entries:")
    for line in inject_lines:
        print(f"       {line.strip()}")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    fix(folder)
