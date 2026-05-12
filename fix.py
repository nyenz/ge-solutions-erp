import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    content = content.replace(old, new, 1)
    write(path, content)
    print(f"OK patch ({label or path})")


# ── FOLDER PAGE STYLING (Highlight Row) ──
content = read('erp-frontend/src/pages/DigitalFolder/FolderPage.module.css')
if '.highlightRow' not in content:
    content += "\n\n/* --- HIGHLIGHT ROW --- */\n.highlightRow {\n    background: rgba(238, 140, 58, 0.25) !important;\n    border-left-color: var(--orange) !important;\n    box-shadow: 0 0 15px rgba(238, 140, 58, 0.4);\n    transition: background 0.5s ease-out, box-shadow 0.5s ease-out;\n}\n"
    write('erp-frontend/src/pages/DigitalFolder/FolderPage.module.css', content)
    print("OK patch (FolderPage.module.css)")

# ── FOLDER PAGE LOGIC ──
patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', 
"""    const [activeTab, setActiveTab] = useState(() => {
    return typeof window !== 'undefined' && window.location.hash.toLowerCase().includes('financials') 
        ? 'FINANCIALS' 
        : 'OVERVIEW';
});""", 
"""    const [activeTab, setActiveTab] = useState(() => {
    const h = typeof window !== 'undefined' ? window.location.hash.toLowerCase() : '';
    return (h.includes('finance') || h.includes('payment')) ? 'FINANCIALS' : 'OVERVIEW';
});""", "FolderPage hash state")

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', 
"""    useEffect(() => {
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
    }, [id]);""",
"""    useEffect(() => {
        const hash = window.location.hash.replace('#', '');
        if (hash === 'payments' || hash === 'finance' || hash === 'financials' || hash.startsWith('payment-')) {
            setActiveTab('FINANCIALS');
            setTimeout(() => {
                if (hash.startsWith('payment-')) {
                    const el = document.getElementById(hash);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add(styles.highlightRow);
                        setTimeout(() => el.classList.remove(styles.highlightRow), 3000);
                    }
                } else {
                    const el = document.getElementById('paymentHistorySection');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 350);
        } else if (hash === 'identity' || hash === 'owners') {
            setActiveTab('OWNERS');
        } else if (hash === 'vault' || hash === 'documents') {
            setActiveTab('DOCUMENTS');
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [id]);""", "FolderPage hash scroll")

patch('erp-frontend/src/pages/DigitalFolder/FolderPage.jsx', 
"""                                            <div key={pay.id || i} className={styles.paymentRow}
                                                style={{borderLeftColor: pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#06b6d4' : '#22c55e'}}>""",
"""                                            <div key={pay.id || i} id={`payment-${pay.id}`} className={styles.paymentRow}
                                                style={{borderLeftColor: pay.paymentType === 'BACKLOG_PARTIAL' ? '#ef4444' : pay.paymentType === 'INITIAL_DEPOSIT' ? '#06b6d4' : '#22c55e'}}>""", "FolderPage row id")

# ── PAYMENTS PAGE ──
patch('erp-frontend/src/pages/Payments/PaymentsPage.jsx',
"""                                <tr key={pay.id || i}
                                    onClick={() => pay.projectId && navigate(`/folder/${pay.projectId}#payments`)}
                                    tabIndex={pay.projectId ? 0 : undefined}
                                    onKeyDown={e => { if (pay.projectId && (e.key==='Enter'||e.key===' ')) { e.preventDefault(); navigate(`/folder/${pay.projectId}`); }}}>""",
"""                                <tr key={pay.id || i}
                                    onClick={() => pay.projectId && navigate(`/folder/${pay.projectId}#payment-${pay.id}`)}
                                    tabIndex={pay.projectId ? 0 : undefined}
                                    onKeyDown={e => { if (pay.projectId && (e.key==='Enter'||e.key===' ')) { e.preventDefault(); navigate(`/folder/${pay.projectId}#payment-${pay.id}`); }}}>""", "PaymentsPage row click")

patch('erp-frontend/src/pages/Payments/PaymentsPage.jsx',
"""                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}#payments`); }}>
                                                <FiChevronRight size={12} /> VIEW
                                            </button>
                                        )}""",
"""                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}#payment-${pay.id}`); }}>
                                                <FiChevronRight size={12} /> VIEW
                                            </button>
                                        )}""", "PaymentsPage button click")

# ── RECOVERY PORTAL ──
patch('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
"""    const [payModal,      setPayModal]      = useState({ open: false, plot: null });
    const [paying,        setPaying]        = useState(false);
    const [monthlyModal,  setMonthlyModal]  = useState({ open: false, plot: null });""",
"", "RecoveryPortal state removal")

patch('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
"""    const handleRecordPayment = async (plot, amount, notes, payType) => {
        setPaying(true);
        try {
            // Always use recordPayment — backend determines type from plot status
            // Notes field carries the payType context for the audit trail
            const fullNotes = payType === 'STORAGE'
                ? `[STORAGE FEE PAYMENT]\${notes ? ' ' + notes : ''}`
                : notes;
            await recoveryService.recordPayment(plot.projectId, amount, fullNotes);
            await loadData();
            setPayModal({ open: false, plot: null });
            toast(`\${payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'} RECORDED`, 'success');
        } catch {
            toast('PAYMENT FAILED', 'error', 8000);
        } finally {
            setPaying(false);
        }
    };""",
"", "RecoveryPortal handleRecordPayment removal")

patch('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
"""                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => setPayModal({ open: true, plot })}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}
                                                {isAdmin && (
                                                    <button className={styles.payBtnMonthly}
                                                        onClick={() => setMonthlyModal({ open: true, plot })}>
                                                        <FiRepeat size={12} /> INSTALMENT
                                                    </button>
                                                )}""",
"""                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}
                                                {isAdmin && (
                                                    <button className={styles.payBtnMonthly}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiRepeat size={12} /> INSTALMENT
                                                    </button>
                                                )}""", "RecoveryPortal active buttons")

patch('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
"""                                                {isAdmin && (
                                                    <button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => setPayModal({ open: true, plot })}>
                                                        <FiZap size={12} /> PAY
                                                    </button>
                                                )}""",
"""                                                {isAdmin && (
                                                    <button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => navigate(`/folder/${plot.projectId}#financials`)}>
                                                        <FiZap size={12} /> PAY
                                                    </button>
                                                )}""", "RecoveryPortal backlog button")

patch('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
"""            {/* PAYMENT MODAL */}
            <PaymentModal
                open={payModal.open}
                plot={payModal.plot}
                onClose={() => setPayModal({ open: false, plot: null })}
                onPay={handleRecordPayment}
                paying={paying}
            />

            {/* MONTHLY INSTALMENT MODAL */}
            <MonthlyInstallmentModal
                open={monthlyModal.open}
                plot={monthlyModal.plot}
                onClose={() => setMonthlyModal({ open: false, plot: null })}
                onPay={handleRecordPayment}
                paying={paying}
            />""",
"", "RecoveryPortal modals bottom removal")

# Remove Component Definitions in RecoveryPortal
content = read('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx')
start = content.find("// ── PAYMENT TYPE MODAL ──────────────────────────────────────────")
end = content.find("// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────")
if start != -1 and end != -1:
    content = content[:start] + content[end:]
    write('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx', content)
    print("OK patch (RecoveryPortal component removal)")
else:
    print("MISSING (RecoveryPortal component removal)")

print("\nDone! Run git add/commit/push to deploy.")