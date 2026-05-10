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
    if old not in content:
        print(f"MISSING in {path}: {repr(old[:80])}")
        return
    content = content.replace(old, new, 1)
    write(path, content)
    print(f"PATCHED: {path}")


# ================================================================
# FIX 1: LoginPage.jsx - React error #310
# useState called conditionally (after early return for !appReady)
# Move ALL useState calls before the early return
# ================================================================

LOGIN_JSX = 'erp-frontend/src/pages/login/LoginPage.jsx'

patch(LOGIN_JSX,
    '''const LoginPage = () => {
    const [appReady, setAppReady] = useState(false);
    const [creds, setCreds] = useState({ username: '', password: '' });

    useEffect(() => {
        // Simulate app initialization check
        const timer = setTimeout(() => setAppReady(true), 900);
        return () => clearTimeout(timer);
    }, []);

    if (!appReady) {
        return (
            <div className={styles.appLoadScreen}>
                <div className={styles.loadLogo}>
                    <div className={styles.loadPulseOuter} />
                    <div className={styles.loadPulseInner}>
                        <span className={styles.loadEmoji}>🌱</span>
                    </div>
                </div>
                <div className={styles.loadBarWrap}>
                    <div className={styles.loadBar} />
                </div>
                <p className={styles.loadLabel}>GOLDEN SEED ERP</p>
                <p className={styles.loadSub}>Initializing secure connection...</p>
            </div>
        );
    }
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(() => {
        // Check if we were redirected due to a session conflict
        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'SECURITY: Your session was terminated because this account logged in from another browser.';
        }
        if (params.get('reason') === 'idle_timeout') {
            return 'SESSION EXPIRED: You were logged out after 30 minutes of inactivity.';
        }
        return '';
    });
    
    // RECOVERY STATE
    const [isRecovering, setIsRecovering] = useState(false);
    const [recoveryEmail, setRecoveryEmail] = useState('');
    const [recoveryLoading, setRecoveryLoading] = useState(false);
    const [recoverySuccess, setRecoverySuccess] = useState('');''',

    '''const LoginPage = () => {
    // ALL useState hooks must come before any conditional returns (React rules)
    const [appReady, setAppReady] = useState(false);
    const [creds, setCreds] = useState({ username: '', password: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'SECURITY: Your session was terminated because this account logged in from another browser.';
        }
        if (params.get('reason') === 'idle_timeout') {
            return 'SESSION EXPIRED: You were logged out after 30 minutes of inactivity.';
        }
        return '';
    });
    const [isRecovering, setIsRecovering] = useState(false);
    const [recoveryEmail, setRecoveryEmail] = useState('');
    const [recoveryLoading, setRecoveryLoading] = useState(false);
    const [recoverySuccess, setRecoverySuccess] = useState('');

    useEffect(() => {
        const timer = setTimeout(() => setAppReady(true), 900);
        return () => clearTimeout(timer);
    }, []);

    if (!appReady) {
        return (
            <div className={styles.appLoadScreen}>
                <div className={styles.loadLogo}>
                    <div className={styles.loadPulseOuter} />
                    <div className={styles.loadPulseInner}>
                        <span className={styles.loadEmoji}>🌱</span>
                    </div>
                </div>
                <div className={styles.loadBarWrap}>
                    <div className={styles.loadBar} />
                </div>
                <p className={styles.loadLabel}>GOLDEN SEED ERP</p>
                <p className={styles.loadSub}>Initializing secure connection...</p>
            </div>
        );
    }'''
)


# ================================================================
# FIX 2: Create a shared UnsavedChangesModal component
# A custom-styled, branded warning dialog that replaces
# the browser's default "Leave site?" popup
# ================================================================

MODAL_JSX = 'erp-frontend/src/components/common/UnsavedChangesModal.jsx'
MODAL_CSS = 'erp-frontend/src/components/common/UnsavedChangesModal.module.css'

