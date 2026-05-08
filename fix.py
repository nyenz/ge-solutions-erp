import os

def patch(path, old, new, label=""):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print(f"  MISSING: {label or path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print(f"  OK: {label or path}")

def write_file(path, content, label=""):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  WRITTEN: {label or path}")

# ============================================================
# FIX 1: PAYMENTS PAGE - rewrite table to match Ledger design
# ============================================================

PAYMENTS_CSS = """.container {
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
    --fs-th:     clamp(8px,  0.85vw, 10px);
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
    border: 1.5px solid rgba(26,46,48,0.2);
    color: #1a2e30;
    border-radius: var(--radius-sm);
    padding: 0 clamp(12px,1.5vw,16px);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: var(--fs-btn);
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.2s;
    height: clamp(34px, 4vw, 40px);
    flex-shrink: 0;
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
    transition: border-color 0.2s, box-shadow 0.2s;
}
.searchWrap:focus-within { border-color: #EE8C3A; box-shadow: 0 0 0 3px rgba(238,140,58,0.14); }
.searchIcon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #EE8C3A; font-size: clamp(14px, 1.5vw, 17px); pointer-events: none; flex-shrink: 0; }
.searchInput {
    width: 100%; border: none; outline: none; background: transparent;
    color: #1a2e30; padding: 0 36px 0 38px;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
    height: 100%;
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    background: transparent; border: none;
    cursor: pointer; color: rgba(26,46,48,0.4); display: flex;
    align-items: center; padding: 4px; border-radius: 4px; transition: color 0.15s, background 0.15s;
}
.clearBtn:hover { color: #1a2e30; background: rgba(26,46,48,0.08); }

/* FILTER ROW - matches Ledger style exactly */
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

/* ─── TABLE SHELL - identical to Ledger ─────────────────────────── */
.tableWrap {
    background: rgba(0, 0, 0, 0.15);
    border-radius: var(--radius);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    scrollbar-color: rgba(238,140,58,0.35) transparent;
}
.tableWrap::-webkit-scrollbar { height: 4px; }
.tableWrap::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.35); border-radius: 2px; }

.table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    min-width: clamp(700px, 90vw, 1100px);
}

/* TABLE HEADER - matches Ledger exactly */
.table thead tr {
    background: #162a2c;
}
.table th {
    background: #162a2c;
    padding: clamp(11px, 1.5vw, 18px) clamp(12px, 1.8vw, 20px);
    text-align: left;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-th);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 3px solid var(--orange);
    box-shadow: 0 3px 0 rgba(238,140,58,0.15);
    white-space: nowrap;
    user-select: none;
}
.table th:first-child { border-radius: var(--radius) 0 0 0; }
.table th:last-child  { border-radius: 0 var(--radius) 0 0; }

/* Sortable header */
.thSortable {
    cursor: pointer;
    transition: background 0.15s;
}
.thSortable:hover { background: rgba(238,140,58,0.07); }

/* ROWS - matches Ledger */
.table tbody tr {
    cursor: pointer;
    transition: background 0.18s, border-left-color 0.18s;
    border-left: 3px solid transparent;
    outline: none;
}
.table tbody tr:hover {
    background: rgba(255, 255, 255, 0.04);
    border-left-color: var(--orange);
}
.table tbody tr:focus-visible {
    background: rgba(238, 140, 58, 0.07);
    outline: 2px solid var(--orange);
    outline-offset: -2px;
}
.table td {
    padding: clamp(9px, 1.3vw, 14px) clamp(12px, 1.8vw, 20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    vertical-align: middle;
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
}

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
    background: rgba(238,140,58,0.1); border: 1.5px solid rgba(238,140,58,0.35);
    color: #EE8C3A; border-radius: var(--radius-sm); padding: clamp(5px,0.7vw,7px) clamp(8px,1vw,10px);
    cursor: pointer; display: flex; align-items: center; gap: 4px;
    transition: all 0.2s; font-size: var(--fs-tag); font-weight: 900;
    font-family: 'DM Sans', sans-serif; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap;
}
.goBtn:hover { background: #EE8C3A; color: #1a2e30; }
.sortArrow { color: #fff; font-size: 10px; opacity: 0.9; margin-left: 3px; }
.sortArrowInactive { color: rgba(255,255,255,0.25); font-size: 10px; margin-left: 3px; }

/* NO RECORDS - matches Ledger emptyCell */
.noRecords { text-align: center; }
.noRecordsInner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(8px, 1.2vw, 14px);
    padding: clamp(40px, 6vw, 70px) 20px;
    color: rgba(255,255,255,0.22);
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
    display: flex; align-items: center; justify-content: center;
}
.emptyInner {
    display: flex; flex-direction: column; align-items: center;
    gap: 14px; color: rgba(255,255,255,0.25);
    font-family: 'Space Mono', monospace; font-size: var(--fs-meta);
    font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
.loadingSpinner {
    width: 32px; height: 32px;
    border: 3px solid rgba(238,140,58,0.15);
    border-top-color: #EE8C3A; border-radius: 50%;
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
}
"""

write_file("erp-frontend/src/pages/Payments/PaymentsPage.module.css", PAYMENTS_CSS, "PaymentsPage.module.css - full rewrite to match Ledger")

# ─── Rewrite PaymentsPage.jsx to use clean table (no column filters, simpler) ───

PAYMENTS_JSX = """// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX,
    FiChevronRight, FiAlertOctagon, FiUser, FiRefreshCw,
    FiLayers, FiArrowUp, FiArrowDown
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
    const [sortKey,    setSortKey]    = useState('date');
    const [sortDir,    setSortDir]    = useState('desc');

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

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    const filtered = useMemo(() => {
        let list = [...payments];
        if (typeFilter !== 'ALL') list = list.filter(p => p.paymentType === typeFilter);
        if (searchTerm.trim()) {
            const t = searchTerm.toLowerCase();
            list = list.filter(p =>
                p.plotNumber?.toLowerCase().includes(t) ||
                p.ownerName?.toLowerCase().includes(t) ||
                p.recordedBy?.toLowerCase().includes(t) ||
                p.notes?.toLowerCase().includes(t)
            );
        }
        list.sort((a, b) => {
            let aVal, bVal;
            if      (sortKey === 'amount') { aVal = Number(a.amountPaid||0); bVal = Number(b.amountPaid||0); }
            else if (sortKey === 'plot')   { aVal = a.plotNumber||''; bVal = b.plotNumber||''; }
            else if (sortKey === 'owner')  { aVal = a.ownerName||''; bVal = b.ownerName||''; }
            else                           { aVal = new Date(a.timestamp); bVal = new Date(b.timestamp); }
            if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDir === 'asc' ?  1 : -1;
            return 0;
        });
        return list;
    }, [payments, typeFilter, searchTerm, sortKey, sortDir]);

    const totalCollected = useMemo(() => filtered.reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);
    const titleTotal     = useMemo(() => filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL').reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);
    const storageTotal   = useMemo(() => filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL').reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const SortIcon = ({ field }) => {
        if (sortKey !== field) return <span className={styles.sortArrowInactive}> ↕</span>;
        return sortDir === 'asc'
            ? <FiArrowUp  style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />
            : <FiArrowDown style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />;
    };

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Payments</h1>
                    <p className={styles.subtitle}>All payment records — title payments and storage fee collections</p>
                </div>
                <button className={styles.refreshBtn} onClick={loadPayments} aria-label="Refresh">
                    <FiRefreshCw size={14} /> REFRESH
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
                                <th className={styles.thSortable} onClick={() => handleSort('date')}
                                    aria-sort={sortKey==='date' ? (sortDir==='asc'?'ascending':'descending') : 'none'}>
                                    DATE <SortIcon field="date" />
                                </th>
                                <th className={styles.thSortable} onClick={() => handleSort('plot')}
                                    aria-sort={sortKey==='plot' ? (sortDir==='asc'?'ascending':'descending') : 'none'}>
                                    PLOT <SortIcon field="plot" />
                                </th>
                                <th className={styles.thSortable} onClick={() => handleSort('owner')}
                                    aria-sort={sortKey==='owner' ? (sortDir==='asc'?'ascending':'descending') : 'none'}>
                                    OWNER <SortIcon field="owner" />
                                </th>
                                <th>TYPE</th>
                                <th className={styles.thSortable} onClick={() => handleSort('amount')}
                                    aria-sort={sortKey==='amount' ? (sortDir==='asc'?'ascending':'descending') : 'none'}>
                                    AMOUNT PAID <SortIcon field="amount" />
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
                                <tr key={pay.id || i}
                                    onClick={() => pay.projectId && navigate(`/folder/${pay.projectId}`)}
                                    tabIndex={pay.projectId ? 0 : undefined}
                                    onKeyDown={e => { if (pay.projectId && (e.key==='Enter'||e.key===' ')) { e.preventDefault(); navigate(`/folder/${pay.projectId}`); }}}>
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
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType] || '#888'}55`
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
                                                onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}`); }}>
                                                <FiChevronRight size={12} /> VIEW
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

write_file("erp-frontend/src/pages/Payments/PaymentsPage.jsx", PAYMENTS_JSX, "PaymentsPage.jsx - clean table matching Ledger")

# ============================================================
# FIX 2: AUDIT PAGE - fix HardwareSelect z-index + filterGrid overflow
# The problem: the select dropdowns were clipped by the filterGrid container
# ============================================================

patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
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
    """.filterGrid {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: clamp(6px, 1vw, 10px);
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: visible;
    scrollbar-width: none;
    width: 100%;
    padding-bottom: 4px;
    padding-top: 4px;
    position: relative;
    z-index: 9000;
    isolation: isolate;
}
.filterGrid::-webkit-scrollbar { display: none; }""",
    "Audit filterGrid - fix z-index and overflow for dropdowns"
)

# Fix hwSelectWrap to have proper stacking context and height
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
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
    """/* Compact select wraps - same height as filter buttons */
.hwSelectWrap {
    flex: 0 0 auto;
    width: clamp(130px, 16vw, 200px);
    min-width: 0;
    position: relative;
    z-index: 9000;
    overflow: visible !important;
}
/* Override HardwareSelect internal margin */
.hwSelectWrap > * { margin-bottom: 0 !important; }
/* Force the inner fieldWrapper to overflow visible too */
.hwSelectWrap > div { overflow: visible !important; z-index: 9000 !important; }

/* Hide HardwareSelect label */
.hwSelectWrap label {
    display: none !important;
}""",
    "Audit hwSelectWrap - ensure dropdown escapes container"
)

# Also fix controlHub z-index
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 200; overflow: visible; }""",
    """.controlHub { display: flex; flex-direction: column; gap: var(--gap-md); margin-bottom: var(--gap-lg); width: 100%; position: relative; z-index: 9500; overflow: visible; isolation: isolate; }""",
    "Audit controlHub - higher z-index"
)

