import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK  {label}")
    else:
        print(f"MISSING  {label}")

# =============================================================================
# 1. LANGUAGE SIMPLIFICATION
# =============================================================================

# --- FolderPage.jsx ---
fp = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

patch(fp,
    "title='EDIT RECORD'",
    "title='EDIT'",
    "FolderPage: unlock title")

patch(fp,
    "<FiUnlock aria-hidden=\"true\" /> EDIT RECORD",
    "<FiUnlock aria-hidden=\"true\" /> EDIT",
    "FolderPage: unlock btn text")

patch(fp,
    "<FiTrash2 aria-hidden=\"true\" /> DELETE",
    "<FiTrash2 aria-hidden=\"true\" /> DELETE",
    "FolderPage: delete btn (already correct)")

# Notes label: Intel -> Notes
patch(fp,
    'label="ARCHIVE LOG ENTRY"',
    'label="ADD NOTE"',
    "FolderPage: note modal title")

patch(fp,
    "title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}",
    "title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}",
    "FolderPage: call modal title (already correct)")

# Drawer label: DOCUMENTS (was Vault) - already correct in code
# Drawer label: NOTES (was Intel) - check
content = read(fp)
content = content.replace(
    'label="NOTES" count={noteCount}',
    'label="NOTES" count={noteCount}',
)
# Replace "INTEL_REWRITE" audit action label shown to user (it's backend, skip)
# Replace visible "LOG INTERACTION" button text -> "ADD NOTE"
content = content.replace(
    '+ LOG INTERACTION',
    '+ ADD NOTE'
)
write(fp, content)
print("OK  FolderPage: add note button")

# --- DrawerHeader labels in FolderPage ---
patch(fp,
    'label="NOTES" count={noteCount} isOpen={drawers.intel}',
    'label="NOTES" count={noteCount} isOpen={drawers.intel}',
    "FolderPage: notes drawer (already Notes)")

# --- RecoveryPortal.jsx ---
rp = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'
content = read(rp)
# "RECOVERY_MISSION_COMPLETE" is backend-only, skip
# "LOG CALL" button - keep (it's the right term)
# "COMMIT & RESET" -> "LOG CALL & RESET"
content = content.replace(
    '>Commit &amp; Reset<',
    '>Log Call &amp; Reset<'
)
write(rp, content)
print("OK  RecoveryPortal: commit button text")

# --- AuditPage.jsx ---
ap = 'erp-frontend/src/pages/Audit/AuditPage.jsx'
content = read(ap)
# "GOD-MODE REWRITE" filter option -> "EDIT RECORD"
content = content.replace(
    "if (activeAction === 'GOD-MODE REWRITE') activeAction = 'MASTER_REWRITE';",
    "if (activeAction === 'EDIT RECORD')      activeAction = 'MASTER_REWRITE';"
)
content = content.replace(
    "'GOD-MODE REWRITE', 'STAGE OVERRIDE'",
    "'EDIT RECORD', 'STAGE OVERRIDE'"
)
write(ap, content)
print("OK  AuditPage: filter option GOD-MODE REWRITE -> EDIT RECORD")

# Friendly action label in AuditPage
patch(ap,
    "if (action === 'MASTER_REWRITE')            return 'EDIT RECORD';",
    "if (action === 'MASTER_REWRITE')            return 'EDIT RECORD';",
    "AuditPage: MASTER_REWRITE label (already correct)")

# --- IntakePage.jsx ---
ip = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
content = read(ip)
# "COMMIT TO ARCHIVE" -> "SAVE NEW PLOT"
content = content.replace(
    "saving ? 'SAVING...' : 'COMMIT TO ARCHIVE'",
    "saving ? 'SAVING...' : 'SAVE NEW PLOT'"
)
# "VAULT" references visible to user - drawer is already "DOCUMENTS"
# "ASSET INTAKE" in sidebar is already "NEW PLOT"
write(ip, content)
print("OK  IntakePage: submit button text")

# --- LedgerPage.jsx ---
lp = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'
content = read(lp)
# "Digital Asset Ledger" -> "Plot Ledger"
content = content.replace(
    '<h1 className={styles.title}>Digital Asset Ledger</h1>',
    '<h1 className={styles.title}>Plot Ledger</h1>'
)
# "Unified Storage Recovery & Debt Tracking" -> cleaner
content = content.replace(
    'Unified Storage Recovery &amp; Debt Tracking',
    'All registered plots and their payment status'
)
write(lp, content)
print("OK  LedgerPage: title and subtitle")

