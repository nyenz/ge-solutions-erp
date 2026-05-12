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

// ── MONTHLY INSTALLMENT MODAL ───────────────────────────────────
// Separate payment scheme: client pays a fixed monthly instalment
// toward their title cost. Distinct from backlog/storage payments.
const MonthlyInstallmentModal = ({ open, plot, onClose, onPay, paying }) => {
    const [amount, setAmount]   = React.useState('');
    const [notes,  setNotes]    = React.useState('');
    const [period, setPeriod]   = React.useState('');   // e.g. "May 2026"

    React.useEffect(() => {
        if (open) {
            setAmount('');
            setNotes('');
            // Auto-fill current month as default period label
            const now = new Date();
            setPeriod(now.toLocaleString('default', { month: 'long', year: 'numeric' }));
        }
    }, [open]);

    if (!plot) return null;

    const balance  = Number(plot.currentBalance  || 0);
    const paid     = Number(plot.amountPaid      || 0);
    const total    = Number(plot.totalCost       || 0);
    const pct      = total > 0 ? Math.round((paid / total) * 100) : 0;

    const handleSubmit = () => {
        if (!amount || Number(amount) <= 0) return;
        const fullNotes = `[MONTHLY INSTALMENT${period ? ' - ' + period : ''}]${notes ? ' ' + notes : ''}`;
        onPay(plot, amount, fullNotes, 'MONTHLY');
    };

    return (
        <HardwareModal isOpen={open} onClose={onClose}
            title={'MONTHLY INSTALMENT — ' + plot.plotNumber}>

            {/* Summary strip */}
            <div style={{
                background: 'rgba(6,182,212,0.08)',
                border: '1px solid rgba(6,182,212,0.25)',
                borderRadius: 8,
                padding: '12px 14px',
                marginBottom: 16,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: 10,
            }}>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        TOTAL COST
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#fff'}}>
                        UGX {total.toLocaleString()}
                    </div>
                </div>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        PAID SO FAR
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#86efac'}}>
                        UGX {paid.toLocaleString()}
                    </div>
                </div>
                <div>
                    <div style={{fontFamily:'DM Sans,sans-serif',fontSize:8,fontWeight:900,color:'rgba(252,165,165,0.8)',textTransform:'uppercase',letterSpacing:1,marginBottom:3}}>
                        OUTSTANDING
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:13,fontWeight:700,color:'#fca5a5'}}>
                        UGX {Math.max(0,balance).toLocaleString()}
                    </div>
                </div>
                {/* Progress bar spanning full width */}
                <div style={{gridColumn:'1/-1'}}>
                    <div style={{height:4,background:'rgba(255,255,255,0.08)',borderRadius:4,overflow:'hidden',marginTop:4}}>
                        <div style={{height:'100%',width:pct+'%',background:'#06b6d4',borderRadius:4,transition:'width 0.4s ease'}} />
                    </div>
                    <div style={{fontFamily:'Space Mono,monospace',fontSize:9,color:'rgba(255,255,255,0.3)',marginTop:3}}>{pct}% collected</div>
                </div>
            </div>

            {/* Period label */}
            <div style={{marginBottom:14}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    INSTALMENT PERIOD
                </label>
                <input
                    type="text"
                    value={period}
                    onChange={e => setPeriod(e.target.value)}
                    placeholder="e.g. May 2026"
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(255,255,255,0.18)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:700,
                        outline:'none', boxSizing:'border-box',
                    }}
                />
            </div>

            {/* Amount */}
            <div style={{marginBottom:14}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    AMOUNT RECEIVED (UGX)
                </label>
                <input
                    type="number"
                    value={amount}
                    onChange={e => setAmount(e.target.value)}
                    placeholder="Enter instalment amount..."
                    autoFocus
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(6,182,212,0.4)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'Space Mono,monospace', fontSize:14, fontWeight:700,
                        outline:'none', boxSizing:'border-box',
                    }}
                />
            </div>

            {/* Notes */}
            <div style={{marginBottom:16}}>
                <label style={{display:'block',fontFamily:'DM Sans,sans-serif',fontSize:9,fontWeight:900,color:'rgba(255,255,255,0.5)',textTransform:'uppercase',letterSpacing:1,marginBottom:6}}>
                    NOTES (optional)
                </label>
                <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="e.g. MTN Mobile Money, cash..."
                    rows={3}
                    style={{
                        width:'100%', padding:'10px 12px',
                        borderRadius:8,
                        background:'rgba(255,255,255,0.07)',
                        border:'1.5px solid rgba(255,255,255,0.15)',
                        color:'rgba(255,255,255,0.9)',
                        fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:700,
                        outline:'none', resize:'vertical', boxSizing:'border-box',
                    }}
                />
            </div>

            <div style={{display:'flex',justifyContent:'flex-end',gap:10,paddingTop:12,borderTop:'1px solid rgba(255,255,255,0.08)'}}>
                <button onClick={onClose} style={{
                    padding:'0 16px', height:38,
                    background:'rgba(255,255,255,0.06)',
                    border:'1.5px solid rgba(255,255,255,0.2)',
                    borderRadius:8, color:'rgba(255,255,255,0.7)',
                    fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,
                    textTransform:'uppercase',letterSpacing:1.5,cursor:'pointer',
                }}>
                    CANCEL
                </button>
                <button onClick={handleSubmit} disabled={paying} style={{
                    padding:'0 20px', height:38,
                    background:'#06b6d4',
                    border:'none',
                    borderRadius:8, color:'#1a2e30',
                    fontFamily:'DM Sans,sans-serif',fontWeight:900,fontSize:10,
                    textTransform:'uppercase',letterSpacing:1.5,cursor:'pointer',
                    display:'flex',alignItems:'center',gap:7,
                    opacity: paying ? 0.5 : 1,
                }}>
                    <FiRepeat size={13} />
                    {paying ? 'PROCESSING...' : 'RECORD INSTALMENT'}
                </button>
            </div>
        </HardwareModal>
    );
};

