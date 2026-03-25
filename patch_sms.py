"""
GigGreen — Patch: Add missing SMS functions to services/at_sms.py
Adds: send_application_alert, send_completion_alert
Also fixes: routes importing 'send_otp as at_send_otp' — no rename needed,
            we just ensure the import alias works (send_otp exists already).
"""

import os

TARGET = "services/at_sms.py"

NEW_FUNCTIONS = '''

def send_application_alert(db, phone: str, gig_title: str, worker_name: str) -> bool:
    """Notify an employer that a worker has applied for their gig."""
    message = (
        f"GigGreen: {worker_name} has applied for '{gig_title}'. "
        f"Log in to review and confirm. giggreen.app/employer/dashboard"
    )
    return _send(db, [phone], message)


def send_completion_alert(db, phone: str, gig_title: str, worker_name: str) -> bool:
    """Notify an employer that a worker has marked a gig as complete."""
    message = (
        f"GigGreen: {worker_name} has marked '{gig_title}' as complete. "
        f"Log in to confirm and release payment. giggreen.app/employer/dashboard"
    )
    return _send(db, [phone], message)
'''

if not os.path.exists(TARGET):
    print(f"❌ File not found: {TARGET}")
    exit(1)

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

# Check what's already there
for fn in ["send_application_alert", "send_completion_alert"]:
    if fn in content:
        print(f"⚠️  {fn} already exists — skipping")
        NEW_FUNCTIONS = NEW_FUNCTIONS.replace(
            f"\ndef {fn}", f"\n# SKIPPED (already exists): {fn}\n# def {fn}"
        )

# Append before the _send function so ordering makes sense
INSERT_BEFORE = "\ndef _send("
if INSERT_BEFORE not in content:
    # Just append at end
    patched = content + NEW_FUNCTIONS
else:
    patched = content.replace(INSERT_BEFORE, NEW_FUNCTIONS + INSERT_BEFORE)

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(patched)

print(f"✅ Patched {TARGET}")
print(f"   + send_application_alert()")
print(f"   + send_completion_alert()")
print()

# Also check routes/auth.py for the alias import issue
AUTH = "routes/auth.py"
if os.path.exists(AUTH):
    with open(AUTH, "r", encoding="utf-8") as f:
        auth_content = f.read()
    
    if "send_otp as at_send_otp" in auth_content:
        # The alias is fine Python — send_otp exists so this will work.
        # But let's verify it's called as at_send_otp() in the file
        if "at_send_otp(" in auth_content:
            print(f"✅ routes/auth.py: 'send_otp as at_send_otp' alias is used correctly")
        else:
            print(f"⚠️  routes/auth.py imports 'send_otp as at_send_otp' but never calls at_send_otp()")
    else:
        print(f"✅ routes/auth.py: no alias issue found")

print()
print("Run 'python audit.py' to verify all issues are resolved.")
