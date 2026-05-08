import os

def patch(path, old, new, label=""):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if old not in content:
            print(f"  MISSING: {label or path}")
            return False
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.replace(old, new, 1))
        print(f"  OK: {label or path}")
        return True
    except Exception as e:
        print(f"  ERROR: {label or path} -> {e}")
        return False

def write_file(path, content, label=""):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  WRITTEN: {label or path}")

# ==============================================================================
# FIX 1: SIDEBAR - Slightly larger nav links, keep NYENZ small, no scroll
# ==============================================================================
print("=== FIX 1: Sidebar nav links slightly larger ===")

SIDEBAR_CSS = "erp-frontend/src/components/layout/Sidebar.module.css"

patch(SIDEBAR_CSS,
    """.navItem {
    display: flex;
    align-items: center;
    gap: clamp(8px, 1vw, 12px);
    padding: clamp(8px, 1vw, 11px) clamp(8px, 1vw, 12px);
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: background 0.25s, color 0.25s, border-color 0.25s;
    border-left: 3px solid transparent;
    white-space: nowrap;
    outline: none;
}""",
    """.navItem {
    display: flex;
    align-items: center;
    gap: clamp(9px, 1.1vw, 13px);
    padding: clamp(9px, 1.1vw, 12px) clamp(9px, 1.1vw, 13px);
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: background 0.25s, color 0.25s, border-color 0.25s;
    border-left: 3px solid transparent;
    white-space: nowrap;
    outline: none;
}""",
    "Sidebar navItem slightly larger padding")

patch(SIDEBAR_CSS,
    """.navIcon {
    font-size: clamp(14px, 1.5vw, 17px);
    min-width: clamp(18px, 1.8vw, 22px);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}""",
    """.navIcon {
    font-size: clamp(15px, 1.6vw, 18px);
    min-width: clamp(19px, 2vw, 23px);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}""",
    "Sidebar navIcon slightly larger")

patch(SIDEBAR_CSS,
    """.navText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px, 0.85vw, 10px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}""",
    """.navText {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.95vw, 11px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}""",
    "Sidebar navText slightly larger font")

patch(SIDEBAR_CSS,
    """.collapsed .navItem {
    padding: clamp(9px, 1.1vw, 12px) 0;
    justify-content: center;
    border-left-width: 0;
    border-right: 3px solid transparent;
}""",
    """.collapsed .navItem {
    padding: clamp(10px, 1.2vw, 13px) 0;
    justify-content: center;
    border-left-width: 0;
    border-right: 3px solid transparent;
}""",
    "Sidebar collapsed navItem slightly larger")

# ==============================================================================
# FIX 2: HARDWARESELECT - Fix dropdown z-index completely
# ==============================================================================
print("=== FIX 2: HardwareSelect - full dropdown z-index fix ===")

HW_SELECT_CSS = "erp-frontend/src/components/common/HardwareSelect.module.css"

# Full rewrite of HardwareSelect CSS
HW_SELECT_CSS_FULL = """.fieldWrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    position: relative;
    margin-bottom: 15px;
    z-index: 1;
}

/* CRITICAL: When open, this wrapper must float above all other content */
.openWrapper {
    z-index: 9999 !important;
    overflow: visible !important;
    position: relative !important;
}

.label {
    color: #FFFFFF !important;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.selectBox {
    background: #ffffff;
    border-radius: var(--input-radius, 8px);
    border: 2px solid rgba(238, 140, 58, 0.3);
    padding: 0 clamp(10px, 1.4vw, 18px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: 0.3s ease;
    height: var(--input-height, 44px);
    position: relative;
    z-index: 1;
}

.selectBox:hover, .active {
    border-color: var(--orange);
    box-shadow: 0 0 20px rgba(238, 140, 58, 0.2);
}

.currentValue {
    color: var(--navy);
    font-weight: 700;
    font-size: var(--input-font, 14px);
}

.icon {
    color: var(--orange);
    transition: 0.3s;
    flex-shrink: 0;
}

.active .icon { transform: rotate(180deg); }

.dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: #ffffff;
    border: 2px solid var(--orange);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 8px 20px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: slideIn 0.2s ease-out;
    z-index: 99999 !important;
    min-width: 100%;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}

.option {
    padding: 14px 20px;
    color: var(--navy);
    font-weight: 600;
    font-size: 14px;
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    transition: 0.2s;
}

.option:last-child { border-bottom: none; }

.option:hover {
    background: var(--orange);
    color: white;
}

.selected {
    background: #f1f5f9;
    border-left: 5px solid var(--orange);
}

/* Mobile responsive */
@media (max-width: 480px) {
    .selectBox {
        height: var(--input-height, 40px);
        font-size: 12px;
    }
    .option {
        padding: 12px 14px;
        font-size: 13px;
    }
}
"""
write_file(HW_SELECT_CSS, HW_SELECT_CSS_FULL, "HardwareSelect CSS - full z-index fix")

# ==============================================================================
# FIX 3: AUDIT PAGE - Filter dropdowns appear on top, mobile fix
# ==============================================================================
print("=== FIX 3: Audit page - full fix for dropdowns and mobile ===")

AUDIT_CSS = "erp-frontend/src/pages/Audit/AuditPage.module.css"

# Read current audit CSS
with open(AUDIT_CSS, "r", encoding="utf-8", errors="replace") as f:
    audit_content = f.read()

# Fix controlHub - needs to be the positioning parent with high z-index
patch(AUDIT_CSS,
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 20; overflow: visible; }""",
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 200; overflow: visible; }""",
    "Audit controlHub z-index 200")

# Fix timelineFrame - overflow visible
patch(AUDIT_CSS,
    """.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: visible; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }
.timelineFrameInner { overflow: hidden; border-radius: var(--radius); }""",
    """.timelineFrame { background: var(--panel-bg); border: 2px solid var(--orange-border); border-radius: var(--radius); overflow: hidden; box-shadow: 0 10px 36px rgba(0,0,0,0.2); }""",
    "Audit timelineFrame overflow hidden (dropdowns escape via z-index now)")

# Fix filterGrid - ensure it has overflow visible for dropdowns
patch(AUDIT_CSS,
    """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: visible;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 4px;
    position: relative;
    z-index: 10;
}
.filterGrid::-webkit-scrollbar { display: none; }""",
    """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: visible;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 4px;
    position: relative;
    z-index: 100;
}
.filterGrid::-webkit-scrollbar { display: none; }""",
    "Audit filterGrid z-index 100")

