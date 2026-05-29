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

// ─── MAIN ─────────────────────────────────────────────────────────
const ReportHub = () => {
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();

    const hasFinancialAccess = user?.isRoot || user?.role === 'ROLE_ADMIN';

    const [drawers, setDrawers] = useState({ finance: true, ops: true, system: false, p2: true });
    const [status,  setStatus]  = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
        backlog: false, completed: false, reconcile: false, monthly: false,
    });

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const triggerPillarExport = async (id, action, label) => {
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
        { id: 'backlog',   title: 'Backlog Breakdown',            desc: 'All backlog plots with storage fees, months owed, and total outstanding.',                                         icon: FiLock,       action: reportService.downloadBacklogBreakdown         },
        { id: 'completed', title: 'Completed Titles',             desc: 'All released or fully paid plots ready for handover.',                                                            icon: FiCheckSquare, action: reportService.downloadCompletedTitles         },
        { id: 'reconcile', title: 'Operator Cash Reconciliation', desc: 'Anti-theft: total cash collected per operator, transaction count, and date range. Compare against physical cash.', icon: FiShield,     action: reportService.downloadOperatorReconciliation   },
        { id: 'monthly',   title: 'Monthly Collection',           desc: 'Total cash collected per calendar month for the last 24 months.',                                                 icon: FiBarChart2,  action: reportService.downloadMonthlyCollection        },
    ];

    const ReportRow = ({ item }) => {
        const ItemIcon = item.icon;
        const isLoading = status[item.id];
        return (
            <div className={styles.reportRow}>
                <div className={styles.iconFrame} aria-hidden="true">
                    <ItemIcon aria-hidden="true" />
                </div>
                <span className={styles.rptTitle}>{item.title}</span>
                <span className={styles.rptDesc}>{item.desc}</span>
                <button
                    className={styles.exportBtn}
                    onClick={() => triggerPillarExport(item.id, item.action, item.title)}
                    disabled={isLoading}
                    aria-label={isLoading ? `Exporting ${item.title}` : `Download ${item.title}`}
                >
                    {isLoading
                        ? 'STREAMING...'
                        : <><FiDownloadCloud aria-hidden="true" /> DOWNLOAD</>
                    }
                </button>
            </div>
        );
    };

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

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