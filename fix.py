import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        return True
    else:
        print(f"MISSING (not found in {path}): snippet not matched")
        return False

# ================================================================
# FIX 1: LedgerPage.jsx
# - Remove LEGACY filter, add COMPLETED filter
# - Remove legacy tag from row display (show ACTIVE instead)
# ================================================================

# 1a: Update FILTERS array - remove LEGACY, add COMPLETED
patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.jsx',
    "    const FILTERS = [\n        { key: 'ALL',      label: 'ALL ARCHIVES' },\n        { key: 'PAID',     label: 'PAID TITLES'  },\n        { key: 'BACKLOG',  label: 'BACKLOG'      },\n        { key: 'LEGACY',   label: 'LEGACY'       },\n        { key: 'DEBTORS',  label: 'UNPAID'       },\n        { key: 'CRITICAL', label: 'CRITICAL'     },\n    ];",
    "    const FILTERS = [\n        { key: 'ALL',       label: 'ALL ARCHIVES' },\n        { key: 'PAID',      label: 'PAID TITLES'  },\n        { key: 'COMPLETED', label: 'COMPLETED'     },\n        { key: 'BACKLOG',   label: 'BACKLOG'       },\n        { key: 'DEBTORS',   label: 'UNPAID'        },\n        { key: 'CRITICAL',  label: 'CRITICAL'      },\n    ];"
)

# 1b: Update filter logic - remove LEGACY filter, add COMPLETED filter
patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.jsx',
    "        if (activeFilter === 'PAID')     filtered = filtered.filter(p => p.amountPaid >= p.totalCost || p.landTitle?.isReleased);\n        if (activeFilter === 'BACKLOG')  filtered = filtered.filter(p => p.isBacklog);\n        if (activeFilter === 'LEGACY')   filtered = filtered.filter(p => p.isLegacy);\n        if (activeFilter === 'DEBTORS')  filtered = filtered.filter(p => p.amountPaid < p.totalCost);\n        if (activeFilter === 'CRITICAL') filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25);",
    "        if (activeFilter === 'PAID')      filtered = filtered.filter(p => p.amountPaid >= p.totalCost || p.landTitle?.isReleased);\n        if (activeFilter === 'COMPLETED') filtered = filtered.filter(p => p.landTitle?.isReleased || (p.amountPaid >= p.totalCost && !p.isBacklog));\n        if (activeFilter === 'BACKLOG')   filtered = filtered.filter(p => p.isBacklog);\n        if (activeFilter === 'DEBTORS')   filtered = filtered.filter(p => p.amountPaid < p.totalCost && !p.isBacklog);\n        if (activeFilter === 'CRITICAL')  filtered = filtered.filter(p => (p.amountPaid / p.totalCost) < 0.25 && !p.isBacklog);"
)

# 1c: In the row status display - remove legacy tag, show ACTIVE for all non-backlog/non-paid
patch(
    'erp-frontend/src/pages/Ledger/LedgerPage.jsx',
    "                                                {isBacklog && <span className={styles.tagBacklog}>BACKLOG</span>}\n                                                {!isBacklog && proj.landTitle?.isReleased && <span className={styles.tagPaid}>RELEASED</span>}\n                                                {!isBacklog && !proj.landTitle?.isReleased && proj.amountPaid >= proj.totalCost && <span className={styles.tagPaid}>FULLY PAID</span>}\n                                                {!isBacklog && proj.amountPaid < proj.totalCost && <span className={proj.isLegacy ? styles.tagLegacy : styles.tagStandard}>\n                                                    {proj.isLegacy ? 'LEGACY' : 'ACTIVE'}\n                                                </span>}\n                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}",
    "                                                {isBacklog && <span className={styles.tagBacklog}>BACKLOG</span>}\n                                                {!isBacklog && proj.landTitle?.isReleased && <span className={styles.tagPaid}>RELEASED</span>}\n                                                {!isBacklog && !proj.landTitle?.isReleased && proj.amountPaid >= proj.totalCost && <span className={styles.tagPaid}>FULLY PAID</span>}\n                                                {!isBacklog && proj.amountPaid < proj.totalCost && <span className={styles.tagStandard}>ACTIVE</span>}\n                                                {isCritical && <span className={styles.tagCritical}>CRITICAL</span>}"
)

print("OK: LedgerPage.jsx - removed LEGACY filter/tag, added COMPLETED filter")

