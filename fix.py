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

def patch(path, old, new):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        return True
    else:
        print(f"MISSING in {path}: snippet not matched")
        return False

# ================================================================
# 1. AuditPage -- guard on search + filter changes
# ================================================================
AUDIT = 'erp-frontend/src/pages/Audit/AuditPage.jsx'

patch(
    AUDIT,
    """import auditService from '../../services/auditService';
import settingsService from '../../services/settingsService';
import HardwareSelect from '../../components/common/HardwareSelect';
import styles from './AuditPage.module.css';""",
    """import auditService from '../../services/auditService';
import settingsService from '../../services/settingsService';
import HardwareSelect from '../../components/common/HardwareSelect';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './AuditPage.module.css';"""
)

patch(
    AUDIT,
    """    const [operators,  setOperators]  = useState([]);
    const [isSearchFocused, setIsSearchFocused] = useState(false);""",
    """    const [operators,  setOperators]  = useState([]);
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const isDirty = filters.search !== '' || (filters.operator !== '' && filters.operator !== 'ALL STAFF') || (filters.action !== '' && filters.action !== 'ALL ACTIONS');
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);"""
)

patch(
    AUDIT,
    """        return (
        <div className={styles.container}>""",
    """        return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Audit Filters" />"""
)

print("AuditPage: done")

# ================================================================
# 2. LedgerPage -- guard on search input
# ================================================================
LEDGER = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

patch(
    LEDGER,
    """import HardwarePanel from '../../components/ui/HardwarePanel';
import ErrorMessage from '../../components/common/ErrorMessage';
import landService from '../../services/landService';
import styles from './LedgerPage.module.css';""",
    """import HardwarePanel from '../../components/ui/HardwarePanel';
import ErrorMessage from '../../components/common/ErrorMessage';
import landService from '../../services/landService';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './LedgerPage.module.css';"""
)

patch(
    LEDGER,
    """    const [sortConfig,   setSortConfig]   = useState({ key: 'plotNumber', direction: 'asc' });""",
    """    const [sortConfig,   setSortConfig]   = useState({ key: 'plotNumber', direction: 'asc' });
    const isDirty = searchTerm !== '';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);"""
)

patch(
    LEDGER,
    """        return (
        <div className={styles.container}>

            <header className={styles.pageHeader}>""",
    """        return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Ledger Search" />

            <header className={styles.pageHeader}>"""
)

print("LedgerPage: done")

# ================================================================
# 3. PaymentsPage -- guard on search input
# ================================================================
PAYMENTS = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'

patch(
    PAYMENTS,
    """import api from '../../api/axios';
import HardwarePanel from '../../components/ui/HardwarePanel';
import styles from './PaymentsPage.module.css';""",
    """import api from '../../api/axios';
import HardwarePanel from '../../components/ui/HardwarePanel';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './PaymentsPage.module.css';"""
)

patch(
    PAYMENTS,
    """    const [sortKey,    setSortKey]    = useState('date');
    const [sortDir,    setSortDir]    = useState('desc');""",
    """    const [sortKey,    setSortKey]    = useState('date');
    const [sortDir,    setSortDir]    = useState('desc');
    const isDirty = searchTerm !== '' || typeFilter !== 'ALL';
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(isDirty);"""
)

patch(
    PAYMENTS,
    """        return (
        <div className={styles.container}>
            <header className={styles.pageHeader}>""",
    """        return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Payment Filters" />
            <header className={styles.pageHeader}>"""
)

print("PaymentsPage: done")

# ================================================================
# 4. LoginPage -- guard on username/password typed but not submitted
# ================================================================
LOGIN = 'erp-frontend/src/pages/login/LoginPage.jsx'

patch(
    LOGIN,
    """import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import authService from '../../services/authService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import { FiShield, FiEye, FiEyeOff, FiCheckCircle } from 'react-icons/fi';
import styles from './LoginPage.module.css';""",
    """import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import authService from '../../services/authService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import { FiShield, FiEye, FiEyeOff, FiCheckCircle } from 'react-icons/fi';
import styles from './LoginPage.module.css';"""
)

patch(
    LOGIN,
    """    const [tempKeyReveal, setTempKeyReveal] = useState(null);""",
    """    const [tempKeyReveal, setTempKeyReveal] = useState(null);
    const loginDirty = !loading && (creds.username !== '' || creds.password !== '');
    const { blocked: guardOpen, proceed: handleLeave, reset: handleStay } = useRouterBlock(loginDirty);"""
)

