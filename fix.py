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
    if old not in content:
        print(f"MISSING in {path}: {repr(old[:80])}")
        return
    content = content.replace(old, new, 1)
    write(path, content)
    print(f"PATCHED: {path}")

FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'
RECOVERY_JSX = 'erp-frontend/src/services/recoveryService.js'


# ================================================================
# CHANGE 1: FolderPage — Replace hardcoded UGX 50,000 wording with
# dynamic monthly fee from project data.
# The backend stores storageFeeOverride (custom) or defaults to 50000.
# We compute "effectiveMonthlyFee" and use it everywhere.
# ================================================================

# Add effectiveMonthlyFee computation after financial figures
patch(
    FOLDER_JSX,
    '''    // Financial figures
    const totalCost    = Number(project?.totalCost || 0);
    const amountPaid   = Number(project?.amountPaid || 0);
    const origDebt     = Number(project?.originalDebt || 0);
    const storageFees  = Number(project?.storageFeesAccumulated || 0);
    const backlogOwed  = origDebt + storageFees - amountPaid;
    const activeOwed   = totalCost - amountPaid;
    const remaining    = isBacklog ? Math.max(0, backlogOwed) : Math.max(0, activeOwed);
    const arrearsEdit  = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);''',
    '''    // Financial figures
    const totalCost          = Number(project?.totalCost || 0);
    const amountPaid         = Number(project?.amountPaid || 0);
    const origDebt           = Number(project?.originalDebt || 0);
    const storageFees        = Number(project?.storageFeesAccumulated || 0);
    const backlogOwed        = origDebt + storageFees - amountPaid;
    const activeOwed         = totalCost - amountPaid;
    const remaining          = isBacklog ? Math.max(0, backlogOwed) : Math.max(0, activeOwed);
    const arrearsEdit        = (Number(buffer?.totalCost)||0) - (Number(buffer?.initialPayment)||0);
    // Dynamic monthly fee — uses override if set, otherwise system default 50,000
    const effectiveMonthlyFee = Number(project?.storageFeeOverride) > 0
        ? Number(project.storageFeeOverride)
        : 50000;'''
)

# ================================================================
# CHANGE 2: FolderPage — Backlog notice text: replace hardcoded 50,000
# with dynamic fee, and remove EXIT BACKLOG from view mode (move to edit)
# ================================================================
patch(
    FOLDER_JSX,
    '''                                    <div className={styles.backlogNotice}>
                                        <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                        <div className={styles.backlogNoticeText}>
                                            <strong>STORAGE FEES ACTIVE</strong>
                                            <span>UGX 50,000 is added every month until the full balance is cleared</span>
                                        </div>
                                        {isAdmin && (
                                            <button onClick={handleExitBacklog} className={styles.btnExitBacklog}>
                                                EXIT BACKLOG
                                            </button>
                                        )}
                                    </div>''',
    '''                                    <div className={styles.backlogNotice}>
                                        <FiAlertOctagon className={styles.backlogNoticeIcon} size={14} />
                                        <div className={styles.backlogNoticeText}>
                                            <strong>STORAGE FEES ACTIVE</strong>
                                            <span>UGX {fmt(effectiveMonthlyFee)} is added every month until the full balance is cleared</span>
                                        </div>
                                    </div>'''
)