# Fix the mobile media query that reverts overflow
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    """    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: visible;
        width: 100%;
        gap: 6px;
        padding-bottom: 6px;
        padding-top: 2px;
    }""",
    """    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: visible;
        width: 100%;
        gap: 6px;
        padding-bottom: 6px;
        padding-top: 4px;
        z-index: 9000;
    }""",
    "Audit mobile filterGrid - keep z-index"
)

# Fix the 480px override too
patch(
    "erp-frontend/src/pages/Audit/AuditPage.module.css",
    """    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 5px;
    }""",
    """    .filterGrid  {
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 5px;
        overflow-y: visible;
        z-index: 9000;
    }""",
    "Audit 480px filterGrid - keep overflow-y visible"
)

# ============================================================
# FIX 3: UNIFORM MODAL POPUP CSS
# Create a shared modal-form.module.css for use inside modals
# Also fix FolderPage modals and RecoveryPortal modals to use uniform styling
# ============================================================

# The key fix: add a global modal form style to HardwareModal.module.css
# so all popup content has the same spacing, fonts, buttons

patch(
    "erp-frontend/src/components/common/HardwareModal.module.css",
    """@keyframes fadeIn {
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
}""",
    """@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── UNIFORM MODAL FORM ELEMENTS ────────────────────────────────
   Use these classes inside any HardwareModal content for
   consistent spacing, fonts, and button design across all popups.
   ──────────────────────────────────────────────────────────────── */

/* Text input / number input inside a modal */
.modalInput {
    width: 100%;
    padding: clamp(11px, 1.4vw, 14px) clamp(12px, 1.6vw, 16px);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.07);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.92);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(13px, 1.3vw, 15px);
    font-weight: 700;
    outline: none;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    display: block;
    margin-top: clamp(5px, 0.6vw, 7px);
}
.modalInput:focus {
    border-color: rgba(238, 140, 58, 0.7);
    background: rgba(238, 140, 58, 0.06);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.14);
}
.modalInput::placeholder { color: rgba(255, 255, 255, 0.25); font-weight: 500; }

/* Textarea inside a modal */
.modalTextarea {
    width: 100%;
    padding: clamp(11px, 1.4vw, 14px) clamp(12px, 1.6vw, 16px);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.07);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    color: rgba(255, 255, 255, 0.92);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(13px, 1.3vw, 15px);
    font-weight: 700;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
    display: block;
    min-height: clamp(100px, 14vw, 140px);
    margin-top: clamp(5px, 0.6vw, 7px);
}
.modalTextarea:focus {
    border-color: rgba(238, 140, 58, 0.7);
    background: rgba(238, 140, 58, 0.06);
    box-shadow: 0 0 0 3px rgba(238, 140, 58, 0.14);
}
.modalTextarea::placeholder { color: rgba(255, 255, 255, 0.25); font-weight: 500; }

/* Field label inside a modal */
.modalLabel {
    display: block;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(9px, 0.9vw, 11px);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0;
}

/* Field group wrapper - adds bottom spacing between fields */
.modalField {
    display: flex;
    flex-direction: column;
    gap: 0;
    margin-bottom: clamp(12px, 1.5vw, 16px);
}

/* Info/context box (green = normal, red = backlog) */
.modalInfoBox {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 8px;
    padding: clamp(10px, 1.3vw, 14px);
    margin-bottom: clamp(14px, 1.8vw, 18px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.6;
}
.modalInfoBoxDanger {
    background: rgba(239, 68, 68, 0.08);
    border-color: rgba(239, 68, 68, 0.3);
}
.modalInfoBoxDanger strong { color: #fca5a5; }

/* Footer row with action buttons */
.modalFooter {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: clamp(8px, 1.2vw, 12px);
    margin-top: clamp(14px, 1.8vw, 20px);
    padding-top: clamp(12px, 1.5vw, 16px);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    flex-wrap: wrap;
}

/* Primary action button (orange) */
.modalBtnPrimary {
    display: inline-flex;
    align-items: center;
    gap: clamp(6px, 0.8vw, 9px);
    padding: 0 clamp(16px, 2vw, 24px);
    height: clamp(38px, 4.8vw, 46px);
    background: #EE8C3A;
    color: #1a2e30;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(10px, 1vw, 12px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
}
.modalBtnPrimary:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 20px rgba(238, 140, 58, 0.4);
    transform: translateY(-1px);
}
.modalBtnPrimary:disabled { opacity: 0.5; cursor: not-allowed; }
.modalBtnPrimary:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 3px; }

/* Cancel / secondary button */
.modalBtnSecondary {
    display: inline-flex;
    align-items: center;
    gap: clamp(5px, 0.7vw, 8px);
    padding: 0 clamp(14px, 1.8vw, 20px);
    height: clamp(38px, 4.8vw, 46px);
    background: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.7);
    border: 1.5px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(10px, 1vw, 12px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, color 0.2s, border-color 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.modalBtnSecondary:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.35);
}
.modalBtnSecondary:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 3px; }

/* Mobile */
@media (max-width: 480px) {
    .modalBody {
        padding: clamp(16px, 5vw, 20px);
        border-radius: 12px;
        max-height: 88vh;
    }
    .title { font-size: 12px; letter-spacing: 1px; }
    .header { margin-bottom: 14px; padding-bottom: 10px; }
    .modalFooter { flex-direction: column-reverse; }
    .modalBtnPrimary, .modalBtnSecondary { width: 100%; justify-content: center; }
}""",
    "HardwareModal.module.css - add uniform modal form classes"
)

