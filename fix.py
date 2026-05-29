import os

PAYMENTS_JSX = r"""// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX,
    FiChevronRight, FiAlertOctagon, FiUser, FiRefreshCw,
    FiLayers, FiArrowUp, FiArrowDown, FiMaximize2,
    FiDatabase, FiFileText
} from 'react-icons/fi';
import api from '../../api/axios';
import HardwarePanel from '../../components/ui/HardwarePanel';
import styles from './PaymentsPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();

const TYPE_LABELS = {
    STANDARD:            'Title Payment',
    INITIAL_DEPOSIT:     'Initial Deposit',
    BACKLOG_PARTIAL:     'Backlog Payment',
};

const TYPE_COLORS = {
    STANDARD:            '#22c55e',
    INITIAL_DEPOSIT:     '#06b6d4',
    BACKLOG_PARTIAL:     '#ef4444',
};

const getAnalysis = (pay) => {
    const amount = fmt(pay.amountPaid);
    const balance = fmt(pay.balanceAfter);
    switch (pay.paymentType) {
        case 'INITIAL_DEPOSIT':
            return `This was the initial deposit of UGX ${amount} paid during plot registration. It established the account and left a remaining title balance of UGX ${balance}.`;
        case 'STANDARD':
            return `This was a standard title payment of UGX ${amount} made toward the plot cost. It successfully reduced the remaining outstanding balance to UGX ${balance}.`;
        case 'BACKLOG_PARTIAL':
            return `This was a backlog storage fee payment of UGX ${amount}. It was applied toward accumulated penalty fees, leaving a total outstanding backlog balance of UGX ${balance}.`;
        default:
            return `A payment of UGX ${amount} was recorded. Remaining balance after this transaction: UGX ${balance}.`;
    }
};

const PaymentsPage = () => {
    const navigate = useNavigate();
    const [payments,    setPayments]   = useState([]);
    const [loading,     setLoading]    = useState(true);
    const [searchTerm,  setSearchTerm] = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [typeFilter,  setTypeFilter] = useState('ALL');
    const [sortKey,     setSortKey]    = useState('date');
    const [sortDir,     setSortDir]    = useState('desc');
    const [expandedId,  setExpandedId] = useState(null);

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
        if (sortKey !== field) return <span className={styles.sortArrowInactive}> &#8597;</span>;
        return sortDir === 'asc'
            ? <FiArrowUp  style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />
            : <FiArrowDown style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />;
    };

    const handleRowClick = (payId) => {
        setExpandedId(prev => prev === payId ? null : payId);
    };

    return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Payment Records</h1>
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
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} />}
                    <input type="search"
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                        placeholder="Search plot ID, owner name, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
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
                <div>
                <HardwarePanel variant="dark">
                    <div className={styles.tableScroll}>
                        <table className={styles.ledgerTable}>
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
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.length === 0 ? (
                                    <tr>
                                        <td colSpan="8" className={styles.noRecords}>
                                            <div className={styles.noRecordsInner}>
                                                <FiLayers className={styles.noRecordsIcon} />
                                                <span>{searchTerm ? `NO RECORDS MATCH "${searchTerm.toUpperCase()}"` : "NO PAYMENT RECORDS FOUND"}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ) : filtered.map((pay, i) => {
                                    const isExpanded = expandedId === (pay.id || i);
                                    return (
                                        <React.Fragment key={pay.id || i}>
                                            <tr
                                                onClick={() => handleRowClick(pay.id || i)}
                                                tabIndex={0}
                                                role="row"
                                                aria-expanded={isExpanded}
                                                className={`${styles.dataRow} ${isExpanded ? styles.dataRowExpanded : ''}`}
                                                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleRowClick(pay.id || i); } }}
                                            >
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
                                                    <span className={styles.typeBadge} style={{ color: TYPE_COLORS[pay.paymentType] || '#888' }}>
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
                                                <td>
                                                    <div className={`${styles.inspectIcon} ${isExpanded ? styles.inspectIconOpen : ''}`} aria-hidden="true">
                                                        {isExpanded ? <FiX size={14} /> : <FiMaximize2 size={14} />}
                                                    </div>
                                                </td>
                                            </tr>
                                            {isExpanded && (
                                                <tr className={styles.drawerRow}>
                                                    <td colSpan="8" className={styles.drawerCell}>
                                                        <div className={styles.drawerInner}>
                                                            <div className={styles.drawerHeader}>
                                                                <FiDatabase aria-hidden="true" />
                                                                <span>PAYMENT DETAILS &amp; ANALYSIS</span>
                                                            </div>
                                                            <div className={styles.drawerBody}>
                                                                <div className={styles.analysisText}>
                                                                    <FiFileText className={styles.analysisIcon} aria-hidden="true" />
                                                                    <p>{getAnalysis(pay)}</p>
                                                                </div>
                                                                <div className={styles.drawerMeta}>
                                                                    <div className={styles.drawerMetaItem}>
                                                                        <span className={styles.drawerMetaLabel}>RECORDED BY</span>
                                                                        <span className={styles.drawerMetaValue}>{pay.recordedBy}</span>
                                                                    </div>
                                                                    <div className={styles.drawerMetaItem}>
                                                                        <span className={styles.drawerMetaLabel}>EXACT TIMESTAMP</span>
                                                                        <span className={styles.drawerMetaValue}>
                                                                            {new Date(pay.timestamp).toLocaleString([], { dateStyle: 'full', timeStyle: 'short' })}
                                                                        </span>
                                                                    </div>
                                                                    <div className={styles.drawerMetaItem}>
                                                                        <span className={styles.drawerMetaLabel}>TRANSACTION NOTES</span>
                                                                        <span className={styles.drawerMetaValue}>{pay.notes || 'No notes recorded.'}</span>
                                                                    </div>
                                                                    <div className={styles.drawerMetaItem}>
                                                                        <span className={styles.drawerMetaLabel}>PAYMENT TYPE</span>
                                                                        <span className={styles.drawerMetaValue} style={{ color: TYPE_COLORS[pay.paymentType] || '#fff' }}>
                                                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                                {pay.projectId && (
                                                                    <div className={styles.drawerActions}>
                                                                        <button
                                                                            className={styles.goBtn}
                                                                            onClick={e => { e.stopPropagation(); navigate(`/folder/${pay.projectId}#payment-${pay.id}`); }}
                                                                        >
                                                                            <FiChevronRight size={12} /> OPEN FOLDER
                                                                        </button>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </React.Fragment>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </HardwarePanel>
                </div>
            )}
        </div>
    );
};

export default PaymentsPage;
"""

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
    width: 100%;
    padding: clamp(14px, 2.5vh, 28px) clamp(12px, 2vw, 24px) clamp(24px, 3vw, 36px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: warmBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
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
    flex-shrink: 0;
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
    flex-shrink: 0;
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
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 200;
    background: transparent;
    padding: clamp(8px, 1vw, 12px) 0;
    margin-left: clamp(-12px, -2vw, -24px);
    margin-right: clamp(-12px, -2vw, -24px);
    padding-left: clamp(12px, 2vw, 24px);
    padding-right: clamp(12px, 2vw, 24px);
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
    color: #1a2e30; padding-right: 36px !important; padding-left: 42px !important;
    font-family: 'DM Sans', sans-serif; font-weight: 800;
    font-size: var(--fs-input);
    height: 100%;
    transition: padding 0.2s ease;
}
.searchInputActive {
    padding-left: 14px !important;
}
.searchInput::placeholder { font-weight: 500; color: rgba(26,46,48,0.3); }
.clearBtn {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    background: transparent; border: none;
    cursor: pointer; color: rgba(26,46,48,0.4); display: flex;
    align-items: center; padding: 4px; border-radius: 4px; transition: color 0.15s, background 0.15s;
}
.clearBtn:hover { color: #1a2e30; background: rgba(26,46,48,0.08); }

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

/* TABLE SHELL */
.tableScroll {
    overflow-x: auto;
    overflow-y: visible;
    border-radius: var(--radius);
    background: rgba(0, 0, 0, 0.15);
    margin: -30px;
    margin-bottom: -30px;
    -webkit-overflow-scrolling: touch;
    flex: 1;
    min-height: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--orange) transparent;
}
.tableScroll::-webkit-scrollbar { width: 5px; height: 4px; }
.tableScroll::-webkit-scrollbar-thumb { background: rgba(238,140,58,0.4); border-radius: 2px; }

