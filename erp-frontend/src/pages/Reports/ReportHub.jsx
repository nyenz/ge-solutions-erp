// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
import React, { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    FiBarChart2, FiMap, FiActivity, FiLayers,
    FiShield, FiTrendingUp, FiLock, FiDownloadCloud,
    FiChevronDown, FiCreditCard, FiDatabase, FiFileText,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import reportService from '../../services/reportService';
import BackToTopButton from '../../components/common/BackToTopButton';
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

// ─── REPORT DATA ──────────────────────────────────────────────────
const REPORT_SCHEMA = {
    debt:      { columns: 'PLOT_ID, PRIMARY_OWNER, PHONE, TOTAL_VAL, PAID_VAL, ARREARS, BOX_LOC, STATUS', desc: 'Lists every plot with an outstanding balance. Shows the full financial picture per client — what they owe, what they have paid, and where their physical file is stored.' },
    revenue:   { columns: 'DATE, PLOT_ID, OWNER_NAME, PAYMENT_TYPE, AMOUNT_UGX, BALANCE_AFTER_UGX, RECORDED_BY, NOTES', desc: 'A chronological log of every cash payment ever recorded in the system, including who logged it and the running balance after each transaction.' },
    perf:      { columns: 'TIMESTAMP, OPERATOR, PLOT_ID, NOTE_SNIPPET', desc: 'Pulls every call log and follow-up note entered by staff. Use this to audit which managers are actively contacting clients and how frequently.' },
    map:       { columns: 'BOX_LOCATION, PLOT_ID, TENURE, DISTRICT, STAGE_INDEX, IS_LEGACY', desc: 'A full inventory of every physical file sorted by cabinet box number. Useful for locating a specific title in the office archive quickly.' },
    stage:     { columns: 'PHASE_NUMBER, TOTAL_FILES_IN_STAGE', desc: 'Shows how many title files are stuck at each of the five survey stages. Helps identify bottlenecks slowing down the processing pipeline.' },
    risk:      { columns: 'OWNER_NAME, SCORE_PERCENT, LAST_CALL_DATE', desc: 'Ranks all registered clients by their reliability score — a measure of payment consistency and responsiveness to calls.' },
    legal:     { columns: 'PLOT, OWNER, PHONE, NIN_STATUS, ADDRESS_STATUS, READINESS', desc: 'Checks whether every registered owner has a valid National ID and home address on file — the two fields required before issuing a legal demand notice.' },
    audit:     { columns: 'TIMESTAMP, OPERATOR, ACTION_CODE, HARDWARE_DETAILS', desc: 'The complete forensic footprint of every action taken inside the system — edits, deletions, logins, payment recordings, and stage changes.' },
    receivable:   { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, RECEIVABLES_START, TITLE_COST_UGX, STORAGE_FEES_UGX, MONTHS_IN_RECEIVABLES, TOTAL_PAID, TOTAL_OWED', desc: 'A detailed breakdown of every plot currently in the receivables system, including accumulated storage fees and months elapsed since the receivables start date.' },
    completed: { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, TOTAL_COST, AMOUNT_PAID, STATUS', desc: 'Lists all titles that have been fully paid or officially released to the client. Use this to track closed cases and measure overall throughput.' },
    reconcile: { columns: 'OPERATOR_ID, TOTAL_CASH_COLLECTED_UGX, NUMBER_OF_TRANSACTIONS, FIRST_PAYMENT_DATE, LAST_PAYMENT_DATE', desc: 'Anti-theft report: groups all payments by the staff member who recorded them. Compare these totals against physical cash in the office to detect discrepancies.' },
    monthly:   { columns: 'YEAR_MONTH, TOTAL_COLLECTED_UGX, TRANSACTION_COUNT', desc: 'Shows total cash collected each calendar month for the past 24 months. Use this to spot seasonal patterns and track collection performance over time.' },
};

// ─── MAIN ─────────────────────────────────────────────────────────
const ReportHub = () => {
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR';

    const [drawers,    setDrawers]    = useState({ finance: true, ops: true, system: false, p2: true });
    const [expandedId, setExpandedId] = useState(null);
    const [status,     setStatus]     = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        receivable: false, completed: false, reconcile: false, monthly: false,
    });

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const triggerPillarExport = async (id, action, label) => {
        setStatus(prev => ({ ...prev, [id]: true }));
        try {
            await action();
            toast(`${label} -- EXPORT COMPLETE`, 'success', 4000);
        } catch (err) {
            toast(`REPORT FAULT: ${err.message || 'UNKNOWN ERROR'}`, 'error', 8000);
        } finally {
            setStatus(prev => ({ ...prev, [id]: false }));
        }
    };

    const FINANCIAL_GROUP = [
        { id: 'debt',    title: 'Master Debt Ledger',     icon: FiCreditCard, action: reportService.downloadDebtLedger   },
        { id: 'revenue', title: 'Revenue Inflow History',  icon: FiDatabase,   action: reportService.downloadRevenue      },
        { id: 'perf',    title: 'Recovery Throughput',     icon: FiActivity,   action: reportService.downloadPerformance  },
    ];
    const OPS_GROUP = [
        { id: 'map',   title: 'Physical Archive Map',  icon: FiMap,        action: reportService.downloadArchiveMap   },
        { id: 'stage', title: 'Survey Stage Audit',    icon: FiLayers,     action: reportService.downloadBottlenecks  },
        { id: 'risk',  title: 'Reliability Scorecard', icon: FiTrendingUp, action: reportService.downloadReliability  },
    ];
    const SYSTEM_GROUP = [
        { id: 'legal', title: 'Legal Readiness Audit', icon: FiFileText, action: reportService.downloadLegalReady  },
        { id: 'audit', title: 'Master System Audit',   icon: FiShield,   action: reportService.downloadAuditTrail  },
    ];
    const PRIORITY2_GROUP = [
        { id: 'receivable',   title: 'Receivables Breakdown',            icon: FiLock,        action: reportService.downloadReceivableBreakdown         },
        { id: 'completed', title: 'Completed Titles',             icon: FiCheckSquare, action: reportService.downloadCompletedTitles         },
        { id: 'reconcile', title: 'Operator Cash Reconciliation', icon: FiShield,      action: reportService.downloadOperatorReconciliation   },
        { id: 'monthly',   title: 'Monthly Collection',           icon: FiBarChart2,   action: reportService.downloadMonthlyCollection        },
    ];

    const ReportRow = ({ item }) => {
        const ItemIcon = item.icon;
        const isLoading = status[item.id];
        const isExpanded = expandedId === item.id;
        const schema = REPORT_SCHEMA[item.id] || {};

        return (
            <div className={styles.reportRowWrap}>
                <div
                    className={`${styles.reportRow} ${isExpanded ? styles.reportRowActive : ''}`}
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    role="button"
                    tabIndex={0}
                    aria-expanded={isExpanded}
                    aria-label={`${item.title}, ${isExpanded ? 'collapse' : 'expand details'}`}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedId(isExpanded ? null : item.id); } }}
                >
                    <div className={styles.iconFrame} aria-hidden="true">
                        <ItemIcon aria-hidden="true" />
                    </div>
                    <span className={styles.rptTitle}>{item.title}</span>
                    <FiChevronDown className={`${styles.rowChevron} ${isExpanded ? styles.rotated : ''}`} aria-hidden="true" />
                </div>

                <div className={`${styles.reportDetails} ${isExpanded ? styles.detailsOpen : styles.detailsClosed}`}>
                    <div className={styles.detailBox}>
                        <div className={styles.detailHeader}>
                            <span>REPORT INTELLIGENCE DISCOVERY [SECURE]</span>
                        </div>
                        <p className={styles.detailDesc}>{schema.desc}</p>
                        {schema.columns && (
                            <div className={styles.schemaBlock}>
                                <span className={styles.schemaLabel}>CSV COLUMN SCHEMA:</span>
                                <p className={styles.schemaColumns}>{schema.columns}</p>
                            </div>
                        )}
                        <div className={styles.detailActions}>
                            <button
                                className={styles.exportBtnLarge}
                                onClick={e => { e.stopPropagation(); triggerPillarExport(item.id, item.action, item.title); }}
                                disabled={isLoading}
                                aria-label={isLoading ? `Exporting ${item.title}` : `Download ${item.title}`}
                            >
                                {isLoading
                                    ? <><div className={styles.exportSpinner} aria-hidden="true" /> STREAMING DATA...</>
                                    : <><FiDownloadCloud aria-hidden="true" /> DOWNLOAD CSV</>
                                }
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <BackToTopButton />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>Reports</h1>
                    <p className={styles.subtitle}>Download CSV reports for analysis</p>
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
