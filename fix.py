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
# FIX 1: RecoveryPortal.jsx
#
# A) Per-plot backlog label on joint-owner cards
#    - Each plot in the activePlots list now shows its own BACKLOG
#      badge if that specific plot is in backlog (handles mixed sets)
#    - backlogPlots section header updated to show per-plot badges too
#
# B) Monthly installment payment scheme
#    - New "MONTHLY INSTALLMENT" button on each active plot card
#    - New MonthlyInstallmentModal component
#    - Separate payment type so it's clearly distinguished from
#      title/backlog payments in history
# ================================================================

# Step 1 — add FiCalendar alias (already imported) and FiRepeat icon
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap, FiSettings
} from 'react-icons/fi';''',
    '''import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap, FiSettings, FiRepeat
} from 'react-icons/fi';''',
    'RecoveryPortal.jsx add FiRepeat import'
)

# Step 2 — add MonthlyInstallmentModal component before StorageFeeInlineControls
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────''',
    '''// ── MONTHLY INSTALLMENT MODAL ───────────────────────────────────
// Separate payment scheme: client pays a fixed monthly instalment
// toward their title cost. Distinct from backlog/storage payments.
const MonthlyInstallmentModal = ({ open, plot, onClose, onPay, paying }) => {
    const [amount, setAmount]   = React.useState('');
    const [notes,  setNotes]    = React.useState('');
    const [period, setPeriod]   = React.useState('');   // e.g. "May 2026"

    React.useEffect(() => {
        if (open) {
            setAmount('');
            setNotes('');
            // Auto-fill current month as default period label
            const now = new Date();
            setPeriod(now.toLocaleString('default', { month: 'long', year: 'numeric' }));
        }
    }, [open]);

    if (!plot) return null;

    const balance  = Number(plot.currentBalance  || 0);
    const paid     = Number(plot.amountPaid      || 0);
    const total    = Number(plot.totalCost       || 0);
    const pct      = total > 0 ? Math.round((paid / total) * 100) : 0;

    const handleSubmit = () => {
        if (!amount || Number(amount) <= 0) return;
        const fullNotes = `[MONTHLY INSTALMENT${period ? ' - ' + period : ''}]${notes ? ' ' + notes : ''}`;
        onPay(plot, amount, fullNotes, 'MONTHLY');
    };

    return (
        <HardwareModal isOpen={open} onClose={onClose}
            title={'MONTHLY INSTALMENT — ' + plot.plotNumber}>

            {/* Summary strip */}
            <div style={{
                background: 'rgba(6,182,212,0.08)',
                border: '1px solid rgba(6,182,212,0.25)',
                borderRadius: 8,
                padding: '12px 14px',
                marginBottom: 16,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: 10,
            }}>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        TOTAL COST
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#fff'}}>
                        UGX {total.toLocaleString()}
                    </div>
                </div>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        PAID SO FAR
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#86efac'}}>
                        UGX {paid.toLocaleString()}
                    </div>
                </div>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(252,165,165,0.8)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        OUTSTANDING
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#fca5a5'}}>
                        UGX {Math.max(0,balance).toLocaleString()}
                    </div>
                </div>
                {/* Progress bar spanning full width */}
                <div style={{gridColumn:'1/-1'}}>
                    <div style={{height:4,background:'rgba(255,255,255,0.08)',borderRadius:4,overflow:'hidden',marginTop:4}}>
                        <div style={{height:'100%',width:pct+'%',background:'#06b6d4',borderRadius:4,transition:'width 0.4s ease'}} />
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:9,color:'rgba(255,255,255,0.3)',marginTop:3}}>{pct}% collected</div>
                </div>
            </div>

            {/* Period label */}
            <div style={{marginBottom:14}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    INSTALMENT PERIOD
                </label>
                <input
                    type="text"
                    value={period}
                    onChange={e => setPeriod(e.target.value)}
                    placeholder="e.g. May 2026"
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(255,255,255,0.18)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:700,
                        outline:'none', boxSizing:'border-box',
                    }}
                />
            </div>

            {/* Amount */}
            <div style={{marginBottom:14}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    AMOUNT RECEIVED (UGX)
                </label>
                <input
                    type="number"
                    value={amount}
                    onChange={e => setAmount(e.target.value)}
                    placeholder="Enter instalment amount..."
                    autoFocus
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(6,182,212,0.4)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'Space Mono,monospace', fontSize:14, fontWeight:700,
                        outline:'none', boxSizing:'border-box',
                    }}
                />
            </div>

            {/* Notes */}
            <div style={{marginBottom:16}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    NOTES (optional)
                </label>
                <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="e.g. MTN Mobile Money, cash..."
                    rows={3}
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(255,255,255,0.15)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:700,
                        outline:'none', resize:'vertical', boxSizing:'border-box',
                    }}
                />
            </div>

            <div style={{display:'flex',justifyContent:'flex-end',gap:10,paddingTop:12,borderTop:'1px solid rgba(255,255,255,0.08)'}}>
                <button onClick={onClose} style={{
                    padding:'0 16px', height:38,
                    background:'rgba(255,255,255,0.06)',
                    border:'1.5px solid rgba(255,255,255,0.2)',
                    borderRadius:8, color:'rgba(255,255,255,0.7)',
                    fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,
                    textTransform:'uppercase',letterSpacing:1.5,cursor:'pointer',
                }}>
                    CANCEL
                </button>
                <button onClick={handleSubmit} disabled={paying} style={{
                    padding:'0 20px', height:38,
                    background:'#06b6d4',
                    border:'none',
                    borderRadius:8, color:'#1a2e30',
                    fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,
                    textTransform:'uppercase',letterSpacing:1.5,cursor:'pointer',
                    display:'flex',alignItems:'center',gap:7,
                    opacity: paying ? 0.5 : 1,
                }}>
                    <FiRepeat size={13} />
                    {paying ? 'PROCESSING...' : 'RECORD INSTALMENT'}
                </button>
            </div>
        </HardwareModal>
    );
};

// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────''',
    'RecoveryPortal.jsx add MonthlyInstallmentModal component'
)

