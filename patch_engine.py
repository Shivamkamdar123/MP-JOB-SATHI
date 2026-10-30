"""Patch engine.py:
1. Insert compute_effective_status before get_for_you_feed.
2. Rewrite the body of get_for_you_feed to skip expired notices and add effective_status.
3. Add compute_effective_status to __all__.
Run from repo root.
"""
import re
import sys
from pathlib import Path

path = Path("backend/app/eligibility/engine.py")
src = path.read_text(encoding="utf-8")

# ------------------------------------------------------------------ guard
if "compute_effective_status" in src:
    print("Already patched – compute_effective_status found. Nothing to do.")
    sys.exit(0)

# ------------------------------------------------------------------ 1. Insert new function before get_for_you_feed
NEW_FUNC = '''\
def compute_effective_status(notification: GovtNotification, today: "str | date | None" = None) -> str:
    """Return a display-safe status for a notification.

    * "closed"       - notification.status is "closed" OR last_date is past
    * "closing_soon" - last_date is within the next 7 days (inclusive)
    * "open"         - everything else (including no last_date)
    """
    if notification.status == "closed":
        return "closed"
    effective_today = today if today is not None else date.today()
    remaining = days_left(notification, effective_today)
    if remaining is not None and remaining < 0:
        return "closed"
    if remaining is not None and remaining <= 7:
        return "closing_soon"
    return "open"


'''

ANCHOR = "def get_for_you_feed("
if ANCHOR not in src:
    print(f"ERROR: anchor '{ANCHOR}' not found in engine.py")
    sys.exit(1)

src = src.replace(ANCHOR, NEW_FUNC + ANCHOR, 1)

# ------------------------------------------------------------------ 2. Rewrite the loop body of get_for_you_feed
# Pattern: the inner for-loop body starts after 'if notification.status == "closed":\n            continue\n'
# and we need to inject the expiry check, then add effective_today / eff_status before ranked.append.

OLD_LOOP_BODY = (
    '        if notification.status == "closed":\r\n'
    '            continue\r\n'
    '        result = evaluate_eligibility(notification, profile)\r\n'
    '        remaining = days_left(notification, today if today is not None else date.today())\r\n'
    '        ranked.append({'
)

NEW_LOOP_BODY = (
    '        if notification.status == "closed":\r\n'
    '            continue\r\n'
    '        effective_today = today if today is not None else date.today()\r\n'
    '        remaining = days_left(notification, effective_today)\r\n'
    '        # D10 fix: skip notices whose deadline has already passed\r\n'
    '        if remaining is not None and remaining < 0:\r\n'
    '            continue\r\n'
    '        result = evaluate_eligibility(notification, profile)\r\n'
    '        eff_status = compute_effective_status(notification, effective_today)\r\n'
    '        ranked.append({'
)

# Try CRLF version first, then LF
if OLD_LOOP_BODY in src:
    src = src.replace(OLD_LOOP_BODY, NEW_LOOP_BODY, 1)
    print("Loop body patched (CRLF)")
else:
    OLD_LOOP_BODY_LF = OLD_LOOP_BODY.replace("\r\n", "\n")
    NEW_LOOP_BODY_LF = NEW_LOOP_BODY.replace("\r\n", "\n")
    if OLD_LOOP_BODY_LF in src:
        src = src.replace(OLD_LOOP_BODY_LF, NEW_LOOP_BODY_LF, 1)
        print("Loop body patched (LF)")
    else:
        print("ERROR: loop body anchor not found. Dumping surrounding context for debug:")
        idx = src.find("def get_for_you_feed")
        print(repr(src[idx:idx+600]))
        sys.exit(1)

# ------------------------------------------------------------------ 3. Add effective_status to the ranked.append dict
# The dict entry for "review_required" exists; we add "effective_status" after "verification_status"
OLD_VS_ENTRY = (
    '            "verification_status": (\r\n'
    '                "fixture" if notification.source_kind == "fixture"\r\n'
    '                else "verified" if notification.verified_by == "curator"\r\n'
    '                else "auto"\r\n'
    '            ),\r\n'
    '        })'
)
NEW_VS_ENTRY = (
    '            "verification_status": (\r\n'
    '                "fixture" if notification.source_kind == "fixture"\r\n'
    '                else "verified" if notification.verified_by == "curator"\r\n'
    '                else "auto"\r\n'
    '            ),\r\n'
    '            "effective_status": eff_status,\r\n'
    '        })'
)

if OLD_VS_ENTRY in src:
    src = src.replace(OLD_VS_ENTRY, NEW_VS_ENTRY, 1)
    print("effective_status field added (CRLF)")
else:
    OLD_VS_ENTRY_LF = OLD_VS_ENTRY.replace("\r\n", "\n")
    NEW_VS_ENTRY_LF = NEW_VS_ENTRY.replace("\r\n", "\n")
    if OLD_VS_ENTRY_LF in src:
        src = src.replace(OLD_VS_ENTRY_LF, NEW_VS_ENTRY_LF, 1)
        print("effective_status field added (LF)")
    else:
        print("ERROR: verification_status anchor not found")
        idx = src.find("verification_status")
        print(repr(src[max(0,idx-100):idx+400]))
        sys.exit(1)

# ------------------------------------------------------------------ 4. Add compute_effective_status to __all__
OLD_ALL = '"get_for_you_feed",'
NEW_ALL = '"get_for_you_feed",\r\n    "compute_effective_status",'
if OLD_ALL not in src:
    OLD_ALL = OLD_ALL.replace(",", ",")  # no-op but keep
    # try without carriage return
    pass
if OLD_ALL in src:
    src = src.replace(OLD_ALL, NEW_ALL, 1)
    print("__all__ updated")
else:
    print("ERROR: __all__ anchor not found")
    sys.exit(1)

# ------------------------------------------------------------------ write
path.write_text(src, encoding="utf-8")
print("engine.py written successfully.")