// ── STORAGE FEE INLINE CONTROLS ────────────────────────────────
// Shows directly on each backlog plot card so admin can set monthly fee
// without opening a separate modal
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
    const [monthlyModal,  setMonthlyModal]  = useState({ open: false, plot: null });

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
                                                    <div style={{display:'flex',alignItems:'center',gap:6}}>
                                                        <span className={styles.plotNum}>{plot.plotNumber}</span>
                                                        {plot.isBacklog && (
                                                            <span style={{
                                                                display:'inline-flex',alignItems:'center',gap:3,
                                                                background:'rgba(239,68,68,0.18)',
                                                                border:'1px solid rgba(239,68,68,0.45)',
                                                                borderRadius:4,padding:'1px 6px',
                                                                fontFamily:'DM Sans,sans-serif',fontSize:7,
                                                                fontWeight:900,color:'#fca5a5',
                                                                textTransform:'uppercase',letterSpacing:0.8,
                                                                flexShrink:0,
                                                            }}>
                                                                <FiAlertOctagon size={7} /> BACKLOG
                                                            </span>
                                                        )}
                                                    </div>
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
                                                {isAdmin && (
                                                    <button className={styles.payBtnMonthly}
                                                        onClick={() => setMonthlyModal({ open: true, plot })}>
                                                        <FiRepeat size={12} /> INSTALMENT
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
                                                    <div style={{display:'flex',alignItems:'center',gap:6}}>
                                                        <span className={styles.plotNum}>{plot.plotNumber}</span>
                                                        <span style={{
                                                            display:'inline-flex',alignItems:'center',gap:3,
                                                            background:'rgba(239,68,68,0.22)',
                                                            border:'1px solid rgba(239,68,68,0.55)',
                                                            borderRadius:4,padding:'1px 6px',
                                                            fontFamily:'DM Sans,sans-serif',fontSize:7,
                                                            fontWeight:900,color:'#fca5a5',
                                                            textTransform:'uppercase',letterSpacing:0.8,
                                                            flexShrink:0,
                                                            animation:'criticalPulse 1.8s ease-in-out infinite',
                                                        }}>
                                                            <FiAlertOctagon size={7} /> BACKLOG
                                                        </span>
                                                    </div>
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
                                        {isAdmin && (
                                            <StorageFeeInlineControls
                                                plot={plot}
                                                onUpdated={loadData}
                                                toast={toast}
                                            />
                                        )}
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

            {/* MONTHLY INSTALMENT MODAL */}
            <MonthlyInstallmentModal
                open={monthlyModal.open}
                plot={monthlyModal.plot}
                onClose={() => setMonthlyModal({ open: false, plot: null })}
                onPay={handleRecordPayment}
                paying={paying}
            />
        </div>
    );
};

export default RecoveryPortal;