# Fix hwSelectWrap - critical z-index for dropdown positioning
patch(AUDIT_CSS,
    """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 1 1 clamp(110px, 14vw, 190px);
    max-width: clamp(130px, 18vw, 210px);
    min-width: 0;
    position: relative;
    z-index: 50;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }

/* Hide HardwareSelect label */
.hwSelectWrap label {
    display: none !important;
}""",
    """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 0 0 auto;
    width: clamp(130px, 16vw, 200px);
    min-width: 0;
    position: relative;
    z-index: 9000;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }

/* Hide HardwareSelect label */
.hwSelectWrap label {
    display: none !important;
}""",
    "Audit hwSelectWrap z-index 9000")

# Fix hwSelectWrap override section - ensure dropdown z-index
patch(AUDIT_CSS,
    """.hwSelectWrap [class*="dropdown"] {
    z-index: 9999 !important;
    position: absolute !important;
}""",
    """.hwSelectWrap [class*="dropdown"] {
    z-index: 99999 !important;
    position: absolute !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.7) !important;
}""",
    "Audit hwSelectWrap dropdown z-index 99999")

# Fix the mobile 768px section
patch(AUDIT_CSS,
    """@media (max-width: 768px) {
    .header      { flex-direction: column; align-items: flex-start; }
    .controlHub  { gap: var(--gap-md); }
    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        width: 100%;
        gap: 6px;
        padding-bottom: 4px;
    }
    .hwSelectWrap { flex: 0 0 auto; max-width: 140px; min-width: 110px; }
    .resetBtn    { flex: 0 0 auto; padding: 0 12px; }
    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }
    .timeMark    { grid-column: 1; }
    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }
    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }
    .iconChassis { display: none; }
    .actionMeta  { align-items: flex-end; }
}""",
    """@media (max-width: 768px) {
    .header      { flex-direction: column; align-items: flex-start; }
    .controlHub  { gap: var(--gap-md); }
    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: visible;
        width: 100%;
        gap: 6px;
        padding-bottom: 6px;
        padding-top: 2px;
    }
    .hwSelectWrap { width: 130px; min-width: 110px; }
    .resetBtn    { flex: 0 0 auto; padding: 0 10px; }
    .logMain     { grid-template-columns: 1fr 1fr; gap: var(--gap-md); align-items: start; }
    .timeMark    { grid-column: 1; }
    .actionMark  { grid-column: 2; justify-self: end; text-align: right; }
    .targetMark  { grid-column: 1 / span 2; margin-top: var(--gap-md); }
    .iconChassis { display: none; }
    .actionMeta  { align-items: flex-end; }
}""",
    "Audit 768px mobile - overflow-y visible for dropdowns")

# Fix hwSelectWrap override for selectBox height on mobile
patch(AUDIT_CSS,
    """.hwSelectWrap .selectBox,
.hwSelectWrap [class*="selectBox"] {
    height: clamp(34px, 4vw, 40px) !important;
    padding: 0 clamp(8px, 1.1vw, 14px) !important;
    font-size: clamp(9px, 0.9vw, 11px) !important;
    letter-spacing: 1.5px !important;
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    border-radius: var(--radius-sm) !important;
    overflow: visible !important;
}""",
    """.hwSelectWrap .selectBox,
.hwSelectWrap [class*="selectBox"] {
    height: clamp(34px, 4vw, 40px) !important;
    padding: 0 clamp(8px, 1.1vw, 14px) !important;
    font-size: clamp(9px, 0.9vw, 11px) !important;
    letter-spacing: 1.5px !important;
    background: rgba(26, 46, 48, 0.75) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
    color: rgba(255, 255, 255, 0.85) !important;
    border-radius: var(--radius-sm) !important;
    overflow: visible !important;
    position: relative !important;
    z-index: 9000 !important;
}""",
    "Audit selectBox position relative z-index")

# ==============================================================================
# FIX 4: PAYMENTS PAGE - Complete rewrite with proper table filters + styling
# ==============================================================================
print("=== FIX 4: Payments page - full rewrite with table filters ===")

PAYMENTS_JSX = "erp-frontend/src/pages/Payments/PaymentsPage.jsx"