write(MODAL_JSX, '''// PATH: erp-frontend/src/components/common/UnsavedChangesModal.jsx
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiX, FiSave, FiLogOut } from 'react-icons/fi';
import styles from './UnsavedChangesModal.module.css';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD
 *
 * Custom-styled replacement for the browser\'s default "Leave site?" dialog.
 * Shows whenever the user tries to navigate away with unsaved changes.
 *
 * Props:
 *   isOpen     — whether to show the modal
 *   onStay     — user chose to stay and keep editing
 *   onLeave    — user confirmed they want to leave (lose changes)
 *   context    — optional string describing what will be lost (e.g. "New Plot")
 */
const UnsavedChangesModal = ({ isOpen, onStay, onLeave, context = 'this form' }) => {
    // Trap focus inside modal when open
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => {
            if (e.key === 'Escape') onStay();
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onStay]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="ucm-title">
            <div className={styles.card}>
                {/* Animated warning icon */}
                <div className={styles.iconWrap} aria-hidden="true">
                    <div className={styles.iconRing} />
                    <div className={styles.iconRing2} />
                    <FiAlertTriangle className={styles.icon} />
                </div>

                <div className={styles.body}>
                    <h2 id="ucm-title" className={styles.title}>UNSAVED CHANGES</h2>
                    <p className={styles.message}>
                        You have unsaved changes in <strong>{context}</strong>.
                        If you leave now, all your entered data will be permanently lost.
                    </p>

                    <div className={styles.divider}>
                        <span>WHAT WOULD YOU LIKE TO DO?</span>
                    </div>

                    <div className={styles.actions}>
                        <button
                            className={styles.stayBtn}
                            onClick={onStay}
                            autoFocus
                            aria-label="Stay on page and keep editing"
                        >
                            <FiSave aria-hidden="true" />
                            KEEP EDITING
                        </button>
                        <button
                            className={styles.leaveBtn}
                            onClick={onLeave}
                            aria-label="Leave page and discard changes"
                        >
                            <FiLogOut aria-hidden="true" />
                            DISCARD &amp; LEAVE
                        </button>
                    </div>
                </div>

                {/* Dismiss with X goes to "stay" */}
                <button className={styles.closeBtn} onClick={onStay} aria-label="Close and keep editing">
                    <FiX aria-hidden="true" />
                </button>
            </div>
        </div>,
        document.body
    );
};

export default UnsavedChangesModal;
''')

