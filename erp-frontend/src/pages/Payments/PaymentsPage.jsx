// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
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
