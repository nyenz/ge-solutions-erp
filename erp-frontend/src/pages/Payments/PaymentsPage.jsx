// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
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