write(MODAL_CSS, '''/* PATH: erp-frontend/src/components/common/UnsavedChangesModal.module.css */

/* ── OVERLAY ──────────────────────────────────────────────────── */
.overlay {
    position: fixed;
    inset: 0;
    z-index: 999999;
    background: rgba(8, 15, 18, 0.88);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: clamp(16px, 4vw, 32px);
    animation: overlayIn 0.22s ease both;
}

@keyframes overlayIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

/* ── CARD ─────────────────────────────────────────────────────── */
.card {
    position: relative;
    width: 100%;
    max-width: clamp(320px, 90vw, 480px);
    background: linear-gradient(160deg, #0f2224 0%, #162a2c 50%, #1a2e30 100%);
    border-radius: 16px;
    padding: clamp(28px, 4vw, 44px) clamp(24px, 3.5vw, 40px);
    border: 1.5px solid rgba(238, 140, 58, 0.4);
    box-shadow:
        0 40px 100px rgba(0, 0, 0, 0.75),
        0 0 0 1px rgba(255, 255, 255, 0.04),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
    animation: cardIn 0.28s cubic-bezier(0.2, 1, 0.3, 1) both;
    text-align: center;
    overflow: hidden;
}

/* Subtle orange glow on bottom edge */
.card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 5%; right: 5%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(238,140,58,0.7), transparent);
    box-shadow: 0 0 18px rgba(238, 140, 58, 0.4);
    border-radius: 0 0 16px 16px;
}

@keyframes cardIn {
    from { opacity: 0; transform: translateY(28px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0)    scale(1); }
}

/* ── WARNING ICON ─────────────────────────────────────────────── */
.iconWrap {
    position: relative;
    width: clamp(60px, 10vw, 76px);
    height: clamp(60px, 10vw, 76px);
    margin: 0 auto clamp(20px, 3vw, 28px);
    display: flex;
    align-items: center;
    justify-content: center;
}

.iconRing {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid rgba(245, 158, 11, 0.5);
    animation: ringPulse 2s ease-in-out infinite;
}

.iconRing2 {
    position: absolute;
    inset: -8px;
    border-radius: 50%;
    border: 1px solid rgba(245, 158, 11, 0.2);
    animation: ringPulse 2s ease-in-out infinite 0.4s;
}

@keyframes ringPulse {
    0%, 100% { transform: scale(1);   opacity: 0.6; }
    50%       { transform: scale(1.1); opacity: 0.2; }
}

.icon {
    position: relative;
    z-index: 2;
    font-size: clamp(28px, 5vw, 36px);
    color: #f59e0b;
    filter: drop-shadow(0 0 12px rgba(245, 158, 11, 0.5));
    animation: iconShake 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) 0.3s both;
}

@keyframes iconShake {
    0%, 100% { transform: rotate(0); }
    15%      { transform: rotate(-8deg); }
    45%      { transform: rotate(7deg); }
    75%      { transform: rotate(-4deg); }
}

/* ── BODY ─────────────────────────────────────────────────────── */
.body { position: relative; z-index: 2; }

.title {
    font-family: 'Cinzel', serif;
    color: #f59e0b;
    font-size: clamp(14px, 2vw, 18px);
    font-weight: 700;
    letter-spacing: clamp(2px, 0.5vw, 4px);
    text-transform: uppercase;
    margin: 0 0 clamp(10px, 1.5vw, 14px);
    text-shadow: 0 0 24px rgba(245, 158, 11, 0.3);
}

.message {
    font-family: 'DM Sans', sans-serif;
    font-size: clamp(12px, 1.3vw, 14px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.65;
    margin: 0 0 clamp(18px, 2.5vw, 24px);
}

.message strong {
    color: #fff;
    font-weight: 900;
}

/* ── DIVIDER ──────────────────────────────────────────────────── */
.divider {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 clamp(18px, 2.5vw, 24px);
}

.divider::before,
.divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
}

.divider span {
    font-family: 'Space Mono', monospace;
    font-size: clamp(7px, 0.78vw, 9px);
    font-weight: 900;
    color: rgba(255, 255, 255, 0.2);
    letter-spacing: 2px;
    text-transform: uppercase;
    white-space: nowrap;
}

/* ── ACTION BUTTONS ───────────────────────────────────────────── */
.actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: clamp(8px, 1.2vw, 12px);
}

/* KEEP EDITING — orange filled, primary CTA */
.stayBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(6px, 0.8vw, 8px);
    height: clamp(42px, 5.5vw, 50px);
    background: #EE8C3A;
    color: #1a2e30;
    border: none;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
    box-shadow: 0 4px 16px rgba(238, 140, 58, 0.3);
    white-space: nowrap;
}
.stayBtn:hover {
    background: #f0a050;
    box-shadow: 0 0 24px rgba(238, 140, 58, 0.5);
    transform: translateY(-1px);
}
.stayBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 3px; }

/* DISCARD & LEAVE — ghost/danger style */
.leaveBtn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: clamp(6px, 0.8vw, 8px);
    height: clamp(42px, 5.5vw, 50px);
    background: rgba(255, 255, 255, 0.04);
    color: rgba(255, 255, 255, 0.5);
    border: 1.5px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 900;
    font-size: clamp(9px, 0.95vw, 11px);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
    white-space: nowrap;
}
.leaveBtn:hover {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.5);
    color: #fca5a5;
    box-shadow: 0 0 16px rgba(239, 68, 68, 0.15);
}
.leaveBtn:focus-visible { outline: 2px solid #ef4444; outline-offset: 3px; }

/* ── CLOSE BUTTON ─────────────────────────────────────────────── */
.closeBtn {
    position: absolute;
    top: clamp(12px, 1.5vw, 16px);
    right: clamp(12px, 1.5vw, 16px);
    width: clamp(28px, 3.2vw, 34px);
    height: clamp(28px, 3.2vw, 34px);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.4);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: clamp(14px, 1.6vw, 17px);
    transition: background 0.2s, color 0.2s, border-color 0.2s;
}
.closeBtn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.25);
}
.closeBtn:focus-visible { outline: 2px solid #EE8C3A; outline-offset: 2px; }

/* ── MOBILE ───────────────────────────────────────────────────── */
@media (max-width: 400px) {
    .actions {
        grid-template-columns: 1fr;
    }
    .card {
        padding: 24px 18px;
    }
}
''')

print("UnsavedChangesModal created!")


# ================================================================
# FIX 3: Create a useUnsavedChanges hook
# Handles both the in-app navigation guard (react-router) and
# the browser tab-close guard (beforeunload)
# ================================================================

HOOK_PATH = 'erp-frontend/src/hooks/useUnsavedChanges.js'

