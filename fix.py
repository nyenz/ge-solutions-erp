import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    write(path, content.replace(old, new, 1))
    print(f"OK patch ({label or path})")

# ================================================================
# FULL REWRITE: RecoveryPortal.jsx
# - New payment modal that clearly separates TITLE vs STORAGE FEE payments
# - Monthly storage fee recording is its own distinct action per plot
# - Filter bar now has tabs: ACTION QUEUE / FULL SCHEDULE / BACKLOG FOCUS
# - Each mission card shows a clear financial summary panel
# - Section grouping: Active vs Backlog with different visual treatment
# ================================================================

PORTAL_CONTENT = r'''// PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
    FiPhoneCall, FiClock, FiSearch,
    FiCheckCircle, FiChevronRight, FiMessageSquare, FiSave,
    FiList, FiCalendar, FiLock, FiUser, FiChevronDown, FiChevronUp,
    FiX, FiCheckSquare, FiAlertCircle, FiAlertTriangle, FiInfo,
    FiDollarSign, FiAlertOctagon, FiActivity, FiHome, FiTrendingDown,
    FiArchive, FiZap
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

// ── PAYMENT TYPE MODAL ──────────────────────────────────────────
// Handles both TITLE PAYMENT and STORAGE FEE payment with clear distinction
const PaymentModal = ({ open, plot, onClose, onPay, paying }) => {
    const [payType, setPayType]   = useState('TITLE');   // 'TITLE' | 'STORAGE'
    const [amount,  setAmount]    = useState('');
    const [notes,   setNotes]     = useState('');

    useEffect(() => {
        if (open) { setPayType('TITLE'); setAmount(''); setNotes(''); }
    }, [open]);

    if (!plot) return null;

    const isBacklog      = plot.isBacklog;
    const titleBalance   = isBacklog
        ? Number(plot.originalDebt || 0) - Number(plot.amountPaid || 0)
        : Number(plot.currentBalance || 0);
    const storageOwed    = Number(plot.storageFeesAccumulated || 0);
    const totalOwed      = Number(plot.totalBacklogOwed || 0);

    const handleSubmit = () => {
        if (!amount || Number(amount) <= 0) return;
        onPay(plot, amount, notes, payType);
    };

    return (
        <HardwareModal isOpen={open} onClose={onClose} title={`RECORD PAYMENT — ${plot.plotNumber}`}>
            {/* FINANCIAL BREAKDOWN HEADER */}
            <div className={styles.payBreakdownBox}>
                {isBacklog ? (
                    <>
                        <div className={styles.payBreakdownTitle}>
                            <FiAlertOctagon size={11} /> BACKLOG BALANCE BREAKDOWN
                        </div>
                        <div className={styles.payBreakdownGrid}>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>ORIGINAL TITLE DEBT</span>
                                <span className={styles.pbVal}>UGX {fmt(plot.originalDebt)}</span>
                            </div>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel} style={{color:'#fca5a5'}}>STORAGE FEES (MONTHLY)</span>
                                <span className={styles.pbVal} style={{color:'#ef4444'}}>+ UGX {fmt(storageOwed)}</span>
                            </div>
                            <div className={styles.pbItem}>
                                <span className={styles.pbLabel}>PAYMENTS MADE</span>
                                <span className={styles.pbVal} style={{color:'#86efac'}}>- UGX {fmt(plot.amountPaid)}</span>
                            </div>
                            <div className={styles.pbItemTotal}>
                                <span className={styles.pbLabel}>TOTAL NOW OWED</span>
                                <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, totalOwed))}</span>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className={styles.payBreakdownGrid}>
                        <div className={styles.pbItem}>
                            <span className={styles.pbLabel}>TITLE COST</span>
                            <span className={styles.pbVal}>UGX {fmt(plot.totalCost)}</span>
                        </div>
                        <div className={styles.pbItem}>
                            <span className={styles.pbLabel}>PAID SO FAR</span>
                            <span className={styles.pbVal} style={{color:'#86efac'}}>UGX {fmt(plot.amountPaid)}</span>
                        </div>
                        <div className={styles.pbItemTotal}>
                            <span className={styles.pbLabel}>REMAINING BALANCE</span>
                            <span className={styles.pbValTotal}>UGX {fmt(Math.max(0, titleBalance))}</span>
                        </div>
                    </div>
                )}
            </div>

            {/* PAYMENT TYPE SELECTOR — only show for backlog */}
            {isBacklog && (
                <div className={styles.payTypeRow}>
                    <div className={styles.payTypeLabel}>WHAT IS THIS PAYMENT FOR?</div>
                    <div className={styles.payTypeButtons}>
                        <button
                            type="button"
                            className={`${styles.payTypeBtn} ${payType === 'TITLE' ? styles.payTypeBtnActive : ''}`}
                            onClick={() => setPayType('TITLE')}>
                            <FiHome size={12} />
                            <div>
                                <div className={styles.payTypeBtnName}>TITLE PAYMENT</div>
                                <div className={styles.payTypeBtnSub}>Reduces the original title debt</div>
                            </div>
                        </button>
                        <button
                            type="button"
                            className={`${styles.payTypeBtn} ${styles.payTypeBtnStorage} ${payType === 'STORAGE' ? styles.payTypeBtnStorageActive : ''}`}
                            onClick={() => setPayType('STORAGE')}>
                            <FiArchive size={12} />
                            <div>
                                <div className={styles.payTypeBtnName}>STORAGE FEE</div>
                                <div className={styles.payTypeBtnSub}>Covers monthly storage charges</div>
                            </div>
                        </button>
                    </div>
                    {payType === 'STORAGE' && (
                        <div className={styles.payTypeHint}>
                            <FiInfo size={11} />
                            Storage fees: UGX {fmt(storageOwed)} accumulated over {plot.storageMonthsCount} month{plot.storageMonthsCount !== 1 ? 's' : ''}. Recording here goes towards clearing the storage fee balance.
                        </div>
                    )}
                </div>
            )}

            <div className={modalStyles.modalField}>
                <label className={modalStyles.modalLabel}>
                    AMOUNT RECEIVED (UGX)
                </label>
                <input
                    type="number"
                    className={modalStyles.modalInput}
                    placeholder={isBacklog && payType === 'STORAGE'
                        ? `e.g. 50000 (1 month)`
                        : `e.g. ${fmt(Math.max(0, isBacklog ? totalOwed : titleBalance))}`}
                    value={amount}
                    onChange={e => setAmount(e.target.value)}
                    autoFocus
                />
            </div>
            <div className={modalStyles.modalField}>
                <label className={modalStyles.modalLabel}>NOTES (optional)</label>
                <textarea
                    className={modalStyles.modalTextarea}
                    placeholder="e.g. MTN Mobile Money, cash, cheque..."
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                />
            </div>
            <div className={modalStyles.modalFooter}>
                <button
                    type="button"
                    className={modalStyles.modalBtnSecondary}
                    onClick={onClose}>
                    <FiX aria-hidden="true" /> CANCEL
                </button>
                <HardwareButton loading={paying} onClick={handleSubmit} icon={FiDollarSign}>
                    CONFIRM {payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'}
                </HardwareButton>
            </div>
        </HardwareModal>
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
    const [expandedPhone, setExpandedPhone] = useState(null);
    const [searchTerm,    setSearchTerm]    = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [statusFilter,  setStatusFilter]  = useState('ALL');

    const [callModal,     setCallModal]     = useState({ open: false, mission: null });
    const [callHistory,   setCallHistory]   = useState([]);
    const [logContent,    setLogContent]    = useState('');
    const [committing,    setCommitting]    = useState(false);

    const [payModal,      setPayModal]      = useState({ open: false, plot: null });
    const [paying,        setPaying]        = useState(false);

    const callDirty = callModal.open && logContent.trim() !== '';
    const isDirty   = callDirty;
    const { blocked: guardOpen, proceed: guardLeave, reset: guardStay } = useRouterBlock(isDirty);

    const handleCloseCallModal = () => {
        if (callDirty && !window.confirm('Discard unsaved call log?')) return;
        setCallModal({ open: false, mission: null });
        setLogContent('');
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
            toast('CALL LOGGED — 14-DAY CLOCK RESET', 'success');
        } catch {
            toast('LOG FAILURE', 'error', 8000);
        } finally {
            setCommitting(false);
        }
    };

    const handleRecordPayment = async (plot, amount, notes, payType) => {
        setPaying(true);
        try {
            // Always use recordPayment — backend determines type from plot status
            // Notes field carries the payType context for the audit trail
            const fullNotes = payType === 'STORAGE'
                ? `[STORAGE FEE PAYMENT]${notes ? ' ' + notes : ''}`
                : notes;
            await recoveryService.recordPayment(plot.projectId, amount, fullNotes);
            await loadData();
            setPayModal({ open: false, plot: null });
            toast(`${payType === 'STORAGE' ? 'STORAGE FEE' : 'PAYMENT'} RECORDED`, 'success');
        } catch {
            toast('PAYMENT FAILED', 'error', 8000);
        } finally {
            setPaying(false);
        }
    };

    const filteredMissions = useMemo(() => {
        let list = missions;

        // Search filter
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase().replace(/\s+/g, '');
            list = list.filter(m =>
                m.phoneNumber?.replace(/\s+/g, '').includes(term) ||
                m.ownerName?.toLowerCase().includes(term) ||
                (m.plots || []).some(p => p.plotNumber?.toLowerCase().includes(term))
            );
        }

        // Status filter
        if (statusFilter === 'BACKLOG') list = list.filter(m => m.hasBacklogPlots);
        if (statusFilter === 'ACTIVE')  list = list.filter(m => !m.hasBacklogPlots);
        if (statusFilter === 'DUE')     list = list.filter(m => !m.isLocked);

        return list;
    }, [missions, searchTerm, statusFilter]);

    const getStatusStyle = (status) => {
        if (status === 'ACTION REQUIRED' || status === 'NEW ASSIGNMENT') return styles.statusRed;
        if (status === 'COOLING DOWN')  return styles.statusBlue;
        if (status === 'MONTHLY LIMIT') return styles.statusGrey;
        return styles.statusDefault;
    };

    const totalBacklogOwed  = useMemo(() => filteredMissions.filter(m => m.hasBacklogPlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0), [filteredMissions]);
    const totalActiveOwed   = useMemo(() => filteredMissions.filter(m => !m.hasBacklogPlots).reduce((s, m) => s + Number(m.totalDemand || 0), 0), [filteredMissions]);
    const totalStorageFees  = useMemo(() => filteredMissions.reduce((s, m) => s + Number(m.totalStorageFees || 0), 0), [filteredMissions]);

    const renderMissionCard = (mission) => {
        const isExpanded = expandedPhone === mission.phoneNumber;
        const toggle = () => setExpandedPhone(prev => prev === mission.phoneNumber ? null : mission.phoneNumber);
        const backlogPlots = (mission.plots || []).filter(p => p.isBacklog);
        const activePlots  = (mission.plots || []).filter(p => !p.isBacklog);

        return (
            <div key={mission.phoneNumber}
                className={`${styles.missionCard} ${mission.isLocked ? styles.cardLocked : ''} ${mission.hasBacklogPlots ? styles.cardBacklog : ''}`}>

                <div className={`${styles.statusBadge} ${getStatusStyle(mission.missionStatus)}`}>
                    {mission.isLocked && <FiLock aria-hidden="true" size={10} />}
                    {mission.missionStatus}
                </div>

                <div className={styles.cardHeader} onClick={toggle} role="button" tabIndex={0}
                    aria-expanded={isExpanded}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }}}>

                    <div className={styles.identity}>
                        <div className={styles.ownerRow}>
                            <h3 className={styles.ownerName}>{mission.ownerName}</h3>
                            {mission.hasBacklogPlots && (
                                <span className={styles.backlogOwnerTag}>
                                    <FiAlertOctagon size={9} /> BACKLOG
                                </span>
                            )}
                        </div>
                        <span className={styles.phoneNum}>{mission.phoneNumber}</span>

                        {/* COMPACT FINANCIAL SUMMARY */}
                        <div className={styles.cardFinSummary}>
                            {activePlots.length > 0 && (
                                <div className={styles.finPill} data-type="active">
                                    <FiHome size={10} />
                                    <span className={styles.finPillLabel}>{activePlots.length} TITLE{activePlots.length > 1 ? 'S' : ''}</span>
                                    <span className={styles.finPillVal}>UGX {fmt(mission.totalDemand - (mission.totalStorageFees || 0) - (mission.totalOriginalDebt || 0) + (activePlots.reduce((s,p) => s + Number(p.currentBalance || 0), 0)))}</span>
                                </div>
                            )}
                            {backlogPlots.length > 0 && (
                                <>
                                    <div className={styles.finPill} data-type="backlog">
                                        <FiAlertOctagon size={10} />
                                        <span className={styles.finPillLabel}>BACKLOG DEBT</span>
                                        <span className={styles.finPillVal}>UGX {fmt(backlogPlots.reduce((s,p) => s + Number(p.originalDebt || 0), 0))}</span>
                                    </div>
                                    {Number(mission.totalStorageFees) > 0 && (
                                        <div className={styles.finPill} data-type="storage">
                                            <FiTrendingDown size={10} />
                                            <span className={styles.finPillLabel}>STORAGE FEES</span>
                                            <span className={styles.finPillVal}>UGX {fmt(mission.totalStorageFees)}</span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className={styles.totalDemandRow}>
                            <span className={styles.demandLabel}>TOTAL OWED:</span>
                            <span className={`${styles.demandValue} ${mission.hasBacklogPlots ? styles.demandValueRed : ''}`}>
                                UGX {fmt(mission.totalDemand)}
                            </span>
                        </div>
                    </div>

                    <div className={styles.expandIcon} aria-hidden="true">
                        {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                    </div>
                </div>

                {isExpanded && (
                    <div className={styles.cardBody}>
                        <div className={styles.divider} />

                        <div className={styles.timingRow}>
                            <FiClock size={12} aria-hidden="true" />
                            <span>Last call: <strong>{mission.lastContactDate}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Next: <strong>{mission.nextCallDue}</strong></span>
                            <span className={styles.timingSep} />
                            <span>Calls this month: <strong>{mission.monthlyCallCount}/2</strong></span>
                        </div>

                        <div className={styles.divider} />

                        {/* ACTIVE PLOTS */}
                        {activePlots.length > 0 && (
                            <div className={styles.plotsSection}>
                                <div className={styles.plotsSectionHeader}>
                                    <FiHome size={11} /> TITLE PLOTS ({activePlots.length})
                                </div>
                                {activePlots.map(plot => (
                                    <div key={plot.projectId} className={styles.plotCard}>
                                        <div className={styles.plotCardTop}>
                                            <div className={styles.plotCardLeft}>
                                                <PaymentBadge badge={plot.paymentHealthBadge} />
                                                <div>
                                                    <div className={styles.plotNum}>{plot.plotNumber}</div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber}</div>
                                                </div>
                                            </div>
                                            <div className={styles.plotCardRight}>
                                                <button className={styles.folderBtn} onClick={() => navigate(`/folder/${plot.projectId}`)}>
                                                    <FiChevronRight size={12} /> OPEN
                                                </button>
                                                {isAdmin && (
                                                    <button className={styles.payBtnTitle}
                                                        onClick={() => setPayModal({ open: true, plot })}>
                                                        <FiDollarSign size={12} /> PAY
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        <div className={styles.plotFinRow}>
                                            <div className={styles.plotFinItem}>
                                                <span>Total cost</span>
                                                <strong>UGX {fmt(plot.totalCost)}</strong>
                                            </div>
                                            <div className={styles.plotFinItem}>
                                                <span>Paid</span>
                                                <strong style={{color:'#86efac'}}>UGX {fmt(plot.amountPaid)}</strong>
                                            </div>
                                            <div className={styles.plotFinItem}>
                                                <span>Balance</span>
                                                <strong style={{color:'#fca5a5'}}>UGX {fmt(plot.currentBalance)}</strong>
                                            </div>
                                        </div>
                                        <div className={styles.plotProgressWrap}>
                                            <div className={styles.plotProgress}>
                                                <div className={styles.plotProgressFill}
                                                    style={{width: plot.totalCost > 0 ? `${Math.min(100, (1 - plot.currentBalance / plot.totalCost) * 100)}%` : '0%'}} />
                                            </div>
                                            <span className={styles.plotProgressPct}>
                                                {plot.totalCost > 0 ? Math.round((1 - plot.currentBalance / plot.totalCost) * 100) : 0}%
                                            </span>
                                        </div>
                                        <div className={styles.lastNote}>
                                            <FiMessageSquare size={11} /><span>"{plot.lastInteractionNote}"</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* BACKLOG PLOTS */}
                        {backlogPlots.length > 0 && (
                            <div className={styles.plotsSection}>
                                <div className={`${styles.plotsSectionHeader} ${styles.plotsSectionHeaderBacklog}`}>
                                    <FiAlertOctagon size={11} /> BACKLOG PLOTS — STORAGE FEES ACTIVE ({backlogPlots.length})
                                </div>
                                {backlogPlots.map(plot => (
                                    <div key={plot.projectId} className={`${styles.plotCard} ${styles.plotCardBacklog}`}>
                                        <div className={styles.plotCardTop}>
                                            <div className={styles.plotCardLeft}>
                                                <PaymentBadge badge={plot.paymentHealthBadge} />
                                                <div>
                                                    <div className={styles.plotNum}>{plot.plotNumber}</div>
                                                    <div className={styles.plotBoxNum}>Box: {plot.physicalBoxNumber} · {plot.storageMonthsCount}mo in backlog</div>
                                                </div>
                                            </div>
                                            <div className={styles.plotCardRight}>
                                                <button className={styles.folderBtn} onClick={() => navigate(`/folder/${plot.projectId}`)}>
                                                    <FiChevronRight size={12} /> OPEN
                                                </button>
                                                {isAdmin && (
                                                    <button className={`${styles.payBtnTitle} ${styles.payBtnBacklog}`}
                                                        onClick={() => setPayModal({ open: true, plot })}>
                                                        <FiZap size={12} /> PAY
                                                    </button>
                                                )}
                                            </div>
                                        </div>

                                        {/* BACKLOG 3-ROW BREAKDOWN */}
                                        <div className={styles.backlogFinBreakdown}>
                                            <div className={styles.bfbRow}>
                                                <div className={styles.bfbItem}>
                                                    <span className={styles.bfbLabel}>ORIGINAL TITLE DEBT</span>
                                                    <span className={styles.bfbVal}>UGX {fmt(plot.originalDebt)}</span>
                                                </div>
                                                <div className={styles.bfbItem} style={{textAlign:'right'}}>
                                                    <span className={styles.bfbLabel} style={{color:'#fca5a5'}}>STORAGE FEES ADDED</span>
                                                    <span className={styles.bfbVal} style={{color:'#ef4444'}}>+ UGX {fmt(plot.storageFeesAccumulated)}</span>
                                                </div>
                                            </div>
                                            <div className={styles.bfbDivider} />
                                            <div className={styles.bfbRow}>
                                                <div className={styles.bfbItem}>
                                                    <span className={styles.bfbLabel}>TOTAL PAID</span>
                                                    <span className={styles.bfbVal} style={{color:'#86efac'}}>- UGX {fmt(plot.amountPaid)}</span>
                                                </div>
                                                <div className={styles.bfbItem} style={{textAlign:'right'}}>
                                                    <span className={styles.bfbLabel} style={{color:'#fca5a5', fontWeight:900}}>NOW OWED</span>
                                                    <span className={styles.bfbValTotal}>UGX {fmt(Math.max(0, plot.totalBacklogOwed))}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={styles.lastNote}>
                                            <FiMessageSquare size={11} /><span>"{plot.lastInteractionNote}"</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className={styles.divider} />

                        <div className={styles.cardActions}>
                            <button className={styles.logCallBtn}
                                onClick={() => setCallModal({ open: true, mission })}
                                disabled={mission.isLocked}>
                                <FiPhoneCall aria-hidden="true" />
                                {mission.isLocked ? 'CALL LOCKED' : 'LOG CALL'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const backlogMissions = filteredMissions.filter(m => m.hasBacklogPlots);
    const activeMissions  = filteredMissions.filter(m => !m.hasBacklogPlots);

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

            {/* FINANCIAL SUMMARY HUD */}
            <div className={styles.finHUD}>
                <div className={styles.finHUDCard}>
                    <label>ACTIVE TITLES OWED</label>
                    <strong style={{color:'#EE8C3A'}}>UGX {fmt(totalActiveOwed)}</strong>
                    <span>{activeMissions.length} owner{activeMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.35)'}}>
                    <label style={{color:'#fca5a5'}}>BACKLOG TOTAL OWED</label>
                    <strong style={{color:'#ef4444'}}>UGX {fmt(totalBacklogOwed)}</strong>
                    <span>{backlogMissions.length} owner{backlogMissions.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={styles.finHUDCard} style={{borderColor:'rgba(239,68,68,0.2)'}}>
                    <label style={{color:'rgba(252,165,165,0.8)'}}>STORAGE FEES IN BACKLOG</label>
                    <strong style={{color:'rgba(239,68,68,0.85)'}}>UGX {fmt(totalStorageFees)}</strong>
                    <span>across all backlog plots</span>
                </div>
            </div>

            {/* SEARCH + FILTER BAR */}
            <div className={styles.filterBar}>
                <div className={styles.searchInner}>
                    <input type="search" placeholder="Search owner, phone, or plot..."
                        className={`${styles.searchInput} ${(searchTerm || isSearchFocused) ? styles.searchInputActive : ''}`}
                        value={searchTerm}
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
                                    <FiActivity aria-hidden="true" /> ACTIVE TITLE OWNERS ({activeMissions.length})
                                </div>
                                {activeMissions.map(renderMissionCard)}
                            </div>
                        )}
                        {backlogMissions.length > 0 && (
                            <div className={styles.sectionGroup}>
                                <div className={`${styles.sectionHeader} ${styles.sectionHeaderBacklog}`}>
                                    <FiAlertOctagon aria-hidden="true" /> BACKLOG — STORAGE FEES RUNNING ({backlogMissions.length})
                                </div>
                                {backlogMissions.map(renderMissionCard)}
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* CALL LOG MODAL */}
            <HardwareModal isOpen={callModal.open} onClose={handleCloseCallModal}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>
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

            {/* PAYMENT MODAL */}
            <PaymentModal
                open={payModal.open}
                plot={payModal.plot}
                onClose={() => setPayModal({ open: false, plot: null })}
                onPay={handleRecordPayment}
                paying={paying}
            />
        </div>
    );
};

export default RecoveryPortal;
'''