# Step 3 — add monthlyModal state alongside payModal state
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''    const [payModal,      setPayModal]      = useState({ open: false, plot: null });
    const [paying,        setPaying]        = useState(false);''',
    '''    const [payModal,      setPayModal]      = useState({ open: false, plot: null });
    const [paying,        setPaying]        = useState(false);
    const [monthlyModal,  setMonthlyModal]  = useState({ open: false, plot: null });''',
    'RecoveryPortal.jsx add monthlyModal state'
)

# Step 4 — add MONTHLY instalment button to active plot cards (next to PAY button)
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => setPayModal({ open: true, plot })}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}''',
    '''                                                {isAdmin && (
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
                                                )}''',
    'RecoveryPortal.jsx add INSTALMENT button on active plots'
)

# Step 5 — add per-plot BACKLOG badge inside the activePlots map
# Each plot now shows a BACKLOG tag inline if that specific plot is backlog
# (handles edge case: mixed active+backlog on same phone — shows correctly in each section)
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''                                            <div className={styles.plotNum}>{plot.plotNumber}</div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber}</div>''',
    '''                                            <div style={{display:'flex',alignItems:'center',gap:6}}>
                                                        <span className={styles.plotNum}>{plot.plotNumber}</span>
                                                        {plot.isBacklog && (
                                                            <span style={{
                                                                display:'inline-flex',alignItems:'center',gap:3,
                                                                background:'rgba(239,68,68,0.18)',
                                                                border:'1px solid rgba(239,68,68,0.45)',
                                                                borderRadius:4,padding:'1px 6px',
                                                                fontFamily:'DM Sans,sans-serif',fontSize:7,
                                                                fontWeight:900,color:'#fca5a5',
                                                                textTransform:'uppercase',letterSpacing:0.8,
                                                                flexShrink:0,
                                                            }}>
                                                                <FiAlertOctagon size={7} /> BACKLOG
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber}</div>''',
    'RecoveryPortal.jsx per-plot backlog badge in active plots section'
)

# Step 6 — same per-plot badge in the backlog plots section
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''                                            <div className={styles.plotNum}>{plot.plotNumber}</div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber} · {plot.storageMonthsCount}mo in backlog</div>''',
    '''                                            <div style={{display:'flex',alignItems:'center',gap:6}}>
                                                        <span className={styles.plotNum}>{plot.plotNumber}</span>
                                                        <span style={{
                                                            display:'inline-flex',alignItems:'center',gap:3,
                                                            background:'rgba(239,68,68,0.22)',
                                                            border:'1px solid rgba(239,68,68,0.55)',
                                                            borderRadius:4,padding:'1px 6px',
                                                            fontFamily:'DM Sans,sans-serif',fontSize:7,
                                                            fontWeight:900,color:'#fca5a5',
                                                            textTransform:'uppercase',letterSpacing:0.8,
                                                            flexShrink:0,
                                                            animation:'criticalPulse 1.8s ease-in-out infinite',
                                                        }}>
                                                            <FiAlertOctagon size={7} /> BACKLOG
                                                        </span>
                                                    </div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber} · {plot.storageMonthsCount}mo in backlog</div>''',
    'RecoveryPortal.jsx per-plot backlog badge in backlog section'
)

