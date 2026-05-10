
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
 
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'
INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
FOLDER_CSS = 'erp-frontend/src/pages/DigitalFolder/FolderPage.module.css'
FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
 
# ================================================================
# 1. IntakePage: "Add Note" button same design as "Select Scans"
#    Also applies to any similar upload/add button on intake
# ================================================================
patch(
    INTAKE_CSS,
    '''.addNoteBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(4px, 0.5vw, 6px);
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
.addNoteBtn:hover { background: rgba(238,140,58,0.12); color: #EE8C3A; border-color: #EE8C3A; }''',
    '''.addNoteBtn {
    background: transparent;
    border: 2px dashed rgba(255, 255, 255, 0.25);
    padding: clamp(12px, 1.5vw, 15px);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: clamp(8px, 1vw, 10px);
    color: rgba(255, 255, 255, 0.5);
    font-weight: 900;
    font-size: var(--fs-btn);
    cursor: pointer;
    transition: border-color 0.25s, color 0.25s, background 0.25s;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'DM Sans', sans-serif;
    user-select: none;
    -webkit-user-select: none;
    width: 100% !important;
}
.addNoteBtn:hover {
    border-color: var(--orange);
    border-style: solid;
    color: var(--orange);
    background: rgba(238, 140, 58, 0.07);
}
.addNoteBtn:active { background: rgba(238, 140, 58, 0.14); }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }'''
)
 
# ================================================================
# 2. IntakePage: "Save New Plot" button same design as "Save Note"
#    in HardwareModal (orange fill, dark text)
# ================================================================
patch(
    INTAKE_CSS,
    '''.primaryCommitBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    height: clamp(34px, 4.2vw, 40px);
    padding: 0 clamp(16px, 2vw, 24px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}
.primaryCommitBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.primaryCommitBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }''',
    '''.primaryCommitBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    padding: 0 clamp(16px, 2vw, 24px);
    height: clamp(36px, 4.5vw, 42px);
    background: #EE8C3A;
    color: #1a2e30;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.primaryCommitBtn:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 18px rgba(238,140,58,0.4);
}
.primaryCommitBtn:disabled { opacity: 0.45; cursor: not-allowed; }
.primaryCommitBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 3px; }'''
)
 
# ================================================================
# 3. IntakePage: Add monthly storage fee toggle in financials
# ================================================================
patch(
    INTAKE_JSX,
    '''    // Financials -- SIMPLIFIED: only totalCost, initialPayment, isBacklog
    const [totalCost,      setTotalCost]      = useState('');
    const [initialPayment, setInitialPayment] = useState('');
    const [isBacklog,      setIsBacklog]      = useState(false);''',
    '''    // Financials -- SIMPLIFIED: only totalCost, initialPayment, isBacklog
    const [totalCost,        setTotalCost]        = useState('');
    const [initialPayment,   setInitialPayment]   = useState('');
    const [isBacklog,        setIsBacklog]         = useState(false);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState('50000');'''
)
 
# Add the monthly fee field and update payload
patch(
    INTAKE_JSX,
    '''                            {/* BACKLOG STATUS -- single clean toggle */}
                            <div className={styles.modeRow}>''',
    '''                            {/* MONTHLY STORAGE FEE (only shown when backlog is selected) */}
                            {isBacklog && (
                                <div className={styles.inputGrid3} style={{marginBottom: 0}}>
                                    <CurrencyInput label="MONTHLY STORAGE FEE (UGX)" value={monthlyStorageFee}
                                        onChange={setMonthlyStorageFee} id="monthlyFee" />
                                    <div className={styles.inputWrap}>
                                        <div className={styles.labelRow}>
                                            <label className={styles.fieldLabel}>RATE NOTE</label>
                                        </div>
                                        <div className={styles.diagBox} style={{fontSize:'0.75rem', color:'rgba(255,255,255,0.5)', background:'rgba(0,0,0,0.2)', border:'1px dashed rgba(255,255,255,0.15)'}}>
                                            Added monthly until balance cleared
                                        </div>
                                    </div>
                                </div>
                            )}
 
                            {/* BACKLOG STATUS -- single clean toggle */}
                            <div className={styles.modeRow}>'''
)
 
