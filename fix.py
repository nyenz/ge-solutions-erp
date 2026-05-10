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

INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'
FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'

# ================================================================
# 1. IntakePage: Add missing state variables
# ================================================================
patch(
    INTAKE_JSX,
    '''    // Financials — SIMPLIFIED: only totalCost, initialPayment, isBacklog
    const [totalCost,      setTotalCost]      = useState('');
    const [initialPayment, setInitialPayment] = useState('');
    const [isBacklog,      setIsBacklog]      = useState(false);''',
    '''    // Financials — SIMPLIFIED: only totalCost, initialPayment, isBacklog
    const [totalCost,         setTotalCost]         = useState('');
    const [initialPayment,    setInitialPayment]    = useState('');
    const [isBacklog,         setIsBacklog]         = useState(false);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState('50000');
    const [initialStorageFee, setInitialStorageFee] = useState('');'''
)

# ================================================================
# 2. IntakePage: Replace the entire financials section with correct UI
#    (backlog fee config below the toggle)
# ================================================================
patch(
    INTAKE_JSX,
    '''                            {/* BACKLOG STATUS — single clean toggle */}
                            <div className={styles.modeRow}>
                                <label>BACKLOG STATUS</label>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button type="button"
                                        className={!isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        onClick={() => setIsBacklog(false)}>
                                        ✓ STANDARD — NOT BACKLOG
                                    </button>
                                    <button type="button"
                                        className={isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        style={isBacklog ? { borderColor:'#ef4444', color:'#ef4444', background:'rgba(239,68,68,0.12)' } : {}}
                                        onClick={() => setIsBacklog(true)}>
                                        ⚠ ENTER AS BACKLOG
                                    </button>
                                </div>
                                {isBacklog && (
                                    <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, fontSize: '0.82rem', color: '#fca5a5' }}>
                                        This plot will immediately start accumulating UGX 50,000 / month storage fees.
                                    </div>
                                )}
                            </div>''',
    '''                            {/* BACKLOG STATUS — single clean toggle */}
                            <div className={styles.modeRow}>
                                <label>BACKLOG STATUS</label>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    <button type="button"
                                        className={!isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        onClick={() => setIsBacklog(false)}>
                                        ✓ STANDARD — NOT BACKLOG
                                    </button>
                                    <button type="button"
                                        className={isBacklog ? styles.toggleLegacy : styles.toggleStandard}
                                        style={isBacklog ? { borderColor:'#ef4444', color:'#ef4444', background:'rgba(239,68,68,0.12)' } : {}}
                                        onClick={() => setIsBacklog(true)}>
                                        ⚠ ENTER AS BACKLOG
                                    </button>
                                </div>
                                {isBacklog && (
                                    <div className={styles.backlogFeeNote}>
                                        Storage fees accumulate monthly until balance is cleared.
                                    </div>
                                )}
                            </div>

                            {/* BACKLOG FEE CONFIG -- only visible when entering as backlog */}
                            {isBacklog && (
                                <div className={styles.backlogFeeConfig}>
                                    <div className={styles.backlogFeeConfigTitle}>
                                        BACKLOG FEE CONFIGURATION
                                    </div>
                                    <div className={styles.grid2} style={{marginBottom: 0}}>
                                        <CurrencyInput
                                            label="MONTHLY STORAGE FEE (UGX)"
                                            value={monthlyStorageFee}
                                            onChange={setMonthlyStorageFee}
                                            id="monthlyFee"
                                        />
                                        <CurrencyInput
                                            label="INITIAL ACCUMULATED FEES (UGX)"
                                            value={initialStorageFee}
                                            onChange={setInitialStorageFee}
                                            id="initialStorageFee"
                                        />
                                    </div>
                                    <div className={styles.backlogFeeHint}>
                                        Set initial fees if this title was entered late into the system
                                        (e.g. was in backlog for 3 months before being registered here).
                                        Leave at 0 if starting fresh.
                                    </div>
                                </div>
                            )}'''
)

# ================================================================
# 3. IntakePage: Pass monthly fee and initial fee in submit payload
# ================================================================
patch(
    INTAKE_JSX,
    '''                isStartAsBacklog: isBacklog,
                isLegacy: false,''',
    '''                isStartAsBacklog: isBacklog,
                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,
                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,
                isLegacy: false,'''
)

# ================================================================
# 4. IntakePage CSS: Add backlog fee config styles
# ================================================================
patch(
    INTAKE_CSS,
    '''.toggleStandard:hover { border-color: rgba(255,255,255,0.3); color: white; }
.toggleLegacy:focus-visible,
.toggleStandard:focus-visible { outline: 2px solid var(--orange); }''',
    '''.toggleStandard:hover { border-color: rgba(255,255,255,0.3); color: white; }
.toggleLegacy:focus-visible,
.toggleStandard:focus-visible { outline: 2px solid var(--orange); }

.backlogFeeNote {
    margin-top: 8px;
    padding: clamp(7px, 0.9vw, 10px) clamp(10px, 1.2vw, 14px);
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: var(--radius-sm);
    font-size: clamp(10px, 1vw, 12px);
    color: rgba(255, 255, 255, 0.55);
    font-weight: 700;
}

.backlogFeeConfig {
    margin-top: var(--gap-md);
    padding: clamp(12px, 1.5vw, 16px);
    background: rgba(0, 0, 0, 0.25);
    border: 1.5px solid rgba(239, 68, 68, 0.25);
    border-radius: var(--radius-sm);
}

.backlogFeeConfigTitle {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 900;
    color: #fca5a5;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: clamp(10px, 1.3vw, 14px);
}

.backlogFeeHint {
    margin-top: clamp(8px, 1vw, 11px);
    font-size: clamp(9px, 0.92vw, 11px);
    color: rgba(255, 255, 255, 0.35);
    font-weight: 700;
    line-height: 1.5;
    font-style: italic;
}'''
)

