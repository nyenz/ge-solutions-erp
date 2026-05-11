// PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity
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

const PaymentBadge = ({ badge }) => (
    <span style={{
        display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
        background: BADGE_COLORS[badge] || BADGE_COLORS.RED,
        marginRight: 6, flexShrink: 0,
        boxShadow: `0 0 6px ${BADGE_COLORS[badge] || BADGE_COLORS.RED}`
    }} aria-label={`Payment health: ${badge}`} />
);

const RecoveryPortal = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const isAdmin = user?.role === 'ROLE_ADMIN' || user?.isRoot;

    const [viewMode,      setViewMode]      = useState('ACTION');
    const [missions,      setMissions]      = useState([]);
    const [loading,       setLoading]       = useState(true);
    const [expandedPhone, setExpandedPhone] = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });
    const [callHistory,   setCallHistory]   = useState([]);
    const [logContent,    setLogContent]    = useState('');
    const [committing,    setCommitting]    = useState(false);

    const [payModal,      setPayModal]      = useState({ open: false, plot: null });
    const [payAmount,     setPayAmount]     = useState('');
    const [payNotes,      setPayNotes]      = useState('');
    const [paying,        setPaying]        = useState(false);

    // Dirty state: true if user has typed in call log or payment modal
    const callDirty = callModal.open && logContent.trim() !== '';
    const payDirty  = payModal.open && payAmount !== '';
    const searchDirty = searchTerm !== '';
    const isDirty = callDirty || payDirty || searchDirty;
    const { blocked: guardOpen, proceed: guardLeave, reset: guardStay } = useRouterBlock(isDirty);

    // Wrapped close handlers that check dirty state before closing modal
    const handleCloseCallModal = () => {
        if (callDirty) {
            // Show inline confirm by clearing modal only if user confirmed elsewhere;
            // use browser confirm as fallback since UnsavedChangesModal is for navigation
            if (!window.confirm('Discard unsaved call log?')) return;
        }
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };
    const handleClosePayModal = () => {
        if (payDirty) {
            if (!window.confirm('Discard unsaved payment details?')) return;
        }
        setPayModal({ open: false, plot: null });
        setPayAmount('');
        setPayNotes('');
    };

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = viewMode === 'ACTION'
                ? await recoveryService.getMissionQueue()
                : await recoveryService.getRecoverySchedule();
            setMissions(data);
        } catch {
            toast('DATA STREAM LOST', 'error', 6000);
        } finally {
            setLoading(false);
        }
    }, [viewMode, toast]);

    useEffect(() => { loadData(); }, [loadData]);

    useEffect(() => {
        if (!callModal.mission) return;
        const firstPlot = callModal.mission.plots?.[0];
        if (!firstPlot) return;
        recoveryService.getHistory(firstPlot.projectId)
            .then(setCallHistory)
            .catch(() => setCallHistory([]));
    }, [callModal.mission]);

    const handleLogCall = async () => {
        if (!logContent.trim() || !callModal.mission) return;
        setCommitting(true);
        try {
            for (const plot of callModal.mission.plots) {
                await recoveryService.logRecoveryCall(plot.projectId, logContent);
            }
            await loadData();
            setCallModal({ open: false, mission: null });
            setLogContent('');
            setExpandedPhone(null);
            toast('CALL LOGGED - 14-DAY CLOCK RESET', 'success');
            // isDirty resets automatically since logContent is cleared
        } catch {
            toast('LOG FAILURE', 'error', 8000);
        } finally {
            setCommitting(false);
        }
    };

    const handleRecordPayment = async () => {
        if (!payAmount || Number(payAmount) <= 0) { toast('ENTER A VALID AMOUNT', 'error'); return; }
        setPaying(true);
        try {
            await recoveryService.recordPayment(payModal.plot.projectId, payAmount, payNotes);
            await loadData();
            setPayModal({ open: false, plot: null });
            setPayAmount(''); setPayNotes('');
            toast('PAYMENT RECORDED SUCCESSFULLY', 'success');
        } catch {
            toast('PAYMENT FAILED', 'error', 8000);
        } finally {
            setPaying(false);
        }
    };

    const filteredMissions = useMemo(() => {
        const term = searchTerm.toLowerCase().replace(/\s+/g, '');
        if (!term) return missions;
        return missions.filter(m =>
            m.phoneNumber?.replace(/\s+/g, '').includes(term) ||
            m.ownerName?.toLowerCase().includes(term) ||
            (m.plots || []).some(p => p.plotNumber?.toLowerCase().includes(term))
        );
    }, [missions, searchTerm]);

    const backlogMissions = filteredMissions.filter(m => m.hasBacklogPlots);
    const activeMissions  = filteredMissions.filter(m => !m.hasBacklogPlots);

    const getStatusStyle = (status) => {
        if (status === 'ACTION REQUIRED' || status === 'NEW ASSIGNMENT') return styles.statusRed;
        if (status === 'COOLING DOWN') return styles.statusBlue;
        if (status === 'MONTHLY LIMIT') return styles.statusGrey;
        return styles.statusDefault;
    };

    const renderMissionCard = (mission) => {
        const isExpanded = expandedPhone === mission.phoneNumber;
        const toggle = () => setExpandedPhone(prev => prev === mission.phoneNumber ? null : mission.phoneNumber);

        return (
            <div key={mission.phoneNumber}
                className={`${styles.missionCard} ${mission.isLocked ? styles.cardLocked : ''} ${mission.hasBacklogPlots ? styles.cardBacklog : ''}`}>

                <div className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                    {mission.isLocked && <FiLock aria-hidden="true" />}
                    {mission.missionStatus}
                    {mission.hasBacklogPlots && <span className={styles.backlogTag}>BACKLOG</span>}
                </div>

                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }}}>
                    <div className={styles.identity}>
                        <h3 className={styles.ownerName}>{mission.ownerName}</h3>
                        <span className={styles.phoneNum}>{mission.phoneNumber}</span>
                        <div className={styles.totalDemandRow}>
                            <span className={styles.demandLabel}>TOTAL DEMAND:</span>
                            <span className={styles.demandValue}>UGX {fmt(mission.totalDemand)}</span>
                        </div>
                        {mission.hasBacklogPlots && Number(mission.totalStorageFees) > 0 && (
                            <div className={styles.feesRow}>
                                <FiAlertOctagon aria-hidden="true" size={11} />
                                <span>Incl. accumulated storage fees: UGX {fmt(mission.totalStorageFees)}</span>
                            </div>
                        )}
                    </div>
                    <div className={styles.expandIcon} aria-hidden="true">
                        {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                    </div>
                </div>

                {isExpanded && (
                    <div className={styles.cardBody}>
                        <div className={styles.divider} aria-hidden="true" />

                        <div className={styles.timingRow}>
                            <FiClock aria-hidden="true" size={13} />
                            <span>Last call: <strong>{mission.lastContactDate}</strong></span>
                            <span style={{ margin: '0 8px' }}>|</span>
                            <span>Next eligible: <strong>{mission.nextCallDue}</strong></span>
                            <span style={{ margin: '0 8px' }}>|</span>
                            <span>Calls this month: <strong>{mission.monthlyCallCount}/2</strong></span>
                        </div>

                        <div className={styles.divider} aria-hidden="true" />

                        <div className={styles.plotsList}>
                            <div className={styles.plotsHeader}>PLOTS FOR THIS OWNER</div>
                            {(mission.plots || []).map(plot => (
                                <div key={plot.projectId}
                                    className={`${styles.plotRow} ${plot.isBacklog ? styles.plotRowBacklog : ''}`}>
                                    <div className={styles.plotRowLeft}>
                                        <PaymentBadge badge={plot.paymentHealthBadge} />
                                        <div className={styles.plotInfo}>
                                            <span className={styles.plotNumber}>{plot.plotNumber}</span>
                                            <span className={styles.plotBox}>BOX: {plot.physicalBoxNumber}</span>
                                            {plot.isBacklog ? (
                                                <div className={styles.backlogBreakdown}>
                                                    <span className={styles.backlogPlotTag}>BACKLOG ({plot.storageMonthsCount} months)</span>
                                                    <div className={styles.debtLine}><span>Original debt: <strong>UGX {fmt(plot.originalDebt)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(plot.storageFeesAccumulated)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(plot.totalBacklogOwed)}</strong></span></div>
                                                    <div className={styles.debtLine}><span>Total paid: <strong>UGX {fmt(plot.amountPaid)}</strong></span></div>
                                                </div>
                                            ) : (
                                                <div className={styles.activePlotFinance}>
                                                    <span>Balance: <strong>UGX {fmt(plot.currentBalance)}</strong></span>
                                                    <span style={{opacity:0.6, fontSize:'0.75rem'}}> of UGX {fmt(plot.totalCost)}</span>
                                                </div>
                                            )}
                                            <div className={styles.lastNote}>
                                                <FiMessageSquare aria-hidden="true" size={11} />
                                                <span>"{plot.lastInteractionNote}"</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className={styles.plotRowActions}>
                                        <button className={styles.folderBtn}
                                            onClick={() => navigate(`/folder/${plot.projectId}`)}>
                                            <FiChevronRight aria-hidden="true" /> BINDER
                                        </button>
                                        {isAdmin && (
                                            <button className={styles.payBtn}
                                                onClick={() => { setPayModal({ open: true, plot }); setPayAmount(''); setPayNotes(''); }}>
                                                <FiDollarSign aria-hidden="true" /> PAY
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className={styles.divider} aria-hidden="true" />

                        <div className={styles.cardActions}>
                            <button className={styles.logCallBtn}
                                onClick={() => setCallModal({ open: true, mission })}
                                disabled={mission.isLocked}>
                                <FiPhoneCall aria-hidden="true" />
                                {mission.isLocked ? 'LOCKED' : 'LOG CALL'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    if (loading) return (
        <div className={styles.bootScreen} role="status">
            <div className={styles.bootSpinner} aria-hidden="true" />
            <span className={styles.bootLabel}>BOOTING RECOVERY TERMINAL...</span>
        </div>
    );

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.pageTitle}>Call Recovery</h1>
                    <p className={styles.pageSubtitle}>Log client calls and track outstanding balances</p>
                </div>
                <div className={styles.headerRight}>
                    <div className={styles.hudStats}>
                        <div className={styles.statBox}>
                            <label>TARGETS</label>
                            <strong style={{color: filteredMissions.length > 0 ? '#EE8C3A' : '#fff'}}>{filteredMissions.length}</strong>
                        </div>
                        <div className={styles.statBox}>
                            <label>BACKLOG</label>
                            <strong style={{color: backlogMissions.length > 0 ? '#ef4444' : '#fff'}}>{backlogMissions.length}</strong>
                        </div>
                    </div>
                    <div className={styles.modeSwitch} role="group" aria-label="View mode">
                        <button className={viewMode === 'ACTION' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('ACTION'); setExpandedPhone(null); }}
                            aria-pressed={viewMode === 'ACTION'}>
                            <FiList aria-hidden="true" /> ACTION QUEUE
                        </button>
                        <button className={viewMode === 'FORECAST' ? styles.modeActive : styles.modeInactive}
                            onClick={() => { setViewMode('FORECAST'); setExpandedPhone(null); }}
                            aria-pressed={viewMode === 'FORECAST'}>
                            <FiCalendar aria-hidden="true" /> FULL SCHEDULE
                        </button>
                    </div>
                </div>
            </header>

            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search owner, phone, or plot ID..."
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`} value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)} />
                    {!(searchTerm || isSearchFocused) && <FiSearch className={styles.searchIcon} aria-hidden="true" />}
                    {searchTerm && (
                        <button className={styles.searchClear} onClick={() => setSearchTerm('')}>
                            <FiX aria-hidden="true" />
                        </button>
                    )}
                </div>
            </div>

            <div className={styles.missionGrid}>
                {filteredMissions.length === 0 ? (
                    <div className={styles.emptyGate} role="status">
                        <FiCheckCircle className={styles.emptyIcon} aria-hidden="true" />
                        <h2 className={styles.emptyTitle}>NO TARGETS FOUND</h2>
                    </div>
                ) : (
                    <>
                        {activeMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={styles.sectionHeader}>
                                    <FiActivity aria-hidden="true" /> ACTIVE ({activeMissions.length})
                                </div>
                                {activeMissions.map(renderMissionCard)}
                            </div>
                        )}
                        {backlogMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={`${styles.sectionHeader} ${styles.sectionHeaderBacklog}`}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG - STORAGE FEES ACTIVE ({backlogMissions.length})
                                </div>
                                {backlogMissions.map(renderMissionCard)}
                            </div>
                        )}
                    </>
                )}
            </div>

            <HardwareModal isOpen={callModal.open}
                onClose={handleCloseCallModal}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>
                <div className={styles.historyStream}>
                    <div className={styles.historyTitle}>PREVIOUS INTERACTIONS</div>
                    {callHistory.length === 0 ? (
                        <div className={styles.emptyHistory}>No prior logs found.</div>
                    ) : callHistory.map(log => (
                        <div key={log.id} className={styles.historyItem}>
                            <div className={styles.historyMeta}>
                                <span><FiUser aria-hidden="true" /> {log.recordedBy}</span>
                                <small>{new Date(log.timestamp).toLocaleDateString()}</small>
                            </div>
                            <p>{log.notes}</p>
                        </div>
                    ))}
                </div>
                <div className={modalStyles.modalField} style={{marginTop: 14}}>
                    <label className={modalStyles.modalLabel}>CALL RESULT / NOTE</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="Enter call result or interaction note..."
                        value={logContent} onChange={e => setLogContent(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton loading={committing} onClick={handleLogCall} icon={FiSave}>
                        Commit &amp; Reset
                    </HardwareButton>
                </div>
            </HardwareModal>

            <HardwareModal isOpen={payModal.open}
                onClose={handleClosePayModal}
                title={`RECORD PAYMENT: ${payModal.plot?.plotNumber || ''}`}>
                {payModal.plot?.isBacklog ? (
                    <div className={`${modalStyles.modalInfoBox} ${modalStyles.modalInfoBoxDanger}`}>
                        <div style={{display:'flex',gap:10,alignItems:'flex-start'}}>
                            <FiAlertOctagon aria-hidden="true" style={{color:'#ef4444',flexShrink:0,marginTop:2}} />
                            <div>
                                <div>Original debt: <strong>UGX {fmt(payModal.plot?.originalDebt)}</strong></div>
                                <div>Storage fees: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.storageFeesAccumulated)}</strong></div>
                                <div>Total owed: <strong style={{color:'#ef4444'}}>UGX {fmt(payModal.plot?.totalBacklogOwed)}</strong></div>
                                <div style={{marginTop:6,opacity:0.65,fontSize:'0.78rem'}}>Storage fees continue until full balance is cleared.</div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className={modalStyles.modalInfoBox}>
                        Current balance: <strong>UGX {fmt(payModal.plot?.currentBalance)}</strong>
                    </div>
                )}
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>AMOUNT RECEIVED (UGX)</label>
                    <input type="number" className={modalStyles.modalInput}
                        placeholder="Enter amount..." value={payAmount}
                        onChange={e => setPayAmount(e.target.value)} />
                </div>
                <div className={modalStyles.modalField}>
                    <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                    <textarea className={modalStyles.modalTextarea}
                        placeholder="e.g. Paid via MTN Mobile Money..."
                        value={payNotes} onChange={e => setPayNotes(e.target.value)} />
                </div>
                <div className={modalStyles.modalFooter}>
                    <HardwareButton loading={paying} onClick={handleRecordPayment} icon={FiDollarSign}>
                        CONFIRM PAYMENT
                    </HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default RecoveryPortal;