PAYMENTS_JSX_FULL = """// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX,
    FiChevronRight, FiAlertOctagon, FiUser, FiRefreshCw,
    FiCalendar, FiMapPin, FiLayers
} from 'react-icons/fi';
import api from '../../api/axios';
import styles from './PaymentsPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const TYPE_LABELS = {
    STANDARD:        'Title Payment',
    INITIAL_DEPOSIT: 'Initial Deposit',
    BACKLOG_PARTIAL: 'Backlog Payment',
};

const TYPE_COLORS = {
    STANDARD:        '#22c55e',
    INITIAL_DEPOSIT: '#06b6d4',
    BACKLOG_PARTIAL: '#ef4444',
};

const PaymentsPage = () => {
    const navigate = useNavigate();
    const [payments,   setPayments]   = useState([]);
    const [loading,    setLoading]    = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [typeFilter, setTypeFilter] = useState('ALL');
    const [sortDir,    setSortDir]    = useState('desc');

    // Column filters for table headers
    const [dateFilter,  setDateFilter]  = useState('');
    const [plotFilter,  setPlotFilter]  = useState('');
    const [ownerFilter, setOwnerFilter] = useState('');
    const [amountSort,  setAmountSort]  = useState(null); // 'asc' | 'desc' | null

    const loadPayments = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get('/recovery/payments/all');
            setPayments(res.data || []);
        } catch {
            setPayments([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadPayments(); }, [loadPayments]);

    const filtered = useMemo(() => {
        let list = [...payments];

        // Top-level type filter
        if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);

        // Global search
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(p =>
                p.plotNumber?.toLowerCase().includes(t) ||
                p.ownerName?.toLowerCase().includes(t) ||
                p.recordedBy?.toLowerCase().includes(t) ||
                p.notes?.toLowerCase().includes(t)
            );
        }

        // Column filters
        if (dateFilter.trim()) {
            const df = dateFilter.toLowerCase();
            list = list.filter(p =>
                new Date(p.timestamp).toLocaleDateString().toLowerCase().includes(df)
            );
        }
        if (plotFilter.trim()) {
            const pf = plotFilter.toLowerCase();
            list = list.filter(p => p.plotNumber?.toLowerCase().includes(pf));
        }
        if (ownerFilter.trim()) {
            const of_ = ownerFilter.toLowerCase();
            list = list.filter(p => p.ownerName?.toLowerCase().includes(of_));
        }

        // Sorting
        if (amountSort) {
            list.sort((a, b) => {
                const diff = Number(a.amountPaid || 0) - Number(b.amountPaid || 0);
                return amountSort === 'asc' ? diff : -diff;
            });
        } else {
            list.sort((a, b) => {
                const da = new Date(a.timestamp), db = new Date(b.timestamp);
                return sortDir === 'desc' ? db - da : da - db;
            });
        }

        return list;
    }, [payments, typeFilter, searchTerm, sortDir, dateFilter, plotFilter, ownerFilter, amountSort]);

    const totalCollected = useMemo(() =>
        filtered.reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const titleTotal = useMemo(() =>
        filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL')
                .reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const storageTotal = useMemo(() =>
        filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL')
                .reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const toggleAmountSort = () => {
        setAmountSort(prev => prev === 'desc' ? 'asc' : prev === 'asc' ? null : 'desc');
    };

    const SortArrow = ({ field }) => {
        if (field === 'amount' && amountSort) {
            return <span className={styles.sortArrow}>{amountSort === 'desc' ? ' ↓' : ' ↑'}</span>;
        }
        if (field === 'date' && !amountSort) {
            return <span className={styles.sortArrow}>{sortDir === 'desc' ? ' ↓' : ' ↑'}</span>;
        }
        return <span className={styles.sortArrowInactive}> ↕</span>;
    };

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records - title payments and storage fee collections</p>
                </div>
                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={16} />
                </button>
            </header>

            <div className={styles.summaryRow}>
                <div className={styles.sumCard}>
                    <label>TOTAL SHOWN</label>
                    <strong>UGX {fmt(totalCollected)}</strong>
                    <span>{filtered.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>
                    <label style={{ color: '#22c55e' }}>TITLE PAYMENTS</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(titleTotal)}</strong>
                    <span>{filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL').length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>
                    <label style={{ color: '#ef4444' }}>BACKLOG PAYMENTS</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(storageTotal)}</strong>
                    <span>{filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL').length} records</span>
                </div>
            </div>

            {/* Global search + type filter row */}
            <div className={styles.controls}>
                <div className={styles.searchWrap}>
                    <FiSearch className={styles.searchIcon} />
                    <input type="search" className={styles.searchInput}
                        placeholder="Search plot ID, owner name, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                    {searchTerm && (
                        <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
                            <FiX size={14} />
                        </button>
                    )}
                </div>
                <div className={styles.filterRow}>
                    {['ALL', 'STANDARD', 'INITIAL_DEPOSIT', 'BACKLOG_PARTIAL'].map(t => (
                        <button key={t}
                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}
                            onClick={() => setTypeFilter(t)}>
                            {t === 'ALL' ? 'ALL TYPES' : TYPE_LABELS[t]}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className={styles.emptyState}>
                    <div className={styles.emptyInner}>
                        <div className={styles.loadingSpinner} />
                        <span>Loading payments...</span>
                    </div>
                </div>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                {/* DATE header with sort + filter */}
                                <th className={styles.thWithFilter}>
                                    <div className={styles.thTop}>
                                        <button className={styles.thSortBtn} onClick={() => { setAmountSort(null); setSortDir(d => d === 'desc' ? 'asc' : 'desc'); }}>
                                            <FiCalendar size={10} /> DATE <SortArrow field="date" />
                                        </button>
                                    </div>
                                    <input className={styles.colFilter} placeholder="Filter date..." value={dateFilter}
                                        onChange={e => setDateFilter(e.target.value)} />
                                </th>
                                {/* PLOT header with filter */}
                                <th className={styles.thWithFilter}>
                                    <div className={styles.thTop}><FiMapPin size={10} /> PLOT</div>
                                    <input className={styles.colFilter} placeholder="Filter plot..." value={plotFilter}
                                        onChange={e => setPlotFilter(e.target.value)} />
                                </th>
                                {/* OWNER header with filter */}
                                <th className={styles.thWithFilter}>
                                    <div className={styles.thTop}><FiUser size={10} /> OWNER</div>
                                    <input className={styles.colFilter} placeholder="Filter owner..." value={ownerFilter}
                                        onChange={e => setOwnerFilter(e.target.value)} />
                                </th>
                                <th>TYPE</th>
                                {/* AMOUNT with sort */}
                                <th className={styles.thSortable} onClick={toggleAmountSort}>
                                    <FiDollarSign size={10} /> AMOUNT PAID <SortArrow field="amount" />
                                </th>
                                <th>BALANCE AFTER</th>
                                <th>RECORDED BY</th>
                                <th>NOTES</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.length === 0 ? (
                                <tr>
                                    <td colSpan="9" className={styles.noRecords}>
                                        <div className={styles.noRecordsInner}>
                                            <FiLayers className={styles.noRecordsIcon} />
                                            <span>NO PAYMENT RECORDS FOUND</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : filtered.map((pay, i) => (
                                <tr key={pay.id || i} className={styles.row}>
                                    <td>
                                        <div className={styles.dateCell}>
                                            <span>{new Date(pay.timestamp).toLocaleDateString()}</span>
                                            <span className={styles.time}>
                                                {new Date(pay.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <strong className={styles.plotNum}>{pay.plotNumber || '---'}</strong>
                                    </td>
                                    <td className={styles.ownerCell}>{pay.ownerName || '---'}</td>
                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            background: `${TYPE_COLORS[pay.paymentType] || '#888'}22`,
                                            color: TYPE_COLORS[pay.paymentType] || '#888',
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType] || '#888'}44`
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={9} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>
                                    <td>
                                        <strong className={styles.amount} style={{ color: TYPE_COLORS[pay.paymentType] || '#fff' }}>
                                            UGX {fmt(pay.amountPaid)}
                                        </strong>
                                    </td>
                                    <td className={styles.balance}>
                                        {pay.balanceAfter != null ? `UGX ${fmt(pay.balanceAfter)}` : '---'}
                                    </td>
                                    <td>
                                        <span className={styles.recorder}>
                                            <FiUser size={10} /> {pay.recordedBy}
                                        </span>
                                    </td>
                                    <td className={styles.notesCell}>{pay.notes || '---'}</td>
                                    <td>
                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={() => navigate(`/folder/${pay.projectId}`)}>
                                                <FiChevronRight size={13} />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PaymentsPage;
"""

write_file(PAYMENTS_JSX, PAYMENTS_JSX_FULL, "PaymentsPage.jsx - full rewrite with column filters")

