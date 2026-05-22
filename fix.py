import os, re

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old in content:
        write_file(path, content.replace(old, new, 1))
        print(f'OK: {label}')
    else:
        print(f'MISSING: {label}')

# ─────────────────────────────────────────────
# 1. useUnsavedChanges.js — ensure strict useBlocker + beforeunload
# ─────────────────────────────────────────────
USE_UNSAVED_PATH = 'erp-frontend/src/hooks/useUnsavedChanges.js'

NEW_USE_UNSAVED = '''// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD HOOK (STRICT)
 *
 * Intercepts ALL navigation: React Router links, browser back/forward,
 * tab close, and hard refresh when isDirty is true.
 *
 * Usage:
 *   const { guardModalOpen, handleStay, handleLeave, guardedNavigate } =
 *     useUnsavedChanges(isDirty, context);
 */
const useUnsavedChanges = (isDirty, context = 'this form') => {
    const blocker = useBlocker(
        ({ currentLocation, nextLocation }) =>
            isDirty && currentLocation.pathname !== nextLocation.pathname
    );

    // beforeunload — tab close, hard refresh, browser-level back to external
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
            return '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);

    const handleStay = useCallback(() => {
        if (blocker.state === 'blocked') blocker.reset?.();
    }, [blocker]);

    const handleLeave = useCallback(() => {
        if (blocker.state === 'blocked') blocker.proceed?.();
    }, [blocker]);

    return {
        guardModalOpen: blocker.state === 'blocked',
        handleStay,
        handleLeave,
        guardContext: context,
    };
};

export default useUnsavedChanges;
'''

write_file(USE_UNSAVED_PATH, NEW_USE_UNSAVED)
print('OK: useUnsavedChanges.js rewritten')

# ─────────────────────────────────────────────
# 2. RouterBlocker.jsx — keep as-is (already correct), just verify
# ─────────────────────────────────────────────
ROUTER_BLOCKER_PATH = 'erp-frontend/src/components/common/RouterBlocker.jsx'

NEW_ROUTER_BLOCKER = '''// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * GOLDEN SEED — ROUTER BLOCKER
 *
 * Wraps react-router-dom useBlocker.
 * Returns { blocked, proceed, reset } for use with UnsavedChangesModal.
 */
export const useRouterBlock = (shouldBlock) => {
    const blocker = useBlocker(
        ({ currentLocation, nextLocation }) =>
            shouldBlock && currentLocation.pathname !== nextLocation.pathname
    );

    useEffect(() => {
        if (!shouldBlock) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [shouldBlock]);

    return {
        blocked: blocker.state === 'blocked',
        proceed: () => blocker.proceed?.(),
        reset:   () => blocker.reset?.(),
    };
};
'''

write_file(ROUTER_BLOCKER_PATH, NEW_ROUTER_BLOCKER)
print('OK: RouterBlocker.jsx rewritten')

# ─────────────────────────────────────────────
# 3. IntakePage.jsx
#    a) isDirty: any single character typed = dirty
#    b) Remove window.confirm() calls, replace with useIntakeConfirm hook
# ─────────────────────────────────────────────
INTAKE_PATH = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# 3a — Replace isDirty logic (too lenient → any change = dirty)
OLD_IS_DIRTY = '''    const isDirty = React.useMemo(() => {
        const hasPlot    = plotNumber.trim() !== '';
        const hasOwner   = owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '');
        const hasCost    = totalCost !== '';
        const hasFiles   = fileQueue.length > 0;
        const hasNotes   = notesList.length > 0;
        // Require at least plotNumber PLUS one other meaningful field
        return hasPlot && (hasOwner || hasCost || hasFiles || hasNotes);
    }, [plotNumber, owners, totalCost, fileQueue, notesList]);'''

NEW_IS_DIRTY = '''    // Any single character entered in any field makes the form dirty
    const isDirty = React.useMemo(() => {
        if (plotNumber !== '') return true;
        if (district !== '') return true;
        if (county !== '') return true;
        if (blockRoad !== '') return true;
        if (physicalBoxNumber !== '') return true;
        if (volume !== '') return true;
        if (folio !== '') return true;
        if (instrumentNo !== '') return true;
        if (totalCost !== '') return true;
        if (initialPayment !== '') return true;
        if (monthlyStorageFee !== '50000') return true;
        if (initialStorageFee !== '') return true;
        if (fileQueue.length > 0) return true;
        if (notesList.length > 0) return true;
        if (owners.some(o =>
            o.fullName !== '' || o.phone !== '' || o.email !== '' ||
            o.nationalId !== '' || o.address !== ''
        )) return true;
        return false;
    }, [plotNumber, district, county, blockRoad, physicalBoxNumber,
        volume, folio, instrumentNo, totalCost, initialPayment,
        monthlyStorageFee, initialStorageFee, fileQueue, notesList, owners]);'''

patch(INTAKE_PATH, OLD_IS_DIRTY, NEW_IS_DIRTY, 'IntakePage isDirty — hyper-strict')

# 3b — Remove window.confirm in note modal close (overlay onClick)
OLD_NOTE_OVERLAY_CLOSE = '''                    onClick={async () => {
                    if (noteModalText.trim() !== '') {
                        const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                        if (!ok) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>'''

