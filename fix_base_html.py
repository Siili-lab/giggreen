"""
GigGreen — Fix Script
Replaces all occurrences of 'gigs.feed' with 'gigs.list_gigs' in templates/base.html
"""

import re

filepath = "templates/base.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

occurrences = content.count("gigs.feed")
print(f"Found {occurrences} occurrence(s) of 'gigs.feed'")

if occurrences == 0:
    print("Nothing to fix!")
else:
    fixed = content.replace("gigs.feed", "gigs.list_gigs")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed)
    print(f"✅ Fixed {occurrences} occurrence(s) — 'gigs.feed' → 'gigs.list_gigs'")

# Verify
with open(filepath, "r", encoding="utf-8") as f:
    verify = f.read()

remaining = verify.count("gigs.feed")
correct = verify.count("gigs.list_gigs")
print(f"✅ Verification: {correct} correct endpoint(s), {remaining} remaining issue(s)")