PAYMENTS_CSS_FULL = """.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --red:           #ef4444;
    --green:         #10b981;
    --cyan:          #06b6d4;

    --gap-xl:    clamp(14px, 2vw, 22px);
    --gap-lg:    clamp(10px, 1.5vw, 18px);
    --gap-md:    clamp(7px,  1.1vw, 13px);
    --radius:    10px;
    --radius-sm: 6px;

    --fs-h1:     clamp(18px, 2.5vw, 24px);
    --fs-sub:    clamp(8px,  0.85vw, 10px);
    --fs-label:  clamp(7px,  0.75vw, 9px);
    --fs-value:  clamp(11px, 1.1vw, 13px);
    --fs-tag:    clamp(7px,  0.75vw, 9px);
    --fs-input:  clamp(11px, 1.1vw, 13px);
    --fs-th:     clamp(7px,  0.78vw, 9px);
    --fs-td:     clamp(10px, 1.05vw, 12px);
    --fs-meta:   clamp(8px,  0.85vw, 10px);
    --fs-btn:    clamp(9px,  0.9vw, 11px);

    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(60px, 8vw, 100px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}

@keyframes warmBoot {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* PAGE HEADER */
.pageHeader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 24px);
    border-left: clamp(3px, 0.4vw, 5px) solid var(--orange);
    padding: clamp(10px, 1.4vw, 16px) clamp(16px, 2.2vw, 28px);
    background: rgba(255, 255, 255, 0.62);
    border-radius: 0 12px 12px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
}
.headerLeft { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.title { font-family: 'Cinzel', serif; color: #1a2e30; font-size: var(--fs-h1); font-weight: 700; margin: 0; letter-spacing: 1.5px; text-transform: uppercase; line-height: 1; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

.refreshBtn {
    background: rgba(26,46,48,0.08);
    border: 1px solid rgba(26,46,48,0.15);
    color: #1a2e30;
    border-radius: 8px;
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    transition: all 0.2s;
    flex-shrink: 0;
    height: var(--btn-height, clamp(36px, 4.5vw, 44px));
}
.refreshBtn:hover { background: #EE8C3A; color: #fff; border-color: #EE8C3A; }

/* SUMMARY CARDS */
.summaryRow {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: clamp(10px, 1.4vw, 16px);
    margin-bottom: clamp(14px, 2vw, 20px);
}
.sumCard {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    padding: clamp(12px, 1.5vw, 18px);
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.sumCard label { font-family: 'DM Sans', sans-serif; font-size: var(--fs-label); font-weight: 900; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1px; }
.sumCard strong { font-family: 'Space Mono', monospace; font-size: var(--fs-value); color: #fff; font-weight: 700; word-break: break-all; }
.sumCard span { font-size: var(--fs-label); color: rgba(255,255,255,0.35); }

/* CONTROLS */
.controls {
    display: flex;
    flex-direction: column;
    gap: var(--gap-md);
    margin-bottom: clamp(14px, 2vw, 20px);
}

.searchWrap {
    position: relative;
    display: flex;
    align-items: center;
    background: #fff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    height: clamp(36px, 4.5vw, 44px);
    max-width: clamp(300px, 50vw, 560px);
    transition: border-color 0.2s;
}
.searchWrap:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 12px; color: #EE8C3A; font-size: clamp(14px, 1.5vw, 17px); pointer-events: none; flex-shrink: 0; }
.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 36px 0 38px;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn {
    position: absolute; right: 8px; background: transparent; border: none;
    cursor: pointer; color: rgba(26,46,48,0.4); display: flex;
    align-items: center; padding: 4px; border-radius: 4px;
}
.clearBtn:hover { color: #1a2e30; }

/* FILTER ROW */
.filterRow {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: clamp(6px, 1vw, 10px);
    padding-bottom: 4px;
    scrollbar-width: none;
}
.filterRow::-webkit-scrollbar { display: none; }

.filterBtn {
    background: rgba(26, 46, 48, 0.75);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.85);
    padding: clamp(7px, 0.9vw, 9px) clamp(10px, 1.3vw, 16px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px);
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

/* TABLE */
.tableWrap {
    overflow-x: auto;
    border-radius: var(--radius);
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    box-shadow: 0 8px 28px rgba(0,0,0,0.15);
    -webkit-overflow-scrolling: touch;
    /* Orange top separator line like ledger */
    border-top: 2px solid var(--orange);
}
.table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    min-width: clamp(700px, 90vw, 1100px);
}

/* TABLE HEADER */
.table thead tr {
    border-bottom: 2px solid var(--orange);
}
.table th {
    background: #162a2c;
    padding: 0;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-th);
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    text-align: left;
    white-space: nowrap;
    vertical-align: top;
    border-right: 1px solid rgba(255,255,255,0.05);
}
.table th:last-child { border-right: none; }

/* Header with column filter input */
.thWithFilter {
    min-width: clamp(100px, 12vw, 150px);
}
.thTop {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
    padding-bottom: 4px;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.colFilter {
    display: block;
    width: calc(100% - 16px);
    margin: 0 8px clamp(6px, 0.8vw, 8px) 8px;
    padding: clamp(4px, 0.5vw, 6px) clamp(6px, 0.8vw, 8px);
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 4px;
    color: rgba(255,255,255,0.8);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.85vw, 10px);
    font-weight: 700;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
}
.colFilter:focus { border-color: var(--orange); background: rgba(238,140,58,0.08); }
.colFilter::placeholder { color: rgba(255,255,255,0.25); font-style: italic; font-weight: 500; }

/* Sortable header */
.thSortable {
    cursor: pointer;
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
    transition: background 0.15s;
    min-width: clamp(100px, 12vw, 150px);
}
.thSortable:hover { background: rgba(238,140,58,0.08); }

.thSortBtn {
    background: transparent;
    border: none;
    color: var(--orange);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-th);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0;
    transition: color 0.2s;
}
.thSortBtn:hover { color: #fff; }

.sortArrow { color: #fff; font-size: 10px; opacity: 0.9; }
.sortArrowInactive { color: rgba(255,255,255,0.25); font-size: 10px; }

/* Regular th (no filter) */
.table th:not(.thWithFilter):not(.thSortable) {
    padding: clamp(8px, 1vw, 11px) clamp(10px, 1.3vw, 14px);
}

/* ROWS */
.row {
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: background 0.15s, border-left-color 0.15s;
    border-left: 3px solid transparent;
}
.row:hover { background: rgba(255,255,255,0.04); border-left-color: var(--orange); }
.table td {
    padding: clamp(9px, 1.2vw, 13px) clamp(10px, 1.3vw, 14px);
    color: rgba(255,255,255,0.9);
    vertical-align: middle;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
    border-right: 1px solid rgba(255,255,255,0.04);
}
.table td:last-child { border-right: none; }

/* CELL TYPES */
.dateCell { display: flex; flex-direction: column; gap: 2px; white-space: nowrap; font-weight: 700; }
.time { font-family: 'Space Mono', monospace; font-size: var(--fs-label); opacity: 0.45; }
.plotNum { font-family: 'Space Mono', monospace; color: #EE8C3A; font-size: var(--fs-value); font-weight: 700; letter-spacing: 0.5px; }
.ownerCell { font-weight: 700; color: #fff; max-width: clamp(100px, 14vw, 180px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.typeBadge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: clamp(2px, 0.3vw, 4px) clamp(6px, 0.8vw, 9px);
    border-radius: 4px;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: 0.5px;
}
.amount { font-family: 'Space Mono', monospace; font-size: var(--fs-value); font-weight: 700; }
.balance { font-family: 'Space Mono', monospace; font-size: var(--fs-meta); color: rgba(255,255,255,0.5); }
.recorder { display: inline-flex; align-items: center; gap: 5px; font-size: var(--fs-meta); color: rgba(255,255,255,0.6); }
.notesCell { font-style: italic; color: rgba(255,255,255,0.45); max-width: clamp(100px, 14vw, 180px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--fs-meta); }
.goBtn {
    background: rgba(238,140,58,0.1); border: 1px solid rgba(238,140,58,0.35);
    color: #EE8C3A; border-radius: 6px; padding: 6px; cursor: pointer;
    display: flex; align-items: center; transition: all 0.2s;
}
.goBtn:hover { background: #EE8C3A; color: #1a2e30; }

/* NO RECORDS */
.noRecords { text-align: center; padding: 0; }
.noRecordsInner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(8px, 1.2vw, 14px);
    padding: clamp(40px, 6vw, 70px) 20px;
    color: rgba(255,255,255,0.2);
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-meta);
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.noRecordsIcon { font-size: clamp(30px, 5vw, 48px); opacity: 0.15; }

/* LOADING / EMPTY STATE */
.emptyState {
    background: var(--panel-bg);
    border: 1.5px solid var(--orange-border);
    border-radius: var(--radius);
    box-shadow: 0 8px 28px rgba(0,0,0,0.15);
    padding: clamp(40px, 6vw, 70px) 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.emptyInner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    color: rgba(255,255,255,0.25);
    font-family: 'Space Mono', monospace;
    font-size: var(--fs-meta);
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.loadingSpinner {
    width: 32px; height: 32px;
    border: 3px solid rgba(238,140,58,0.15);
    border-top-color: #EE8C3A;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* RESPONSIVE */
@media (max-width: 900px) {
    .summaryRow { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
    .summaryRow { grid-template-columns: 1fr; gap: 8px; }
    .searchWrap { max-width: 100%; }
    .filterRow { gap: 6px; }
    .table { min-width: 650px; }
}
@media (max-width: 480px) {
    .summaryRow { grid-template-columns: 1fr 1fr; }
    .sumCard strong { font-size: 13px; }
    .table { min-width: 600px; }
    .table th { font-size: 7px; letter-spacing: 1px; }
    .table td { padding: 8px; }
    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
    .colFilter { font-size: 8px; padding: 3px 5px; }
}
"""