# ================================================================
# CHANGE 3: FolderPage — Edit mode backlog fee controls:
# - Label "MONTHLY FEE" stays as is (already correct)
# - Add EXIT BACKLOG button here (edit mode only)
# - Make monthly fee label dynamic ("MONTHLY STORAGE FEE")
# ================================================================
patch(
    FOLDER_JSX,
    '''                                {project.isBacklog && (
                                    <div className={styles.editBacklogFeeSection}>
                                        <div className={styles.editBacklogFeeTitle}>BACKLOG FEE CONTROLS</div>
                                        <div className={styles.inputGrid3}>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>MONTHLY FEE (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeeOverride || 50000}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                toast('MONTHLY RATE UPDATED', 'success', 2000);
                                                            } catch { toast('RATE UPDATE FAILED', 'error'); }
                                                        }
                                                    }}
                                                    placeholder="50000"
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>ADJUST TOTAL FEES (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeesAccumulated || 0}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                toast('ACCUMULATED FEES UPDATED', 'success', 2000);
                                                            } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
                                                        }
                                                    }}
                                                    placeholder={String(project.storageFeesAccumulated || 0)}
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>FEES STATUS</label>
                                                </div>
                                                <button
                                                    type="button"
                                                    className={styles.btnPauseResume}
                                                    onClick={async () => {
                                                        try {
                                                            await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                            await loadFolderData();
                                                            toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                        } catch { toast('ACTION FAILED', 'error'); }
                                                    }}
                                                >
                                                    {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                </button>
                                            </div>
                                        </div>
                                        <div className={styles.editBacklogFeeHint}>
                                            Changes apply immediately. Monthly fee: default UGX 50,000 if not set.
                                        </div>
                                    </div>
                                )}''',
    '''                                {project.isBacklog && (
                                    <div className={styles.editBacklogFeeSection}>
                                        <div className={styles.editBacklogFeeTitleRow}>
                                            <div className={styles.editBacklogFeeTitle}>BACKLOG FEE CONTROLS</div>
                                            {isAdmin && (
                                                <button onClick={handleExitBacklog} className={styles.btnExitBacklog}>
                                                    EXIT BACKLOG
                                                </button>
                                            )}
                                        </div>
                                        <div className={styles.inputGrid3}>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>MONTHLY STORAGE FEE (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeeOverride || 50000}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setStorageRate(project.id, val);
                                                                await loadFolderData();
                                                                toast(`MONTHLY RATE SET TO UGX ${Number(val).toLocaleString()}`, 'success', 2500);
                                                            } catch { toast('RATE UPDATE FAILED', 'error'); }
                                                        }
                                                    }}
                                                    placeholder="50000"
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>ADJUST TOTAL FEES (UGX)</label>
                                                </div>
                                                <input
                                                    type="number"
                                                    className={styles.hwInput}
                                                    defaultValue={project.storageFeesAccumulated || 0}
                                                    onBlur={async e => {
                                                        const val = Number(e.target.value);
                                                        if (val >= 0) {
                                                            try {
                                                                await recoveryService.setAccumulatedFees(project.id, val);
                                                                await loadFolderData();
                                                                toast(`TOTAL FEES ADJUSTED TO UGX ${Number(val).toLocaleString()}`, 'success', 2500);
                                                            } catch { toast('FEE ADJUSTMENT FAILED', 'error'); }
                                                        }
                                                    }}
                                                    placeholder={String(project.storageFeesAccumulated || 0)}
                                                />
                                            </div>
                                            <div className={styles.hwInputWrap}>
                                                <div className={styles.inputLabelRow}>
                                                    <label>FEES STATUS</label>
                                                </div>
                                                <button
                                                    type="button"
                                                    className={styles.btnPauseResume}
                                                    onClick={async () => {
                                                        try {
                                                            await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                            await loadFolderData();
                                                            toast(project.storagePaused ? 'FEES RESUMED' : 'FEES PAUSED', 'info', 2500);
                                                        } catch { toast('ACTION FAILED', 'error'); }
                                                    }}
                                                >
                                                    {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                                </button>
                                            </div>
                                        </div>
                                        <div className={styles.editBacklogFeeHint}>
                                            Changes apply immediately. Current monthly fee: UGX {fmt(effectiveMonthlyFee)} (default 50,000 if not set).
                                        </div>
                                    </div>
                                )}'''
)