# ================================================================
# 4. FolderPage: Edit / Save buttons same design as "Save Note"
#    (orange fill like modalBtnPrimary, abort keeps red style)
# ================================================================
patch(
    FOLDER_CSS,
    '''.btnPrimary {
    background: rgba(26, 46, 48, 0.75);
    border-color: rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
}
.btnPrimary:not(:disabled):hover {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
    box-shadow: 0 0 16px rgba(238,140,58,0.4);
}''',
    '''.btnPrimary {
    background: #EE8C3A;
    border-color: #EE8C3A;
    color: #1a2e30;
    box-shadow: 0 4px 12px rgba(238,140,58,0.3);
}
.btnPrimary:not(:disabled):hover {
    background: #f0a050;
    border-color: #f0a050;
    color: #1a2e30;
    box-shadow: 0 0 18px rgba(238,140,58,0.5);
}'''
)
 
# Also update the Edit (unlockMasterBtn) to solid orange
patch(
    FOLDER_CSS,
    '''.unlockMasterBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.6);
    color: #EE8C3A;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, color 0.2s;
    line-height: 1;
}
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible {
    background: #EE8C3A;
    color: #1a2e30;
    border-color: #EE8C3A;
    box-shadow: 0 0 14px rgba(238,140,58,0.35);
    outline: none;
}''',
    '''.unlockMasterBtn {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 7px);
    height: clamp(32px, 4vw, 38px);
    padding: 0 clamp(10px, 1.3vw, 15px);
    background: #EE8C3A;
    border: none;
    color: #1a2e30;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, box-shadow 0.2s;
    line-height: 1;
    box-shadow: 0 3px 10px rgba(238,140,58,0.3);
}
.unlockMasterBtn:hover, .unlockMasterBtn:focus-visible {
    background: #f0a050;
    box-shadow: 0 0 16px rgba(238,140,58,0.5);
    outline: none;
}'''
)
 
# ================================================================
# 5. FolderPage: Print button same design as Payment but teal color
# ================================================================
patch(
    FOLDER_CSS,
    '''.printBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: clamp(32px, 4vw, 38px);
    height: clamp(32px, 4vw, 38px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.6);
    border-radius: var(--radius-sm);
    font-size: clamp(14px, 1.6vw, 17px);
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
    flex-shrink: 0;
    line-height: 1;
}
.printBtn:hover { background: rgba(255,255,255,0.12); color: #fff; border-color: rgba(255,255,255,0.35); }''',
    '''.printBtn {
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
.printBtn:focus-visible { outline: 2px solid #06b6d4; outline-offset: 2px; }'''
)
 
# Update print button in JSX to show text label
patch(
    FOLDER_JSX,
    '''                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record" title="Print">
                                <FiPrinter aria-hidden="true" />
                            </button>''',
    '''                            <button className={styles.printBtn} onClick={() => window.print()} aria-label="Print record">
                                <FiPrinter aria-hidden="true" /> PRINT
                            </button>'''
)
 
# ================================================================
# 6. FolderPage: Add monthly storage fee field in EDIT mode financials
# ================================================================
patch(
    FOLDER_JSX,
    '''                    {isEditing ? (
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => setBuffer({...buffer, totalCost:v})} />
                                    <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => setBuffer({...buffer, initialPayment:v})} />
                                    <div className={styles.hwInputWrap}>
                                        <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                        <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                    </div>
                                </div>
                            ) : isBacklog ? (''',
    '''                    {isEditing ? (
                                <>
                                <div className={styles.inputGrid3}>
                                    <CurrencyInput label="TOTAL COST" value={buffer.totalCost} onChange={v => setBuffer({...buffer, totalCost:v})} />
                                    <CurrencyInput label="AMOUNT PAID" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => setBuffer({...buffer, initialPayment:v})} />
                                    <div className={styles.hwInputWrap}>
                                        <div className={styles.inputLabelRow}><label>ARREARS</label><span className={styles.autoCalcBadge}>AUTO</span></div>
                                        <input className={`${styles.hwInput} ${styles.calcInput}`} value={arrearsEdit.toLocaleString()} disabled />
                                    </div>
                                </div>
                                {project.isBacklog && (
                                    <div className={styles.inputGrid3} style={{marginTop: 8}}>
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
                                                        try { await recoveryService.setStorageRate(project.id, val); }
                                                        catch { /* non-fatal */ }
                                                    }
                                                }}
                                                placeholder="50000"
                                            />
                                        </div>
                                    </div>
                                )}
                                </>
                            ) : isBacklog ? ('''
)
 
