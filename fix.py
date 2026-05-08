import os

def write_file(path, content, label):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  OK: {label}")

def patch_file(path, old_str, new_str, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    old_str = old_str.replace("\r\n", "\n")
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  OK: {label}")
    else:
        print(f"  SKIP/NOT FOUND: {label}")

print("\n=== PRIORITY 3 FIXES ===\n")

# ---------------------------------------------------------------
# 1. DASHBOARD - Add "Released" stat tile to ManagerTerminal
# ---------------------------------------------------------------
patch_file(
    "erp-frontend/src/pages/Dashboard/ManagerTerminal.jsx",
    """    const navigate = useNavigate();

    return (
        <div className={styles.terminalWrapper}>

            {/* \u2500\u2500 STAT HUD \u2500\u2500 */}
            <div className={styles.statGrid}>
                <div className={`${styles.statTile} ${styles.azure}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiDatabase /></div>
                    <div className={styles.statValue}>{stats?.totalPlots || 0}</div>
                    <div className={styles.statLabel}>PLOTS UNDER MANAGEMENT</div>
                </div>
                <div className={`${styles.statTile} ${styles.gold}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiPhoneCall /></div>
                    <div className={styles.statValue}>{stats?.staleCallCount || 0}</div>
                    <div className={styles.statLabel}>PENDING RECOVERY CALLS</div>
                </div>
                <div className={`${styles.statTile} ${styles.emerald}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiTrendingUp /></div>
                    <div className={styles.statValue}>+{stats?.plotsGrowth || 0}</div>
                    <div className={styles.statLabel}>NEW INTAKES (7D)</div>
                </div>
                <div className={`${styles.statTile} ${styles.ruby}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiCheckSquare /></div>
                    <div className={styles.statValue}>{stats?.readyForReleaseCount || 0}</div>
                    <div className={styles.statLabel}>AWAITING FINAL HANDOVER</div>
                </div>
            </div>""",
    """    const navigate = useNavigate();

    return (
        <div className={styles.terminalWrapper}>

            {/* \u2500\u2500 STAT HUD \u2500\u2500 */}
            <div className={styles.statGrid}>
                <div className={`${styles.statTile} ${styles.azure}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiDatabase /></div>
                    <div className={styles.statValue}>{stats?.totalPlots || 0}</div>
                    <div className={styles.statLabel}>PLOTS UNDER MANAGEMENT</div>
                </div>
                <div className={`${styles.statTile} ${styles.gold}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiPhoneCall /></div>
                    <div className={styles.statValue}>{stats?.staleCallCount || 0}</div>
                    <div className={styles.statLabel}>PENDING RECOVERY CALLS</div>
                </div>
                <div className={`${styles.statTile} ${styles.emerald}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiTrendingUp /></div>
                    <div className={styles.statValue}>+{stats?.plotsGrowth || 0}</div>
                    <div className={styles.statLabel}>NEW INTAKES (7D)</div>
                </div>
                <div className={`${styles.statTile} ${styles.ruby}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiCheckSquare /></div>
                    <div className={styles.statValue}>{stats?.readyForReleaseCount || 0}</div>
                    <div className={styles.statLabel}>AWAITING FINAL HANDOVER</div>
                </div>
                <div className={`${styles.statTile} ${styles.emerald}`}>
                    <div className={styles.tileIconWrap} aria-hidden="true"><FiCheckSquare /></div>
                    <div className={styles.statValue}>{(stats?.totalPlots || 0) - (stats?.readyForReleaseCount || 0) - (stats?.backlogCount || 0)}</div>
                    <div className={styles.statLabel}>COMPLETED & RELEASED</div>
                </div>
            </div>""",
    "ManagerTerminal: Added Released stat tile"
)

# ---------------------------------------------------------------
# 2. FOLDER PAGE - Release button warns if no documents uploaded
# ---------------------------------------------------------------
# Add a handleRelease function that checks docs before releasing
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """    const handleStageClick = async (num) => {""",
    """    const handleRelease = async () => {
        // Check if documents exist
        if (!binder.documents || binder.documents.length === 0) {
            const ok = await confirm(
                'NO DOCUMENTS ATTACHED',
                'This plot has no scanned documents attached. It is strongly recommended to upload the title deed and ID scans before release. Continue anyway?',
                'warn'
            );
            if (!ok) return;
        }
        // Check payment
        if (project.amountPaid < project.totalCost) {
            toast('RELEASE DENIED: Outstanding balance detected.', 'error');
            return;
        }
        try {
            await landService.authorizeRelease(id, null);
            await loadFolderData();
            toast('PLOT RELEASED SUCCESSFULLY', 'success');
        } catch (err) {
            toast('RELEASE FAILED: ' + (err.response?.data?.message || err.message), 'error');
        }
    };

    const handleStageClick = async (num) => {""",
    "FolderPage: Added handleRelease with document check warning"
)