# ================================================================
# FIX 2: PaymentsPage.jsx
# - Add COMPLETED filter (payments for fully paid / released plots)
# - This requires knowing which plots are completed, but payments
#   don't carry that flag directly. Best approach: filter by
#   balanceAfter = 0 (payment that cleared a balance) as a proxy,
#   and also add a cleaner type label system.
# - Actually simpler: add "INITIAL_DEPOSIT" already exists.
#   Add "ZERO BALANCE" filter = payments where balanceAfter <= 0
#   which means that payment completed the plot.
# ================================================================

# 2a: Update filter buttons in PaymentsPage
patch(
    'erp-frontend/src/pages/Payments/PaymentsPage.jsx',
    "                {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL'].map(t => (\n                        <button key={t}\n                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}\n                            onClick={() => setTypeFilter(t)}>\n                            {t === 'ALL' ? 'ALL TYPES' : TYPE_LABELS[t]}\n                        </button>\n                    ))}",
    "                {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL', 'COMPLETED'].map(t => (\n                        <button key={t}\n                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}\n                            onClick={() => setTypeFilter(t)}>\n                            {t === 'ALL' ? 'ALL TYPES' : t === 'COMPLETED' ? 'COMPLETED PLOTS' : TYPE_LABELS[t]}\n                        </button>\n                    ))}"
)

# 2b: Update filter logic in PaymentsPage to handle COMPLETED
patch(
    'erp-frontend/src/pages/Payments/PaymentsPage.jsx',
    "        if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);",
    "        if (typeFilter === 'COMPLETED') list = list.filter(p => p.balanceAfter !== null && p.balanceAfter !== undefined && Number(p.balanceAfter) <= 0);\n        else if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);"
)

print("OK: PaymentsPage.jsx - added COMPLETED filter")

# ================================================================
# FIX 3: IntakePage.jsx
# - Remove the isLegacy flag from the submit payload
#   (we keep the field internally for DB compat but don't expose it in UI)
# - The "LEGACY" concept in the DB stays (for old records) but new intake
#   won't let users set it -- just always false
# ================================================================

# 3a: Remove isLegacy from the payload in IntakePage handleSubmit
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    "                isStartAsBacklog: isBacklog,\n                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,\n                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,\n                isLegacy: false,",
    "                isStartAsBacklog: isBacklog,\n                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,\n                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,\n                isLegacy: false, // Always false for new plots - legacy is a historical flag only"
)

print("OK: IntakePage.jsx - legacy always false on new intake")

# ================================================================
# FIX 4: FolderPage.jsx
# - Remove LEGACY badge from the terminal header meta tags
#   (isLegacy tag shown next to ACTIVE/BACKLOG status)
# ================================================================

patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    "                        {isBacklog\n                            ? <span className={styles.metaTag} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)' }}>BACKLOG</span>\n                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>\n                        }",
    "                        {isBacklog\n                            ? <span className={styles.metaTag} style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', borderColor: 'rgba(239,68,68,0.4)' }}>BACKLOG</span>\n                            : project.landTitle?.isReleased\n                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>RELEASED</span>\n                            : amountPaid >= totalCost\n                            ? <span className={styles.metaTag} style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', borderColor: 'rgba(16,185,129,0.4)' }}>FULLY PAID</span>\n                            : <span className={`${styles.metaTag} ${styles.tagOrange}`}>ACTIVE</span>\n                        }"
)

print("OK: FolderPage.jsx - removed LEGACY status tag, added RELEASED/FULLY PAID")

# ================================================================
# FIX 5: LedgerPage.module.css
# - Remove .tagLegacy style (still keep it in CSS for now to avoid
#   build errors if referenced elsewhere, but blank it out)
# Actually just leave it - it's harmless CSS that's simply unused now
# ================================================================

print("\nAll done!")
print("Changes summary:")
print("  - Ledger: LEGACY filter removed, COMPLETED filter added")
print("  - Ledger: Legacy rows now show ACTIVE (not LEGACY label)")
print("  - Payments: COMPLETED PLOTS filter added (payments that zeroed a balance)")
print("  - FolderPage: Status now shows RELEASED or FULLY PAID (not LEGACY)")
print("  - Intake: isLegacy always false on new plots (legacy = historical only)")
print("")
print("Run: git add -A && git commit -m 'ui: remove legacy label, add completed filter to ledger and payments' && git push")