# ================================================================
# 7. FolderPage: Clean up backlog financials section
#    - Remove red background from backlog warning
#    - Remove BacklogFeeControls admin section (set total / apply rate buttons)
#    - EXIT BACKLOG button same design as other buttons but scaled down
#    - PAUSE/RESUME FEES button orange version
# ================================================================
 
# Remove the BacklogFeeControls component render from the JSX
patch(
    FOLDER_JSX,
    '''                                    {isAdmin && <BacklogFeeControls project={project} projectId={id} onRefresh={loadFolderData} toast={toast} />}''',
    '''                                    {isAdmin && (
                                        <div style={{marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap'}}>
                                            <button
                                                className={styles.btnPauseResume}
                                                onClick={async () => {
                                                    try {
                                                        await recoveryService.pauseStorageFees(id, !project.storagePaused);
                                                        await loadFolderData();
                                                        toast(project.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
                                                    } catch { toast('ACTION FAILED', 'error'); }
                                                }}
                                            >
                                                {project.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                                            </button>
                                        </div>
                                    )}'''
)
 
# Clean up the backlog warning: remove red background, keep minimal
patch(
    FOLDER_JSX,
    '''                                    <div style={{
                                        background: 'rgba(239,68,68,0.10)', border: '1px solid rgba(239,68,68,0.35)',
                                        borderRadius: 7, padding: '10px 14px', marginBottom: 14,
                                        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap'
                                    }}>
                                        <FiAlertOctagon style={{ color: '#ef4444', flexShrink: 0 }} size={16} />
                                        <div style={{ flex: 1 }}>
                                            <strong style={{ color: '#ef4444', fontSize: '0.8rem', fontFamily: 'DM Sans,sans-serif', fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1 }}>BACKLOG STATUS -- STORAGE FEES ACTIVE</strong>
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
                                            <strong>BACKLOG — STORAGE FEES ACTIVE</strong>
                                            <span>UGX 50,000 added monthly until balance cleared</span>
                                        </div>
                                        {isAdmin && (
                                            <button onClick={handleExitBacklog} className={styles.btnExitBacklog}>
                                                EXIT BACKLOG
                                            </button>
                                        )}
                                    </div>'''
)
 
# Add new CSS classes for backlog notice, exit backlog, pause/resume
patch(
    FOLDER_CSS,
    '''/* ── PRINT\n   @media print {''',
    '''/* ── BACKLOG NOTICE & CONTROLS ───────────────────────────────────── */
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
 
/* Exit backlog -- same button family, smaller scale */
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
 
/* Pause/resume fees -- orange version, smaller scale */
.btnPauseResume {
    display: inline-flex;
    align-items: center;
    gap: clamp(4px, 0.5vw, 6px);
    height: clamp(26px, 3.2vw, 30px);
    padding: 0 clamp(8px, 1vw, 12px);
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(238, 140, 58, 0.5);
    color: #EE8C3A;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(8px, 0.8vw, 9px);
    text-transform: uppercase;
    letter-spacing: 1px;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}
.btnPauseResume:hover { background: #EE8C3A; color: #1a2e30; border-color: #EE8C3A; box-shadow: 0 0 10px rgba(238,140,58,0.3); }
.btnPauseResume:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }
 
/* ── PRINT
   @media print {'''
)
 
print("\nAll patches applied!")
print("Run: git add -A && git commit -m 'ui: uniform buttons, backlog notice cleanup, monthly fee in intake/folder edit, print=teal, save=orange' && git push")