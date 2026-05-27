// PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap, FiSettings, FiRepeat
} from 'react-icons/fi';
import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';

const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        if (duration > 0) setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    const dismiss = useCallback((id) => setToasts(prev => prev.filter(t => t.id !== id)), []);
    return { toasts, toast, dismissToast: dismiss };
};

const TOAST_ICONS = {
    success: <FiCheckSquare aria-hidden="true" />,
    error:   <FiAlertCircle aria-hidden="true" />,
    warn:    <FiAlertTriangle aria-hidden="true" />,
    info:    <FiInfo aria-hidden="true" />,
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

const fmt = (n) => Number(n || 0).toLocaleString();

const BADGE_COLORS = { GREEN: '#22c55e', YELLOW: '#f59e0b', RED: '#ef4444' };
const BADGE_LABELS = { GREEN: 'Paid within 14 days', YELLOW: 'Paid within 30 days', RED: 'No recent payment' };

const PaymentBadge = ({ badge }) => (
    <span
        style={{
            display: 'inline-block', width: 9, height: 9, borderRadius: '50%',
            background: BADGE_COLORS[badge] || BADGE_COLORS.RED,
            flexShrink: 0, marginTop: 3,
            boxShadow: `0 0 5px ${BADGE_COLORS[badge] || BADGE_COLORS.RED}`
        }}
        title={BADGE_LABELS[badge] || 'No recent payment'}
        aria-label={BADGE_LABELS[badge] || 'No recent payment'}
    />
);

// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────
const StorageFeeInlineControls = ({ plot, onUpdated, toast }) => {
    const [rateInput, setRateInput] = React.useState('');
    const [saving, setSaving] = React.useState(false);
    const [expanded, setExpanded] = React.useState(false);

    const handleSetRate = async () => {
        const val = Number(rateInput);
        if (rateInput === '' || val < 0) {
            toast('ENTER A VALID MONTHLY RATE', 'error');
            return;
        }
        setSaving(true);
        try {
            await recoveryService.setStorageRate(plot.projectId, val);
            setRateInput('');
            setExpanded(false);
            await onUpdated();
            toast('MONTHLY FEE UPDATED', 'success');
        } catch {
            toast('FEE UPDATE FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleTogglePause = async () => {
        setSaving(true);
        try {
            await recoveryService.pauseStorageFees(plot.projectId, !plot.storagePaused);
            await onUpdated();
            toast(plot.storagePaused ? 'STORAGE FEES RESUMED' : 'STORAGE FEES PAUSED', 'info');
        } catch {
            toast('ACTION FAILED', 'error');
        } finally {
            setSaving(false);
        }
    };

    const currentRate = plot.storageFeeOverride && Number(plot.storageFeeOverride) > 0
        ? Number(plot.storageFeeOverride)
        : 50000;

    if (!expanded) {
        return (
            <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <button
                    onClick={() => setExpanded(true)}
                    style={{
                        background: 'transparent',
                        border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 5,
                        color: 'rgba(252,165,165,0.7)',
                        fontFamily: 'DM Sans,sans-serif',
                        fontSize: 9,
                        fontWeight: 900,
                        letterSpacing: 1,
                        textTransform: 'uppercase',
                        padding: '4px 10px',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                    }}>
                    <FiSettings size={10} />
                    FEE: UGX {Number(currentRate).toLocaleString()}/mo
                    {plot.storagePaused && <span style={{color:'#fcd34d'}}> · PAUSED</span>}
                </button>
            </div>
        );
    }

    return (
        <div style={{
            marginTop: 10,
            padding: '10px 12px',
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 7,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 9, fontWeight: 900, color: '#fca5a5', textTransform: 'uppercase', letterSpacing: 1.5 }}>
                    STORAGE FEE SETTINGS
                </span>
                <button onClick={() => setExpanded(false)} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 14 }}>
                    <FiX size={13} />
                </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        MONTHLY RATE (UGX)
                    </div>
                    <div style={{ display: 'flex', gap: 5 }}>
                        <input
                            type="number"
                            value={rateInput}
                            onChange={e => setRateInput(e.target.value)}
                            placeholder={String(currentRate)}
                            style={{
                                flex: 1,
                                background: '#fff',
                                border: '1.5px solid #c8d6d7',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'Space Mono,monospace',
                                fontWeight: 700,
                                fontSize: 11,
                                padding: '5px 8px',
                                outline: 'none',
                                minWidth: 0,
                            }}
                        />
                        <button
                            onClick={handleSetRate}
                            disabled={saving}
                            style={{
                                background: '#EE8C3A',
                                border: 'none',
                                borderRadius: 5,
                                color: '#1a2e30',
                                fontFamily: 'DM Sans,sans-serif',
                                fontSize: 9,
                                fontWeight: 900,
                                padding: '0 9px',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                flexShrink: 0,
                            }}>
                            SET
                        </button>
                    </div>
                </div>
                <div>
                    <div style={{ fontFamily: 'DM Sans,sans-serif', fontSize: 8, fontWeight: 900, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>
                        FEE STATUS
                    </div>
                    <button
                        onClick={handleTogglePause}
                        disabled={saving}
                        style={{
                            width: '100%',
                            background: plot.storagePaused ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                            border: plot.storagePaused ? '1.5px solid rgba(16,185,129,0.5)' : '1.5px solid rgba(245,158,11,0.5)',
                            borderRadius: 5,
                            color: plot.storagePaused ? '#34d399' : '#fcd34d',
                            fontFamily: 'DM Sans,sans-serif',
                            fontSize: 9,
                            fontWeight: 900,
                            padding: '6px 0',
                            cursor: 'pointer',
                            textTransform: 'uppercase',
                            letterSpacing: 1,
                        }}>
                        {plot.storagePaused ? 'RESUME FEES' : 'PAUSE FEES'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── MAIN COMPONENT ──────────────────────────────────────────────
const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const [viewMode,      setViewMode]      = useState('ACTION');
    const [missions,      setMissions]      = useState([]);
    const [loading,       setLoading]       = useState(true);
    const [expandedId,    setExpandedId]    = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [statusFilter,  setStatusFilter]  = useState('ALL');

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });
    const [callHistory,   setCallHistory]   = useState([]);
    const [logContent,    setLogContent]    = useState('');
    const [committing,    setCommitting]    = useState(false);

    const callDirty = callModal.open && logContent.trim() !== '';
    const { blocked: guardOpen, proceed: guardLeave, reset: guardStay } = useRouterBlock(callDirty);

    const [discardModalOpen, setDiscardModalOpen] = useState(false);

    const handleCloseCallModal = () => {
        if (callDirty) {
            setDiscardModalOpen(true);
            return;
        }
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };

    const handleConfirmDiscard = () => {
        setDiscardModalOpen(false);
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };

    const handleCancelDiscard = () => {
        setDiscardModalOpen(false);
    };

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch {
            toast('Failed to load recovery data', 'error', 6000);
        } finally {
            setLoading(false);
        }
    }, [viewMode, toast]);

    useEffect(() => { loadData(); }, [loadData]);

    useEffect(() => {
        if (!callModal.mission) return;
        recoveryService.getHistory(callModal.mission.projectId)
            .then(setCallHistory)
            .catch(() => setCallHistory([]));
    }, [callModal.mission]);

    const handleLogCall = async () => {
        if (!logContent.trim() || !callModal.mission) return;
        setCommitting(true);
        try {
            await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);
            await loadData();
            setCallModal({ open: false, mission: null });
            setLogContent('');
            setExpandedId(null);
            toast('Call logged. 14-day timer reset.', 'success');
        } catch {
            toast('LOG FAILURE', 'error', 8000);
        } finally {
            setCommitting(false);
        }
    };

    const filteredMissions = useMemo(() => {
        let list = missions;

        // Search filter
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase().replace(/\s+/g, '');
            list = list.filter(m =>
                m.plotNumber?.toLowerCase().includes(term) ||
                m.physicalBoxNumber?.toLowerCase().includes(term) ||
                (m.owners || []).some(o =>
                    o.fullName?.toLowerCase().includes(term) ||
                    o.phoneNumber?.replace(/\s+/g, '').includes(term)
                )
            );
        }

        // Status filter
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.backlog || m.isBacklog);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !(m.backlog || m.isBacklog));
        if (statusFilter === 'DUE')     list = list.filter(m => !m.isLocked);

        return list;
    }, [missions, searchTerm, statusFilter]);

    const getStatusStyle = (status) => {
        if (status === 'ACTION REQUIRED' || status === 'NEW ASSIGNMENT') return styles.statusRed;
        if (status === 'COOLING DOWN')  return styles.statusBlue;
        if (status === 'MONTHLY LIMIT') return styles.statusGrey;
        return styles.statusDefault;
    };

    const totalBacklogOwed  = useMemo(() => filteredMissions.filter(m => m.isBacklog || m.backlog).reduce((s, m) => s + Number(m.totalBacklogOwed || 0), 0), [filteredMissions]);
    const totalActiveOwed   = useMemo(() => filteredMissions.filter(m => !(m.isBacklog || m.backlog)).reduce((s, m) => s + Number(m.currentBalance || 0), 0), [filteredMissions]);
    const totalStorageFees  = useMemo(() => filteredMissions.reduce((s, m) => s + Number(m.storageFeesAccumulated || 0), 0), [filteredMissions]);

    const renderCard = (mission) => {
        const isExpanded = expandedId === mission.projectId;
        const toggle = () => setExpandedId(prev => prev === mission.projectId ? null : mission.projectId);
        const owners = mission.owners || [];
        const ownerNames = owners.map(o => o.fullName).join(' & ') || '---';
        const phones = owners.map(o => o.phoneNumber).join(' / ') || '---';
        const balance = mission.isBacklog || mission.backlog
            ? mission.totalBacklogOwed
            : mission.currentBalance;

        return (
            <div key={mission.projectId}
                className={`${styles.missionCard} ${mission.isLocked ? styles.cardLocked : ''} ${(mission.isBacklog || mission.backlog) ? styles.cardBacklog : ''}`}>

                <div className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                    {mission.isLocked && <FiLock size={10} />}
                    {mission.missionStatus}
                </div>

                {/* COMPACT CLOSED VIEW */}
                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } }}>

                    <div className={styles.cardMain}>
                        <div className={styles.cardTopRow}>
                            <PaymentBadge badge={mission.paymentHealthBadge} />
                            <span className={styles.plotId}>{mission.plotNumber}</span>
                            {(mission.isBacklog || mission.backlog) && (
                                <span className={styles.backlogPill}>BACKLOG</span>
                            )}
                        </div>
                        <div className={styles.ownerLine}>{ownerNames}</div>
                        <div className={styles.phoneLine}>{phones}</div>
                        <div className={styles.balanceLine}>
                            <span className={styles.balanceLabel}>OWED:</span>
                            <span className={`${styles.balanceVal} ${(mission.isBacklog || mission.backlog) ? styles.balanceRed : ''}`}>
                                UGX {fmt(balance)}
                            </span>
                        </div>
                    </div>

                    <div className={styles.cardSideActions}>
                        <button className={styles.logCallBtnSmall}
                            disabled={mission.isLocked}
                            onClick={e => { e.stopPropagation(); setCallModal({ open: true, mission }); setLogContent(''); }}
                            aria-label="Log call">
                            <FiPhoneCall size={12} />
                            {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                        </button>
                        <div className={styles.expandIcon} aria-hidden="true">
                            {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                        </div>
                    </div>
                </div>

                {/* EXPANDED DETAILS */}
                {isExpanded && (
                    <div className={styles.cardBody}>
                        <div className={styles.divider} />
                        <div className={styles.timingRow}>
                            <FiClock size={11} />
                            <span>Last call: <strong>{mission.lastContactDate}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Next: <strong>{mission.nextCallDue}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Calls: <strong>{mission.monthlyCallCount}/2</strong></span>
                        </div>
                        {/* financial detail */}
                        {(mission.isBacklog || mission.backlog) ? (
                            <div className={styles.finDetail}>
                                <div className={styles.finDetailRow}>
                                    <span>Title cost</span><strong>UGX {fmt(mission.totalCost)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span style={{color:'#fca5a5'}}>+ Storage fees</span>
                                    <strong style={{color:'#ef4444'}}>UGX {fmt(mission.storageFeesAccumulated)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span>- Paid</span>
                                    <strong style={{color:'#86efac'}}>UGX {fmt(mission.amountPaid)}</strong>
                                </div>
                                <div className={`${styles.finDetailRow} ${styles.finDetailTotal}`}>
                                    <span>NOW OWED</span>
                                    <strong style={{color:'#ef4444'}}>UGX {fmt(mission.totalBacklogOwed)}</strong>
                                </div>
                            </div>
                        ) : (
                            <div className={styles.finDetail}>
                                <div className={styles.finDetailRow}>
                                    <span>Total cost</span><strong>UGX {fmt(mission.totalCost)}</strong>
                                </div>
                                <div className={styles.finDetailRow}>
                                    <span>Paid</span>
                                    <strong style={{color:'#86efac'}}>UGX {fmt(mission.amountPaid)}</strong>
                                </div>
                                <div className={`${styles.finDetailRow} ${styles.finDetailTotal}`}>
                                    <span>BALANCE</span>
                                    <strong>UGX {fmt(mission.currentBalance)}</strong>
                                </div>
                            </div>
                        )}
                        <div className={styles.lastNote}>
                            <FiMessageSquare size={11} />
                            <span>"{mission.lastInteractionNote}"</span>
                        </div>
                        
                        {(mission.isBacklog || mission.backlog) && isAdmin && (
                            <StorageFeeInlineControls
                                plot={mission}
                                onUpdated={loadData}
                                toast={toast}
                            />
                        )}

                        <div className={styles.expandedActions}>
                            <button className={styles.folderBtn}
                                onClick={() => navigate(`/folder/${mission.projectId}#financials`)}>
                                <FiChevronRight size={12} /> OPEN FOLDER
                            </button>
                            {isAdmin && (
                                <button className={styles.payBtn}
                                    onClick={() => navigate(`/folder/${mission.projectId}?action=pay#financials`)}>
                                    <FiDollarSign size={12} /> RECORD PAYMENT
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const backlogMissions = filteredMissions.filter(m => m.backlog || m.isBacklog);
    const activeMissions  = filteredMissions.filter(m => !(m.backlog || m.isBacklog));

    if (loading) return (
        <div className={styles.bootScreen} role="status">
            <div className={styles.bootSpinner} aria-hidden="true" />
            <span className={styles.bootLabel}>LOADING RECOVERY DATA...</span>
        </div>
    );

    return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={guardStay} onLeave={guardLeave} context="Recovery Portal" />
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and record payments</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.modeSwitch} role="group" aria-label="View mode">
                        <button className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('ACTION'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'ACTION'}>
                            <FiList aria-hidden="true" /> DUE FOR CALL
                        </button>
                        <button className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('FORECAST'); setExpandedId(null); }}
                            aria-pressed={viewMode === 'FORECAST'}>
                            <FiCalendar aria-hidden="true" /> ALL TARGETS
                        </button>
                    </div>
                </div>
            </header>

            {/* FINANCIAL SUMMARY HUD */}
            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}>
                    <label>ACTIVE TITLES OWED</label>
                    <strong style={{color:'#EE8C3A'}}>UGX {fmt(totalActiveOwed)}</strong>
                    <span>{activeMissions.length} active plot{activeMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.35)'}}>
                    <label style={{color:'#fca5a5'}}>BACKLOG TOTAL OWED</label>
                    <strong style={{color:'#ef4444'}}>UGX {fmt(totalBacklogOwed)}</strong>
                    <span>{backlogMissions.length} backlog plot{backlogMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.2)'}}>
                    <label style={{color:'rgba(252,165,165,0.8)'}}>STORAGE FEES IN BACKLOG</label>
                    <strong style={{color:'rgba(239,68,68,0.85)'}}>UGX {fmt(totalStorageFees)}</strong>
                    <span>across all backlog plots</span>
                </div>
            </div>

            {/* SEARCH + FILTER */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search plot ID, owner, or phone..."
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                    {searchTerm && (
                        <button className={styles.searchClear} onClick={() => setSearchTerm('')} aria-label="Clear">
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
                <div className={styles.filterPills}>
                    {[
                        { key: 'ALL',     label: 'ALL' },
                        { key: 'DUE',     label: 'DUE NOW' },
                        { key: 'ACTIVE',  label: 'ACTIVE TITLES' },
                        { key: 'BACKLOG', label: 'BACKLOG' },
                    ].map(f => (
                        <button key={f.key}
                            className={`${styles.filterPill} ${statusFilter === f.key ? styles.filterPillActive : ''}`}
                            onClick={() => setStatusFilter(f.key)}>
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* PAYMENT HEALTH LEGEND */}
            <div className={styles.legend}>
                {Object.entries(BADGE_COLORS).map(([k, c]) => (
                    <span key={k} className={styles.legendItem}>
                        <span style={{
                            width: 9, height: 9, borderRadius: '50%',
                            background: c, display: 'inline-block', flexShrink: 0,
                            boxShadow: `0 0 4px ${c}`
                        }} />
                        {BADGE_LABELS[k]}
                    </span>
                ))}
            </div>

            <div className={styles.missionGrid}>
                {filteredMissions.length === 0 ? (
                    <div className={styles.emptyGate} role="status">
                        <FiCheckCircle className={styles.emptyIcon} />
                        <h2 className={styles.emptyTitle}>NO TARGETS FOUND</h2>
                    </div>
                ) : (
                    <>
                        {activeMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={styles.sectionHeader}>
                                    <FiActivity aria-hidden="true" /> ACTIVE TITLES ({activeMissions.length})
                                </div>
                                {activeMissions.map(renderCard)}
                            </div>
                        )}
                        {backlogMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={`${styles.sectionHeader} ${styles.sectionHeaderBacklog}`}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG — STORAGE FEES RUNNING ({backlogMissions.length})
                                </div>
                                {backlogMissions.map(renderCard)}
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* DISCARD CONFIRM MODAL */}
            {discardModalOpen && typeof document !== 'undefined' && (
                <div style={{
                    position:'fixed',inset:0,zIndex:99999,
                    background:'rgba(10,20,22,0.88)',backdropFilter:'blur(6px)',
                    display:'flex',alignItems:'center',justifyContent:'center',padding:'clamp(16px,3vw,32px)'
                }} role="dialog" aria-modal="true">
                    <div style={{
                        background:'linear-gradient(160deg,#1c3335 0%,#213E40 100%)',
                        border:'1.5px solid rgba(238,140,58,0.4)',borderRadius:14,
                        maxWidth:460,width:'100%',overflow:'hidden',
                        boxShadow:'0 30px 80px rgba(0,0,0,0.7)'
                    }}>
                        <div style={{display:'flex',alignItems:'center',gap:12,padding:'14px 20px',borderBottom:'1px solid rgba(245,158,11,0.2)',background:'rgba(245,158,11,0.12)'}}>
                            <FiAlertTriangle style={{fontSize:20,color:'#f59e0b',flexShrink:0}} />
                            <span style={{fontFamily:'Space Mono,monospace',fontSize:11,fontWeight:900,textTransform:'uppercase',letterSpacing:1.5,color:'#fcd34d'}}>DISCARD CALL LOG?</span>
                        </div>
                        <p style={{padding:'16px 20px',fontFamily:'DM Sans,sans-serif',fontSize:13,fontWeight:800,lineHeight:1.6,color:'rgba(255,255,255,0.8)',margin:0}}>
                            Your call log has unsaved content. Discard it?
                        </p>
                        <div style={{display:'flex',justifyContent:'flex-end',gap:10,padding:'12px 20px',background:'rgba(0,0,0,0.2)',borderTop:'1px solid rgba(255,255,255,0.06)'}}>
                            <button onClick={handleCancelDiscard} autoFocus style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'rgba(255,255,255,0.06)',border:'1.5px solid rgba(255,255,255,0.2)',color:'rgba(255,255,255,0.7)',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                                KEEP EDITING
                            </button>
                            <button onClick={handleConfirmDiscard} style={{display:'inline-flex',alignItems:'center',gap:6,padding:'8px 16px',background:'#EE8C3A',border:'none',color:'#1a2e30',borderRadius:7,fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,textTransform:'uppercase',cursor:'pointer'}}>
                                DISCARD
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CALL LOG MODAL */}
            <HardwareModal isOpen={callModal.open} onClose={handleCloseCallModal}
                title={`LOG CALL: ${callModal.mission?.plotNumber || ''}`}>
                <div className={styles.historyStream}>
                    <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                    {callHistory.length === 0 ? (
                        <div className={styles.emptyHistory}>No prior logs found.</div>
                    ) : callHistory.slice(0, 5).map(log => (
                        <div key={log.id} className={styles.historyItem}>
                            <div className={styles.historyMeta}>
                                <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                            </div>
                            <p>{log.notes}</p>
                        </div>
                    ))}
                </div>
                <div className={modalStyles.modalField} style={{marginTop:14}}>
                    <label className={modalStyles.modalLabel}>CALL RESULT / NOTE</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="Enter call result or interaction note..."
                        value={logContent} onChange={e => setLogContent(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                        COMMIT &amp; RESET CLOCK
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;