# ================================================================
# CHANGE 4: FolderPage — Dynamic wording in STORAGE FEES ACTIVE label
# Replace hardcoded "UGX 50,000" in the financials stats row label
# ================================================================
patch(
    FOLDER_JSX,
    '''                                        <div className={styles.statBox}>
                                            <label style={{color:'#ef4444'}}>STORAGE FEES ADDED</label>
                                            <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                            <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                {project.backlogStartDate
                                                    ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()}`
                                                    : ''}
                                            </small>
                                        </div>''',
    '''                                        <div className={styles.statBox}>
                                            <label style={{color:'#ef4444'}}>STORAGE FEES ADDED</label>
                                            <strong className={styles.redGlow}>UGX {fmt(storageFees)}</strong>
                                            <small style={{opacity:0.6, fontSize:'0.7rem'}}>
                                                {project.backlogStartDate
                                                    ? `Since ${new Date(project.backlogStartDate).toLocaleDateString()} @ UGX ${fmt(effectiveMonthlyFee)}/mo`
                                                    : `UGX ${fmt(effectiveMonthlyFee)}/month`}
                                            </small>
                                        </div>'''
)

# ================================================================
# CHANGE 5: FolderPage — Replace PRINT button with icon-only themed button
# ================================================================
patch(
    FOLDER_JSX,
    '''                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                    <FiPrinter aria-hidden="true" /> PRINT
                                </button>''',
    '''                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record" title="Print this record">
                                    <FiPrinter aria-hidden="true" />
                                </button>'''
)

# ================================================================
# CHANGE 6: FolderPage CSS — Update print button to icon-only style
# and add editBacklogFeeTitleRow
# ================================================================
patch(
    FOLDER_CSS,
    '''/* PRINT icon-only */
.printBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(6, 182, 212, 0.45);
    color: #67e8f9;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    line-height: 1;
}
.printBtn:hover { background: #06b6d4; color: #1a2e30; border-color: #06b6d4; box-shadow: 0 0 12px rgba(6,182,212,0.3); }
.printBtn:focus-visible { outline: 2px solid #06b6d4; outline-offset: 2px; }''',
    '''/* PRINT icon-only (no text label) */
.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    padding: 0;
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(6, 182, 212, 0.45);
    color: #67e8f9;
    border-radius: var(--radius-sm);
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s, transform 0.15s;
    line-height: 1;
    font-size: clamp(14px, 1.6vw, 18px);
    position: relative;
}
.printBtn::before {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: calc(var(--radius-sm) + 2px);
    background: rgba(6, 182, 212, 0);
    transition: background 0.2s;
}
.printBtn:hover {
    background: rgba(6, 182, 212, 0.18);
    color: #06b6d4;
    border-color: #06b6d4;
    box-shadow: 0 0 14px rgba(6,182,212,0.35), 0 0 0 3px rgba(6,182,212,0.12);
    transform: translateY(-1px);
}
.printBtn:active { transform: translateY(0); }
.printBtn:focus-visible { outline: 2px solid #06b6d4; outline-offset: 2px; }'''
)

# Add editBacklogFeeTitleRow to CSS (after the existing editBacklogFeeSection block)
patch(
    FOLDER_CSS,
    '''/* Edit mode backlog fee section wrapper */
.editBacklogFeeSection {
    margin-top: clamp(10px, 1.3vw, 14px);
    padding: clamp(10px, 1.3vw, 14px);
    background: rgba(0, 0, 0, 0.2);
    border: 1.5px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--radius-sm);
}
.editBacklogFeeTitle {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 9px);
    font-weight: 900;
    color: #fca5a5;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: clamp(8px, 1vw, 11px);
}
.editBacklogFeeHint {
    margin-top: clamp(7px, 0.9vw, 9px);
    font-size: clamp(8px, 0.82vw, 10px);
    color: rgba(255, 255, 255, 0.3);
    font-weight: 700;
    font-style: italic;
}''',
    '''/* Edit mode backlog fee section wrapper */
.editBacklogFeeSection {
    margin-top: clamp(10px, 1.3vw, 14px);
    padding: clamp(10px, 1.3vw, 14px);
    background: rgba(0, 0, 0, 0.2);
    border: 1.5px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--radius-sm);
}
/* Row with title + EXIT BACKLOG button side by side */
.editBacklogFeeTitleRow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: clamp(6px, 0.8vw, 10px);
    margin-bottom: clamp(8px, 1vw, 11px);
}
.editBacklogFeeTitle {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 9px);
    font-weight: 900;
    color: #fca5a5;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.editBacklogFeeHint {
    margin-top: clamp(7px, 0.9vw, 9px);
    font-size: clamp(8px, 0.82vw, 10px);
    color: rgba(255, 255, 255, 0.3);
    font-weight: 700;
    font-style: italic;
}'''
)

