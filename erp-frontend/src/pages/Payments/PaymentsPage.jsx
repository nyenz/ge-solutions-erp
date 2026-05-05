// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX, FiFilter,
    FiChevronRight, FiAlertOctagon, FiClock, FiUser
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
    const [payments,    setPayments]    = useState([]);
    const [loading,     setLoading]     = useState(true);
    const [searchTerm,  setSearchTerm]  = useState('');
    const [typeFilter,  setTypeFilter]  = useState('ALL');
    const [sortDir,     setSortDir]     = useState('desc');

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
            const da = new Date(a.timestamp), db = new Date(b.timestamp);
            return sortDir === 'desc' ? db - da : da - db;
        });
        return list;
    }, [payments, typeFilter, searchTerm, sortDir]);

    const totalCollected = useMemo(() =>
        filtered.reduce((s, p) => s + Number(p.amountPaid || 0), 0), [filtered]);

    const titlePayments   = filtered.filter(p => p.paymentType !== 'BACKLOG_PARTIAL');
    const storagePayments = filtered.filter(p => p.paymentType === 'BACKLOG_PARTIAL');

    const titleTotal   = titlePayments.reduce((s, p) => s + Number(p.amountPaid || 0), 0);
    const storageTotal = storagePayments.reduce((s, p) => s + Number(p.amountPaid || 0), 0);

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>PAYMENTS</h1>
                    <p className={styles.subtitle}>All payment records — title payments and storage fee collections</p>
                </div>
            </header>

            {/* SUMMARY CARDS */}
            <div className={styles.summaryRow}>
                <div className={styles.sumCard}>
                    <label>TOTAL SHOWN</label>
                    <strong>UGX {fmt(totalCollected)}</strong>
                    <span>{filtered.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#22c55e' }}>
                    <label style={{ color: '#22c55e' }}>TITLE PAYMENTS</label>
                    <strong style={{ color: '#22c55e' }}>UGX {fmt(titleTotal)}</strong>
                    <span>{titlePayments.length} records</span>
                </div>
                <div className={styles.sumCard} style={{ borderColor: '#ef4444' }}>
                    <label style={{ color: '#ef4444' }}>STORAGE FEE COLLECTIONS</label>
                    <strong style={{ color: '#ef4444' }}>UGX {fmt(storageTotal)}</strong>
                    <span>{storagePayments.length} records</span>
                </div>
            </div>

            {/* CONTROLS */}
            <div className={styles.controls}>
                <div className={styles.searchWrap}>
                    <FiSearch className={styles.searchIcon} />
                    <input type="search" className={styles.searchInput}
                        placeholder="Search plot, owner, recorded by..."
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                    {searchTerm && (
                        <button className={styles.clearBtn} onClick={() => setSearchTerm('')}>
                            <FiX />
                        </button>
                    )}
                </div>
                <div className={styles.filterRow}>
                    {['ALL','STANDARD','INITIAL_DEPOSIT','BACKLOG_PARTIAL'].map(t => (
                        <button key={t}
                            className={`${styles.filterBtn} ${typeFilter === t ? styles.filterActive : ''}`}
                            onClick={() => setTypeFilter(t)}>
                            {t === 'ALL' ? 'ALL' : TYPE_LABELS[t] || t}
                        </button>
                    ))}
                    <button className={styles.filterBtn} onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                        DATE {sortDir === 'desc' ? '↓' : '↑'}
                    </button>
                </div>
            </div>

            {/* TABLE */}
            {loading ? (
                <div className={styles.loading}>Loading payments...</div>
            ) : filtered.length === 0 ? (
                <div className={styles.empty}>No payment records found.</div>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                            <tr>
                                <th>DATE</th>
                                <th>PLOT</th>
                                <th>OWNER</th>
                                <th>TYPE</th>
                                <th>AMOUNT</th>
                                <th>BALANCE AFTER</th>
                                <th>RECORDED BY</th>
                                <th>NOTES</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((pay, i) => (
                                <tr key={pay.id || i} className={styles.row}>
                                    <td className={styles.dateCell}>
                                        {new Date(pay.timestamp).toLocaleDateString()}
                                        <span className={styles.time}>
                                            {new Date(pay.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </td>
                                    <td className={styles.plotCell}>
                                        <strong>{pay.plotNumber || '---'}</strong>
                                    </td>
                                    <td>{pay.ownerName || '---'}</td>
                                    <td>
                                        <span className={styles.typeBadge} style={{
                                            background: `${TYPE_COLORS[pay.paymentType]}22`,
                                            color: TYPE_COLORS[pay.paymentType],
                                            border: `1px solid ${TYPE_COLORS[pay.paymentType]}44`
                                        }}>
                                            {pay.paymentType === 'BACKLOG_PARTIAL' && <FiAlertOctagon size={10} />}
                                            {TYPE_LABELS[pay.paymentType] || pay.paymentType}
                                        </span>
                                    </td>
                                    <td className={styles.amountCell}>
                                        <strong style={{ color: TYPE_COLORS[pay.paymentType] }}>
                                            UGX {fmt(pay.amountPaid)}
                                        </strong>
                                    </td>
                                    <td className={styles.balanceCell}>
                                        {pay.balanceAfter != null ? `UGX ${fmt(pay.balanceAfter)}` : '---'}
                                    </td>
                                    <td>
                                        <span className={styles.recorder}>
                                            <FiUser size={11} /> {pay.recordedBy}
                                        </span>
                                    </td>
                                    <td className={styles.notesCell}>
                                        {pay.notes || '---'}
                                    </td>
                                    <td>
                                        {pay.projectId && (
                                            <button className={styles.goBtn}
                                                onClick={() => navigate(`/folder/${pay.projectId}`)}>
                                                <FiChevronRight size={14} />
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