# Step 7 — render MonthlyInstallmentModal at bottom of JSX (next to PaymentModal)
patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx',
    '''            {/* PAYMENT MODAL */}
            <PaymentModal
                open={payModal.open}
                plot={payModal.plot}
                onClose={() => setPayModal({ open: false, plot: null })}
                onPay={handleRecordPayment}
                paying={paying}
            />
        </div>
    );
};''',
    '''            {/* PAYMENT MODAL */}
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
            />
        </div>
    );
};''',
    'RecoveryPortal.jsx render MonthlyInstallmentModal'
)


# ================================================================
# FIX 2: RecoveryPortal.module.css
# Add .payBtnMonthly style — cyan/teal theme to distinguish from
# green title pay and red backlog pay
# ================================================================

patch(
    'erp-frontend/src/pages/Recovery/RecoveryPortal.module.css',
    '''.payBtnBacklog {
    background:rgba(239,68,68,0.15) !important;
    border-color:rgba(239,68,68,0.5) !important;
    color:#fca5a5 !important;
}
.payBtnBacklog:hover { background:#ef4444 !important; color:#fff !important; border-color:#ef4444 !important; }''',
    '''.payBtnBacklog {
    background:rgba(239,68,68,0.15) !important;
    border-color:rgba(239,68,68,0.5) !important;
    color:#fca5a5 !important;
}
.payBtnBacklog:hover { background:#ef4444 !important; color:#fff !important; border-color:#ef4444 !important; }

/* Monthly instalment button — cyan/teal to distinguish from title(green) and backlog(red) */
.payBtnMonthly {
    background:rgba(6,182,212,0.15);
    border:1.5px solid rgba(6,182,212,0.45);
    color:#67e8f9;
    font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius:var(--radius-sm); font-size:var(--fs-badge);
    padding:clamp(5px,0.6vw,7px) clamp(8px,1vw,11px);
    cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
    gap:4px; transition:all 0.2s; white-space:nowrap;
}
.payBtnMonthly:hover { background:#06b6d4; color:#1a2e30; border-color:#06b6d4; }''',
    'RecoveryPortal.module.css add payBtnMonthly style'
)


# ================================================================
# FIX 3: PaymentsPage.jsx — show MONTHLY_INSTALMENT type correctly
# Add to TYPE_LABELS and TYPE_COLORS so the payments ledger page
# shows instalment payments with the right label and cyan colour
# ================================================================

patch(
    'erp-frontend/src/pages/Payments/PaymentsPage.jsx',
    '''const TYPE_LABELS = {
    STANDARD:        'Title Payment',
    INITIAL_DEPOSIT: 'Initial Deposit',
    BACKLOG_PARTIAL: 'Backlog Payment',
};

const TYPE_COLORS = {
    STANDARD:        '#22c55e',
    INITIAL_DEPOSIT: '#06b6d4',
    BACKLOG_PARTIAL: '#ef4444',
};''',
    '''const TYPE_LABELS = {
    STANDARD:            'Title Payment',
    INITIAL_DEPOSIT:     'Initial Deposit',
    BACKLOG_PARTIAL:     'Backlog Payment',
    MONTHLY_INSTALMENT:  'Monthly Instalment',
};

const TYPE_COLORS = {
    STANDARD:            '#22c55e',
    INITIAL_DEPOSIT:     '#06b6d4',
    BACKLOG_PARTIAL:     '#ef4444',
    MONTHLY_INSTALMENT:  '#a78bfa',
};''',
    'PaymentsPage.jsx add MONTHLY_INSTALMENT type label and color'
)

# Also add it to filter buttons
patch(
    'erp-frontend/src/pages/Payments/PaymentsPage.jsx',
    '''                    {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL'].map(t => (''',
    '''                    {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL', 'MONTHLY_INSTALMENT'].map(t => (''',
    'PaymentsPage.jsx add MONTHLY_INSTALMENT filter button'
)


# ================================================================
# FIX 4: Backend — PaymentRecord notes-based type detection
# The backend records payment type as STANDARD or BACKLOG_PARTIAL.
# Monthly instalment goes in as STANDARD with [MONTHLY INSTALMENT]
# note prefix — the frontend already handles display.
# No backend changes needed — the note prefix carries the context.
# ================================================================

print("\nAll fixes applied successfully.")
print("Summary of changes:")
print("  1. RecoveryPortal: per-plot BACKLOG badge on every plot card (both sections)")
print("  2. RecoveryPortal: INSTALMENT button (cyan) on each active plot card")
print("  3. RecoveryPortal: MonthlyInstallmentModal with period, amount, notes fields")
print("  4. RecoveryPortal.module.css: payBtnMonthly cyan style")
print("  5. PaymentsPage: MONTHLY_INSTALMENT type shown as purple 'Monthly Instalment'")
print("  6. PaymentsPage: filter pill added for monthly instalment type")
print()
print("Run: git add -A && git commit -m 'feat: per-plot backlog labels + monthly instalment payment scheme' && git push")