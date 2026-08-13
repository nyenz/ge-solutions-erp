# PATH: fix.py
# PHASE 3C - ADD ROLE_DIRECTOR TO SETTINGS PAGE UI (ADDITIVE)
# Run from project root: py fix.py
#
# SCOPE OF THIS PATCH:
#
# Adds 'ROLE_DIRECTOR' as a selectable option in the "INITIALIZE IDENTITY"
# provisioning modal's rank dropdown, and updates the operator card label
# so a Director shows "TIER 2: DIRECTOR" instead of falling through to
# "TIER 3: OPERATOR".
#
# 100% ADDITIVE:
#   - Root can now provision a brand new operator directly as ROLE_DIRECTOR
#     from the UI (previously only possible via Postman).
#   - Existing ROLE_ADMIN / ROLE_MANAGER accounts are completely unaffected.
#
# KNOWN LIMITATION (not fixed in this patch, flagged for awareness):
#   The promote/demote arrow button (FiArrowUp / FiArrowDown) on each
#   operator card only toggles between ROLE_ADMIN and ROLE_MANAGER. If
#   clicked on an existing ROLE_DIRECTOR account, it will demote them to
#   ROLE_ADMIN (since ROLE_DIRECTOR is treated as "not ROLE_ADMIN" by that
#   toggle's logic). This is a pre-existing 2-tier toggle that was never
#   designed for 3+ tiers. Rebuilding it into a proper rank <select> is
#   out of scope for this quick patch -- flagging as Phase 3D if desired.
#   For now, promote a Director back up via Postman if this happens.
#
# TEST PLAN:
#   1. Log in as admin_root, go to Settings.
#   2. Click "PROVISION NEW OPERATOR" -- confirm the rank dropdown now
#      shows MANAGER / ADMIN / DIRECTOR.
#   3. Provision a test account as ROLE_DIRECTOR, confirm the temp
#      password modal appears as normal.
#   4. Confirm the new operator's card in the Governance Ledger reads
#      "TIER 2: DIRECTOR".
#   5. Confirm existing ROLE_ADMIN and ROLE_MANAGER cards are unchanged.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

print("Starting Phase 3C Patch - ROLE_DIRECTOR in Settings UI...")
print("-" * 60)

path = "erp-frontend/src/pages/settings/SettingsPage.jsx"

# ---- 1. Add ROLE_DIRECTOR to the provisioning modal's rank dropdown ----
patch_file(path,
    """<HardwareSelect label="INITIAL RANK" options={['ROLE_MANAGER', 'ROLE_ADMIN']} value={newOpData.role} onChange={v => setNewOpData({...newOpData, role: v})} />""",
    """<HardwareSelect label="INITIAL RANK" options={['ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR']} value={newOpData.role} onChange={v => setNewOpData({...newOpData, role: v})} />""",
    "SettingsPage.jsx provisioning dropdown (+DIRECTOR)")

# ---- 2. Show "TIER 2: DIRECTOR" label on operator cards ----
patch_file(path,
    """                                                    <span className={op.role === 'ROLE_ADMIN' ? styles.rankAdmin : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_ADMIN' ? 'TIER 2: ADMIN' : 'TIER 3: OPERATOR'}
                                                    </span>""",
    """                                                    <span className={(op.role === 'ROLE_ADMIN' || op.role === 'ROLE_DIRECTOR') ? styles.rankAdmin : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_DIRECTOR' ? 'TIER 2: DIRECTOR' : op.role === 'ROLE_ADMIN' ? 'TIER 2: ADMIN' : 'TIER 3: OPERATOR'}
                                                    </span>""",
    "SettingsPage.jsx operator card label (+DIRECTOR)")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If everything shows OK, run:")
print("git add -A && git commit -m 'feat: Phase 3C - ROLE_DIRECTOR in Settings UI' && git push")
print("")
print("REMINDER:")
print("  - The promote/demote arrow button still only toggles ADMIN <-> MANAGER.")
print("    Clicking it on a Director will demote them to Admin. Use Postman")
print("    to re-promote if that happens. Not fixed in this patch (see header).")
print("  - Test plan: provision a new operator as DIRECTOR from the dropdown,")
print("    confirm the temp password modal appears, and confirm their card")
print("    reads 'TIER 2: DIRECTOR' in the Governance Ledger.")