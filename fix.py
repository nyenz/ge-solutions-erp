import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erp-frontend', 'src', 'pages', 'Reports')

# ── ReportHub.jsx ─────────────────────────────────────────────────────────────
JSX = r"""// PATH: erp-frontend/src/pages/Reports/ReportHub.jsx
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
    backlog:   { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, BACKLOG_START, TITLE_COST_UGX, STORAGE_FEES_UGX, MONTHS_IN_BACKLOG, TOTAL_PAID, TOTAL_OWED', desc: 'A detailed breakdown of every plot currently in the backlog system, including accumulated storage fees and months elapsed since the backlog start date.' },
    completed: { columns: 'PLOT_ID, BOX, DISTRICT, TENURE, PRIMARY_OWNER, PHONE, TOTAL_COST, AMOUNT_PAID, STATUS', desc: 'Lists all titles that have been fully paid or officially released to the client. Use this to track closed cases and measure overall throughput.' },
    reconcile: { columns: 'OPERATOR_ID, TOTAL_CASH_COLLECTED_UGX, NUMBER_OF_TRANSACTIONS, FIRST_PAYMENT_DATE, LAST_PAYMENT_DATE', desc: 'Anti-theft report: groups all payments by the staff member who recorded them. Compare these totals against physical cash in the office to detect discrepancies.' },
    monthly:   { columns: 'YEAR_MONTH, TOTAL_COLLECTED_UGX, TRANSACTION_COUNT', desc: 'Shows total cash collected each calendar month for the past 24 months. Use this to spot seasonal patterns and track collection performance over time.' },
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
        { id: 'backlog',   title: 'Backlog Breakdown',            icon: FiLock,        action: reportService.downloadBacklogBreakdown         },
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
"""

