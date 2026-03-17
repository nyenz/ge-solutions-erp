// PATH: erp-frontend/src/pages/settings/SettingsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    FiShield, FiKey, FiUsers, FiUserPlus, FiRefreshCcw,
    FiPower, FiMail, FiSave, FiAlertTriangle, FiArrowUp,
    FiArrowDown, FiChevronDown, FiActivity,
    FiX, FiCheckSquare, FiAlertCircle, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import HardwareModal from '../../components/common/HardwareModal';
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
                    {isDanger ? <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" /> : <FiAlertTriangle className={styles.confirmIcon} aria-hidden="true" />}
                    <span id="confirm-title" className={styles.confirmTitle}>{state.title}</span>
                </div>
                <p className={styles.confirmMessage}>{state.message}</p>
                <div className={styles.confirmFooter}>
                    <button className={styles.confirmCancelBtn} onClick={() => onAnswer(false)} autoFocus><FiX aria-hidden="true" /> CANCEL</button>
                    <button className={`${styles.confirmOkBtn} ${isDanger ? styles.confirmOkDanger : styles.confirmOkWarn}`} onClick={() => onAnswer(true)}>CONFIRM</button>
                </div>
            </div>
        </div>,
        document.body
    );
};

// ─── DRAWER HEADER ────────────────────────────────────────────────
const DrawerTitle = ({ label, isOpen, onClick, icon: IconComponent }) => (
    <div
        className={styles.drawerHeader}
        onClick={onClick}
        role="button" tabIndex={0}
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

    const [drawers,    setDrawers]    = useState({ security: true, governance: true });
    const [pwdState,   setPwdState]   = useState({ old: '', new: '', confirm: '' });
    const [pwdLoading, setPwdLoading] = useState(false);
    const [operators,  setOperators]  = useState([]);
    const [opLoading,  setOpLoading]  = useState(false);
    const [newOpModal, setNewOpModal] = useState(false);
    const [newOpData,  setNewOpData]  = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
    const [tempKeyReveal, setTempKeyReveal] = useState(null);

    const toggleDrawer = key => setDrawers(prev => ({ ...prev, [key]: !prev[key] }));

    const fetchOperators = useCallback(async () => {
        if (!isRoot) return;
        setOpLoading(true);
        try { const data = await settingsService.getAllOperators(); setOperators(data); }
        catch { /* handled by interceptor */ }
        finally { setOpLoading(false); }
    }, [isRoot]);

    useEffect(() => { fetchOperators(); }, [fetchOperators]);

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
            toast(err.message || 'KEY REWRITE FAILED', 'error', 8000);
        } finally { setPwdLoading(false); }
    };

    const handleCreateManager = async e => {
        e.preventDefault();
        try {
            const response = await settingsService.registerManager(newOpData);
            setTempKeyReveal(response.temporaryPassword);
            setNewOpModal(false);
            setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
            fetchOperators();
        } catch (err) {
            toast(err.message || 'PROVISIONING FAILED', 'error', 8000);
        }
    };

    const handleToggleStatus = async (username, currentStatus) => {
        const verb = currentStatus ? 'SUSPEND' : 'RESTORE';
        const ok = await confirm(`${verb} OPERATOR`, `Physically ${verb.toLowerCase()} access for ${username}?`, 'warn');
        if (!ok) return;
        try { await settingsService.toggleOperator(username, !currentStatus); fetchOperators(); }
        catch (err) { toast(err.message || 'ACTION FAILED', 'error', 8000); }
    };

    const handleRoleSwitch = async (username, currentRole) => {
        const isAdmin  = currentRole === 'ROLE_ADMIN';
        const newRole  = isAdmin ? 'ROLE_MANAGER' : 'ROLE_ADMIN';
        const action   = isAdmin ? 'DEMOTE TO OPERATOR' : 'PROMOTE TO ADMIN';
        const ok = await confirm(action, `${action} for ${username}?`, 'warn');
        if (!ok) return;
        try { await settingsService.updateOperatorRole(username, newRole); fetchOperators(); }
        catch (err) { toast(err.message || 'ROLE SWITCH FAILED', 'error', 8000); }
    };

    return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />

            <header className={styles.header}>
                <div className={styles.titleGroup}>
                    <h1 className={styles.title}>Security Mastery</h1>
                    <p className={styles.subtitle}>Identity Protocols &amp; Operator Governance</p>
                </div>
                {user?.mustChangePassword && (
                    <div className={styles.emergencyBadge} role="alert">
                        <FiAlertTriangle className={styles.pulseIcon} aria-hidden="true" />
                        MANDATORY KEY REWRITE REQUIRED
                    </div>
                )}
            </header>

            <div className={styles.workstationGrid}>

                <div className={styles.hwPanel}>
                    <DrawerTitle label="OPERATOR SECURITY CABINET" isOpen={drawers.security} onClick={() => toggleDrawer('security')} icon={FiKey} />
                    <div className={`${styles.panelBody} ${drawers.security ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.security}>
                        <div className={styles.panelInner}>
                            <form onSubmit={handlePasswordChange} className={styles.personalForm}>
                                <div className={styles.encryptionAlert}>
                                    <div className={styles.iconBox}><FiShield aria-hidden="true" /></div>
                                    <p>Hardware key encryption active. Rewrite current key to clear lockouts.</p>
                                </div>
                                <HardwareInput label="Current Master Key" type="password" value={pwdState.old} onChange={e => setPwdState({...pwdState, old: e.target.value})} required />
                                <div className={styles.dualFieldRow}>
                                    <HardwareInput label="New Hardware Key" type="password" value={pwdState.new} onChange={e => setPwdState({...pwdState, new: e.target.value})} required />
                                    <HardwareInput label="Confirm Configuration" type="password" value={pwdState.confirm} onChange={e => setPwdState({...pwdState, confirm: e.target.value})} required />
                                </div>
                                <div className={styles.submitRow}>
                                    <HardwareButton type="submit" loading={pwdLoading} icon={FiSave}>Rewrite Hardware Key</HardwareButton>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                {isRoot && (
                    <div className={styles.hwPanel}>
                        <DrawerTitle label="GOVERNANCE LEDGER" isOpen={drawers.governance} onClick={() => toggleDrawer('governance')} icon={FiUsers} />
                        <div className={`${styles.panelBody} ${drawers.governance ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.governance}>
                            <div className={styles.panelInner}>
                                <div className={styles.ledgerControls}>
                                    <button className={styles.provisionTrigger} onClick={() => setNewOpModal(true)} aria-label="Provision new manager">
                                        <FiUserPlus aria-hidden="true" /> PROVISION NEW MANAGER
                                    </button>
                                </div>
                                <div className={styles.staffStream} role="list" aria-label="Operators">
                                    {opLoading ? <p className={styles.hint}>INTERROGATING REGISTRY...</p> :
                                     operators.length === 0 ? <p className={styles.hint}>NO SECONDARY OPERATORS</p> :
                                     operators.map(op => (
                                        <div key={op.id} className={`${styles.operatorCard} ${!op.active ? styles.deadCircuit : ''}`} role="listitem">
                                            <div className={styles.opMain}>
                                                <div className={styles.opAvatar} aria-hidden="true">
                                                    {op.username.charAt(0).toUpperCase()}
                                                    <div className={`${styles.statusDot} ${op.active ? styles.dotGreen : styles.dotRed}`} />
                                                </div>
                                                <div className={styles.opIdentity}>
                                                    <strong>{op.username}</strong>
                                                    <span className={op.role === 'ROLE_ADMIN' ? styles.rankAdmin : styles.rankManager}>
                                                        {op.isRoot ? 'MASTER FOUNDER' : op.role === 'ROLE_ADMIN' ? 'TIER 2: SYSTEM ADMIN' : 'TIER 3: OPERATOR'}
                                                    </span>
                                                </div>
                                                <div className={styles.opActions}>
                                                    {!op.isRoot && (<>
                                                        <button className={styles.rankBtn} onClick={() => handleRoleSwitch(op.username, op.role)} aria-label={op.role === 'ROLE_ADMIN' ? `Demote ${op.username} to Manager` : `Promote ${op.username} to Admin`}>
                                                            {op.role === 'ROLE_ADMIN' ? <FiArrowDown aria-hidden="true" /> : <FiArrowUp aria-hidden="true" />}
                                                        </button>
                                                        <button className={op.active ? styles.killSwitchBtn : styles.reviveBtn} onClick={() => handleToggleStatus(op.username, op.active)} aria-label={op.active ? `Suspend ${op.username}` : `Restore ${op.username}`}>
                                                            <FiPower aria-hidden="true" />
                                                        </button>
                                                    </>)}
                                                    <button className={styles.resetTrigger} onClick={() => settingsService.resetOperatorKey(op.username).then(k => setTempKeyReveal(k))} aria-label={`Force password reset for ${op.username}`}>
                                                        <FiRefreshCcw aria-hidden="true" />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className={styles.opDetails}>
                                                <p><FiActivity aria-hidden="true" /> STATUS: {op.active ? 'ONLINE' : 'REVOKED'}</p>
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

            <HardwareModal isOpen={newOpModal} onClose={() => setNewOpModal(false)} title="INITIALIZE IDENTITY">
                <form onSubmit={handleCreateManager} className={styles.modalBody}>
                    <HardwareInput label="Operator Username" value={newOpData.username} onChange={e => setNewOpData({...newOpData, username: e.target.value})} required />
                    <HardwareInput label="Recovery Email" value={newOpData.email} onChange={e => setNewOpData({...newOpData, email: e.target.value})} required type="email" />
                    <div className={styles.selectWrap}>
                        <HardwareSelect label="Initial Clearance Level" options={['ROLE_MANAGER', 'ROLE_ADMIN']} value={newOpData.role} onChange={val => setNewOpData({...newOpData, role: val})} />
                    </div>
                    <div className={styles.modalCenter}>
                        <HardwareButton type="submit">Execute Provisioning</HardwareButton>
                    </div>
                </form>
            </HardwareModal>

            <HardwareModal isOpen={!!tempKeyReveal} onClose={() => setTempKeyReveal(null)} title="TEMPORARY CREDENTIAL">
                <div className={styles.keyRevealTerminal}>
                    <FiAlertTriangle className={styles.warningIcon} aria-hidden="true" />
                    <p>NEW HARDWARE KEY GENERATED:</p>
                    <div className={styles.serialBox}>{tempKeyReveal}</div>
                    <p className={styles.disclaimer}>Hand this code to the operator. One-time use only.</p>
                    <HardwareButton onClick={() => setTempKeyReveal(null)}>Credential Secured</HardwareButton>
                </div>
            </HardwareModal>
        </div>
    );
};

export default SettingsPage;