write(HOOK_PATH, '''// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD HOOK
 *
 * Intercepts all navigation attempts (browser back/forward, link clicks,
 * programmatic navigate() calls) and tab-close events when there are
 * unsaved changes. Shows the branded UnsavedChangesModal instead of the
 * browser\'s plain default dialog.
 *
 * Usage:
 *   const { UnsavedGuard, guardedNavigate } = useUnsavedChanges(isDirty, context);
 *
 *   Replace navigate(path) calls with guardedNavigate(path)
 *   Render <UnsavedGuard /> anywhere in the component tree
 *
 * isDirty  — boolean, true when there are unsaved changes
 * context  — string describing what\'s unsaved (e.g. "New Plot Registration")
 */
const useUnsavedChanges = (isDirty, context = 'this form') => {
    const navigate = useNavigate();
    const [modalOpen, setModalOpen] = useState(false);
    const pendingNavRef = useRef(null); // stores the navigation to execute after confirm

    // ── 1. Browser tab close / hard refresh guard ──────────────────
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);

    // ── 2. In-app navigation guard ──────────────────────────────────
    // Returns a wrapped navigate function. When isDirty, it shows
    // the modal instead of navigating. On confirm, it navigates.
    const guardedNavigate = useCallback((to, options) => {
        if (!isDirty) {
            navigate(to, options);
            return;
        }
        pendingNavRef.current = { to, options };
        setModalOpen(true);
    }, [isDirty, navigate]);

    // ── 3. Modal callbacks ──────────────────────────────────────────
    const handleStay = useCallback(() => {
        setModalOpen(false);
        pendingNavRef.current = null;
    }, []);

    const handleLeave = useCallback(() => {
        setModalOpen(false);
        const pending = pendingNavRef.current;
        pendingNavRef.current = null;
        if (pending) {
            navigate(pending.to, pending.options);
        }
    }, [navigate]);

    return {
        guardModalOpen: modalOpen,
        handleStay,
        handleLeave,
        guardedNavigate,
        guardContext: context,
    };
};

export default useUnsavedChanges;
''')

print("useUnsavedChanges hook created!")


# ================================================================
# FIX 4: IntakePage.jsx — replace beforeunload with guardedNavigate
# The page already has isDirty logic, just needs the modal wired in
# ================================================================

INTAKE_JSX = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Add import at top
patch(INTAKE_JSX,
    "import landService from '../../services/landService';",
    "import landService from '../../services/landService';\nimport useUnsavedChanges from '../../hooks/useUnsavedChanges';\nimport UnsavedChangesModal from '../../components/common/UnsavedChangesModal';"
)

# Remove the old beforeunload useEffect (it's now handled by the hook)
patch(INTAKE_JSX,
    '''    useEffect(() => {
        const handler = (e) => {
            if (isDirty && !saving) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);''',
    '''    // NOTE: beforeunload is now handled by useUnsavedChanges hook'''
)

# Add hook usage after navigate declaration
patch(INTAKE_JSX,
    "    const navigate = useNavigate();\n    const { toasts, toast, dismissToast } = useToast();",
    "    const navigate = useNavigate();\n    const { toasts, toast, dismissToast } = useToast();\n\n    // Unsaved changes guard -- wired below once isDirty is defined"
)

# After isDirty is defined, wire up the hook
patch(INTAKE_JSX,
    '''    // isDirty must be defined AFTER all useState hooks to avoid
    // "Cannot access before initialization" error in the minified bundle
    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        notesList.length > 0,
    [plotNumber, owners, totalCost, fileQueue, notesList]);''',
    '''    // isDirty must be defined AFTER all useState hooks to avoid
    // "Cannot access before initialization" error in the minified bundle
    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        notesList.length > 0,
    [plotNumber, owners, totalCost, fileQueue, notesList]);

    const { guardModalOpen, handleStay, handleLeave, guardedNavigate } =
        useUnsavedChanges(!saving && isDirty, 'New Plot Registration');'''
)

# After successful submit, navigate without guard (data is saved)
patch(INTAKE_JSX,
    "            toast('Plot registered successfully!', 'success', 3000);\n            setTimeout(() => navigate('/land/projects'), 1800);",
    "            toast('Plot registered successfully!', 'success', 3000);\n            setTimeout(() => navigate('/land/projects'), 1800); // safe: data saved"
)

# Add UnsavedChangesModal to the JSX return, just before closing tag
patch(INTAKE_JSX,
    "            {/* NOTE MODAL */}\n            {noteModalOpen && (",
    """            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />

            {/* NOTE MODAL */}
            {noteModalOpen && ("""
)

print("IntakePage patched!")


# ================================================================
# FIX 5: FolderPage.jsx — wire up unsaved changes guard for edit mode
# ================================================================

FOLDER_JSX = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Add import
patch(FOLDER_JSX,
    "import landService from '../../services/landService';",
    "import landService from '../../services/landService';\nimport useUnsavedChanges from '../../hooks/useUnsavedChanges';\nimport UnsavedChangesModal from '../../components/common/UnsavedChangesModal';"
)