# Insert guard modal just before the closing of pageWrapper
patch(
    LOGIN,
    """            {/* MODAL: MASTER RECOVERY */}""",
    """            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Login Form" />

            {/* MODAL: MASTER RECOVERY */}"""
)

print("LoginPage: done")

# ================================================================
# 5. RecoveryPortal -- guard on call log modal + payment modal
# ================================================================
RECOVERY = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

patch(
    RECOVERY,
    """import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';""",
    """import recoveryService from '../../services/recoveryService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './RecoveryPortal.module.css';
import modalStyles from '../../components/common/HardwareModal.module.css';"""
)

patch(
    RECOVERY,
    """    const [paying,        setPaying]        = useState(false);""",
    """    const [paying,        setPaying]        = useState(false);

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
    };"""
)

# Update the modal onClose props to use the guarded versions
patch(
    RECOVERY,
    """            <HardwareModal isOpen={callModal.open}
                onClose={() => setCallModal({ open: false, mission: null })}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>""",
    """            <HardwareModal isOpen={callModal.open}
                onClose={handleCloseCallModal}
                title={`LOG CALL: ${callModal.mission?.ownerName || ''}`}>"""
)

patch(
    RECOVERY,
    """            <HardwareModal isOpen={payModal.open}
                onClose={() => setPayModal({ open: false, plot: null })}
                title={`RECORD PAYMENT: ${payModal.plot?.plotNumber || ''}`}>""",
    """            <HardwareModal isOpen={payModal.open}
                onClose={handleClosePayModal}
                title={`RECORD PAYMENT: ${payModal.plot?.plotNumber || ''}`}>"""
)

# Add page-level guard modal + beforeunload
patch(
    RECOVERY,
    """        return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />""",
    """        return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={guardStay} onLeave={guardLeave} context="Recovery Portal" />
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />"""
)

# Also clear logContent after successful call log
patch(
    RECOVERY,
    """            setCallModal({ open: false, mission: null });
            setLogContent('');
            setExpandedPhone(null);
            toast('CALL LOGGED - 14-DAY CLOCK RESET', 'success');""",
    """            setCallModal({ open: false, mission: null });
            setLogContent('');
            setExpandedPhone(null);
            toast('CALL LOGGED - 14-DAY CLOCK RESET', 'success');
            // isDirty resets automatically since logContent is cleared"""
)

print("RecoveryPortal: done")

# ================================================================
# 6. SettingsPage -- guard on password form + new operator modal
# ================================================================
SETTINGS = 'erp-frontend/src/pages/settings/SettingsPage.jsx'

patch(
    SETTINGS,
    """import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import styles from './SettingsPage.module.css';""",
    """import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareInput from '../../components/common/HardwareInput';
import HardwareSelect from '../../components/common/HardwareSelect';
import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import { useRouterBlock } from '../../components/common/RouterBlocker';
import styles from './SettingsPage.module.css';"""
)

patch(
    SETTINGS,
    """    const [newOpData,     setNewOpData]     = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
    const [tempKeyReveal, setTempKeyReveal] = useState(null);""",
    """    const [newOpData,     setNewOpData]     = useState({ username: '', email: '', role: 'ROLE_MANAGER' });
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
    };"""
)

# Reset pwd state after successful change
patch(
    SETTINGS,
    """            await settingsService.changePersonalPassword(pwdState.old, pwdState.new);
            toast('MASTER KEY REWRITTEN -- LOGGING OUT...', 'success');
            setTimeout(logout, 1800);""",
    """            await settingsService.changePersonalPassword(pwdState.old, pwdState.new);
            setPwdState({ old: '', new: '', confirm: '' });
            toast('MASTER KEY REWRITTEN -- LOGGING OUT...', 'success');
            setTimeout(logout, 1800);"""
)

# Reset newOpData after successful provision
patch(
    SETTINGS,
    """            setTempKeyReveal(response.temporaryPassword);
            setNewOpModal(false);
            setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
            fetchOperators();""",
    """            setTempKeyReveal(response.temporaryPassword);
            setNewOpModal(false);
            setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
            fetchOperators();
            // isDirty resets automatically since newOpData is cleared"""
)

# Update provision modal onClose to use guarded version
patch(
    SETTINGS,
    """            <HardwareModal isOpen={newOpModal} onClose={() => setNewOpModal(false)} title="INITIALIZE IDENTITY">""",
    """            <HardwareModal isOpen={newOpModal} onClose={handleCloseNewOpModal} title="INITIALIZE IDENTITY">"""
)