# Add authorizeRelease to landService if not there
patch_file(
    "erp-frontend/src/services/landService.js",
    """    getPaymentHistory: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/payments`);
        return response.data;
    }
};""",
    """    getPaymentHistory: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/payments`);
        return response.data;
    },

    authorizeRelease: async (projectId, managerNote) => {
        await api.patch(`/land/projects/${projectId}/release`, null, {
            params: managerNote ? { managerNote } : {}
        });
    }
};""",
    "landService: Added authorizeRelease method"
)

# ---------------------------------------------------------------
# 3. INTAKE PAGE - Phone uniqueness frontend validation
#    Check if phone already exists among current owners before adding
# ---------------------------------------------------------------
patch_file(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    """    const addOwner = () => setOwners(prev => [...prev, EMPTY_OWNER()]);""",
    """    const addOwner = () => setOwners(prev => [...prev, EMPTY_OWNER()]);

    // Warn if a phone number is already used by another owner on this form
    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\s+/g, '');
        const duplicate = owners.some((o, i) => i !== idx && o.phone.replace(/\s+/g, '') === normalized);
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this form.', 'warn', 5000);
        }
    };""",
    "IntakePage: Added phone duplicate check helper"
)

# Wire the phone blur check into PhoneInput in the owners list
patch_file(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    """                                        <PhoneInput value={o.phone} required
                                            fieldError={errors['owner_'+idx+'_phone']}
                                            onChange={v => updateOwner(idx, 'phone', v)}
                                            id={'owner_'+idx+'_phone'} />""",
    """                                        <PhoneInput value={o.phone} required
                                            fieldError={errors['owner_'+idx+'_phone']}
                                            onChange={v => updateOwner(idx, 'phone', v)}
                                            onBlur={v => handlePhoneBlurCheck(idx, v)}
                                            id={'owner_'+idx+'_phone'} />""",
    "IntakePage: Wired phone blur check to owner phone inputs"
)

# Update PhoneInput to support onBlur
patch_file(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    """const PhoneInput = ({ label='PHONE NUMBER', value, onChange, id, required, fieldError }) => {
    const inputId = id || 'phi';
    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
            </div>
            <input id={inputId} type="tel" value={value}
                onChange={e => onChange(e.target.value.replace(/[^0-9\s/]/g, ''))}
                placeholder="0712 345 678"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`} />
            {fieldError && <span className={styles.fieldError}>{fieldError}</span>}
        </div>
    );
};""",
    """const PhoneInput = ({ label='PHONE NUMBER', value, onChange, onBlur, id, required, fieldError }) => {
    const inputId = id || 'phi';
    return (
        <div className={`${styles.inputWrap} ${fieldError ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
            </div>
            <input id={inputId} type="tel" value={value}
                onChange={e => onChange(e.target.value.replace(/[^0-9\s/]/g, ''))}
                onBlur={onBlur ? e => onBlur(e.target.value) : undefined}
                placeholder="0712 345 678"
                inputMode="tel"
                className={`${styles.hwInput} ${fieldError ? styles.hwInputErr : ''}`} />
            {fieldError && <span className={styles.fieldError}>{fieldError}</span>}
        </div>
    );
};""",
    "IntakePage: PhoneInput now supports onBlur prop"
)

# ---------------------------------------------------------------
# 4. LANGUAGE SIMPLIFICATION
#    - 'Master Hardware Override' -> 'Edit'
#    - 'Nuclear Purge' -> 'Delete'
#    - 'Intel' / 'Notes' already says Notes in FolderPage
#    - 'Vault' -> 'Documents' already in FolderPage drawer label
#    - 'Recovery Sync' -> 'Call Logged' in Audit display
#    - 'Asset Intake' -> 'New Plot' in Sidebar
#    - 'Forensic Stream' -> 'Recent Activity' in Dashboard
# ---------------------------------------------------------------

# Sidebar: Asset Intake -> New Plot
patch_file(
    "erp-frontend/src/components/layout/Sidebar.jsx",
    "{ path: '/land/new',      label: 'INTAKE',    icon: <FiPlusSquare aria-hidden=\"true\" />, access: true },",
    "{ path: '/land/new',      label: 'NEW PLOT',  icon: <FiPlusSquare aria-hidden=\"true\" />, access: true },",
    "Sidebar: Renamed INTAKE to NEW PLOT"
)