write_file("erp-frontend/src/pages/Payments/PaymentsPage.module.css", PAYMENTS_CSS_FULL, "PaymentsPage CSS - full rewrite with column filters")

# ==============================================================================
# FIX 5: RECOVERY PORTAL - Fix "NO TARGETS FOUND" visibility + ACTIVE badge
# ==============================================================================
print("=== FIX 5: Recovery portal - fix empty state + section header visibility ===")

RECOVERY_CSS = "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"

# Fix emptyGate - make it more visible on light background
patch(RECOVERY_CSS,
    """.emptyGate { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; padding:60px 20px; text-align:center; }
.emptyIcon  { font-size:50px; color:var(--emerald); opacity:0.25; }
.emptyTitle { font-family:'Cinzel',serif; font-size:clamp(13px,1.6vw,18px); font-weight:700; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1.5px; margin:0; }""",
    """.emptyGate {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: clamp(40px, 8vw, 80px) 20px;
    text-align: center;
    background: rgba(26, 46, 48, 0.35);
    border: 1.5px solid rgba(238, 140, 58, 0.15);
    border-radius: 12px;
    margin-top: 8px;
}
.emptyIcon {
    font-size: clamp(40px, 6vw, 60px);
    color: #10b981;
    opacity: 0.4;
    filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.3));
}
.emptyTitle {
    font-family: 'Cinzel', serif;
    font-size: clamp(14px, 1.8vw, 20px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.55);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 0;
    text-shadow: 0 0 20px rgba(255,255,255,0.1);
}""",
    "Recovery emptyGate - better visible on any background")

# Fix sectionHeader - ACTIVE (1) label visibility - it's on dark panel bg so white is fine
# The issue is when it renders on a light background - need dark text
patch(RECOVERY_CSS,
    """.sectionHeader { font-family:'DM Sans',sans-serif; font-size:var(--fs-label); font-weight:900; color:rgba(255,255,255,0.6); text-transform:uppercase; letter-spacing:2px; margin-bottom:var(--gap-lg); display:flex; align-items:center; gap:8px; padding-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.07); }
.sectionHeaderBacklog { color:#fca5a5; border-bottom-color:rgba(239,68,68,0.2); }""",
    """.sectionHeader {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 1vw, 11px);
    font-weight: 900;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: var(--gap-lg);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: clamp(5px, 0.7vw, 8px) clamp(10px, 1.3vw, 16px);
    padding-bottom: clamp(5px, 0.7vw, 8px);
    border-radius: 6px;
    background: rgba(26, 46, 48, 0.75);
    border: 1px solid rgba(238, 140, 58, 0.25);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.sectionHeaderBacklog {
    color: #fca5a5;
    background: rgba(127, 29, 29, 0.5);
    border-color: rgba(239, 68, 68, 0.35);
}""",
    "Recovery sectionHeader - dark pill badge always visible")

# ==============================================================================
# FIX 6: SEARCH ICON - Fix icon appearing above text (icon and text on same line)
# ==============================================================================
print("=== FIX 6: Search inputs - icon inline with text, not above ===")

# Fix Recovery search
patch(RECOVERY_CSS,
    """.searchIcon { position:absolute; left:12px; color:var(--orange); font-size:16px; pointer-events:none; }""",
    """.searchIcon { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--orange); font-size:16px; pointer-events:none; flex-shrink:0; }""",
    "Recovery searchIcon - vertically centered")

# Fix Ledger search icon
LEDGER_CSS = "erp-frontend/src/pages/Ledger/LedgerPage.module.css"
patch(LEDGER_CSS,
    """.searchIcon {
    position: absolute;
    left: clamp(10px, 1.2vw, 14px);
    top: 50%;
    transform: translateY(-50%);
    color: var(--orange);
    font-size: clamp(14px, 1.5vw, 18px);
    pointer-events: none;
    flex-shrink: 0;
}""",
    """.searchIcon {
    position: absolute;
    left: clamp(10px, 1.2vw, 14px);
    top: 50%;
    transform: translateY(-50%);
    color: var(--orange);
    font-size: clamp(14px, 1.5vw, 18px);
    pointer-events: none;
    flex-shrink: 0;
    line-height: 1;
    display: flex;
    align-items: center;
}""",
    "Ledger searchIcon - flex align center")

# Fix Audit search icon
AUDIT_CSS = "erp-frontend/src/pages/Audit/AuditPage.module.css"
patch(AUDIT_CSS,
    """.searchIcon { position: absolute; left: clamp(10px,1.2vw,14px); color: var(--orange); font-size: clamp(14px,1.5vw,18px); pointer-events: none; }""",
    """.searchIcon { position: absolute; left: clamp(10px,1.2vw,14px); top: 50%; transform: translateY(-50%); color: var(--orange); font-size: clamp(14px,1.5vw,18px); pointer-events: none; flex-shrink: 0; display: flex; align-items: center; line-height: 1; }""",
    "Audit searchIcon - vertically centered")

