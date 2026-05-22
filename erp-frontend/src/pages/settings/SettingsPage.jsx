// PATH: erp-frontend/src/pages/settings/SettingsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    FiShield, FiKey, FiUsers, FiUserPlus, FiRefreshCcw,
    FiPower, FiMail, FiSave, FiAlertTriangle, FiArrowUp,
    FiArrowDown, FiChevronDown, FiActivity, FiEye, FiEyeOff,
    FiX, FiCheckSquare, FiAlertCircle, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './SettingsPage.module.css';

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

// ─── CONFIRM MODAL ────────────────────────────────────────────────
const useConfirm = () => {
    const [state, setState] = useState({ open: false, title: '', message: '', variant: 'warn', resolve: null });
    const confirm = useCallback((title, message, variant = 'warn') =>
        new Promise(resolve => setState({ open: true, title, message, variant, resolve })), []);
    const handleAnswer = useCallback(answer => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState: state, confirm, handleAnswer };
};
const ConfirmModal = ({ state, onAnswer }) => {
    if (!state.open || typeof document === 'undefined') return null;
    const isDanger = state.variant === 'danger';
    return createPortal(
        <div className={styles.confirmOverlay} role="dialog" aria-modal="true" aria-labelledby="confirm-title">
            <div className={styles.confirmBox}>
                <div className={`${styles.confirmHeader} ${isDanger ? styles.confirmHeaderDanger : styles.confirmHeaderWarn}`}>
                    <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />
                    <span id="confirm-title" className={styles.confirmTitle}>{state.title}</span>
                </div>
                <p className={styles.confirmMessage}>{state.message}</p>
                <div className={styles.confirmFooter}>
                    <button className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus>
                        <FiX aria-hidden="true" /> CANCEL
                    </button>
                    <button className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`} onClick={() => onAnswer(true)}>
                        CONFIRM
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
};

// ─── DRAWER HEADER ────────────────────────────────────────────────
const DrawerHeader = ({ label, isOpen, onClick, icon: IconComponent }) => (
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
const SettingsPage = () => {
    const { user, logout } = useAuth();
    const { toasts, toast, dismissToast } = useToast();
    const { confirmState, confirm, handleAnswer } = useConfirm();
    const isRoot = user?.isRoot;

    const [drawers,       setDrawers]       = useState({ security: true, governance: true });
    const [pwdState,      setPwdState]      = useState({ old: '', new: '', confirm: '' });
    const [pwdLoading,    setPwdLoading]    = useState(false);
    const [showOld,       setShowOld]       = useState(false);
    const [showNew,       setShowNew]       = useState(false);
    const [showConfirm,   setShowConfirm]   = useState(false);
    const [operators,     setOperators]     = useState([]);
    const [opLoading,     setOpLoading]     = useState(false);
    const [newOpModal,    setNewOpModal]    = useState(false);
    const [newOpData,     setNewOpData]     = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
    const [tempKeyReveal, setTempKeyReveal] = useState(null);

    const pwdDirty   = pwdState.old !== '' || pwdState.new !== '' || pwdState.confirm !== '';
    const newOpDirty = newOpModal && (newOpData.username !== '' || newOpData.email !== '');
    const isDirty    = pwdDirty || newOpDirty;
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);

    // Guarded modal close for new operator modal
    const handleCloseNewOpModal = () => {
        if (newOpDirty) {
            if (!window.confirm('Discard new operator details?')) return;
        }
        setNewOpModal(false);
        setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
    };

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    // beforeunload for tab close / hard refresh
    // useRouterBlock also adds beforeunload — this is belt-and-suspenders
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; return ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);

    const fetchOperators = useCallback(async () => {
        if (!isRoot) return;
        setOpLoading(true);
        try { const data = await settingsService.getAllOperators(); setOperators(data); }
        catch { /* handled by interceptor */ }
        finally { setOpLoading(false); }
    }, [isRoot]);

    useEffect(() => { fetchOperators(); }, [fetchOperators]);

    // ── PASSWORD CHANGE ──
    const handlePasswordChange = async e => {
        e.preventDefault();
        if (pwdState.new !== pwdState.confirm) {
            toast('SECURITY ALERT: KEYS DO NOT MATCH', 'error', 6000);
            return;
        }
        setPwdLoading(true);
        try {
            await settingsService.changePersonalPassword(pwdState.old, pwdState.new);
            toast('MASTER KEY REWRITTEN — LOGGING OUT...', 'success');
            setTimeout(logout, 1800);
        } catch (err) {
            toast(`REWRITE REJECTED: ${err.message || 'UNKNOWN ERROR'}`, 'error', 8000);
        } finally { setPwdLoading(false); }
    };

    // ── PROVISION ──
    const handleCreateManager = async e => {
        e.preventDefault();
        try {
            const response = await settingsService.registerManager(newOpData);
            setTempKeyReveal(response.temporaryPassword);
            setNewOpModal(false);
            setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
            fetchOperators();
            // isDirty resets automatically since newOpData is cleared
        } catch (err) {
            toast(err.message || 'PROVISIONING FAILED', 'error', 8000);
        }
    };

    // ── ROLE SWITCH ──
    const handleRoleSwitch = async (opUsername, currentRole) => {
        const targetRole = currentRole === 'ROLE_ADMIN' ? 'ROLE_MANAGER' : 'ROLE_ADMIN';
        const label = targetRole === 'ROLE_ADMIN' ? 'PROMOTE TO ADMIN' : 'DEMOTE TO OPERATOR';
        const ok = await confirm(label, `${label} for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.updateOperatorRole(opUsername, targetRole); fetchOperators(); }
        catch (err) { toast(err.message || 'ROLE SWITCH FAILED', 'error', 8000); }
    };

    // ── STATUS TOGGLE ──
    const handleStatusToggle = async (opUsername, isActive) => {
        const action = isActive ? 'SUSPEND' : 'RESTORE';
        const ok = await confirm(`${action} OPERATOR`, `Physically ${action.toLowerCase()} access for ${opUsername}?`, 'warn');
        if (!ok) return;
        try { await settingsService.toggleOperator(opUsername, !isActive); fetchOperators(); }
        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }
    };

    return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Security Settings" />
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />

            {/* HEADER */}
            <header className={styles.pageHeader}>
                <div className={styles.titleGroup}>
                    <h1 className={styles.title}>Security Mastery</h1>
                    <p className={styles.subtitle}>Hardware Protocols &amp; Identity Registry</p>
                </div>
                {user?.mustChangePassword && (
                    <div className={styles.handbrakeBadge} role="alert">
                        <FiAlertTriangle className={styles.blink} aria-hidden="true" /> KEY REWRITE MANDATORY
                    </div>
                )}
            </header>

            <div className={styles.workstationGrid}>

                {/* PANEL: PERSONAL SECURITY */}
                <div className={styles.hwPanel}>
                    <DrawerHeader label="OPERATOR SECURITY CABINET" isOpen={drawers.security} onClick={() => toggleDrawer('security')} icon={FiKey} />
                    <div className={`${styles.panelBody} ${drawers.security ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.security}>
                        <div className={styles.panelInner}>
                            <form onSubmit={handlePasswordChange} className={styles.personalForm}>
                                <div className={styles.securityAlert}>
                                    <FiShield aria-hidden="true" />
                                    <span>Updating this key will clear the mandatory reset handbrake.</span>
                                </div>

                                <div className={styles.eyeInpWrap}>
                                    <HardwareInput label="CURRENT MASTER KEY" type={showOld ? 'text' : 'password'} value={pwdState.old} onChange={e => setPwdState({...pwdState, old: e.target.value})} required />
                                    <button type="button" className={styles.eyeBtn} onClick={() => setShowOld(v => !v)} aria-label={showOld ? 'Hide password' : 'Show password'}>
                                        {showOld ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}
                                    </button>
                                </div>

                                <div className={styles.dualRow}>
                                    <div className={styles.eyeInpWrap}>
                                        <HardwareInput label="NEW HARDWARE KEY" type={showNew ? 'text' : 'password'} value={pwdState.new} onChange={e => setPwdState({...pwdState, new: e.target.value})} required />
                                        <button type="button" className={styles.eyeBtn} onClick={() => setShowNew(v => !v)} aria-label={showNew ? 'Hide new password' : 'Show new password'}>
                                            {showNew ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}
                                        </button>
                                    </div>
                                    <div className={styles.eyeInpWrap}>
                                        <HardwareInput label="CONFIRM CONFIGURATION" type={showConfirm ? 'text' : 'password'} value={pwdState.confirm} onChange={e => setPwdState({...pwdState, confirm: e.target.value})} required />
                                        <button type="button" className={styles.eyeBtn} onClick={() => setShowConfirm(v => !v)} aria-label={showConfirm ? 'Hide confirmation' : 'Show confirmation'}>
                                            {showConfirm ? <FiEyeOff aria-hidden="true" /> : <FiEye aria-hidden="true" />}
                                        </button>
                                    </div>
                                </div>

                                <div className={styles.submitRow}>
                                    <button className={styles.commitBtn} type="submit" disabled={pwdLoading}>
                                        {pwdLoading ? 'REWRITING...' : <><FiSave aria-hidden="true" /> REWRITE HARDWARE KEY</>}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                {/* PANEL: GOVERNANCE (ROOT ONLY) */}
                {isRoot && (
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="GOVERNANCE LEDGER" isOpen={drawers.governance} onClick={() => toggleDrawer('governance')} icon={FiUsers} />
                        <div className={`${styles.panelBody} ${drawers.governance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.governance}>
                            <div className={styles.panelInner}>
                                <div className={styles.ledgerActions}>
                                    <button className={styles.addOpBtn} onClick={() => setNewOpModal(true)} aria-label="Provision new operator">
                                        <FiUserPlus aria-hidden="true" /> PROVISION NEW OPERATOR
                                    </button>
                                </div>

                                <div className={styles.staffStream} role="list" aria-label="Operators">
                                    {opLoading ? (
                                        <div className={styles.hint}>
                                            <FiActivity className={styles.spin} aria-hidden="true" /> INTERROGATING REGISTRY...
                                        </div>
                                    ) : operators.length === 0 ? (
                                        <div className={styles.hint}>NO SECONDARY OPERATORS IN REGISTRY.</div>
                                    ) : operators.map(op => (
                                        <div key={op.id} className={`${styles.opCard} ${!op.active ? styles.cardDimmed : ''}`} role="listitem">
                                            <div className={styles.opHeader}>
                                                <div className={styles.opAvatar} aria-hidden="true">
                                                    {op.username.charAt(0).toUpperCase()}
                                                    <div className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} />
                                                </div>
                                                <div className={styles.opInfo}>
                                                    <strong>{op.username}</strong>
                                                    <span className={op.role === 'ROLE_ADMIN' ? styles.rankAdmin : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_ADMIN' ? 'TIER 2: ADMIN' : 'TIER 3: OPERATOR'}
                                                    </span>
                                                </div>
                                                <div className={styles.opActions}>
                                                    {!op.isRoot && (<>
                                                        <button className={styles.rankBtn} onClick={() => handleRoleSwitch(op.username, op.role)} aria-label={op.role === 'ROLE_ADMIN' ? `Demote ${op.username}` : `Promote ${op.username}`}>
                                                            {op.role === 'ROLE_ADMIN' ? <FiArrowDown aria-hidden="true" /> : <FiArrowUp aria-hidden="true" />}
                                                        </button>
                                                        <button className={`${styles.killSwitchBtn} ${op.active ? styles.killSwitchActive : styles.killSwitchInactive}`} onClick={() => handleStatusToggle(op.username, op.active)} aria-label={op.active ? `Suspend ${op.username}` : `Restore ${op.username}`}>
                                                            <FiPower aria-hidden="true" />
                                                        </button>
                                                        <button className={styles.resetTrigger} onClick={() => settingsService.resetOperatorKey(op.username).then(k => setTempKeyReveal(k))} aria-label={`Force key reset for ${op.username}`}>
                                                            <FiRefreshCcw aria-hidden="true" />
                                                        </button>
                                                    </>)}
                                                </div>
                                            </div>
                                            <div className={styles.opDetails}>
                                                <p><FiMail aria-hidden="true" /> {op.email || 'NO_RECOVERY_EMAIL'}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* PROVISION MODAL */}
            <HardwareModal isOpen={newOpModal} onClose={handleCloseNewOpModal} title="INITIALIZE IDENTITY">
                <form onSubmit={handleCreateManager} className={styles.modalBody}>
                    <HardwareInput label="USERNAME" value={newOpData.username} onChange={e => setNewOpData({...newOpData, username: e.target.value})} required />
                    <HardwareInput label="RECOVERY EMAIL" type="email" value={newOpData.email} onChange={e => setNewOpData({...newOpData, email: e.target.value})} required />
                    <div className={styles.selectWrap}>
                        <HardwareSelect label="INITIAL RANK" options={['ROLE_MANAGER', 'ROLE_ADMIN']} value={newOpData.role} onChange={v => setNewOpData({...newOpData, role: v})} />
                    </div>
                    <div className={styles.modalCenter}>
                        <button className={styles.commitBtn} type="submit">EXECUTE PROVISIONING</button>
                    </div>
                </form>
            </HardwareModal>

            {/* KEY REVEAL MODAL */}
            <HardwareModal isOpen={!!tempKeyReveal} onClose={() => setTempKeyReveal(null)} title="TEMPORARY CREDENTIAL">
                <div className={styles.revealBox}>
                    <FiAlertTriangle className={styles.warningIcon} aria-hidden="true" />
                    <p className={styles.revealHint}>ONE-TIME HARDWARE KEY GENERATED:</p>
                    <div className={styles.serial}>{tempKeyReveal}</div>
                    <p className={styles.revealDisclaimer}>PROVIDE THIS CODE TO THE OPERATOR IMMEDIATELY.</p>
                    <button className={styles.commitBtn} onClick={() => setTempKeyReveal(null)}>KEY SECURED</button>
                </div>
            </HardwareModal>
        </div>
    );
};

export default SettingsPage;