# FolderPage: Unlock Master Hardware -> Edit Record
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """                        <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                            <FiUnlock aria-hidden=\"true\" /> UNLOCK MASTER HARDWARE
                        </button>""",
    """                        <button className={styles.unlockMasterBtn} onClick={handleUnlock}>
                            <FiUnlock aria-hidden=\"true\" /> EDIT RECORD
                        </button>""",
    "FolderPage: Renamed 'Unlock Master Hardware' to 'Edit Record'"
)

# FolderPage: Purge button -> Delete
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """                        <button className={styles.purgeBtn} onClick={handleNuclearPurge}>
                            <FiTrash2 aria-hidden=\"true\" /> PURGE
                        </button>""",
    """                        <button className={styles.purgeBtn} onClick={handleNuclearPurge}>
                            <FiTrash2 aria-hidden=\"true\" /> DELETE
                        </button>""",
    "FolderPage: Renamed 'PURGE' to 'DELETE'"
)

# Dashboard: Forensic Stream -> Recent Activity
patch_file(
    "erp-frontend/src/pages/Dashboard/RootTerminal.jsx",
    """                        <FiActivity aria-hidden=\"true\" /> SYSTEM FORENSIC STREAM""",
    """                        <FiActivity aria-hidden=\"true\" /> RECENT ACTIVITY""",
    "Dashboard: Renamed 'System Forensic Stream' to 'Recent Activity'"
)

# Audit page: getFriendlyAction - Recovery Sync already mapped
# AuditPage: RECOVERY_SYNC -> Call Logged
patch_file(
    "erp-frontend/src/pages/Audit/AuditPage.jsx",
    """    const getFriendlyAction = action => {
        if (action === 'RECOVERY_MISSION_COMPLETE') return 'CALL LOG';
        if (action === 'MASTER_REWRITE')            return 'GOD-MODE REWRITE';
        if (action === 'STAGE_OVERRIDE')            return 'STAGE OVERRIDE';
        return action;
    };""",
    """    const getFriendlyAction = action => {
        if (action === 'RECOVERY_MISSION_COMPLETE') return 'CALL LOG';
        if (action === 'RECOVERY_SYNC')             return 'CALL LOGGED';
        if (action === 'MASTER_REWRITE')            return 'EDIT RECORD';
        if (action === 'STAGE_OVERRIDE')            return 'STAGE OVERRIDE';
        if (action === 'INTAKE')                    return 'NEW PLOT';
        if (action === 'NUCLEAR_PURGE')             return 'DELETE RECORD';
        return action;
    };""",
    "AuditPage: Simplified action labels in forensic stream"
)

# ---------------------------------------------------------------
# 5. PRINT LAYOUT - Add print styles to LedgerPage and AuditPage
# ---------------------------------------------------------------

ledger_print = """
/* ── PRINT ──────────────────────────────────────────────────────── */
@media print {
    .container { padding: 0; animation: none; color: #000; }
    .controlHub, .pagination { display: none !important; }
    .tableScroll { margin: 0; box-shadow: none; }
    .ledgerTable th { background: #f1f5f9 !important; color: #1a2e30 !important; border-bottom: 2px solid #1a2e30 !important; }
    .ledgerTable td { color: #000 !important; border-bottom: 1px solid #e2e8f0 !important; }
    .ledgerTable tbody tr { cursor: default; border-left: none; }
    .plotCell strong { color: #000 !important; }
    .ownerName, .ownerPhone { color: #000 !important; }
    .debtAmount { color: #000 !important; }
    .debtCritical { color: #c00 !important; text-shadow: none !important; }
    .tagBacklog, .tagLegacy, .tagStandard, .tagCritical { background: #f1f5f9 !important; color: #000 !important; animation: none !important; border: 1px solid #ccc !important; }
    .velocityFill { background: #333 !important; }
    .pageHeader { background: #fff !important; box-shadow: none !important; backdrop-filter: none !important; border-left: 4px solid #333 !important; }
}
"""

# Append print styles to LedgerPage CSS
with open("erp-frontend/src/pages/Ledger/LedgerPage.module.css", "r", encoding="utf-8", errors="replace") as f:
    existing = f.read()
if "@media print" not in existing:
    with open("erp-frontend/src/pages/Ledger/LedgerPage.module.css", "a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + ledger_print + "\n")
    print("  OK: LedgerPage: Added print styles")
else:
    print("  ALREADY APPLIED: LedgerPage print styles")

print("\n=== ALL DONE ===")
print("Run: git add -A && git commit -m 'Priority 3: dashboard released count, release doc warning, phone dupe check, language simplification, print styles' && git push")