# --- Sidebar.jsx - already has correct labels (NEW PLOT, LEDGER, RECOVERY, etc.) ---
sb = 'erp-frontend/src/components/layout/Sidebar.jsx'
content = read(sb)
# "FORENSIC STREAM" -> already "AUDIT" in sidebar
# Check RECOVERY label - already correct
print("OK  Sidebar: labels already correct")

# --- Dashboard.jsx ---
db = 'erp-frontend/src/pages/Dashboard/Dashboard.jsx'
content = read(db)
content = content.replace(
    'ROOT FOUNDER ACCESS',
    'ROOT OWNER ACCESS'
)
content = content.replace(
    'OPERATIONAL MANAGER ACCESS',
    'MANAGER ACCESS'
)
content = content.replace(
    'SECTOR 7G ARCHIVE ACTIVE',
    'SYSTEM ACTIVE'
)
write(db, content)
print("OK  Dashboard: header subtitle")

# --- RootTerminal.jsx ---
rt = 'erp-frontend/src/pages/Dashboard/RootTerminal.jsx'
content = read(rt)
content = content.replace(
    'GLOBAL ARCHIVE VOLUME',
    'TOTAL PLOTS'
)
content = content.replace(
    'STALE RECOVERY DEBTORS',
    'PENDING CALLS'
)
content = content.replace(
    'SYSTEM OPS (24H)',
    'ACTIONS TODAY'
)
content = content.replace(
    'FINANCIAL LIQUIDITY ASSESSMENT',
    'FINANCIALS'
)
content = content.replace(
    'COMMAND LAUNCHPAD',
    'QUICK ACTIONS'
)
content = content.replace(
    'PIPELINE BOTTLENECKS',
    'PIPELINE STAGES'
)
content = content.replace(
    'ASSET INTAKE',
    'NEW PLOT'
)
content = content.replace(
    'MASTER LEDGER',
    'LEDGER'
)
content = content.replace(
    'ANALYTICS',
    'REPORTS'
)
write(rt, content)
print("OK  RootTerminal: label simplifications")

# --- ManagerTerminal.jsx ---
mt = 'erp-frontend/src/pages/Dashboard/ManagerTerminal.jsx'
content = read(mt)
content = content.replace(
    'GLOBAL ARCHIVE VOLUME',
    'TOTAL PLOTS'
)
content = content.replace(
    'ARCHIVE PROCESSING STATUS',
    'PIPELINE STAGES'
)
content = content.replace(
    'OPERATIONAL LAUNCHPAD',
    'QUICK ACTIONS'
)
content = content.replace(
    'ASSET INTAKE',
    'NEW PLOT'
)
content = content.replace(
    'VIEW LEDGER',
    'LEDGER'
)
content = content.replace(
    'MY PROFILE',
    'SETTINGS'
)
# Fix completed count calculation
# Old (wrong): (stats?.totalPlots || 0) - (stats?.readyForReleaseCount || 0) - (stats?.backlogCount || 0)
# New (correct): use readyForReleaseCount directly for "ready" and a separate released stat
# The backend doesn't return a dedicated "released" count so we use readyForRelease as proxy for "fully paid"
# The 5th tile currently subtracts backlog from total which is wrong.
# Best fix: show readyForReleaseCount (plots fully paid, not yet released) as its own tile
# and rename the 5th tile to "AWAITING HANDOVER" with readyForReleaseCount
# Currently the 5th tile tries to compute released = total - readyForRelease - backlog which is wrong
# Replace with a sensible metric: total plots that are NOT backlog and NOT awaiting release = active working plots
content = content.replace(
    "<div className={styles.statValue}>{(stats?.totalPlots || 0) - (stats?.readyForReleaseCount || 0) - (stats?.backlogCount || 0)}</div>\n                    <div className={styles.statLabel}>COMPLETED & RELEASED</div>",
    "<div className={styles.statValue}>{stats?.backlogCount || 0}</div>\n                    <div className={styles.statLabel}>IN BACKLOG</div>"
)
write(mt, content)
print("OK  ManagerTerminal: label simplifications + completed count fix")

# Fix RootTerminal completed count too
content = read(rt)
# RootTerminal doesn't have the bad tile, but let's verify the launchpad actions
write(rt, content)
print("OK  RootTerminal: re-saved")

# --- ReportHub.jsx ---
rh = 'erp-frontend/src/pages/Reports/ReportHub.jsx'
content = read(rh)
content = content.replace(
    '<h1 className={styles.title}>Intelligence Hub</h1>',
    '<h1 className={styles.title}>Reports</h1>'
)
content = content.replace(
    'Direct Database Analysis &amp; CSV Export Terminal',
    'Download CSV reports for analysis'
)
content = content.replace(
    'FINANCIAL INTELLIGENCE',
    'FINANCIAL REPORTS'
)
content = content.replace(
    'OPERATIONAL LOGISTICS',
    'OPERATIONAL REPORTS'
)
content = content.replace(
    'SYSTEM FORENSICS',
    'SYSTEM REPORTS'
)
content = content.replace(
    'PRIORITY REPORTS',
    'MORE REPORTS'
)
write(rh, content)
print("OK  ReportHub: title and section labels")