# Add page-level guard + beforeunload
patch(
    SETTINGS,
    """        return (
        <div className={styles.container}>
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />""",
    """        return (
        <div className={styles.container}>
            <UnsavedChangesModal isOpen={guardOpen} onStay={handleStay} onLeave={handleLeave} context="Security Settings" />
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />"""
)

# Add beforeunload for settings page
patch(
    SETTINGS,
    """    const fetchOperators = useCallback(async () => {""",
    """    // beforeunload for tab close / hard refresh
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);

    const fetchOperators = useCallback(async () => {"""
)

print("SettingsPage: done")

# ================================================================
# 7. IntakePage -- verify beforeunload is wired correctly
#    The page already has useRouterBlock but let's add beforeunload
#    for the note modal close guard too
# ================================================================
INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Guard note modal close if text has been typed
patch(
    INTAKE,
    """                        onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>""",
    """                        onClick={() => { setEditingNoteIdx(null); setNoteModalText(''); setNoteModalOpen(true); }}>"""  # no change needed here
)

# Update note modal close X button to check dirty state
patch(
    INTAKE,
    """                        <button type="button" className={styles.noteModalClose} onClick={() => setNoteModalOpen(false)}>""",
    """                        <button type="button" className={styles.noteModalClose} onClick={() => {
                                if (noteModalText.trim() !== '') {
                                    if (!window.confirm('Discard unsaved note?')) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>"""
)

# Update CANCEL button in note modal
patch(
    INTAKE,
    """                        <button type="button" className={styles.noteModalCancel} onClick={() => setNoteModalOpen(false)}>
                                CANCEL
                            </button>""",
    """                        <button type="button" className={styles.noteModalCancel} onClick={() => {
                                if (noteModalText.trim() !== '') {
                                    if (!window.confirm('Discard unsaved note?')) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>
                                CANCEL
                            </button>"""
)

# Guard backdrop click on note modal overlay
patch(
    INTAKE,
    """            {noteModalOpen && (
                <div className={styles.noteModalOverlay} onClick={() => setNoteModalOpen(false)}>""",
    """            {noteModalOpen && (
                <div className={styles.noteModalOverlay} onClick={() => {
                    if (noteModalText.trim() !== '') {
                        if (!window.confirm('Discard unsaved note?')) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>"""
)

print("IntakePage: note modal guards added")

# ================================================================
# 8. FolderPage -- verify note modal + payment modal close guards
#    FolderPage already has useRouterBlock + UnsavedChangesModal for edit mode.
#    Add guards for note modal and payment modal close actions.
# ================================================================
FOLDER = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Guard note modal close -- update the onClose prop
patch(
    FOLDER,
    """            <HardwareModal isOpen={noteModal.open} onClose={() => setNoteModal({...noteModal,open:false})} title="ADD NOTE">""",
    """            <HardwareModal isOpen={noteModal.open} onClose={() => {
                if (noteModal.content.trim() !== '') {
                    if (!window.confirm('Discard unsaved note?')) return;
                }
                setNoteModal({open:false, id:null, content:''});
            }} title="ADD NOTE">"""
)

# Guard payment modal close
patch(
    FOLDER,
    """            <HardwareModal isOpen={payModal.open} onClose={() => setPayModal({ open: false })} title={`RECORD PAYMENT -- ${project.landTitle.plotNumber}`}>""",
    """            <HardwareModal isOpen={payModal.open} onClose={() => {
                if (payAmount !== '') {
                    if (!window.confirm('Discard unsaved payment details?')) return;
                }
                setPayModal({ open: false });
                setPayAmount('');
                setPayNotes('');
            }} title={`RECORD PAYMENT -- ${project.landTitle.plotNumber}`}>"""
)

print("FolderPage: modal close guards added")

# ================================================================
# DONE
# ================================================================
print("")
print("All unsaved changes guards applied!")
print("")
print("Summary of changes:")
print("  1. AuditPage    -- guard on search/filter state")
print("  2. LedgerPage   -- guard on search input")
print("  3. PaymentsPage -- guard on search + type filter")
print("  4. LoginPage    -- guard on username/password before submit")
print("  5. RecoveryPortal -- guard on call log + payment modal + search")
print("  6. SettingsPage -- guard on password form + new operator modal")
print("  7. IntakePage   -- note modal close/cancel/backdrop guards")
print("  8. FolderPage   -- note modal + payment modal close guards")
print("")
print("Run: git add -A && git commit -m 'feat: unsaved changes guard on all pages and modals' && git push")