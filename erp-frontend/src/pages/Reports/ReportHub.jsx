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

    const [drawers, setDrawers] = useState({ finance: true, ops: true, system: false });
    const [status,  setStatus]  = useState({
        debt: false, map: false, perf: false,
        stage: false, legal: false, risk: false,
        audit: false, revenue: false,
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

            <header className={styles.header}>
                <h1 className={styles.title}>Intelligence Hub</h1>
                <p className={styles.subtitle}>Direct Database Analysis &amp; CSV Export Terminal</p>
            </header>

            <div className={styles.pillarStack}>

                {hasFinancialAccess ? (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="FINANCIAL INTELLIGENCE" isOpen={drawers.finance} onClick={() => toggleDrawer('finance')} icon={FiBarChart2} />
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
                    <DrawerTitle label="OPERATIONAL LOGISTICS" isOpen={drawers.ops} onClick={() => toggleDrawer('ops')} icon={FiMap} />
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
                        <DrawerTitle label="SYSTEM FORENSICS" isOpen={drawers.system} onClick={() => toggleDrawer('system')} icon={FiShield} />
                        <div className={`${styles.panelBody} ${drawers.system ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.system}>
                            <div className={styles.panelInner}>
                                <div className={styles.reportList}>
                                    {SYSTEM_GROUP.map(item => <ReportRow key={item.id} item={item} />)}
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