# ================================================================
# 5. IntakePage CSS: Fix addNoteBtn focus-visible (was missing)
# ================================================================
patch(
    INTAKE_CSS,
    '''.addNoteBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }''',
    '''.addNoteBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }'''
)

# ================================================================
# 6. FolderPage: Replace the backlog financials notice (clean version)
#    The previous fix missed the correct old text — use actual current text
# ================================================================
patch(
    FOLDER_JSX,
    '''                                    {/* Backlog notice at top of financials */}
                                    <div style={{
                                        background: 'rgba(239,68,68,0.10)', border: '1px solid rgba(239,68,68,0.35)',
                                        borderRadius: 7, padding: '10px 14px', marginBottom: 14,
                                        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap'
                                    }}>
                                        <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={16} />
                                        <div style={{ flex: 1 }}>
                                            <strong style={{ color: '#ef4444', fontSize: '0.8rem', fontFamily: 'DM Sans,sans-serif', fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }}>BACKLOG STATUS — STORAGE FEES ACTIVE</strong>
                                            <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', marginTop: 2, fontFamily: 'DM Sans,sans-serif' }}>
                                                UGX 50,000 is added every month until the full balance is cleared.
                                            </div>
                                        </div>
                                        {isAdmin && (
                                            <button onClick={handleExitBacklog} className={styles.ctrlBtnBacklog} style={{ height: 30, fontSize: 10, padding: '0 10px' }}>
                                                EXIT BACKLOG
                                            </button>
                                        )}
                                    </div>''',
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
                                    </div>'''
)

# ================================================================
# 7. FolderPage: Replace the edit-mode backlog fee controls with
#    clean inline fields (no BacklogFeeControls component)
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
                                                    className={`${styles.feesToggleBtn} ${project.storagePaused ? styles.feesTogglePaused : styles.feesToggleActive}`}
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
                                )}'''
)

# ================================================================
# 8. FolderPage CSS: Add missing classes for backlog notice + fee controls
# ================================================================
patch(
    FOLDER_CSS,
    '''/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */''',
    '''/* ═══════════════════════════════════════════════════════════════════
   BACKLOG NOTICE (view mode) + EDIT MODE FEE CONTROLS
   ═══════════════════════════════════════════════════════════════════ */

/* View mode: clean left-border notice row */
.backlogNotice {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
    border-left: 2px solid rgba(239, 68, 68, 0.5);
    background: rgba(239, 68, 68, 0.06);
    border-radius: 0 6px 6px 0;
    margin-bottom: clamp(10px, 1.3vw, 14px);
}
.backlogNoticeIcon { color: #ef4444; flex-shrink: 0; opacity: 0.8; }
.backlogNoticeText {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
    min-width: 0;
}
.backlogNoticeText strong {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.82vw, 10px);
    font-weight: 900;
    color: #fca5a5;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.backlogNoticeText span {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.8vw, 9px);
    color: rgba(255, 255, 255, 0.45);
    font-weight: 700;
}

/* Exit backlog button — small, red outline */
.btnExitBacklog {
    display: inline-flex;
    align-items: center;
    gap: clamp(4px, 0.5vw, 6px);
    height: clamp(26px, 3.2vw, 30px);
    padding: 0 clamp(8px, 1vw, 12px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.8vw, 9px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.btnExitBacklog:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
.btnExitBacklog:focus-visible { outline: 2px solid #ef4444; outline-offset: 2px; }

/* Pause/Resume fees button — same design as Ledger "PAID TITLES" filter:
   orange fill when active (resume), orange outline when inactive (pause) */
.btnPauseResume {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(5px, 0.6vw, 7px);
    width: 100%;
    height: var(--input-h, clamp(34px, 4.5vw, 40px));
    background: #EE8C3A;
    border: 1.5px solid #EE8C3A;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.82vw, 10px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 2px 8px rgba(238, 140, 58, 0.25);
}
.btnPauseResume:hover {
    background: #f0a050;
    border-color: #f0a050;
    box-shadow: 0 0 14px rgba(238, 140, 58, 0.45);
}
.btnPauseResume:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* Edit mode backlog fee section wrapper */
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
}

/* ═══════════════════════════════════════════════════════════════════
   PRINT
   ═══════════════════════════════════════════════════════════════════ */'''
)

print("\nAll patches applied!")
print("Run: git add -A && git commit -m 'fix: intake monthly fee state, backlog fee config, folder edit-mode fee controls, uniform button styles' && git push")