NEW_NOTE_OVERLAY_CLOSE = '''                    onClick={async () => {
                    if (noteModalText.trim() !== '') {
                        const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');
                        if (!ok) return;
                    }
                    setNoteModalOpen(false);
                    setNoteModalText('');
                }}>'''

patch(INTAKE_PATH, OLD_NOTE_OVERLAY_CLOSE, NEW_NOTE_OVERLAY_CLOSE, 'IntakePage note overlay close — uses confirmNote')

# 3c — Remove window.confirm in note modal X button
OLD_NOTE_X_CLOSE = '''                            <button type="button" className={styles.noteModalClose} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''

NEW_NOTE_X_CLOSE = '''                            <button type="button" className={styles.noteModalClose} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''

patch(INTAKE_PATH, OLD_NOTE_X_CLOSE, NEW_NOTE_X_CLOSE, 'IntakePage note X-button close — uses confirmNote')

# 3d — Remove window.confirm in note modal CANCEL button
OLD_NOTE_CANCEL = '''                            <button type="button" className={styles.noteModalCancel} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?', 'warn');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''

NEW_NOTE_CANCEL = '''                            <button type="button" className={styles.noteModalCancel} onClick={async () => {
                                if (noteModalText.trim() !== '') {
                                    const ok = await confirmNote('DISCARD NOTE', 'This note has unsaved content. Discard it?');
                                    if (!ok) return;
                                }
                                setNoteModalOpen(false);
                                setNoteModalText('');
                            }}>'''

patch(INTAKE_PATH, OLD_NOTE_CANCEL, NEW_NOTE_CANCEL, 'IntakePage note Cancel button — uses confirmNote')

# ─────────────────────────────────────────────
# 4. FolderPage.jsx — remove window.confirm calls
# ─────────────────────────────────────────────
FOLDER_PATH = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# 4a — handleCloseCallModal uses window.confirm — but FolderPage doesn't have
# window.confirm; it already uses the useConfirm hook. Check for any stragglers.

# The RecoveryPortal uses window.confirm in handleCloseCallModal
RECOVERY_PATH = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

OLD_RECOVERY_CLOSE = '''    const handleCloseCallModal = () => {
        if (callDirty && !window.confirm('Discard unsaved call log?')) return;
        setCallModal({ open: false, mission: null });
        setLogContent('');
    };'''

NEW_RECOVERY_CLOSE = '''    const [discardModalOpen, setDiscardModalOpen] = React.useState(false);
    const [pendingClose, setPendingClose] = React.useState(false);

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
    };'''

patch(RECOVERY_PATH, OLD_RECOVERY_CLOSE, NEW_RECOVERY_CLOSE, 'RecoveryPortal — remove window.confirm from handleCloseCallModal')

# 4b — Add React import if not present (it's already imported), add discard modal JSX
OLD_RECOVERY_MODAL_JSX = '''            {/* CALL LOG MODAL */}
            <HardwareModal isOpen={callModal.open} onClose={handleCloseCallModal}'''

NEW_RECOVERY_MODAL_JSX = '''            {/* DISCARD CONFIRM MODAL */}
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
            <HardwareModal isOpen={callModal.open} onClose={handleCloseCallModal}'''

patch(RECOVERY_PATH, OLD_RECOVERY_MODAL_JSX, NEW_RECOVERY_MODAL_JSX, 'RecoveryPortal — add custom discard confirm modal JSX')

# Also need to add React to the import if missing — it's already there via useState
# Add React.useState reference fix — the component uses useState not React.useState
OLD_RECOVERY_STATE = '''    const [discardModalOpen, setDiscardModalOpen] = React.useState(false);
    const [pendingClose, setPendingClose] = React.useState(false);'''

NEW_RECOVERY_STATE = '''    const [discardModalOpen, setDiscardModalOpen] = useState(false);
    const [pendingClose, setPendingClose] = useState(false);'''

patch(RECOVERY_PATH, OLD_RECOVERY_STATE, NEW_RECOVERY_STATE, 'RecoveryPortal — fix React.useState to useState')

# 4c — SettingsPage.jsx uses window.confirm in handleCloseNewOpModal
SETTINGS_PATH = 'erp-frontend/src/pages/settings/SettingsPage.jsx'

OLD_SETTINGS_CONFIRM = '''    const handleCloseNewOpModal = () => {
        if (newOpDirty) {
            if (!window.confirm('Discard new operator details?')) return;
        }
        setNewOpModal(false);
        setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
    };'''

NEW_SETTINGS_CONFIRM = '''    const handleCloseNewOpModal = async () => {
        if (newOpDirty) {
            const ok = await confirm('DISCARD CHANGES', 'Discard new operator details?', 'warn');
            if (!ok) return;
        }
        setNewOpModal(false);
        setNewOpData({ username: '', email: '', role: 'ROLE_MANAGER' });
    };'''

patch(SETTINGS_PATH, OLD_SETTINGS_CONFIRM, NEW_SETTINGS_CONFIRM, 'SettingsPage — remove window.confirm from handleCloseNewOpModal')

print('\nAll patches applied.')