.ledgerTable {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    min-width: clamp(700px, 90vw, 1100px);
}

/* TABLE HEADER */
.ledgerTable th {
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
    position: sticky;
    top: 0;
    z-index: 100;
}

.thSortable { cursor: pointer; transition: background 0.18s, color 0.18s; }
.thSortable:hover { background: rgba(238, 140, 58, 0.07); color: #fff; }

/* TABLE BODY */
.ledgerTable td {
    padding: clamp(9px, 1.3vw, 14px) clamp(12px, 1.8vw, 20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    vertical-align: middle;
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-td);
}

/* DATA ROW — clickable, no immediate navigation */
.dataRow {
    cursor: pointer;
    transition: background 0.18s, border-left-color 0.18s;
    border-left: 3px solid transparent;
    outline: none;
}
.dataRow:hover {
    background: rgba(255, 255, 255, 0.04);
    border-left-color: var(--orange);
}
.dataRow:focus-visible {
    background: rgba(238, 140, 58, 0.07);
    border-left-color: var(--orange);
    outline: 2px solid var(--orange);
    outline-offset: -2px;
}
.dataRowExpanded {
    background: rgba(238, 140, 58, 0.06);
    border-left-color: var(--orange);
}

/* INSPECT ICON */
.inspectIcon {
    color: rgba(255,255,255,0.2);
    font-size: clamp(14px,1.5vw,17px);
    transition: color 0.18s, transform 0.25s;
    display: flex;
    align-items: center;
    justify-content: center;
}
.dataRow:hover .inspectIcon { color: var(--orange); }
.inspectIconOpen { color: var(--orange) !important; }

/* DRAWER ROW */
.drawerRow {
    background: #0a0a0a;
}
.drawerRow td {
    border-bottom: 2px solid rgba(238, 140, 58, 0.2);
    padding: 0 !important;
}
.drawerCell { padding: 0 !important; }

.drawerInner {
    border-top: 1px solid rgba(255,255,255,0.08);
    overflow: hidden;
}

.drawerHeader {
    display: flex;
    align-items: center;
    gap: clamp(7px, 0.9vw, 10px);
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: #4ade80;
    letter-spacing: 2px;
    padding: clamp(10px, 1.3vw, 13px) clamp(14px, 1.8vw, 22px);
    text-transform: uppercase;
    background: rgba(0,0,0,0.4);
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.drawerHeader svg { color: #4ade80; flex-shrink: 0; }

.drawerBody {
    padding: clamp(14px, 1.8vw, 20px) clamp(14px, 1.8vw, 22px);
    display: flex;
    flex-direction: column;
    gap: clamp(14px, 1.8vw, 20px);
}

/* Analysis text block — plain English explanation */
.analysisText {
    display: flex;
    align-items: flex-start;
    gap: clamp(10px, 1.3vw, 14px);
    padding: clamp(12px, 1.5vw, 16px) clamp(14px, 1.8vw, 18px);
    background: rgba(238, 140, 58, 0.05);
    border: 1px solid rgba(238, 140, 58, 0.2);
    border-left: clamp(3px, 0.4vw, 4px) solid var(--orange);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.analysisIcon {
    color: var(--orange);
    font-size: clamp(15px, 1.6vw, 18px);
    flex-shrink: 0;
    margin-top: 2px;
}
.analysisText p {
    margin: 0;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.2vw, 14px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.82);
    line-height: 1.65;
}

/* Meta grid */
.drawerMeta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(clamp(180px, 20vw, 220px), 1fr));
    gap: clamp(10px, 1.3vw, 14px);
}
.drawerMetaItem {
    display: flex;
    flex-direction: column;
    gap: clamp(4px, 0.5vw, 6px);
    border-left: 2px solid rgba(238,140,58,0.25);
    padding-left: clamp(8px, 1vw, 11px);
}
.drawerMetaLabel {
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-label);
    font-weight: 900;
    color: rgba(255,255,255,0.3);
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.drawerMetaValue {
    font-family: 'Space Mono', monospace;
    font-size: clamp(10px, 1.05vw, 12px);
    font-weight: 700;
    color: #fff;
    word-break: break-word;
    line-height: 1.4;
}

/* Drawer action buttons */
.drawerActions {
    display: flex;
    gap: clamp(8px, 1.1vw, 12px);
    flex-wrap: wrap;
}

/* CELL TYPES */
.dateCell { display: flex; flex-direction: column; gap: 2px; white-space: nowrap; font-weight: 700; }
.time { font-family: 'Space Mono', monospace; font-size: var(--fs-label); opacity: 0.45; }
.plotNum { font-family: 'Space Mono', monospace; color: #EE8C3A; font-size: var(--fs-value); font-weight: 700; letter-spacing: 0.5px; }
.ownerCell { font-weight: 700; color: #fff; max-width: clamp(100px, 14vw, 180px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.typeBadge {
    display: inline-flex; align-items: center; gap: 4px;
    font-family: 'DM Sans', sans-serif;
    font-size: var(--fs-tag);
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    letter-spacing: 0.5px;
    background: transparent !important;
    border: none !important;
    padding: 0;
}
.amount { font-family: 'Space Mono', monospace; font-size: var(--fs-value); font-weight: 700; }
.balance { font-family: 'Space Mono', monospace; font-size: var(--fs-meta); color: rgba(255,255,255,0.5); }
.recorder { display: inline-flex; align-items: center; gap: 5px; font-size: var(--fs-meta); color: rgba(255,255,255,0.6); }

.goBtn {
    background: rgba(238,140,58,0.1); border: 1.5px solid rgba(238,140,58,0.35);
    color: #EE8C3A; border-radius: var(--radius-sm); padding: clamp(7px,0.9vw,10px) clamp(14px,1.8vw,20px);
    cursor: pointer; display: flex; align-items: center; gap: 6px;
    transition: all 0.2s; font-size: var(--fs-btn); font-weight: 900;
    font-family: 'DM Sans', sans-serif; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap;
}
.goBtn:hover { background: #EE8C3A; color: #1a2e30; box-shadow: 0 0 14px rgba(238,140,58,0.35); }
.goBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

.sortArrow { color: #fff; font-size: 10px; opacity: 0.9; margin-left: 3px; }
.sortArrowInactive { color: rgba(255,255,255,0.25); font-size: 10px; margin-left: 3px; }

/* NO RECORDS */
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
    .ledgerTable { min-width: 650px; }
    .drawerMeta { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 480px) {
    .summaryRow { grid-template-columns: 1fr 1fr; }
    .sumCard strong { font-size: 13px; }
    .ledgerTable { min-width: 600px; }
    .ledgerTable th { font-size: 7px; letter-spacing: 1px; }
    .ledgerTable td { padding: 8px; }
    .filterBtn { padding: 6px 10px; font-size: 9px; letter-spacing: 1px; }
    .drawerMeta { grid-template-columns: 1fr; }
    .drawerBody { padding: 12px; }
}
"""

base = os.path.join('erp-frontend', 'src', 'pages', 'Payments')
os.makedirs(base, exist_ok=True)

jsx_path = os.path.join(base, 'PaymentsPage.jsx')
css_path = os.path.join(base, 'PaymentsPage.module.css')

with open(jsx_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(PAYMENTS_JSX)
print(f'OK: {jsx_path}')

with open(css_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(PAYMENTS_CSS)
print(f'OK: {css_path}')