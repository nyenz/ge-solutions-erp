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

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    write(path, content.replace(old, new, 1))
    print(f"OK patch ({label or path})")


# ================================================================
# STAGE 1: FOLDER PAGE COMPONENT UPDATES
# 1. Imports for HardwareButton & Icons
# 2. State for Payment Modal Type (Title vs Storage)
# 3. Router Blocker Unsaved Guard Hook Fix
# 4. Hash Navigation crash fix
# 5. Payment Modal Logic
# 6. Backlog Controls & "EXIT BACKLOG" Placement
# ================================================================

# 1 & 2: Imports and Payment State
OLD_IMPORTS = """import HardwareModal from '../../components/common/HardwareModal';
import ErrorMessage from '../../components/common/ErrorMessage';"""
NEW_IMPORTS = """import HardwareModal from '../../components/common/HardwareModal';
import HardwareButton from '../../components/common/HardwareButton';
import ErrorMessage from '../../components/common/ErrorMessage';"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_IMPORTS, NEW_IMPORTS, "Imports")

OLD_ICONS = """        FiDollarSign, FiActivity
    } from 'react-icons/fi';"""
NEW_ICONS = """        FiDollarSign, FiActivity, FiHome, FiArchive
    } from 'react-icons/fi';"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_ICONS, NEW_ICONS, "Icons")

OLD_STATE = """    const [payModal,   setPayModal]   = useState({ open:false });
    const [payAmount,  setPayAmount]  = useState('');
    const [payNotes,   setPayNotes]   = useState('');
    const [paying,     setPaying]     = useState(false);"""