# Now update FolderPage.jsx to use uniform modal classes for its note + payment modals
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """            {/* NOTE MODAL */}
            <HardwareModal isOpen={noteModal.open} onClose={() => setNoteModal({...noteModal,open:false})} title="ARCHIVE LOG ENTRY">
                <textarea className={styles.notebookArea} value={noteModal.content}
                    onChange={e => setNoteModal({...noteModal,content:e.target.value})}
                    placeholder="Enter interaction note..." aria-label="Note content" />
                <div className={styles.modalFooter}>
                    <button type="button" className={`${styles.btn} ${styles.btnDanger}`}
                        onClick={() => setNoteModal({open:false,id:null,content:''})}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleNoteSave}>
                        <FiSave aria-hidden="true" /> SAVE ENTRY
                    </button>
                </div>
            </HardwareModal>""",
    """            {/* NOTE MODAL */}
            <HardwareModal isOpen={noteModal.open} onClose={() => setNoteModal({...noteModal,open:false})} title="ARCHIVE LOG ENTRY">
                <div className={modalStyles.modalField}>
                    <textarea className={modalStyles.modalTextarea} value={noteModal.content}
                        onChange={e => setNoteModal({...noteModal,content:e.target.value})}
                        placeholder="Enter interaction note..." aria-label="Note content" />
                </div>
                <div className={modalStyles.modalFooter}>
                    <button type="button" className={modalStyles.modalBtnSecondary}
                        onClick={() => setNoteModal({open:false,id:null,content:''})}>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button type="button" className={modalStyles.modalBtnPrimary} onClick={handleNoteSave}>
                        <FiSave aria-hidden="true" /> SAVE ENTRY
                    </button>
                </div>
            </HardwareModal>""",
    "FolderPage - note modal uses uniform classes"
)

patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """            {/* PAYMENT MODAL */}
            <HardwareModal isOpen={payModal.open} onClose={() => setPayModal({ open: false })} title={`RECORD PAYMENT — ${project.landTitle.plotNumber}`}>
                <div style={{ padding: '0 4px' }}>
                    {isBacklog ? (
                        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                            borderRadius: 8, padding: 14, marginBottom: 16, display:'flex', gap: 12 }}>
                            <FiAlertOctagon style={{ color: '#ef4444', flexShrink:0, marginTop:2 }} />
                            <div style={{ fontSize: '0.85rem' }}>
                                <div>Original debt: <strong>UGX {fmt(origDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(storageFees)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(Math.max(0,backlogOwed))}</strong></div>
                                <div style={{marginTop:6,opacity:0.6,fontSize:'0.75rem'}}>
                                    Storage fees continue until full balance is cleared.
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ marginBottom: 16, fontSize: '0.85rem' }}>
                            Current balance: <strong>UGX {fmt(remaining)}</strong>
                        </div>
                    )}
                    <div style={{ marginBottom: 12 }}>
                        <label style={{ display:'block', marginBottom:6, fontSize:'0.8rem', opacity:0.7 }}>AMOUNT RECEIVED (UGX)</label>
                        <input type="number" style={{ width:'100%', padding:'10px 14px', borderRadius:6,
                            background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.15)',
                            color:'inherit', fontSize:'1.1rem' }}
                            placeholder="Enter amount..." value={payAmount}
                            onChange={e => setPayAmount(e.target.value)} />
                    </div>
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display:'block', marginBottom:6, fontSize:'0.8rem', opacity:0.7 }}>NOTES (optional)</label>
                        <textarea style={{ width:'100%', padding:'10px 14px', borderRadius:6, height:80,
                            background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.15)',
                            color:'inherit', resize:'vertical' }}
                            placeholder="e.g. Paid via MTN Mobile Money..."
                            value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                    </div>
                    <div className={styles.modalFooter}>
                        <button type="button" className={`${styles.btn} ${styles.btnPrimary}`}
                            onClick={handleRecordPayment} disabled={paying}>
                            <FiDollarSign aria-hidden="true" /> {paying ? 'PROCESSING...' : 'CONFIRM PAYMENT'}
                        </button>
                    </div>
                </div>
            </HardwareModal>""",
    """            {/* PAYMENT MODAL */}
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
            </HardwareModal>""",
    "FolderPage - payment modal uses uniform classes"
)