# Fix Recovery search inner container
patch(RECOVERY_CSS,
    """.searchInner { position:relative; display:flex; align-items:center; background:#fff; border:1.5px solid #c8d6d7; border-radius:var(--radius-sm); width:100%; max-width:clamp(300px,42vw,500px); height:clamp(36px,4vw,42px); transition:border-color 0.2s; }""",
    """.searchInner { position:relative; display:flex; align-items:center; background:#fff; border:1.5px solid #c8d6d7; border-radius:var(--radius-sm); width:100%; max-width:clamp(300px,42vw,500px); height:clamp(36px,4vw,42px); transition:border-color 0.2s; overflow:hidden; }""",
    "Recovery searchInner overflow hidden")

# Fix clear button vertical centering in all search bars
patch(RECOVERY_CSS,
    """.searchClear { position:absolute; right:8px; background:transparent; border:none; cursor:pointer; color:rgba(26,46,48,0.4); display:flex; align-items:center; padding:3px; border-radius:4px; }""",
    """.searchClear { position:absolute; right:8px; top:50%; transform:translateY(-50%); background:transparent; border:none; cursor:pointer; color:rgba(26,46,48,0.4); display:flex; align-items:center; padding:3px; border-radius:4px; }""",
    "Recovery searchClear - vertically centered")

# ==============================================================================
# FIX 7: MODAL POPUPS - Uniform styling for all modals (HardwareModal)
# ==============================================================================
print("=== FIX 7: HardwareModal - uniform, responsive, professional ===")

HW_MODAL_CSS = "erp-frontend/src/components/common/HardwareModal.module.css"

HW_MODAL_CSS_FULL = """/* PATH: erp-frontend/src/components/common/HardwareModal.module.css
   Uniform modal design - all popups (Record Payment, Archive Log, etc.)
*/

.backdrop {
    position: fixed;
    inset: 0;
    background: rgba(10, 20, 25, 0.80);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
    animation: fadeIn 0.2s ease-out;
    padding: clamp(12px, 3vw, 24px);
    box-sizing: border-box;
}

.modalBody {
    width: 100%;
    max-width: clamp(300px, 90vw, 520px);
    max-height: 90vh;
    overflow-y: auto;
    background: linear-gradient(160deg, #1c3335 0%, #213e40 100%);
    border: 2px solid rgba(238, 140, 58, 0.4);
    border-radius: 14px;
    padding: clamp(20px, 3vw, 32px);
    position: relative;
    box-shadow:
        0 30px 80px rgba(0, 0, 0, 0.7),
        0 0 0 1px rgba(255,255,255,0.04),
        inset 0 1px 0 rgba(255,255,255,0.06);
    animation: slideUp 0.25s cubic-bezier(0.2, 1, 0.3, 1);
    scrollbar-width: thin;
    scrollbar-color: rgba(238,140,58,0.4) transparent;
}
.modalBody::-webkit-scrollbar { width: 4px; }
.modalBody::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: clamp(16px, 2.5vw, 24px);
    padding-bottom: clamp(10px, 1.5vw, 14px);
    border-bottom: 1px solid rgba(238, 140, 58, 0.25);
}

.title {
    font-family: 'Cinzel', serif;
    color: var(--orange, #EE8C3A);
    font-size: clamp(12px, 1.4vw, 16px);
    font-weight: 700;
    letter-spacing: clamp(1px, 0.2vw, 2.5px);
    text-transform: uppercase;
    line-height: 1.2;
    flex: 1;
    min-width: 0;
    word-break: break-word;
}

.closeBtn {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.5);
    font-size: clamp(16px, 2vw, 20px);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    width: clamp(28px, 3.5vw, 36px);
    height: clamp(28px, 3.5vw, 36px);
    border-radius: 8px;
    flex-shrink: 0;
    margin-left: 12px;
}

.closeBtn:hover {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.4);
    color: #ef4444;
    transform: rotate(90deg);
}

.content {
    position: relative;
    z-index: 2;
}

/* Bottom orange glow accent */
.footerGlow {
    position: absolute;
    bottom: 0;
    left: 10%;
    right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(238, 140, 58, 0.6), transparent);
    box-shadow: 0 0 12px rgba(238, 140, 58, 0.3);
    border-radius: 0 0 14px 14px;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Mobile */
@media (max-width: 480px) {
    .modalBody {
        padding: clamp(16px, 5vw, 20px);
        border-radius: 12px;
        max-height: 88vh;
    }
    .title { font-size: 12px; letter-spacing: 1px; }
    .header { margin-bottom: 14px; padding-bottom: 10px; }
}
"""

write_file(HW_MODAL_CSS, HW_MODAL_CSS_FULL, "HardwareModal CSS - uniform responsive design")

# ==============================================================================
# FIX 8: RECOVERY PORTAL - Record Payment modal improvements
# ==============================================================================
print("=== FIX 8: Recovery portal - modal input improvements ===")

RECOVERY_CSS = "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css"

# Fix notebookArea in recovery - consistent with other modals
patch(RECOVERY_CSS,
    """.notebookArea { width:100%; min-height:90px; background:#fff; border-radius:8px; border:1.5px solid rgba(238,140,58,0.5); padding:10px 12px; color:#1a2e30; font-family:'DM Sans',sans-serif; font-size:13px; font-weight:600; resize:vertical; box-sizing:border-box; display:block; outline:none; transition:box-shadow 0.2s; }
.notebookArea:focus { box-shadow:0 0 0 3px rgba(238,140,58,0.2); }
.notebookArea::placeholder { font-weight:500; color:rgba(26,46,48,0.35); }
.modalFooter { margin-top:12px; display:flex; justify-content:flex-end; }""",
    """.notebookArea {
    width: 100% !important;
    min-height: 90px;
    background: #fff;
    border-radius: 8px;
    border: 1.5px solid rgba(238, 140, 58, 0.5);
    padding: clamp(10px, 1.3vw, 14px);
    color: #1a2e30;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 600;
    resize: vertical;
    box-sizing: border-box;
    display: block;
    outline: none;
    transition: box-shadow 0.2s, border-color 0.2s;
}
.notebookArea:focus {
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.2);
    border-color: #EE8C3A;
}
.notebookArea::placeholder { font-weight: 500; color: rgba(26,46,48,0.35); }
.modalFooter { margin-top: clamp(12px, 1.5vw, 16px); display: flex; justify-content: flex-end; }""",
    "Recovery notebookArea - responsive sizing")