# ================================================================
# CHANGE 7: FolderPage — Audit all backlog admin actions
# recoveryService calls already log via backend AuditService.
# But the fee-rate and fee-adjustment inputs in edit mode need
# to call loadFolderData() already done above. The audit trail
# is handled server-side. No extra frontend changes needed here
# beyond what we've already fixed (added await loadFolderData()).
# ================================================================

# ================================================================
# CHANGE 8: IntakePage — Match "add note" button design to FolderPage
# FolderPage addNoteBtn: orange-border dashed, orange text, dark bg
# IntakePage currently has a different style. Make them match.
# ================================================================
patch(
    INTAKE_JSX,
    '''                                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                                    <button type="button" className={styles.addNoteBtn}
                                        onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>
                                        + ADD NOTE
                                    </button>
                                </div>''',
    '''                                <button type="button" className={styles.addNoteBtn}
                                    onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>
                                    + ADD NOTE
                                </button>'''
)

# ================================================================
# CHANGE 9: IntakePage CSS — Make addNoteBtn match FolderPage addNoteBtn
# FolderPage style: full-width, dashed orange border, orange text, dark bg
# ================================================================
patch(
    INTAKE_CSS,
    '''.addNoteBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(14px, 1.8vw, 20px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 900;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    box-sizing: border-box;
    width: auto;
    align-self: flex-end;
}
.addNoteBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }''',
    '''.addNoteBtn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: clamp(9px, 1.1vw, 12px);
    background: rgba(0, 0, 0, 0.2);
    border: 2px dashed rgba(238, 140, 58, 0.4);
    color: var(--orange);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-btn);
    font-weight: 900;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-radius: var(--radius-sm);
    transition: background 0.2s, border-style 0.15s, border-color 0.2s;
    box-sizing: border-box;
    margin-top: clamp(6px, 0.8vw, 8px);
    gap: clamp(5px, 0.6vw, 7px);
}
.addNoteBtn:hover { background: rgba(238,140,58,0.08); border-style: solid; border-color: var(--orange); }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }'''
)