# Add the modalStyles import to FolderPage.jsx
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    "import styles from './FolderPage.module.css';",
    "import styles from './FolderPage.module.css';\nimport modalStyles from '../../components/common/HardwareModal.module.css';",
    "FolderPage - import modalStyles"
)

# Now fix RecoveryPortal payment modal to use uniform classes
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "import styles from './RecoveryPortal.module.css';",
    "import styles from './RecoveryPortal.module.css';\nimport modalStyles from '../../components/common/HardwareModal.module.css';",
    "RecoveryPortal - import modalStyles"
)

patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    """            <HardwareModal isOpen={payModal.open}
                onClose={() => setPayModal({ open: false, plot: null })}
                title={`RECORD PAYMENT: ${payModal.plot?.plotNumber || ''}`}>
                <div className={styles.modalBody}>
                    {payModal.plot?.isBacklog ? (
                        <div className={styles.backlogPayInfo}>
                            <FiAlertOctagon aria-hidden="true" />
                            <div>
                                <div>Original debt: <strong>UGX {fmt(payModal.plot?.originalDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.storageFeesAccumulated)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.totalBacklogOwed)}</strong></div>
                                <div style={{marginTop:4,fontSize:'0.75rem',opacity:0.7}}>Storage fees continue until full balance is cleared.</div>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.activePayInfo}>
                            <div>Current balance: <strong>UGX {fmt(payModal.plot?.currentBalance)}</strong></div>
                        </div>
                    )}
                    <div style={{marginTop:16}}>
                        <label style={{display:'block',marginBottom:6,fontSize:'0.8rem',opacity:0.7}}>AMOUNT RECEIVED (UGX)</label>
                        <input type="number" className={styles.notebookArea} style={{height:48,fontSize:'1.1rem'}}
                            placeholder="Enter amount..." value={payAmount}
                            onChange={e => setPayAmount(e.target.value)} />
                    </div>
                    <div style={{marginTop:12}}>
                        <label style={{display:'block',marginBottom:6,fontSize:'0.8rem',opacity:0.7}}>NOTES (optional)</label>
                        <textarea className={styles.notebookArea} style={{height:80}}
                            placeholder="e.g. Paid via MTN Mobile Money..."
                            value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                    </div>
                    <div className={styles.modalFooter}>
                        <HardwareButton loading={paying} onClick={handleRecordPayment} icon={FiDollarSign}>
                            CONFIRM PAYMENT
                        </HardwareButton>
                    </div>
                </div>
            </HardwareModal>""",
    """            <HardwareModal isOpen={payModal.open}
                onClose={() => setPayModal({ open: false, plot: null })}
                title={`RECORD PAYMENT: ${payModal.plot?.plotNumber || ''}`}>
                {payModal.plot?.isBacklog ? (
                    <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>
                        <div style={{display:'flex',gap:10,alignItems:'flex-start'}}>
                            <FiAlertOctagon aria-hidden="true" style={{color:'#ef4444',flexShrink:0,marginTop:2}} />
                            <div>
                                <div>Original debt: <strong>UGX {fmt(payModal.plot?.originalDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.storageFeesAccumulated)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.totalBacklogOwed)}</strong></div>
                                <div style={{marginTop:6,opacity:0.65,fontSize:'0.78rem'}}>Storage fees continue until full balance is cleared.</div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className={modalStyles.modalInfoBox}>
                        Current balance: <strong>UGX {fmt(payModal.plot?.currentBalance)}</strong>
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
                    <HardwareButton loading={paying} onClick={handleRecordPayment} icon={FiDollarSign}>
                        CONFIRM PAYMENT
                    </HardwareButton>
                </div>
            </HardwareModal>""",
    "RecoveryPortal - payment modal uses uniform classes"
)