# ==============================================================================
# FIX 9: FOLDER PAGE - Record Payment modal styling (inline styles to proper classes)
# ==============================================================================
print("=== FIX 9: Folder page modal inputs - responsive ===")

FOLDER_CSS = "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css"

# Add proper modal input styles after .modalFooter
patch(FOLDER_CSS,
    """.modalFooter { display: flex; justify-content: flex-end; gap: clamp(8px, 1.2vw, 12px); margin-top: clamp(10px, 1.4vw, 16px); flex-wrap: wrap; }""",
    """.modalFooter { display: flex; justify-content: flex-end; gap: clamp(8px, 1.2vw, 12px); margin-top: clamp(10px, 1.4vw, 16px); flex-wrap: wrap; }

/* Modal form inputs - consistent across all popup modals */
.modalInput {
    width: 100% !important;
    padding: clamp(10px, 1.3vw, 13px) clamp(12px, 1.5vw, 16px);
    border-radius: 8px;
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.9);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(13px, 1.3vw, 15px);
    font-weight: 600;
    outline: none;
    transition: border-color 0.2s, background 0.2s;
    box-sizing: border-box;
    display: block;
}
.modalInput:focus {
    border-color: rgba(238,140,58,0.6);
    background: rgba(238,140,58,0.06);
}
.modalInput::placeholder { color: rgba(255,255,255,0.25); font-weight: 500; }

.modalTextarea {
    width: 100% !important;
    padding: clamp(10px, 1.3vw, 13px) clamp(12px, 1.5vw, 16px);
    border-radius: 8px;
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.9);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 600;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
    display: block;
    min-height: clamp(70px, 10vw, 90px);
}
.modalTextarea:focus { border-color: rgba(238,140,58,0.6); }
.modalTextarea::placeholder { color: rgba(255,255,255,0.25); font-weight: 500; }

.modalLabel {
    display: block;
    margin-bottom: clamp(5px, 0.7vw, 8px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 900;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.modalInfoBox {
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 8px;
    padding: clamp(10px, 1.3vw, 14px);
    margin-bottom: clamp(14px, 1.8vw, 18px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(11px, 1.1vw, 13px);
    font-weight: 700;
    color: rgba(255,255,255,0.8);
    line-height: 1.5;
}

.modalInfoBoxDanger {
    background: rgba(239,68,68,0.08);
    border-color: rgba(239,68,68,0.25);
    color: #fef2f2;
}
.modalFieldGroup { margin-bottom: clamp(12px, 1.5vw, 16px); }""",
    "FolderPage modal form input classes")

# ==============================================================================
# FIX 10: RECOVERY PORTAL - improve backlogPayInfo and activePayInfo
# ==============================================================================
print("=== FIX 10: Recovery portal - fix modal inline styles ===")

patch(RECOVERY_CSS,
    """.backlogPayInfo { display:flex; align-items:flex-start; gap:12px; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.35); border-radius:8px; padding:14px; margin-bottom:14px; font-size:13px; color:#fef2f2; }
.activePayInfo { background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.3); border-radius:8px; padding:12px; margin-bottom:14px; font-size:13px; color:#f0fdf4; }""",
    """.backlogPayInfo {
    display: flex;
    align-items: flex-start;
    gap: clamp(10px, 1.3vw, 14px);
    background: rgba(239,68,68,0.10);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px;
    padding: clamp(12px, 1.5vw, 16px);
    margin-bottom: clamp(12px, 1.5vw, 16px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 13px);
    color: #fef2f2;
    line-height: 1.6;
    font-weight: 700;
}
.activePayInfo {
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 8px;
    padding: clamp(10px, 1.3vw, 14px);
    margin-bottom: clamp(12px, 1.5vw, 16px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 13px);
    color: #f0fdf4;
    font-weight: 700;
    line-height: 1.5;
}""",
    "Recovery modal info boxes - responsive")

# ==============================================================================
# FIX 11: RECOVERY + ALL PAGES - fix search input so icon is NEVER above text
# ==============================================================================
print("=== FIX 11: All search inputs - icon always beside text, not above ===")

# The root cause is that if searchInner uses display:flex but the icon has position:absolute
# without top:50%, the browser might render it differently on some screens.
# Add defensive height to all search containers.

# Fix LedgerPage search
patch(LEDGER_CSS,
    """.searchInner {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 100%;
}""",
    """.searchInner {
    position: relative;
    display: flex;
    flex-direction: row;
    align-items: center;
    width: 100%;
    height: clamp(36px, 4.5vw, 44px);
}""",
    "Ledger searchInner - row direction, fixed height")

# The ledger search pill already has correct positioning, let's fix the input padding
patch(LEDGER_CSS,
    """.searchInput {
    width: 100%;
    height: clamp(36px, 4.5vw, 44px);
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(32px, 4vw, 40px) 0 clamp(34px, 4.5vw, 44px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 800;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    -webkit-appearance: none;
    appearance: none;
}""",
    """.searchInput {
    width: 100%;
    height: clamp(36px, 4.5vw, 44px);
    background: #ffffff;
    border: 1.5px solid #c8d6d7;
    border-radius: var(--radius-sm);
    padding: 0 clamp(32px, 4vw, 40px) 0 clamp(36px, 4.5vw, 46px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-input);
    font-weight: 800;
    color: var(--navy);
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    -webkit-appearance: none;
    appearance: none;
    line-height: clamp(36px, 4.5vw, 44px);
}""",
    "Ledger searchInput line-height equals height")

# ==============================================================================
# FIX 12: LEDGER PAGE - Add orange separator + corner decor visual cue
# ==============================================================================
print("=== FIX 12: Ledger page - orange separator already via HardwarePanel, enhance ===")

# The HardwarePanel already has the orange border. The ledger has a -30px margin on tableScroll
# which breaks it out of the panel. Let's ensure the table header has strong orange separator.
patch(LEDGER_CSS,
    """.table thead tr {
    border-bottom: 2px solid var(--orange);
}""",
    """.table thead tr {
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
}""",
    "Ledger table thead - stronger orange separator")

# ==============================================================================
# FIX 13: ALL PAGES - Ensure all error/warning/empty states are uniformly visible
# ==============================================================================
print("=== FIX 13: All pages - uniform error/warning state visibility ===")

# Fix IntakePage error states - ensure they're visible
INTAKE_CSS = "erp-frontend/src/pages/Intake/IntakePage.module.css"
# The intake page error states use .fieldError which should be visible, already done

# Fix Dashboard error HUD
DASH_CSS = "erp-frontend/src/pages/Dashboard/Dashboard.module.css"
# Already has errorHUD with good styling