NEW_STATE = """    const [payModal,   setPayModal]   = useState({ open:false });
    const [payAmount,  setPayAmount]  = useState('');
    const [payNotes,   setPayNotes]   = useState('');
    const [payType,    setPayType]    = useState('TITLE');
    const [paying,     setPaying]     = useState(false);"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_STATE, NEW_STATE, "Payment State")

# 3 & 4: Router Guard & Hash Navigation
OLD_HOOKS = """    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing && touchedRef.current);

    useEffect(() => {
        // If navigated here with a hash (e.g. #payments from PaymentsPage),
        // open the matching drawer and scroll to it. Otherwise scroll to top.
        const hash = window.location.hash.replace('#', '');
        if (hash && ['tech','identity','finance','vault','intel','payments'].includes(hash)) {
            setDrawers(prev => ({ ...prev, [hash]: true }));
            setTimeout(() => {
                const el = document.getElementById('drawer-' + hash);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 350);
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);"""

NEW_HOOKS = """    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =
        useRouterBlock(!committing && isEditing && touchedRef.current);

    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials') {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                const el = document.getElementById('paymentHistorySection');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_HOOKS, NEW_HOOKS, "Guard & Hash Effect")

# 5: Handle Record Payment Function
OLD_PAY = """    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            await recoveryService.recordPayment(id, payAmount, payNotes);
            await loadFolderData();
            setPayModal({ open: false });
            setPayAmount(''); setPayNotes('');
            toast('PAYMENT RECORDED', 'success');
        } catch { toast('PAYMENT FAILED', 'error', 8000); }
        finally { setPaying(false); }
    };"""

NEW_PAY = """    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            const fullNotes = payType === 'STORAGE'
                ? `[STORAGE FEE PAYMENT] ${payNotes}`.trim()
                : payNotes;
            await recoveryService.recordPayment(id, payAmount, fullNotes);
            await loadFolderData();
            setPayModal({ open: false });
            setPayAmount(''); setPayNotes(''); setPayType('TITLE');
            toast('PAYMENT RECORDED', 'success');
        } catch { toast('PAYMENT FAILED', 'error', 8000); }
        finally { setPaying(false); }
    };"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_PAY, NEW_PAY, "Payment Handler")

# 6: Add ID to payment section for scroll target
OLD_PH = """                        {/* ── 3. PAYMENT HISTORY ── */}
                        <section className={styles.hwPanel} aria-label="Payment History">"""

NEW_PH = """                        {/* ── 3. PAYMENT HISTORY ── */}
                        <section className={styles.hwPanel} aria-label="Payment History" id="paymentHistorySection">"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_PH, NEW_PH, "Payment ID target")

# 7: The new advanced Payment Modal JSX
OLD_MODAL = """            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => setPayModal({ open: false })} title={`RECORD PAYMENT — ${project.landTitle.plotNumber}`}>
                {isBacklog ? (
                    <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>
                        <div style={{display:'flex',gap:10,alignItems:'flex-start'}}>
                            <FiAlertOctagon style={{ color: '#ef4444', flexShrink:0, marginTop:2 }} aria-hidden="true" />
                            <div>
                                <div>Original debt: <strong>UGX {fmt(origDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(storageFees)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(Math.max(0,backlogOwed))}</strong></div>
                                <div style={{marginTop:6,opacity:0.6,fontSize:'0.8rem'}}>Storage fees continue until full balance is cleared.</div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className={modalStyles.modalInfoBox}>
                        Current balance: <strong>UGX {fmt(remaining)}</strong>
                    </div>
                )}
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput}
                        placeholder="Enter amount..." value={payAmount}
                        onChange={e => setPayAmount(e.target.value)} />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via MTN Mobile Money..."
                        value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnPrimary}
                        onClick={handleRecordPayment} disabled={paying}>
                        <FiDollarSign aria-hidden="true" /> {paying ? 'PROCESSING...' : 'CONFIRM PAYMENT'}
                    </button>
                </div>
            </HardwareModal>"""

NEW_MODAL = """            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT — ${project.landTitle.plotNumber}`}>
                <div className={styles.payBreakdownBox}>
                    {isBacklog ? (
                        <>
                            <div className={styles.payBreakdownTitle}>
                                <FiAlertOctagon size={11} /> BACKLOG BALANCE BREAKDOWN
                            </div>
                            <div className={styles.payBreakdownGrid}>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel}>ORIGINAL TITLE DEBT</span>
                                    <span className={styles.pbVal}>UGX {fmt(origDebt)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel} style={{color:'#fca5a5'}}>STORAGE FEES (MONTHLY)</span>
                                    <span className={styles.pbVal} style={{color:'#ef4444'}}>+ UGX {fmt(storageFees)}</span>
                                </div>
                                <div className={styles.pbItem}>
                                    <span className={styles.pbLabel}>PAYMENTS MADE</span>
                                    <span className={styles.pbVal} style={{color:'#86efac'}}>- UGX {fmt(amountPaid)}</span>
                                </div>
                                <div className={styles.pbItemTotal}>
                                    <span className={styles.pbLabel}>TOTAL NOW OWED</span>
                                    <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, backlogOwed))}</span>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className={styles.payBreakdownGrid}>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>TITLE COST</span>
                                <span className={styles.pbVal}>UGX {fmt(totalCost)}</span>
                            </div>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>PAID SO FAR</span>
                                <span className={styles.pbVal} style={{color:'#86efac'}}>UGX {fmt(amountPaid)}</span>
                            </div>
                            <div className={styles.pbItemTotal}>
                                <span className={styles.pbLabel}>REMAINING BALANCE</span>
                                <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, activeOwed))}</span>
                            </div>
                        </div>
                    )}
                </div>

                {isBacklog && (
                    <div className={styles.payTypeRow}>
                        <div className={styles.payTypeLabel}>WHAT IS THIS PAYMENT FOR?</div>
                        <div className={styles.payTypeButtons}>
                            <button type="button" className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`} onClick={() => setPayType('TITLE')}>
                                <FiHome size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>TITLE PAYMENT</div>
                                    <div className={styles.payTypeBtnSub}>Reduces the original title debt</div>
                                </div>
                            </button>
                            <button type="button" className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`} onClick={() => setPayType('STORAGE')}>
                                <FiArchive size={12} />
                                <div>
                                    <div className={styles.payTypeBtnName}>STORAGE FEE</div>
                                    <div className={styles.payTypeBtnSub}>Covers monthly storage charges</div>
                                </div>
                            </button>
                        </div>
                    </div>
                )}

                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput}
                        placeholder={isBacklog && payType === 'STORAGE' ? "e.g. 50000 (1 month)" : `e.g. ${fmt(Math.max(0, remaining))}`}
                        value={payAmount} onChange={e => setPayAmount(e.target.value)} />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via MTN Mobile Money..."
                        value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <HardwareButton type="button" onClick={handleRecordPayment} loading={paying} icon={FiDollarSign}>
                        CONFIRM {payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'}
                    </HardwareButton>
                </div>
            </HardwareModal>"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', OLD_MODAL, NEW_MODAL, "Payment Modal Block")


# ================================================================
# STAGE 2: CSS UPDATES (Consistency)
# ================================================================
OLD_CSS = """/* Sticky Tab Bar with Dark Navy Panel Style */
.tabBar {"""

NEW_CSS = """/* ── FILTER BTNS (Pause/Resume, Tabs) ── */
.filterBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(12px, 1.5vw, 18px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    flex-shrink: 0;
}
.filterBtn:hover { background: rgba(238, 140, 58, 0.12); color: #EE8C3A; border-color: #EE8C3A; }
.filterActive {
    background: #EE8C3A !important;
    color: #1a2e30 !important;
    border-color: #EE8C3A !important;
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.35);
}

/* ── PAYMENT MODAL STYLES ── */
.payBreakdownBox { background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: clamp(10px,1.3vw,14px); margin-bottom: clamp(12px,1.5vw,16px); }
.payBreakdownTitle { display: flex; align-items: center; gap: 6px; font-family: 'DM Sans', sans-serif; font-size: 8px; font-weight: 900; color: #fca5a5; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; }
.payBreakdownGrid { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(7px,0.9vw,10px); }
.pbItem { display: flex; flex-direction: column; gap: 3px; }
.pbLabel { font-family: 'DM Sans', sans-serif; font-size: 8px; font-weight: 900; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.8px; }
.pbVal { font-family: 'Space Mono', monospace; font-size: clamp(11px,1.1vw,13px); font-weight: 700; color: #fff; }
.pbItemTotal { grid-column: 1/-1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: clamp(6px,0.8vw,9px); margin-top: 2px; display: flex; flex-direction: column; gap: 3px; }
.pbValTotal { font-family: 'Space Mono', monospace; font-size: clamp(14px,1.5vw,18px); font-weight: 900; color: #EE8C3A; }

.payTypeRow { margin-bottom: clamp(12px,1.5vw,16px); display: flex; flex-direction: column; gap: 8px; }
.payTypeLabel { font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1px; }
.payTypeButtons { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.payTypeBtn { background: rgba(255,255,255,0.05); border: 1.5px solid rgba(255,255,255,0.12); border-radius: 8px; padding: clamp(10px,1.3vw,14px); cursor: pointer; display: flex; align-items: flex-start; gap: 10px; transition: all 0.2s; text-align: left; color: rgba(255,255,255,0.7); }
.payTypeBtn:hover { border-color: rgba(34,197,94,0.5); background: rgba(34,197,94,0.07); color: #fff; }
.payTypeBtnActive { border-color: #22c55e !important; background: rgba(34,197,94,0.14) !important; color: #fff !important; box-shadow: 0 0 14px rgba(34,197,94,0.2); }
.payTypeBtnStorage:hover { border-color: rgba(239,68,68,0.5) !important; background: rgba(239,68,68,0.07) !important; }
.payTypeBtnStorageActive { border-color: #ef4444 !important; background: rgba(239,68,68,0.14) !important; color: #fff !important; box-shadow: 0 0 14px rgba(239,68,68,0.2); }
.payTypeBtnName { font-family: 'DM Sans', sans-serif; font-size: clamp(10px,1vw,12px); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 2px; }
.payTypeBtnSub { font-family: 'DM Sans', sans-serif; font-size: 9px; font-weight: 700; color: rgba(255,255,255,0.45); display: block; line-height: 1.4; }

/* Sticky Tab Bar with Dark Navy Panel Style */
.tabBar {"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.module.css', OLD_CSS, NEW_CSS, "CSS Filter Button & Modals")


OLD_ADD_NOTE = """.addNoteBtn {
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
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }"""

NEW_ADD_NOTE = """.addNoteBtn {
    display: flex; align-items: center; justify-content: center; width: 100%; padding: clamp(7px, 1vw, 9px); margin-top: clamp(6px, 0.8vw, 8px); border: 2px dashed var(--orange); color: var(--orange); font-family: 'DM Sans', sans-serif; font-size: var(--fs-tag); font-weight: 900; cursor: pointer; background: rgba(238,140,58,0.04); text-transform: uppercase; letter-spacing: 1px; text-align: center; border-radius: 4px; transition: background 0.2s, border-style 0.15s; box-sizing: border-box; 
}
.addNoteBtn:hover { background: var(--orange-dim); border-style: solid; }
.addNoteBtn:focus-visible { outline: 2px solid var(--orange); }"""

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.module.css', OLD_ADD_NOTE, NEW_ADD_NOTE, "CSS Note Button Uniformity")

print()
print("Final uniformity and structural logic fixes have been executed successfully.")
print("Run: py fix.py")