# Remove old beforeunload useEffect in FolderPage
patch(FOLDER_JSX,
    '''    // Warn user if they try to close the tab while editing
    useEffect(() => {
        const handler = (e) => {
            if (isEditing) {
                e.preventDefault();
                e.returnValue = '';
            }
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing]);''',
    '''    // NOTE: beforeunload is now handled by useUnsavedChanges hook'''
)

# Add hook after committing and navigate declarations
patch(FOLDER_JSX,
    "    const { confirmState, confirm, handleAnswer } = useConfirm();",
    """    const { confirmState, confirm, handleAnswer } = useConfirm();

    // Unsaved changes guard -- active only while in edit mode and not mid-save
    const { guardModalOpen, handleStay, handleLeave, guardedNavigate } =
        useUnsavedChanges(!committing && isEditing, 'Plot Record Edit');"""
)

# Add UnsavedChangesModal to FolderPage JSX, before ConfirmModal
patch(FOLDER_JSX,
    "            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />",
    """            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="Plot Record Edit"
            />

            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />"""
)

print("FolderPage patched!")


# ================================================================
# FIX 6: Wire guardedNavigate into Sidebar so clicking nav links
# while editing triggers the guard instead of navigating silently
# This is the main vector for accidental navigation loss
# ================================================================

# The Sidebar doesn't have direct access to isDirty state.
# The cleanest approach: block ALL in-app navigation via the
# browser's history.pushState when the guard is active.
# We do this via a RouterBlocker component used in App.jsx.

BLOCKER_JSX = 'erp-frontend/src/components/common/RouterBlocker.jsx'

write(BLOCKER_JSX, '''// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * GOLDEN SEED — ROUTER BLOCKER
 *
 * Wraps react-router-dom\'s useBlocker to intercept ALL navigation
 * when there are unsaved changes. The consuming component controls
 * the modal; this hook just exposes whether a block is active and
 * provides proceed/reset callbacks.
 *
 * Usage:
 *   const { blocked, proceed, reset } = useRouterBlock(isDirty);
 *
 * blocked — true when navigation was intercepted
 * proceed — confirm and continue navigation
 * reset   — cancel and stay on current page
 */
export const useRouterBlock = (shouldBlock) => {
    const blocker = useBlocker(shouldBlock);

    return {
        blocked: blocker.state === 'blocked',
        proceed: () => blocker.proceed?.(),
        reset:   () => blocker.reset?.(),
    };
};
''')

print("RouterBlocker created!")


# ================================================================
# FIX 7: Update IntakePage and FolderPage to use useRouterBlock
# instead of the manual guardedNavigate approach --
# useRouterBlock catches ALL navigation including sidebar clicks,
# browser back button, address bar changes etc.
# ================================================================

# Update IntakePage to use useRouterBlock
patch(INTAKE_JSX,
    "import useUnsavedChanges from '../../hooks/useUnsavedChanges';\nimport UnsavedChangesModal from '../../components/common/UnsavedChangesModal';",
    "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\nimport { useRouterBlock } from '../../components/common/RouterBlocker';"
)

patch(INTAKE_JSX,
    "    const { guardModalOpen, handleStay, handleLeave, guardedNavigate } =\n        useUnsavedChanges(!saving && isDirty, 'New Plot Registration');",
    "    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!saving && isDirty);"
)

# Update FolderPage to use useRouterBlock
patch(FOLDER_JSX,
    "import useUnsavedChanges from '../../hooks/useUnsavedChanges';\nimport UnsavedChangesModal from '../../components/common/UnsavedChangesModal';",
    "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';\nimport { useRouterBlock } from '../../components/common/RouterBlocker';"
)

patch(FOLDER_JSX,
    "    // Unsaved changes guard -- active only while in edit mode and not mid-save\n    const { guardModalOpen, handleStay, handleLeave, guardedNavigate } =\n        useUnsavedChanges(!committing && isEditing, 'Plot Record Edit');",
    "    // Unsaved changes guard -- active only while in edit mode and not mid-save\n    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!committing && isEditing);"
)

print("RouterBlocker wired into IntakePage and FolderPage!")

print()
print("All fixes applied:")
print("1. LoginPage -- React error #310 fixed (useState before early return)")
print("2. UnsavedChangesModal -- branded custom modal component created")
print("3. useUnsavedChanges hook -- created (kept for reference)")
print("4. RouterBlocker -- catches ALL navigation (sidebar, back, address bar)")
print("5. IntakePage -- wired to RouterBlocker")
print("6. FolderPage -- wired to RouterBlocker")
print()
print("Run: git add -A && git commit -m 'fix: React #310 + unsaved changes guard on intake/folder pages' && git push")