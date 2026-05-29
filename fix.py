import os

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'OK: {path}')

BASE = r'C:/Users/nyenz/Desktop/app/ge solns'

# ─── PaymentsPage.jsx ────────────────────────────────────────────────────────
payments_jsx = r"""// PATH: erp-frontend/src/pages/Payments/PaymentsPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiDollarSign, FiSearch, FiX,
    FiAlertOctagon, FiUser, FiRefreshCw,
    FiLayers, FiArrowUp, FiArrowDown
} from 'react-icons/fi';
import api from '../../api/axios';
import HardwarePanel from '../../components/ui/HardwarePanel';
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
    const [isSearchFocused, setIsSearchFocused] = useState(false);
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
        if (sortKey !== field) return <span className={styles.sortArrowInactive}> &#8597;</span>;
        return sortDir === 'asc'
            ? <FiArrowUp  style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />
            : <FiArrowDown style={{display:'inline',marginLeft:3,fontSize:10,color:'#fff'}} />;
    };

    const handleRowClick = (pay) => {
        if (pay.projectId) {
            navigate(`/folder/${pay.projectId}#payment-${pay.id}`);
        }
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
                                    <th>NOTES</th>
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
                                ) : filtered.map((pay, i) => (
                                    <tr
                                        key={pay.id || i}
                                        onClick={() => handleRowClick(pay)}
                                        tabIndex={0}
                                        role="row"
                                        className={styles.dataRow}
                                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleRowClick(pay); } }}
                                        title={pay.projectId ? 'Click to open folder' : ''}
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
                                        <td className={styles.notesCell}>
                                            {pay.notes || '---'}
                                        </td>
                                    </tr>
                                ))}
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

# ─── ReportHub.jsx ────────────────────────────────────────────────────────────
report_jsx = r"""// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
import React, { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    FiBarChart2, FiMap, FiActivity, FiLayers,
    FiShield, FiTrendingUp, FiLock, FiDownloadCloud,
    FiChevronDown, FiCreditCard, FiDatabase, FiFileText,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiMaximize2
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import reportService from '../../services/reportService';
import styles from './ReportHub.module.css';

// ─── TOAST ────────────────────────────────────────────────────────
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismiss = useCallback(id => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast: dismiss };
};
const TOAST_ICONS = {
    success: <FiCheckSquare  aria-hidden="true" />,
    error:   <FiAlertCircle  aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo          aria-hidden="true" />,
};
const ToastContainer = ({ toasts, onDismiss }) => {
    if (typeof document === 'undefined') return null;
    return createPortal(
        <div className={styles.toastContainer} role="region" aria-label="Notifications" aria-live="polite">
            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles['toast_' + t.type]}`} role="alert">
                    <span className={styles.toastIcon}>{TOAST_ICONS[t.type]}</span>
                    <span className={styles.toastMsg}>{t.message}</span>
                    <button className={styles.toastClose} onClick={() => onDismiss(t.id)} aria-label="Dismiss">
                        <FiX aria-hidden="true" />
                    </button>
                </div>
            ))}
        </div>,
        document.body
    );
};

// ─── DRAWER HEADER ────────────────────────────────────────────────
const DrawerTitle = ({ label, isOpen, onClick, icon: IconComponent }) => (
    <div
        className={styles.drawerHeader}
        onClick={onClick}
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        aria-label={`${label}, ${isOpen ? 'collapse' : 'expand'}`}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}
    >
        <div className={styles.drawerTitle}>
            {IconComponent && <IconComponent className={styles.drawerIcon} aria-hidden="true" />}
            {label}
        </div>
        <FiChevronDown className={`${styles.chevron} ${isOpen ? styles.rotated : ''}`} aria-hidden="true" />
    </div>
);

// ─── REPORT EXPLANATIONS ──────────────────────────────────────────
const REPORT_EXPLANATIONS = {
    debt:      { desc: 'Lists all active plots with unpaid balances. Use this to audit outstanding arrears across your entire portfolio and identify which clients owe the most.', columns: 'PLOT_ID, PRIMARY_OWNER, PHONE, TOTAL_VAL, PAID_VAL, AMOUNT_OWED, BOX_LOC, STATUS' },
    revenue:   { desc: 'A complete chronological history of every single payment received across the system. Use this to verify cash flow, track collection trends, and reconcile revenue.', columns: 'DATE, PLOT_ID, OWNER_NAME, PAYMENT_TYPE, AMOUNT_UGX, BALANCE_AFTER_UGX, RECORDED_BY, NOTES' },
    perf:      { desc: 'Audits manager activity by logging all recovery calls and follow-up interactions. Shows who called which client, when, and what notes were recorded.', columns: 'TIMESTAMP, OPERATOR, PLOT_ID, NOTE_SNIPPET' },
    map:       { desc: 'A complete physical filing cabinet checklist sorted by Box Location. Use this to do physical archive audits and verify all documents are in the right box.', columns: 'BOX_LOCATION, PLOT_ID, TENURE, DISTRICT, STAGE_INDEX, IS_LEGACY' },
    stage:     { desc: 'Shows how many title files are stuck in each of the 5 survey pipeline stages. Use this to identify bottlenecks and understand where work is backing up.', columns: 'PHASE_NUMBER, TOTAL_FILES_IN_STAGE' },
    risk:      { desc: 'Ranks all clients from 0% to 100% based on their historical payment reliability. Use this to prioritize recovery efforts and identify high-risk clients.', columns: 'OWNER_NAME, SCORE_PERCENT, LAST_CALL_DATE' },
    legal:     { desc: 'Identifies which clients are fully ready for legal demand notices. A client is READY if they have both a valid National ID (NIN) and a home address on file.', columns: 'PLOT, OWNER, PHONE, NIN_STATUS, ADDRESS_STATUS, READINESS' },
    audit:     { desc: 'The complete forensic trail of all staff actions including logins, record edits, stage changes, payments recorded, and deletions. Use for accountability and security audits.', columns: 'TIMESTAMP, OPERATOR, ACTION_CODE, HARDWARE_DETAILS' },
    backlog:   { desc: 'All plots currently in backlog status with a full breakdown of storage fees accumulated, months in backlog, and total amount owed including fees.', columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, BACKLOG_START, TITLE_COST_UGX, STORAGE_FEES_UGX, MONTHS_IN_BACKLOG, TOTAL_PAID, TOTAL_OWED' },
    completed: { desc: 'All plots that have been either fully paid or officially released to the client. Use this to track completed business and verify handover records.', columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, TOTAL_COST, AMOUNT_PAID, STATUS' },
    reconcile: { desc: 'Anti-theft report. Groups all payments by the staff member who recorded them. Compare totals against physical cash collected to detect discrepancies.', columns: 'OPERATOR_ID, TOTAL_CASH_COLLECTED_UGX, NUMBER_OF_TRANSACTIONS, FIRST_PAYMENT_DATE, LAST_PAYMENT_DATE' },
    monthly:   { desc: 'Shows total cash collected per calendar month for the last 24 months. Use this to track monthly revenue trends and set collection targets.', columns: 'YEAR_MONTH, TOTAL_COLLECTED_UGX, TRANSACTION_COUNT' },
};

// ─── MAIN ─────────────────────────────────────────────────────────
const ReportHub = () => {
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';

    const [drawers,    setDrawers]    = useState({ finance: true, ops: true, system: false, p2: true });
    const [expandedId, setExpandedId] = useState(null);
    const [status,     setStatus]     = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        backlog: false, completed: false, reconcile: false, monthly: false,
    });

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const triggerPillarExport = async (e, id, action, label) => {
        e.stopPropagation();
        setStatus(prev => ({ ...prev, [id]: true }));
        try {
            await action();
            toast(`${label} — EXPORT COMPLETE`, 'success', 4000);
        } catch (err) {
            toast(`REPORT FAULT: ${err.message || 'UNKNOWN ERROR'}`, 'error', 8000);
        } finally {
            setStatus(prev => ({ ...prev, [id]: false }));
        }
    };

    const FINANCIAL_GROUP = [
        { id: 'debt',    title: 'Master Debt Ledger',     desc: 'Global map of all plots with outstanding arrears.',         icon: FiCreditCard, action: reportService.downloadDebtLedger   },
        { id: 'revenue', title: 'Revenue Inflow History',  desc: 'Chronological log of all cash ingested into the system.',   icon: FiDatabase,   action: reportService.downloadRevenue      },
        { id: 'perf',    title: 'Recovery Throughput',     desc: 'Manager performance audit based on call volume.',           icon: FiActivity,   action: reportService.downloadPerformance  },
    ];
    const OPS_GROUP = [
        { id: 'map',   title: 'Physical Archive Map',  desc: 'Inventory list sorted by Cabinet Box numbers.',            icon: FiMap,        action: reportService.downloadArchiveMap   },
        { id: 'stage', title: 'Survey Stage Audit',    desc: 'Bottleneck analysis of titles in the 5-phase pipeline.',   icon: FiLayers,     action: reportService.downloadBottlenecks  },
        { id: 'risk',  title: 'Reliability Scorecard', desc: 'Client rankings based on historical payment behavior.',     icon: FiTrendingUp, action: reportService.downloadReliability  },
    ];
    const SYSTEM_GROUP = [
        { id: 'legal', title: 'Legal Readiness Audit', desc: 'NIN and Address completeness check for demand notices.',   icon: FiFileText, action: reportService.downloadLegalReady  },
        { id: 'audit', title: 'Master System Audit',   desc: 'Forensic footprint of data rewrites and stage jumps.',     icon: FiShield,   action: reportService.downloadAuditTrail  },
    ];
    const PRIORITY2_GROUP = [
        { id: 'backlog',   title: 'Backlog Breakdown',            desc: 'All backlog plots with storage fees, months owed, and total outstanding.',                                         icon: FiLock,        action: reportService.downloadBacklogBreakdown         },
        { id: 'completed', title: 'Completed Titles',             desc: 'All released or fully paid plots ready for handover.',                                                             icon: FiCheckSquare, action: reportService.downloadCompletedTitles         },
        { id: 'reconcile', title: 'Operator Cash Reconciliation', desc: 'Anti-theft: total cash collected per operator. Compare against physical cash.',                                    icon: FiShield,      action: reportService.downloadOperatorReconciliation   },
        { id: 'monthly',   title: 'Monthly Collection',           desc: 'Total cash collected per calendar month for the last 24 months.',                                                  icon: FiBarChart2,   action: reportService.downloadMonthlyCollection        },
    ];

    const ReportRow = ({ item }) => {
        const ItemIcon = item.icon;
        const isLoading   = status[item.id];
        const isExpanded  = expandedId === item.id;
        const explanation = REPORT_EXPLANATIONS[item.id];

        return (
            <>
                <div
                    className={`${styles.reportRow} ${isExpanded ? styles.reportRowExpanded : ''}`}
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    role="button"
                    tabIndex={0}
                    aria-expanded={isExpanded}
                    aria-label={`${item.title}, ${isExpanded ? 'collapse' : 'expand'}`}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(isExpanded ? null : item.id); } }}
                >
                    <div className={styles.iconFrame} aria-hidden="true">
                        <ItemIcon aria-hidden="true" />
                    </div>
                    <span className={styles.rptTitle}>{item.title}</span>
                    <span className={styles.rptDesc}>{item.desc}</span>
                    <div className={styles.inspectIcon} aria-hidden="true">
                        {isExpanded ? <FiX /> : <FiMaximize2 />}
                    </div>
                </div>

                {isExpanded && explanation && (
                    <div className={styles.reportDrawer}>
                        <div className={styles.drawerRawBox}>
                            <div className={styles.drawerRawHeader}>
                                <FiDatabase aria-hidden="true" />
                                <span>REPORT EXPLANATION &amp; SCHEMA</span>
                            </div>
                            <div className={styles.drawerDescription}>
                                {explanation.desc}
                            </div>
                            <div className={styles.drawerColumnsLabel}>COLUMNS INCLUDED IN DOWNLOAD:</div>
                            <div className={styles.drawerColumns}>
                                {explanation.columns.split(', ').map((col, i) => (
                                    <span key={i} className={styles.colChip}>{col}</span>
                                ))}
                            </div>
                            <div className={styles.drawerFooter}>
                                <button
                                    className={styles.exportBtn}
                                    onClick={e => triggerPillarExport(e, item.id, item.action, item.title)}
                                    disabled={isLoading}
                                    aria-label={isLoading ? `Exporting ${item.title}` : `Download ${item.title}`}
                                >
                                    {isLoading
                                        ? 'STREAMING...'
                                        : <><FiDownloadCloud aria-hidden="true" /> DOWNLOAD CSV</>
                                    }
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </>
        );
    };

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Reports</h1>
                    <p className={styles.subtitle}>Click any report to preview its contents, then download as CSV</p>
                </div>
            </header>

            <div className={styles.pillarStack}>

                {hasFinancialAccess ? (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="FINANCIAL REPORTS" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiBarChart2} />
                        <div className={`${styles.panelBody} ${drawers.finance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.finance}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {FINANCIAL_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className={styles.restrictionHandbrake} role="alert">
                        <FiLock className={styles.lockIcon} aria-hidden="true" />
                        <div className={styles.warningText}>
                            <strong>SECURITY HANDBRAKE ACTIVE</strong>
                            <p>FINANCIAL PILLARS ARE ENCRYPTED. CONTACT ROOT OWNER FOR ACCESS.</p>
                        </div>
                    </div>
                )}

                <div className={styles.hwPanel}>
                    <DrawerTitle label="OPERATIONAL REPORTS" isOpen={drawers.ops} onClick={() => toggleDrawer('ops')} icon={FiMap} />
                    <div className={`${styles.panelBody} ${drawers.ops ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.ops}>
                        <div className={styles.panelInner}>
                            <div className={styles.reportList}>
                                {OPS_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                            </div>
                        </div>
                    </div>
                </div>

                {hasFinancialAccess && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="SYSTEM REPORTS" isOpen={drawers.system} onClick={() => toggleDrawer('system')} icon={FiShield} />
                        <div className={`${styles.panelBody} ${drawers.system ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.system}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {hasFinancialAccess && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="MORE REPORTS" isOpen={drawers.p2} onClick={() => toggleDrawer('p2')} icon={FiBarChart2} />
                        <div className={`${styles.panelBody} ${drawers.p2 ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.p2}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {PRIORITY2_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportHub;
"""

# ─── ReportHub.module.css ─────────────────────────────────────────────────────
report_css = r"""/* PATH: erp-frontend/src/pages/Reports/ReportHub.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --panel-border:  rgba(238, 140, 58, 0.2);
    --red:           #ef4444;

    --gap-lg:   clamp(10px, 1.5vw, 13px);
    --gap-md:   clamp(7px,  1.1vw, 9px);
    --radius:   12px;
    --radius-sm: 6px;

    --fs-h1:    clamp(18px, 2.5vw, 24px);
    --fs-sub:   clamp(8px,  0.85vw, 10px);
    --fs-drawer:clamp(9px,  0.9vw, 11px);
    --fs-title: clamp(11px, 1.1vw, 13px);
    --fs-desc:  clamp(10px, 1vw,   12px);
    --fs-btn:   clamp(8px,  0.85vw, 10px);
    --fs-label: clamp(7px,  0.75vw, 9px);

    max-width: 1400px;
    margin: 0 auto;
    padding: clamp(8px, 2vw, 18px) clamp(8px, 2vw, 18px) clamp(28px, 4.5vw, 52px);
    font-family: 'DM Sans', sans-serif;
    color: #fff;
    animation: hubBoot 0.6s cubic-bezier(0.2, 1, 0.3, 1) both;
}

@keyframes hubBoot {
    from { opacity: 0; filter: brightness(0.5); transform: translateY(14px); }
    to   { opacity: 1; filter: brightness(1);   transform: translateY(0); }
}

/* ── TOAST ── */
.toastContainer { position: fixed; bottom: clamp(20px,3vh,36px); right: clamp(14px,2vw,26px); z-index: 99999; display: flex; flex-direction: column-reverse; gap: clamp(6px,0.8vw,10px); max-width: clamp(280px,90vw,400px); pointer-events: none; }
.toast { display: flex; align-items: flex-start; gap: clamp(8px,1vw,12px); padding: clamp(11px,1.3vw,15px) clamp(13px,1.6vw,18px); border-radius: 8px; box-shadow: 0 8px 28px rgba(0,0,0,0.5); pointer-events: all; animation: toastIn 0.3s cubic-bezier(0.18,0.89,0.32,1.28) both; }
@keyframes toastIn { from{opacity:0;transform:translateX(40px)} to{opacity:1;transform:translateX(0)} }
.toast_success { background: rgba(16,185,129,0.92);  border-left: 4px solid #059669; color: #fff; }
.toast_error   { background: rgba(239,68,68,0.92);   border-left: 4px solid #b91c1c; color: #fff; }
.toast_warn    { background: rgba(245,158,11,0.92);  border-left: 4px solid #b45309; color: #fff; }
.toast_info    { background: rgba(6,182,212,0.92);   border-left: 4px solid #0369a1; color: #fff; }
.toastIcon  { font-size: clamp(13px,1.5vw,17px); flex-shrink: 0; margin-top: 1px; }
.toastMsg   { font-family: 'Space Mono', monospace; font-size: clamp(9px,1vw,11px); font-weight: 700; line-height: 1.4; flex: 1; min-width: 0; word-break: break-word; }
.toastClose { background: transparent; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 2px; font-size: clamp(12px,1.3vw,15px); flex-shrink: 0; transition: opacity 0.15s; }
.toastClose:hover { opacity: 1; }

/* ── HEADER ── */
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
.headerLeft { display: flex; flex-direction: column; gap: clamp(3px, 0.4vw, 5px); flex: 1; min-width: 0; }
.title { font-family: 'Cinzel', serif; color: var(--navy); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; line-height: 1; margin: 0; }
.subtitle { font-family: 'DM Sans', sans-serif; color: #64748b; font-size: var(--fs-sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin: 0; }

/* ── PILLAR STACK ── */
.pillarStack { display: flex; flex-direction: column; gap: var(--gap-md); }

/* ── HW PANEL ── */
.hwPanel {
    background: var(--panel-bg); border: 1.5px solid var(--panel-border);
    border-radius: var(--radius); overflow: visible;
    box-shadow: 0 8px 24px rgba(0,0,0,0.14); transition: border-color 0.2s;
}
.hwPanel:hover { border-color: rgba(238,140,58,0.38); }

.drawerHeader { display: flex; justify-content: space-between; align-items: center; padding: clamp(8px, 1.1vw, 11px) clamp(12px, 1.5vw, 17px); border-bottom: 1px solid rgba(238,140,58,0.12); cursor: pointer; user-select: none; outline: none; transition: background 0.2s; }
.drawerHeader:hover { background: rgba(238,140,58,0.04); }
.drawerHeader:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.drawerTitle { display: flex; align-items: center; gap: clamp(7px, 0.9vw, 11px); font-family: 'DM Sans', sans-serif; color: var(--orange); font-weight: 900; font-size: var(--fs-drawer); letter-spacing: 2px; text-transform: uppercase; }
.drawerIcon { font-size: clamp(13px, 1.4vw, 16px); color: var(--orange); }
.chevron { color: var(--orange); font-size: clamp(15px, 1.7vw, 19px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); flex-shrink: 0; }
.rotated { transform: rotate(180deg); }
.panelBody { overflow: hidden; transition: max-height 0.45s cubic-bezier(0.4,0,0.2,1), opacity 0.35s; }
.bodyOpen   { max-height: 4000px; opacity: 1; }
.bodyClosed { max-height: 0;      opacity: 0; }
.panelInner { padding: 0; }

/* ── REPORT LIST & ROWS ── */
.reportList { display: flex; flex-direction: column; }

.reportRow {
    display: grid;
    grid-template-columns: clamp(36px, 4vw, 48px) 1.5fr 2fr clamp(28px, 3vw, 36px);
    align-items: center;
    gap: clamp(8px, 1.2vw, 13px);
    padding: clamp(9px, 1.2vw, 13px) clamp(12px, 1.5vw, 17px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    cursor: pointer;
    transition: background 0.18s;
    outline: none;
}
.reportRow:hover { background: rgba(255,255,255,0.04); }
.reportRow:focus-visible { background: rgba(238,140,58,0.06); outline: 2px solid var(--orange); outline-offset: -2px; }
.reportRow:last-child { border-bottom: none; }
.reportRowExpanded { background: rgba(0,0,0,0.2); border-bottom: none !important; }

.iconFrame {
    width:  clamp(28px, 3.2vw, 36px);
    height: clamp(28px, 3.2vw, 36px);
    background: var(--orange-dim); border: 1px solid var(--orange-border);
    border-radius: var(--radius-sm);
    display: flex; align-items: center; justify-content: center;
    color: var(--orange); font-size: clamp(12px, 1.3vw, 15px);
    flex-shrink: 0;
}
.rptTitle { font-family: 'Space Mono', monospace; font-weight: 900; color: #fff; font-size: var(--fs-title); letter-spacing: 0.5px; }
.rptDesc  { font-family: 'DM Sans', sans-serif; font-weight: 800; font-size: var(--fs-desc); color: rgba(255,255,255,0.5); }

.inspectIcon {
    color: rgba(255,255,255,0.25); font-size: clamp(14px,1.6vw,18px);
    justify-self: end; transition: color 0.18s;
}
.reportRow:hover .inspectIcon { color: var(--orange); }

/* ── EXPANDABLE REPORT DRAWER ── */
.reportDrawer {
    background: #0a0a0a;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    overflow: hidden;
    animation: drawerSlide 0.3s cubic-bezier(0.4,0,0.2,1) both;
}
@keyframes drawerSlide {
    from { opacity: 0; max-height: 0; }
    to   { opacity: 1; max-height: 400px; }
}

.drawerRawBox {
    padding: clamp(12px, 1.5vw, 16px) clamp(14px, 1.8vw, 20px);
    border-left: clamp(3px, 0.4vw, 4px) solid var(--orange);
    margin: clamp(8px, 1vw, 12px) clamp(12px, 1.5vw, 17px);
    border-radius: 0 4px 4px 0;
    background: rgba(255,255,255,0.025);
}

.drawerRawHeader {
    display: flex; align-items: center; gap: clamp(7px, 0.9vw, 10px);
    font-family: 'DM Sans', sans-serif; font-size: var(--fs-label);
    font-weight: 900; color: #4ade80; letter-spacing: 2px;
    margin-bottom: clamp(10px, 1.3vw, 14px); text-transform: uppercase;
}
.drawerRawHeader svg { color: #4ade80; font-size: 12px; }

.drawerDescription {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(11px, 1.1vw, 13px);
    font-weight: 800;
    color: rgba(255,255,255,0.75);
    line-height: 1.6;
    margin-bottom: clamp(12px, 1.5vw, 16px);
}

.drawerColumnsLabel {
    font-family: 'Space Mono', monospace;
    font-size: clamp(8px, 0.82vw, 9px);
    font-weight: 900;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: clamp(8px, 1vw, 10px);
}

.drawerColumns {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(5px, 0.7vw, 8px);
    margin-bottom: clamp(14px, 1.8vw, 18px);
}

.colChip {
    font-family: 'Space Mono', monospace;
    font-size: clamp(9px, 0.9vw, 10px);
    font-weight: 700;
    color: #ffffff;
    background: rgba(6, 182, 212, 0.12);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 4px;
    padding: clamp(3px, 0.4vw, 4px) clamp(7px, 0.9vw, 9px);
    letter-spacing: 0.5px;
    white-space: nowrap;
}

.drawerFooter {
    display: flex;
    justify-content: flex-end;
    padding-top: clamp(10px, 1.3vw, 14px);
    border-top: 1px solid rgba(255,255,255,0.07);
}

/* ── EXPORT BUTTON (inside drawer) ── */
.exportBtn {
    background: #EE8C3A;
    border: none;
    color: #1a2e30;
    padding: clamp(8px, 1vw, 11px) clamp(16px, 2vw, 22px);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif; font-weight: 900;
    font-size: clamp(9px, 0.9vw, 11px); letter-spacing: 1px; text-transform: uppercase;
    cursor: pointer; display: inline-flex; align-items: center;
    justify-content: center; gap: clamp(5px, 0.6vw, 7px);
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
    box-shadow: 0 4px 14px rgba(238,140,58,0.3);
    white-space: nowrap;
}
.exportBtn:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 20px rgba(238,140,58,0.5);
    transform: translateY(-1px);
}
.exportBtn:disabled { opacity: 0.4; cursor: wait; background: rgba(238,140,58,0.5); transform: none; box-shadow: none; }
.exportBtn:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* ── SECURITY HANDBRAKE ── */
.restrictionHandbrake {
    border-radius: var(--radius);
    background: rgba(69,10,10,0.6); border: 1px solid #7f1d1d;
    padding: clamp(12px, 1.5vw, 18px) clamp(16px, 2vw, 24px);
    display: flex; align-items: center; gap: clamp(10px, 1.3vw, 16px);
}
.lockIcon { color: #ef4444; font-size: clamp(20px, 2.5vw, 28px); flex-shrink: 0; animation: lockPulse 2s infinite; }
@keyframes lockPulse { 0%,100%{opacity:1} 50%{opacity:0.55} }
.warningText strong { display: block; font-family: 'DM Sans', sans-serif; color: #fca5a5; font-size: var(--fs-drawer); font-weight: 900; letter-spacing: 1px; margin-bottom: clamp(2px,0.3vw,4px); text-transform: uppercase; }
.warningText p { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.65); font-size: var(--fs-label); font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    .reportRow { grid-template-columns: clamp(28px, 6vw, 36px) 1fr clamp(24px, 3vw, 30px); grid-template-rows: auto auto; }
    .rptDesc { grid-column: 2; }
    .inspectIcon { grid-row: 1; grid-column: 3; }
    .drawerColumns { gap: 4px; }
    .colChip { font-size: 9px; padding: 2px 6px; }
}
@media (max-width: 480px) {
    .container { --gap-lg: 8px; --gap-md: 5px; --fs-h1: 16px; --fs-drawer: 9px; --fs-btn: 8px; }
    .drawerRawBox { padding: 10px; margin: 6px; }
    .drawerDescription { font-size: 11px; }
    .exportBtn { width: 100%; }
    .drawerFooter { justify-content: stretch; }
}
"""

write(os.path.join(BASE, 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'), payments_jsx)
write(os.path.join(BASE, 'erp-frontend/src/pages/Reports/ReportHub.jsx'), report_jsx)
write(os.path.join(BASE, 'erp-frontend/src/pages/Reports/ReportHub.module.css'), report_css)

print('\nAll patches applied.')