# ── ReportHub.module.css ──────────────────────────────────────────────────────
CSS = r"""/* PATH: erp-frontend/src/pages/Reports/ReportHub.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238, 140, 58, 0.18);
    --orange-border: rgba(238, 140, 58, 0.28);
    --navy:          #1a2e30;
    --panel-bg:      linear-gradient(160deg, #1c3335 0%, #213E40 100%);
    --panel-border:  rgba(238, 140, 58, 0.2);
    --red:           #ef4444;
    --green:         #4ade80;

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
.toastClose { background: transparent; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 2px; font-size: clamp(12px,1.3vw,15px); flex-shrink: 0; }
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
.headerLeft { display: flex; flex-direction: column; gap: clamp(3px,0.4vw,5px); min-width: 0; flex: 1; }
.title  { font-family: 'Cinzel', serif; color: var(--navy); font-size: var(--fs-h1); font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; line-height: 1; margin: 0; }
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

.drawerHeader {
    display: flex; justify-content: space-between; align-items: center;
    padding: clamp(8px, 1.1vw, 11px) clamp(12px, 1.5vw, 17px);
    border-bottom: 1px solid rgba(238,140,58,0.12);
    cursor: pointer; user-select: none; outline: none; transition: background 0.2s;
}
.drawerHeader:hover { background: rgba(238,140,58,0.04); }
.drawerHeader:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.drawerTitle { display: flex; align-items: center; gap: clamp(7px,0.9vw,11px); font-family: 'DM Sans', sans-serif; color: var(--orange); font-weight: 900; font-size: var(--fs-drawer); letter-spacing: 2px; text-transform: uppercase; }
.drawerIcon { font-size: clamp(13px,1.4vw,16px); color: var(--orange); }
.chevron { color: var(--orange); font-size: clamp(15px,1.7vw,19px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1); flex-shrink: 0; }
.rotated { transform: rotate(180deg); }
.panelBody { overflow: hidden; transition: max-height 0.45s cubic-bezier(0.4,0,0.2,1), opacity 0.35s; }
.bodyOpen   { max-height: 6000px; opacity: 1; }
.bodyClosed { max-height: 0;      opacity: 0; }
.panelInner { padding: 0; }

/* ── REPORT LIST ── */
.reportList { display: flex; flex-direction: column; }

/* ── REPORT ROW WRAPPER ── */
.reportRowWrap { border-bottom: 1px solid rgba(255,255,255,0.05); }
.reportRowWrap:last-child { border-bottom: none; }

/* ── CLICKABLE HEADER ROW ── */
.reportRow {
    display: grid;
    grid-template-columns: clamp(36px,4vw,48px) 1fr clamp(24px,2.8vw,32px);
    align-items: center;
    gap: clamp(8px,1.2vw,13px);
    padding: clamp(11px,1.4vw,16px) clamp(12px,1.5vw,17px);
    cursor: pointer;
    user-select: none;
    outline: none;
    transition: background 0.18s;
}
.reportRow:hover { background: rgba(255,255,255,0.035); }
.reportRow:focus-visible { outline: 2px solid var(--orange); outline-offset: -2px; }
.reportRowActive { background: rgba(238,140,58,0.06); border-left: 3px solid var(--orange); }

.iconFrame {
    width:  clamp(28px,3.2vw,36px); height: clamp(28px,3.2vw,36px);
    background: var(--orange-dim); border: 1px solid var(--orange-border);
    border-radius: var(--radius-sm); display: flex; align-items: center;
    justify-content: center; color: var(--orange); font-size: clamp(12px,1.3vw,15px); flex-shrink: 0;
}
.rptTitle { font-family: 'Space Mono', monospace; font-weight: 900; color: #fff; font-size: var(--fs-title); letter-spacing: 0.5px; }
.rowChevron { color: rgba(255,255,255,0.3); font-size: clamp(14px,1.6vw,18px); transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), color 0.2s; flex-shrink: 0; justify-self: end; }
.reportRow:hover .rowChevron { color: var(--orange); }

/* ── FORENSIC DRAWER ── */
.reportDetails { overflow: hidden; transition: max-height 0.4s cubic-bezier(0.4,0,0.2,1); }
.detailsOpen   { max-height: 600px; }
.detailsClosed { max-height: 0; }

/* Pure black forensic drawer -- matches AuditPage traceDetails exactly */
.detailBox {
    background: #0a0a0a;
    border-top: 1px solid rgba(255,255,255,0.08);
    border-left: clamp(3px,0.4vw,4px) solid var(--orange);
    padding: clamp(14px,1.8vw,20px) clamp(16px,2vw,22px);
    page-break-inside: avoid;
    break-inside: avoid;
}

/* Terminal-green header */
.detailHeader {
    display: flex;
    align-items: center;
    gap: clamp(7px,0.9vw,10px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px,0.82vw,10px);
    font-weight: 900;
    color: #4ade80;
    letter-spacing: 2px;
    margin-bottom: clamp(10px,1.3vw,14px);
    text-transform: uppercase;
}

/* Plain English description in soft grey */
.detailDesc {
    margin: 0 0 clamp(12px,1.5vw,16px);
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(11px,1.1vw,13px);
    font-weight: 700;
    color: rgba(255,255,255,0.65);
    line-height: 1.65;
}

/* Schema block */
.schemaBlock {
    margin-bottom: clamp(14px,1.8vw,20px);
}
.schemaLabel {
    display: block;
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(8px,0.82vw,10px);
    font-weight: 900;
    color: var(--orange);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: clamp(5px,0.6vw,7px);
}
.schemaColumns {
    margin: 0;
    font-family: 'Space Mono', monospace;
    font-size: clamp(10px,1.05vw,12px);
    font-weight: 900;
    color: #ffffff;
    line-height: 1.6;
    word-break: break-word;
}

/* Action row with the big download button */
.detailActions {
    display: flex;
    justify-content: flex-start;
    padding-top: clamp(10px,1.3vw,14px);
    border-top: 1px solid rgba(255,255,255,0.08);
}

/* Large, beautiful download button */
.exportBtnLarge {
    display: inline-flex;
    align-items: center;
    gap: clamp(8px,1vw,12px);
    padding: 0 clamp(20px,2.5vw,30px);
    height: clamp(40px,5vw,48px);
    background: var(--orange);
    color: #1a2e30;
    border: none;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(10px,1vw,12px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
    box-shadow: 0 4px 16px rgba(238,140,58,0.35);
    white-space: nowrap;
}
.exportBtnLarge:hover:not(:disabled) {
    background: #f0a050;
    box-shadow: 0 0 24px rgba(238,140,58,0.55);
    transform: translateY(-1px);
}
.exportBtnLarge:disabled { opacity: 0.5; cursor: wait; }
.exportBtnLarge:focus-visible { outline: 2px solid var(--orange); outline-offset: 3px; }

/* Spinner inside export button */
.exportSpinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(26,46,48,0.3);
    border-top-color: #1a2e30;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── SECURITY HANDBRAKE ── */
.restrictionHandbrake {
    border-radius: var(--radius); background: rgba(69,10,10,0.6); border: 1px solid #7f1d1d;
    padding: clamp(12px,1.5vw,18px) clamp(16px,2vw,24px); display: flex; align-items: center; gap: clamp(10px,1.3vw,16px);
}
.lockIcon { color: #ef4444; font-size: clamp(20px,2.5vw,28px); flex-shrink: 0; animation: lockPulse 2s infinite; }
@keyframes lockPulse { 0%,100%{opacity:1} 50%{opacity:0.55} }
.warningText strong { display: block; font-family: 'DM Sans', sans-serif; color: #fca5a5; font-size: var(--fs-drawer); font-weight: 900; letter-spacing: 1px; margin-bottom: clamp(2px,0.3vw,4px); text-transform: uppercase; }
.warningText p { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.65); font-size: var(--fs-label); font-weight: 800; margin: 0; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    .reportRow { grid-template-columns: clamp(28px,6vw,36px) 1fr clamp(20px,4vw,28px); }
    .detailBox { padding: clamp(12px,3vw,16px); }
    .exportBtnLarge { width: 100%; justify-content: center; }
}
@media (max-width: 480px) {
    .container { --gap-lg: 8px; --gap-md: 5px; --fs-h1: 16px; --fs-drawer: 9px; }
    .rptTitle { font-size: 11px; }
    .schemaColumns { font-size: 10px; }
}
"""

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'OK: {path}')

write(os.path.join(BASE, 'ReportHub.jsx'), JSX)
write(os.path.join(BASE, 'ReportHub.module.css'), CSS)

print('\nAll patches applied.')