# Fix AuditPage empty/loading states
patch(AUDIT_CSS,
    """.loadingPulse { text-align: center; padding: clamp(36px,6vw,60px) 0; font-family: 'DM Sans', sans-serif; color: var(--orange); font-weight: 900; letter-spacing: 3px; animation: glowPulse 2s infinite; font-size: var(--fs-meta); text-transform: uppercase; }
@keyframes glowPulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.emptySignal { text-align: center; padding: clamp(28px,5vw,50px) 0; font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.2); font-weight: 900; font-size: var(--fs-meta); letter-spacing: 2px; text-transform: uppercase; }""",
    """.loadingPulse {
    text-align: center;
    padding: clamp(36px,6vw,60px) 0;
    font-family: 'DM Sans', sans-serif;
    color: var(--orange);
    font-weight: 900;
    letter-spacing: 3px;
    animation: glowPulse 2s infinite;
    font-size: var(--fs-meta);
    text-transform: uppercase;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
}
@keyframes glowPulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.emptySignal {
    text-align: center;
    padding: clamp(28px,5vw,50px) 20px;
    font-family: 'Space Mono', monospace;
    color: rgba(255,255,255,0.25);
    font-weight: 900;
    font-size: var(--fs-meta);
    letter-spacing: 2px;
    text-transform: uppercase;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: rgba(255,255,255,0.02);
    border-radius: 8px;
    border: 1px dashed rgba(255,255,255,0.08);
    margin: 8px;
}""",
    "Audit loadingPulse + emptySignal - better styled")

# ==============================================================================
# FIX 14: Index.css - Remove global input height override that breaks modals
# ==============================================================================
print("=== FIX 14: Index.css - fix global input override ===")

INDEX_CSS = "erp-frontend/src/index.css"

# The global input height override forces height on ALL inputs including modal inputs
# which breaks them. Let's make it only apply to form contexts, not modal inputs.
# Actually, let's just add a min-height instead of fixed height for textarea
patch(INDEX_CSS,
    """/* Apply to all native inputs */
input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
textarea {
    height: var(--input-height);
    font-size: var(--input-font) !important;
    padding-left: var(--input-px) !important;
    padding-right: var(--input-px) !important;
    border-radius: var(--input-radius) !important;
    box-sizing: border-box;
    width: 100% !important;
}

textarea {
    height: auto !important;
    min-height: clamp(80px, 12vw, 120px);
    padding-top: var(--input-px) !important;
    padding-bottom: var(--input-px) !important;
}

/* Labels */
label {
    font-size: var(--label-font);
}""",
    """/* Apply to all native inputs */
input:not([type="checkbox"]):not([type="radio"]):not([type="file"]) {
    height: var(--input-height);
    font-size: var(--input-font) !important;
    padding-left: var(--input-px) !important;
    padding-right: var(--input-px) !important;
    border-radius: var(--input-radius) !important;
    box-sizing: border-box;
    width: 100% !important;
    line-height: var(--input-height);
}

textarea {
    height: auto !important;
    min-height: clamp(80px, 12vw, 120px);
    padding-top: var(--input-px) !important;
    padding-bottom: var(--input-px) !important;
    font-size: var(--input-font) !important;
    padding-left: var(--input-px) !important;
    padding-right: var(--input-px) !important;
    border-radius: var(--input-radius) !important;
    box-sizing: border-box;
    width: 100% !important;
    resize: vertical;
}

/* Labels */
label {
    font-size: var(--label-font);
}""",
    "Index.css - separate input and textarea rules, add line-height")

# ==============================================================================
# FIX 15: LLM Guide Addendum
# ==============================================================================
print("=== FIX 15: LLM Guide Addendum update ===")

guide_lines = [
    "# GE SOLUTIONS ERP -- CONTEXT ADDENDUM V2",
    "# Last updated: May 2026 - Full UI Polish Pass",
    "",
    "## KEY FIXES THIS SESSION",
    "",
    "### SIDEBAR",
    "- Nav links slightly larger (9-11px font, 9-12px padding)",
    "- NYENZ branding stays small",
    "- No scroll - all 8 items always visible",
    "- Collapsed width 52px",
    "",
    "### HARDWARESELECT DROPDOWN",
    "- z-index: 99999 on dropdown - always appears above everything",
    "- openWrapper has z-index: 9999 and overflow: visible",
    "- Fixed full CSS rewrite",
    "",
    "### AUDIT PAGE",
    "- controlHub z-index: 200",
    "- hwSelectWrap z-index: 9000",
    "- filterGrid overflow-y: visible on all screen sizes",
    "- Mobile: filter row stays horizontal, overflow-x scroll",
    "- Dropdown z-index 99999 guaranteed",
    "",
    "### PAYMENTS PAGE",
    "- Full rewrite with column-level filters on DATE, PLOT, OWNER columns",
    "- AMOUNT PAID column is sortable",
    "- Removed redundant DATE sort button (date sort is in th header)",
    "- Ledger-style dark table with orange border-top separator",
    "- NO RECORDS FOUND uses ledger-style empty state with icon",
    "- Type filters match ledger style (dark inactive, orange active)",
    "",
    "### RECOVERY PAGE",
    "- NO TARGETS FOUND now has dark pill background with visible border",
    "- ACTIVE (1) section header uses dark pill badge (always visible on any bg)",
    "- BACKLOG section header uses red pill badge",
    "",
    "### SEARCH INPUTS (ALL PAGES)",
    "- Search icon always vertically centered beside text (top: 50%, transform: translateY(-50%))",
    "- Never appears above text",
    "",
    "### MODAL POPUPS (ALL POPUPS)",
    "- HardwareModal CSS fully rewritten for uniform design",
    "- Responsive max-height: 90vh with scrollbar",
    "- Consistent padding, border, animation across all modals",
    "- Close button has hover state with rotation animation",
    "",
    "### EMPTY / ERROR STATES",
    "- Audit emptySignal has subtle dashed border background",
    "- Recovery emptyGate has dark panel background with border",
    "- Payments uses icon + text empty state like ledger",
    "",
    "## RULES FOR FUTURE CHANGES",
    "- Search icon: always use position:absolute, left:12px, top:50%, transform:translateY(-50%)",
    "- Section headers on variable backgrounds: always use dark pill with border, never bare text",
    "- Dropdown z-index: minimum 9999, use 99999 for critical dropdowns",
    "- Modal: always use HardwareModal component, max-height:90vh, overflow-y:auto",
    "- Empty states: dark panel bg + rgba border + icon + Space Mono text",
    "",
    "See LLM_CONTEXT_GUIDE.md for full project context.",
]

guide_content = "\n".join(guide_lines)
with open("LLM_CONTEXT_GUIDE_ADDENDUM.md", "w", encoding="utf-8") as f:
    f.write(guide_content)
print("  OK: LLM_CONTEXT_GUIDE_ADDENDUM.md")

print("")
print("=== ALL DONE ===")
print("Run: git add -A && git commit -m 'UI polish: sidebar links, dropdown z-index, payments column filters, recovery visibility, search icon fix, modal uniformity' && git push")