write('erp-frontend/src/pages/Recovery/RecoveryPortal.jsx', PORTAL_CONTENT)

# ================================================================
# FULL REWRITE: RecoveryPortal.module.css
# ================================================================

CSS_CONTENT = '''/* PATH: erp-frontend/src/pages/Recovery/RecoveryPortal.module.css */

.container {
    --orange:        #EE8C3A;
    --orange-dim:    rgba(238,140,58,0.15);
    --orange-border: rgba(238,140,58,0.3);
    --navy:          #1a2e30;
    --navy-mid:      #213E40;
    --panel-bg:      linear-gradient(160deg,#1c3335 0%,#213E40 100%);
    --red:           #ef4444;
    --emerald:       #10b981;
    --cyan:          #06b6d4;
    --gap-xl:   clamp(12px,1.8vw,20px);
    --gap-lg:   clamp(8px,1.2vw,14px);
    --gap-md:   clamp(6px,0.9vw,11px);
    --pad-card: clamp(12px,1.5vw,18px);
    --radius:   10px;
    --radius-sm:7px;
    --fs-label: clamp(8px,0.82vw,10px);
    --fs-meta:  clamp(9px,0.9vw,11px);
    --fs-value: clamp(11px,1.1vw,13px);
    --fs-phone: clamp(12px,1.2vw,14px);
    --fs-owner: clamp(14px,1.5vw,17px);
    --fs-demand:clamp(12px,1.4vw,16px);
    --fs-badge: clamp(7px,0.75vw,9px);
    --fs-btn:   clamp(9px,0.9vw,11px);
    --fs-note:  clamp(10px,1vw,12px);
    --fs-h1:    clamp(18px,2.5vw,24px);
    max-width: 1600px;
    margin: 0 auto;
    padding: clamp(8px,1.5vw,16px) clamp(8px,1.5vw,16px) clamp(24px,4vw,48px);
    font-family: 'DM Sans',sans-serif;
    color: #fff;
}

/* ── TOAST ── */
.toastContainer { position:fixed; bottom:20px; right:20px; z-index:99999; display:flex; flex-direction:column-reverse; gap:8px; max-width:380px; pointer-events:none; }
.toast { display:flex; align-items:flex-start; gap:10px; padding:12px 14px; border-radius:8px; box-shadow:0 6px 22px rgba(0,0,0,0.5); pointer-events:all; animation:toastIn 0.3s cubic-bezier(0.18,0.89,0.32,1.28) both; }
@keyframes toastIn { from{opacity:0;transform:translateX(40px)} to{opacity:1;transform:translateX(0)} }
.toast_success { background:rgba(16,185,129,0.95); border-left:4px solid #059669; color:#fff; }
.toast_error   { background:rgba(239,68,68,0.95);  border-left:4px solid #b91c1c; color:#fff; }
.toast_warn    { background:rgba(245,158,11,0.95); border-left:4px solid #b45309; color:#fff; }
.toast_info    { background:rgba(6,182,212,0.95);  border-left:4px solid #0369a1; color:#fff; }
.toastIcon  { font-size:15px; flex-shrink:0; margin-top:1px; }
.toastMsg   { font-family:'Space Mono',monospace; font-size:10px; font-weight:700; line-height:1.4; flex:1; min-width:0; word-break:break-word; }
.toastClose { background:transparent; border:none; color:inherit; opacity:0.6; cursor:pointer; padding:2px; font-size:13px; flex-shrink:0; }
.toastClose:hover { opacity:1; }

/* ── BOOT ── */
.bootScreen  { height:60vh; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; }
.bootSpinner { width:36px; height:36px; border:3px solid rgba(238,140,58,0.15); border-top-color:#EE8C3A; border-radius:50%; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.bootLabel   { font-family:'Cinzel',serif; font-size:11px; font-weight:700; letter-spacing:4px; color:#EE8C3A; text-transform:uppercase; }

/* ── HEADER ── */
.pageHeader {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    gap:clamp(10px,1.4vw,16px); margin-bottom:clamp(10px,1.5vw,16px);
    border-left:clamp(3px,0.4vw,5px) solid #EE8C3A;
    padding:clamp(10px,1.4vw,16px) clamp(16px,2.2vw,28px);
    background:rgba(255,255,255,0.62); border-radius:0 var(--radius) var(--radius) 0;
    backdrop-filter:blur(15px); box-shadow:0 4px 15px rgba(0,0,0,0.07);
}
.headerLeft { display:flex; flex-direction:column; gap:3px; min-width:0; flex:1; }
.headerRight { display:flex; align-items:center; gap:clamp(8px,1.2vw,14px); flex-shrink:0; flex-wrap:wrap; }
.pageTitle { font-family:'Cinzel',serif; color:#1a2e30; font-size:var(--fs-h1); font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin:0; line-height:1.1; }
.pageSubtitle { font-family:'DM Sans',sans-serif; color:#64748b; font-size:var(--fs-badge); font-weight:900; text-transform:uppercase; letter-spacing:1px; margin:0; }

/* ── MODE SWITCH ── */
.modeSwitch { display:flex; background:var(--navy); padding:4px; border-radius:var(--radius-sm); border:1px solid var(--orange-border); gap:3px; flex-wrap:nowrap; flex-shrink:0; }
.modeActive   { background:var(--orange); color:var(--navy); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; }
.modeInactive { background:transparent; color:rgba(255,255,255,0.75); border:none; padding:clamp(6px,0.9vw,8px) clamp(10px,1.3vw,16px); border-radius:5px; font-family:'DM Sans',sans-serif; font-weight:900; font-size:clamp(9px,1vw,11px); letter-spacing:1px; text-transform:uppercase; cursor:pointer; display:flex; align-items:center; gap:6px; white-space:nowrap; transition:background 0.2s,color 0.2s; }
.modeInactive:hover { background:rgba(255,255,255,0.1); color:#fff; }

/* ── FINANCIAL HUD ── */
.finHUD {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:var(--gap-md);
    margin-bottom:var(--gap-lg);
}
.finHUDCard {
    background:var(--panel-bg);
    border:1.5px solid var(--orange-border);
    border-radius:var(--radius);
    padding:clamp(10px,1.3vw,14px) clamp(12px,1.5vw,16px);
    display:flex; flex-direction:column; gap:3px;
}
.finHUDCard label { font-family:'DM Sans',sans-serif; font-size:var(--fs-badge); font-weight:900; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1px; }
.finHUDCard strong { font-family:'Space Mono',monospace; font-size:clamp(13px,1.6vw,18px); font-weight:700; word-break:break-all; }
.finHUDCard span { font-size:var(--fs-badge); color:rgba(255,255,255,0.35); }

/* ── FILTER BAR ── */
.filterBar {
    display:flex; flex-direction:column; gap:var(--gap-md);
    margin-bottom:var(--gap-xl);
}

.searchInner {
    position:relative; display:flex; align-items:center;
    background:#fff; border:1.5px solid #c8d6d7;
    border-radius:var(--radius-sm);
    width:100%; max-width:clamp(300px,42vw,500px);
    height:clamp(36px,4vw,42px);
    transition:border-color 0.2s;
}
.searchInner:focus-within { border-color:var(--orange); box-shadow:0 0 0 3px rgba(238,140,58,0.15); }
.searchIcon { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--orange); font-size:16px; pointer-events:none; }
.searchInput {
    width:100%; border:none; outline:none; background:transparent;
    color:var(--navy); padding-right:34px !important; padding-left:42px !important;
    font-family:'DM Sans',sans-serif; font-weight:800; font-size:clamp(11px,1.1vw,13px);
    height:100%; transition:padding 0.2s ease;
}
.searchInputActive { padding-left:14px !important; }
.searchInput::placeholder { font-weight:500; color:rgba(26,46,48,0.35); }
.searchClear { position:absolute; right:8px; top:50%; transform:translateY(-50%); background:transparent; border:none; cursor:pointer; color:rgba(26,46,48,0.4); display:flex; align-items:center; padding:3px; border-radius:4px; }
.searchClear:hover { color:var(--navy); }

.filterPills { display:flex; flex-wrap:nowrap; overflow-x:auto; gap:clamp(6px,0.8vw,10px); scrollbar-width:none; padding-bottom:2px; }
.filterPills::-webkit-scrollbar { display:none; }
.filterPill {
    background:rgba(26,46,48,0.75);
    border:1.5px solid rgba(255,255,255,0.18);
    color:rgba(255,255,255,0.85);
    padding:clamp(6px,0.8vw,8px) clamp(12px,1.4vw,18px);
    border-radius:var(--radius-sm);
    font-family:'DM Sans',sans-serif; font-weight:900;
    font-size:clamp(9px,0.9vw,11px); letter-spacing:1.5px;
    text-transform:uppercase; cursor:pointer; white-space:nowrap;
    transition:all 0.2s ease; flex-shrink:0;
}
.filterPill:hover { background:rgba(238,140,58,0.12); color:#EE8C3A; border-color:#EE8C3A; }
.filterPillActive { background:#EE8C3A !important; color:#1a2e30 !important; border-color:#EE8C3A !important; box-shadow:0 0 12px rgba(238,140,58,0.35); }

/* ── SECTION GROUPS ── */
.sectionGroup { margin-bottom:var(--gap-xl); }
.sectionHeader {
    font-family:'DM Sans',sans-serif; font-size:clamp(9px,0.95vw,11px);
    font-weight:900; color:#fff; text-transform:uppercase; letter-spacing:2px;
    margin-bottom:var(--gap-md);
    display:inline-flex; align-items:center; gap:8px;
    padding:clamp(5px,0.7vw,8px) clamp(10px,1.3vw,16px);
    border-radius:6px; background:rgba(26,46,48,0.75);
    border:1px solid rgba(238,140,58,0.25);
}
.sectionHeaderBacklog { color:#fca5a5; background:rgba(127,29,29,0.5); border-color:rgba(239,68,68,0.35); }

/* ── MISSION GRID ── */
.missionGrid { display:flex; flex-direction:column; gap:var(--gap-md); }

/* ── MISSION CARD ── */
.missionCard {
    background:var(--panel-bg);
    border:1.5px solid rgba(238,140,58,0.2);
    border-radius:var(--radius);
    box-shadow:0 3px 12px rgba(0,0,0,0.2);
    transition:border-color 0.2s,box-shadow 0.2s;
    overflow:hidden; width:100%;
}
.missionCard:hover { border-color:rgba(238,140,58,0.5); box-shadow:0 6px 22px rgba(0,0,0,0.3); }
.cardLocked  { opacity:0.7; border-style:dashed; }
.cardBacklog { border-color:rgba(239,68,68,0.3); }
.cardBacklog:hover { border-color:rgba(239,68,68,0.6); }

/* ── STATUS BADGE ── */
.statusBadge {
    float:right; display:inline-flex; align-items:center; gap:5px;
    padding:4px 9px; font-family:'DM Sans',sans-serif;
    font-size:var(--fs-badge); font-weight:900; letter-spacing:0.8px;
    text-transform:uppercase;
}
.statusRed     { color:#fca5a5; }
.statusBlue    { color:#93c5fd; }
.statusGrey    { color:rgba(255,255,255,0.4); }
.statusDefault { color:rgba(255,255,255,0.5); }

/* ── CARD HEADER ── */
.cardHeader {
    display:flex; justify-content:space-between; align-items:flex-start;
    padding:clamp(10px,1.3vw,14px) var(--pad-card);
    cursor:pointer; user-select:none; clear:both; gap:10px;
}
.cardHeader:focus-visible { outline:2px solid var(--orange); outline-offset:-2px; border-radius:var(--radius); }

.identity { display:flex; flex-direction:column; gap:4px; min-width:0; flex:1; }

.ownerRow { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.ownerName { font-family:'Cinzel',serif; color:#fff; font-size:var(--fs-owner); font-weight:700; margin:0; letter-spacing:0.5px; }
.backlogOwnerTag {
    display:inline-flex; align-items:center; gap:4px;
    background:rgba(239,68,68,0.2); color:#fca5a5;
    border:1px solid rgba(239,68,68,0.4); border-radius:4px;
    padding:2px 7px; font-size:8px; font-weight:900;
    text-transform:uppercase; letter-spacing:0.8px;
    flex-shrink:0;
}
.phoneNum { font-family:'Space Mono',monospace; color:var(--orange); font-weight:900; font-size:var(--fs-phone); }

/* ── CARD FIN SUMMARY (pills in header) ── */
.cardFinSummary {
    display:flex; flex-wrap:wrap; gap:clamp(5px,0.7vw,8px);
    margin:clamp(4px,0.6vw,6px) 0;
}
.finPill {
    display:inline-flex; align-items:center; gap:5px;
    padding:clamp(3px,0.4vw,5px) clamp(8px,1vw,12px);
    border-radius:20px; font-family:'DM Sans',sans-serif;
    font-size:clamp(8px,0.82vw,10px); font-weight:900;
    text-transform:uppercase; letter-spacing:0.8px; white-space:nowrap;
    border:1px solid transparent;
}
.finPill[data-type="active"] {
    background:rgba(34,197,94,0.1); border-color:rgba(34,197,94,0.3); color:#86efac;
}
.finPill[data-type="backlog"] {
    background:rgba(239,68,68,0.1); border-color:rgba(239,68,68,0.3); color:#fca5a5;
}
.finPill[data-type="storage"] {
    background:rgba(239,68,68,0.07); border-color:rgba(239,68,68,0.2); color:rgba(252,165,165,0.75);
}
.finPillLabel { opacity:0.8; }
.finPillVal { font-family:'Space Mono',monospace; }

.totalDemandRow { display:flex; align-items:baseline; gap:6px; margin-top:2px; }
.demandLabel { font-size:var(--fs-label); font-weight:900; color:rgba(255,255,255,0.55); text-transform:uppercase; letter-spacing:1px; white-space:nowrap; }
.demandValue { font-family:'Space Mono',monospace; font-size:var(--fs-demand); color:#fff; font-weight:700; }
.demandValueRed { color:#fca5a5 !important; }

.expandIcon { color:rgba(255,255,255,0.4); font-size:18px; flex-shrink:0; transition:color 0.2s; margin-top:2px; }
.missionCard:hover .expandIcon { color:var(--orange); }

/* ── CARD BODY ── */
.cardBody { padding:0 var(--pad-card) var(--pad-card); }
.divider  { height:1px; background:rgba(238,140,58,0.18); margin:clamp(8px,1vw,11px) 0; }

.timingRow {
    display:flex; align-items:center; flex-wrap:wrap; gap:6px;
    font-size:var(--fs-meta); color:#e2e8f0; font-weight:700;
    background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px;
    border:1px solid rgba(255,255,255,0.06);
}
.timingRow strong { color:#fff; }
.timingSep { width:1px; height:12px; background:rgba(255,255,255,0.2); flex-shrink:0; }

/* ── PLOTS SECTIONS ── */
.plotsSection { margin-bottom:clamp(10px,1.3vw,14px); }

.plotsSectionHeader {
    display:flex; align-items:center; gap:6px;
    font-family:'DM Sans',sans-serif; font-size:var(--fs-label);
    font-weight:900; color:rgba(34,197,94,0.9);
    text-transform:uppercase; letter-spacing:1.5px;
    margin-bottom:clamp(7px,0.9vw,10px);
    padding:4px 0;
}
.plotsSectionHeaderBacklog { color:rgba(239,68,68,0.85); }

/* ── PLOT CARDS ── */
.plotCard {
    background:rgba(0,0,0,0.25);
    border:1px solid rgba(34,197,94,0.25);
    border-left:3px solid rgba(34,197,94,0.6);
    border-radius:8px;
    padding:clamp(9px,1.2vw,13px);
    margin-bottom:8px;
}
.plotCard:last-child { margin-bottom:0; }
.plotCardBacklog {
    border-color:rgba(239,68,68,0.25);
    border-left-color:rgba(239,68,68,0.7);
    background:rgba(239,68,68,0.06);
}

.plotCardTop { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; margin-bottom:clamp(8px,1vw,11px); }
.plotCardLeft { display:flex; align-items:flex-start; gap:8px; flex:1; min-width:0; }
.plotCardRight { display:flex; gap:6px; flex-shrink:0; }

.plotNum { font-family:'Space Mono',monospace; color:#EE8C3A; font-size:clamp(11px,1.1vw,13px); font-weight:700; margin-bottom:2px; }
.plotBoxNum { font-size:var(--fs-label); color:rgba(255,255,255,0.5); font-weight:700; }

/* ── ACTIVE PLOT FINANCIALS ── */
.plotFinRow {
    display:grid; grid-template-columns:repeat(3,1fr);
    gap:clamp(6px,0.8vw,10px);
    background:rgba(0,0,0,0.25); border-radius:6px;
    padding:clamp(7px,0.9vw,10px); margin-bottom:7px;
}
.plotFinItem { display:flex; flex-direction:column; gap:2px; }
.plotFinItem span { font-family:'DM Sans',sans-serif; font-size:7px; font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.8px; }
.plotFinItem strong { font-family:'Space Mono',monospace; font-size:clamp(10px,1.05vw,12px); font-weight:700; color:#fff; }

.plotProgressWrap { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.plotProgress { flex:1; height:4px; background:rgba(255,255,255,0.1); border-radius:4px; overflow:hidden; }
.plotProgressFill { height:100%; background:#22c55e; border-radius:4px; transition:width 0.4s ease; }
.plotProgressPct { font-family:'Space Mono',monospace; font-size:9px; font-weight:700; color:rgba(255,255,255,0.4); flex-shrink:0; min-width:28px; text-align:right; }

/* ── BACKLOG FIN BREAKDOWN ── */
.backlogFinBreakdown {
    background:rgba(0,0,0,0.3);
    border:1px solid rgba(239,68,68,0.2);
    border-radius:7px; padding:clamp(9px,1.1vw,12px);
    margin-bottom:7px;
}
.bfbRow { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.bfbItem { display:flex; flex-direction:column; gap:3px; }
.bfbLabel { font-family:'DM Sans',sans-serif; font-size:7px; font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.8px; }
.bfbVal { font-family:'Space Mono',monospace; font-size:clamp(11px,1.1vw,13px); font-weight:700; color:#fff; }
.bfbValTotal { font-family:'Space Mono',monospace; font-size:clamp(13px,1.4vw,16px); font-weight:900; color:#ef4444; }
.bfbDivider { height:1px; background:rgba(239,68,68,0.2); margin:clamp(7px,0.9vw,10px) 0; }

/* ── LAST NOTE ── */
.lastNote { display:flex; align-items:flex-start; gap:5px; font-size:var(--fs-label); color:rgba(255,255,255,0.5); font-style:italic; font-weight:600; line-height:1.4; }

/* ── PLOT ACTION BUTTONS ── */
.folderBtn {
    background:rgba(255,255,255,0.1); border:1.5px solid rgba(255,255,255,0.25);
    color:#fff; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius:var(--radius-sm); font-size:var(--fs-badge);
    padding:clamp(5px,0.6vw,7px) clamp(8px,1vw,11px);
    cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
    gap:4px; transition:all 0.2s; white-space:nowrap;
}
.folderBtn:hover { border-color:var(--orange); color:var(--orange); background:rgba(238,140,58,0.1); }

.payBtnTitle {
    background:rgba(34,197,94,0.15); border:1.5px solid rgba(34,197,94,0.45);
    color:#4ade80; font-family:'DM Sans',sans-serif; font-weight:900;
    border-radius:var(--radius-sm); font-size:var(--fs-badge);
    padding:clamp(5px,0.6vw,7px) clamp(8px,1vw,11px);
    cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
    gap:4px; transition:all 0.2s; white-space:nowrap;
}
.payBtnTitle:hover { background:#22c55e; color:#1a2e30; border-color:#22c55e; }

.payBtnBacklog {
    background:rgba(239,68,68,0.15) !important;
    border-color:rgba(239,68,68,0.5) !important;
    color:#fca5a5 !important;
}
.payBtnBacklog:hover { background:#ef4444 !important; color:#fff !important; border-color:#ef4444 !important; }

/* ── CARD ACTIONS ── */
.cardActions { display:flex; gap:var(--gap-md); flex-wrap:wrap; }
.logCallBtn {
    flex:1; min-width:120px; background:var(--orange); color:var(--navy);
    font-family:'DM Sans',sans-serif; font-weight:900; border-radius:var(--radius-sm);
    font-size:var(--fs-btn); text-transform:uppercase; letter-spacing:1px;
    padding:clamp(9px,1.1vw,12px); cursor:pointer;
    display:flex; align-items:center; justify-content:center; gap:7px;
    border:none; transition:background 0.2s;
}
.logCallBtn:hover:not(:disabled) { background:#d4732a; }
.logCallBtn:disabled { background:transparent; color:rgba(255,255,255,0.25); border:1.5px solid rgba(255,255,255,0.1); cursor:not-allowed; }

/* ── PAYMENT BREAKDOWN BOX (in modal) ── */
.payBreakdownBox {
    background:rgba(0,0,0,0.35);
    border:1px solid rgba(255,255,255,0.1);
    border-radius:8px;
    padding:clamp(10px,1.3vw,14px);
    margin-bottom:clamp(12px,1.5vw,16px);
}
.payBreakdownTitle {
    display:flex; align-items:center; gap:6px;
    font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900;
    color:#fca5a5; text-transform:uppercase; letter-spacing:1.5px;
    margin-bottom:10px;
}
.payBreakdownGrid {
    display:grid; grid-template-columns:1fr 1fr;
    gap:clamp(7px,0.9vw,10px);
}
.pbItem { display:flex; flex-direction:column; gap:3px; }
.pbLabel { font-family:'DM Sans',sans-serif; font-size:8px; font-weight:900; color:rgba(255,255,255,0.45); text-transform:uppercase; letter-spacing:0.8px; }
.pbVal { font-family:'Space Mono',monospace; font-size:clamp(11px,1.1vw,13px); font-weight:700; color:#fff; }
.pbItemTotal {
    grid-column:1/-1;
    border-top:1px solid rgba(255,255,255,0.1);
    padding-top:clamp(6px,0.8vw,9px);
    margin-top:2px;
    display:flex; flex-direction:column; gap:3px;
}
.pbValTotal { font-family:'Space Mono',monospace; font-size:clamp(14px,1.5vw,18px); font-weight:900; color:#EE8C3A; }

/* ── PAYMENT TYPE SELECTOR ── */
.payTypeRow {
    margin-bottom:clamp(12px,1.5vw,16px);
    display:flex; flex-direction:column; gap:8px;
}
.payTypeLabel {
    font-family:'DM Sans',sans-serif; font-size:9px; font-weight:900;
    color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1px;
}
.payTypeButtons { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.payTypeBtn {
    background:rgba(255,255,255,0.05);
    border:1.5px solid rgba(255,255,255,0.12);
    border-radius:8px;
    padding:clamp(10px,1.3vw,14px);
    cursor:pointer;
    display:flex; align-items:flex-start; gap:10px;
    transition:all 0.2s; text-align:left;
    color:rgba(255,255,255,0.7);
}
.payTypeBtn:hover { border-color:rgba(34,197,94,0.5); background:rgba(34,197,94,0.07); color:#fff; }
.payTypeBtnActive {
    border-color:#22c55e !important;
    background:rgba(34,197,94,0.14) !important;
    color:#fff !important;
    box-shadow:0 0 14px rgba(34,197,94,0.2);
}
.payTypeBtnStorage:hover { border-color:rgba(239,68,68,0.5) !important; background:rgba(239,68,68,0.07) !important; }
.payTypeBtnStorageActive {
    border-color:#ef4444 !important;
    background:rgba(239,68,68,0.14) !important;
    color:#fff !important;
    box-shadow:0 0 14px rgba(239,68,68,0.2);
}
.payTypeBtnName { font-family:'DM Sans',sans-serif; font-size:clamp(10px,1vw,12px); font-weight:900; text-transform:uppercase; letter-spacing:1px; display:block; margin-bottom:2px; }
.payTypeBtnSub { font-family:'DM Sans',sans-serif; font-size:9px; font-weight:700; color:rgba(255,255,255,0.45); display:block; line-height:1.4; }
.payTypeHint {
    display:flex; align-items:flex-start; gap:7px;
    background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
    border-radius:6px; padding:8px 10px;
    font-family:'DM Sans',sans-serif; font-size:10px; font-weight:700;
    color:rgba(252,165,165,0.85); line-height:1.5;
}

/* ── CALL MODAL ── */
.historyStream { max-height:160px; overflow-y:auto; background:#f8fafc; border-radius:8px; padding:10px; margin-bottom:12px; border:1px solid #e2e8f0; scrollbar-width:thin; }
.historyTitle  { font-family:'DM Sans',sans-serif; font-size:9px; font-weight:900; color:#475569; margin-bottom:8px; border-bottom:1px solid #e2e8f0; padding-bottom:5px; text-transform:uppercase; letter-spacing:1px; }
.historyItem   { border-bottom:1px solid #f1f5f9; padding-bottom:7px; margin-bottom:7px; }
.historyItem:last-child { border-bottom:none; margin-bottom:0; }
.historyMeta   { display:flex; justify-content:space-between; align-items:center; font-family:'DM Sans',sans-serif; font-size:10px; font-weight:800; color:#c2410c; margin-bottom:3px; }
.historyItem p { font-family:'DM Sans',sans-serif; font-size:12px; color:#1a2e30; line-height:1.5; font-weight:600; margin:0; }
.emptyHistory  { font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700; color:#94a3b8; text-align:center; padding:16px 0; }

/* ── EMPTY STATE ── */
.emptyGate {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:16px; padding:clamp(40px,8vw,80px) 20px; text-align:center;
    background:rgba(26,46,48,0.35); border:1.5px solid rgba(238,140,58,0.15);
    border-radius:12px;
}
.emptyIcon  { font-size:clamp(40px,6vw,60px); color:#10b981; opacity:0.4; }
.emptyTitle { font-family:'Cinzel',serif; font-size:clamp(14px,1.8vw,20px); font-weight:700; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:2px; margin:0; }

/* ── RESPONSIVE ── */
@media (max-width:900px) {
    .finHUD { grid-template-columns:repeat(3,1fr); }
    .pageHeader { flex-direction:column; align-items:flex-start; }
    .headerRight { width:100%; }
    .modeSwitch { width:100%; }
    .modeActive,.modeInactive { flex:1; justify-content:center; }
}
@media (max-width:640px) {
    .finHUD { grid-template-columns:1fr 1fr; }
    .finHUD .finHUDCard:last-child { grid-column:1/-1; }
    .plotFinRow { grid-template-columns:1fr 1fr 1fr; }
    .payTypeButtons { grid-template-columns:1fr; }
    .payBreakdownGrid { grid-template-columns:1fr; }
}
@media (max-width:480px) {
    .finHUD { grid-template-columns:1fr; }
    .cardHeader { padding:9px 11px; }
    .cardBody   { padding:0 11px 11px; }
    .ownerName  { font-size:13px; }
    .plotFinRow { grid-template-columns:repeat(3,1fr); }
    .bfbRow     { flex-direction:column; gap:8px; }
    .bfbItem[style*="right"] { text-align:left !important; }
}
'''

write('erp-frontend/src/pages/Recovery/RecoveryPortal.module.css', CSS_CONTENT)

print("\nAll files written.")
print("Run: git add -A && git commit -m 'feat: recovery portal - payment type distinction (title vs storage fees), backlog breakdown grid, financial HUD' && git push")