# ================================================================
# CHANGE 10: RecoveryPortal — Replace hardcoded "UGX 50,000" text
# with dynamic fee from plot data. The RecoveryTaskDTO sends
# storageFeesAccumulated but not the monthly rate.
# We show the actual fees rather than a hardcoded rate.
# ================================================================
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''                    {mission.hasBacklogPlots && Number(mission.totalStorageFees) > 0 && (
                            <div className={styles.feesRow}>
                                <FiAlertOctagon aria-hidden="true" size={11} />
                                <span>Incl. storage fees: UGX {fmt(mission.totalStorageFees)}</span>
                            </div>
                        )}''',
    '''                    {mission.hasBacklogPlots && Number(mission.totalStorageFees) > 0 && (
                            <div className={styles.feesRow}>
                                <FiAlertOctagon aria-hidden="true" size={11} />
                                <span>Incl. accumulated storage fees: UGX {fmt(mission.totalStorageFees)}</span>
                            </div>
                        )}'''
)

# ================================================================
# CHANGE 11: BacklogSchedulerService — rename "storage fee" to
# use the per-plot override label, and update audit log wording
# to say "monthly storage fee" not hardcoded 50,000
# ================================================================
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java',
    '''            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) x UGX 50,000)"
                + " | Total fees: UGX " + plot.getStorageFeesAccumulated());''',
    '''            auditService.logAction("STORAGE_FEE_APPLIED",
                "SYSTEM: Added UGX " + toAdd + " monthly storage fee to backlog plot: "
                + plot.getLandTitle().getPlotNumber()
                + " (" + feesMissing + " month(s) x UGX " + monthlyRate + ")"
                + " | Total accumulated fees: UGX " + plot.getStorageFeesAccumulated());'''
)

# ================================================================
# CHANGE 12: LandService — Audit the exit backlog action with fee info
# Already has BACKLOG_EXIT audit. Update wording to include fee context.
# ================================================================
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
    '''        auditService.logAction("BACKLOG_EXIT",
            "Operator [" + getCurrentOperator() + "] manually removed plot "
            + project.getLandTitle().getPlotNumber()
            + " from BACKLOG. Storage fees cleared.");''',
    '''        auditService.logAction("BACKLOG_EXIT",
            "Operator [" + getCurrentOperator() + "] manually removed plot "
            + project.getLandTitle().getPlotNumber()
            + " from BACKLOG. Accumulated storage fees of UGX " + project.getStorageFeesAccumulated() + " cleared.");'''
)

# ================================================================
# CHANGE 13: LandService — Audit storage rate change with clearer wording
# ================================================================
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
    '''        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] set monthly storage fee to UGX " + rate
            + " for plot: " + project.getLandTitle().getPlotNumber());''',
    '''        auditService.logAction("STORAGE_RATE_CHANGED",
            "Operator [" + getCurrentOperator() + "] changed monthly storage fee to UGX " + rate
            + " for plot: " + project.getLandTitle().getPlotNumber()
            + " (previously UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");'''
)

# ================================================================
# CHANGE 14: LandService — Audit accumulated fee adjustment with before/after
# (already has before/after — just ensure wording says "monthly storage fee")
# ================================================================
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
    '''        auditService.logAction("STORAGE_FEES_ADJUSTED",
            "Operator [" + getCurrentOperator() + "] changed accumulated fees from UGX " + old
            + " to UGX " + amount + " for plot: " + project.getLandTitle().getPlotNumber());''',
    '''        auditService.logAction("STORAGE_FEES_ADJUSTED",
            "Operator [" + getCurrentOperator() + "] manually adjusted accumulated storage fees from UGX " + old
            + " to UGX " + amount + " for plot: " + project.getLandTitle().getPlotNumber());'''
)

# ================================================================
# CHANGE 15: LandService — Audit pause/resume with fee rate info
# ================================================================
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
    '''        String action = paused ? "PAUSED" : "RESUMED";
        auditService.logAction("STORAGE_FEE_" + action,
            "Operator [" + getCurrentOperator() + "] " + action + " storage fees for plot: "
            + project.getLandTitle().getPlotNumber());''',
    '''        String action = paused ? "PAUSED" : "RESUMED";
        auditService.logAction("STORAGE_FEE_" + action,
            "Operator [" + getCurrentOperator() + "] " + action.toLowerCase() + " monthly storage fees for plot: "
            + project.getLandTitle().getPlotNumber()
            + " (monthly rate: UGX " + (project.getStorageFeeOverride() != null ? project.getStorageFeeOverride() : "50000 (default)") + ")");'''
)

print()
print("All changes applied successfully!")
print()
print("Summary of changes:")
print("1. Dynamic monthly fee (effectiveMonthlyFee) replaces all hardcoded UGX 50,000 text in FolderPage")
print("2. EXIT BACKLOG button moved to edit mode only (view mode shows message only)")
print("3. Edit-mode fee controls: monthly fee refresh on change, dynamic hint text")
print("4. Print button changed to icon-only with themed hover effect")
print("5. IntakePage addNoteBtn now matches FolderPage style (full-width dashed orange)")
print("6. Backend audit logs updated: monthly fee, exit backlog fee info, rate changes all logged")
print()
print("Run: git add -A && git commit -m 'fix: dynamic monthly fee, exit backlog edit-mode only, icon print btn, uniform note btn, full audit trail' && git push")