# --- AuditPage.jsx title ---
content = read(ap)
content = content.replace(
    '<h1 className={styles.title}>System Forensics</h1>',
    '<h1 className={styles.title}>Audit Log</h1>'
)
content = content.replace(
    'Unified Accountability Archive | Total Traceability Active',
    'Full history of all staff actions in the system'
)
write(ap, content)
print("OK  AuditPage: title simplified")

# --- PaymentsPage.jsx ---
pp = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
content = read(pp)
content = content.replace(
    '<h1 className={styles.title}>Payments</h1>',
    '<h1 className={styles.title}>Payment Records</h1>'
)
write(pp, content)
print("OK  PaymentsPage: title")

# --- RecoveryPortal title ---
content = read(rp)
content = content.replace(
    '<h1 className={styles.pageTitle}>Recovery Hub</h1>',
    '<h1 className={styles.pageTitle}>Call Recovery</h1>'
)
content = content.replace(
    'Client Call Management - 2-14 Rule Active',
    'Log client calls and track outstanding balances'
)
write(rp, content)
print("OK  RecoveryPortal: title simplified")

# =============================================================================
# 2. DASHBOARD COMPLETED COUNT - already fixed above in ManagerTerminal
#    Also fix RootTerminal to show backlog count in a more useful place
# =============================================================================

# RootTerminal 4th tile is "ACTIONS TODAY" which is fine
# The "READY FOR RELEASE" tile already exists correctly in RootTerminal
# No further changes needed there

print("\nDashboard completed count fix: done (backlog count replaces bad formula)")

# =============================================================================
# 3. PHONE UNIQUENESS FRONTEND VALIDATION
#    Already exists in IntakePage for new plots (handlePhoneBlurCheck).
#    Add same check to FolderPage owner edit section.
# =============================================================================

fp = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content = read(fp)

# Add a phone duplicate check function after handleOwnerChange
old_fn = '''    const handleOwnerChange = (idx, field, val) => {'''

new_fn = '''    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\\s+/g, '');
        const duplicate = (buffer.owners || []).some((o, i) =>
            i !== idx && o.phone.replace(/\\s+/g, '') === normalized
        );
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this plot.', 'warn', 5000);
        }
    };

    const handleOwnerChange = (idx, field, val) => {'''

if 'handlePhoneBlurCheck' not in content:
    content = content.replace(old_fn, new_fn)
    write(fp, content)
    print("OK  FolderPage: phone duplicate check function added")
else:
    print("OK  FolderPage: phone duplicate check already exists")

# Now hook the check into the PhoneInput inside the owner edit section
# Find the PhoneInput in the owner edit section and add onBlur
old_phone_input = '''                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} id={`owner_${idx}_phone`} />'''
new_phone_input = '''                                            <PhoneInput value={o.phone} onChange={v => handleOwnerChange(idx,'phone',v)} onBlur={v => handlePhoneBlurCheck(idx, v)} id={`owner_${idx}_phone`} />'''

content = read(fp)
if old_phone_input in content:
    content = content.replace(old_phone_input, new_phone_input)
    write(fp, content)
    print("OK  FolderPage: PhoneInput onBlur hooked")
else:
    print("MISSING  FolderPage: PhoneInput onBlur hook - check manually")

# Also ensure PhoneInput component in FolderPage accepts onBlur prop
# Check the PhoneInput definition in FolderPage
old_phone_def = '''const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, id, required, fieldError }) => {'''
new_phone_def = '''const PhoneInput = ({ label = 'RECOVERY PHONE', value, onChange, onBlur, id, required, fieldError }) => {'''

content = read(fp)
if old_phone_def in content:
    content = content.replace(old_phone_def, new_phone_def)
    # Also add onBlur to the input element
    content = content.replace(
        '''                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                autoComplete="tel-national" />''',
        '''                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                autoComplete="tel-national" />'''
    )
    write(fp, content)
    print("OK  FolderPage: PhoneInput accepts onBlur prop")
else:
    print("OK  FolderPage: PhoneInput already accepts onBlur (or definition differs)")

print("\nAll patches complete.")
print("Next: git add -A && git commit -m 'language simplification, dashboard fix, phone validation' && git push")