# Also fix RecoveryPortal call log modal
patch(
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    """            <HardwareModal isOpen={callModal.open}
                onClose={() => setCallModal({ open: false, mission: null })}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>
                <div className={styles.modalBody}>
                    <div className={styles.historyStream}>
                        <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                        {callHistory.length === 0 ? (
                            <div className={styles.emptyHistory}>No prior logs found.</div>
                        ) : callHistory.map(log => (
                            <div key={log.id} className={styles.historyItem}>
                                <div className={styles.historyMeta}>
                                    <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                    <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                                </div>
                                <p>{log.notes}</p>
                            </div>
                        ))}
                    </div>
                    <textarea className={styles.notebookArea}
                        placeholder="Enter call result or interaction note..."
                        value={logContent} onChange={e => setLogContent(e.target.value)} />
                    <div className={styles.modalFooter}>
                        <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                            Commit &amp; Reset
                        </HardwareButton>
                    </div>
                </div>
            </HardwareModal>""",
    """            <HardwareModal isOpen={callModal.open}
                onClose={() => setCallModal({ open: false, mission: null })}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>
                <div className={styles.historyStream}>
                    <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                    {callHistory.length === 0 ? (
                        <div className={styles.emptyHistory}>No prior logs found.</div>
                    ) : callHistory.map(log => (
                        <div key={log.id} className={styles.historyItem}>
                            <div className={styles.historyMeta}>
                                <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                            </div>
                            <p>{log.notes}</p>
                        </div>
                    ))}
                </div>
                <div className={modalStyles.modalField} style={{marginTop: 14}}>
                    <label className={modalStyles.modalLabel}>CALL RESULT / NOTE</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="Enter call result or interaction note..."
                        value={logContent} onChange={e => setLogContent(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                        Commit &amp; Reset
                    </HardwareButton>
                </div>
            </HardwareModal>""",
    "RecoveryPortal - call modal uses uniform classes"
)

print("\n=== ALL FIXES DONE ===")
print("""
Changes made:
1. PaymentsPage.module.css - full rewrite to match Ledger table design
2. PaymentsPage.jsx - clean sortable table (no messy column filters)
3. AuditPage.module.css - fixed z-index chain for dropdown visibility
4. HardwareModal.module.css - added uniform modal form classes
   (modalInput, modalTextarea, modalLabel, modalField, modalInfoBox,
    modalBtnPrimary, modalBtnSecondary, modalFooter)
5. FolderPage.jsx - note & payment modals use uniform classes
6. RecoveryPortal.jsx - call log & payment modals use uniform classes

Deploy:
  git add -A && git commit -m 'fix: payments table matches ledger, audit dropdowns, uniform modal design' && git push
""")