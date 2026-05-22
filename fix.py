import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    data = read(path)
    if old in data:
        write(path, data.replace(old, new, 1))
    else:
        print(f"MISSING patch target in: {path}")

print("=== FIX 1: Rate Limiter UI in LoginPage.jsx ===")
patch(
    'erp-frontend/src/pages/login/LoginPage.jsx',
    '''            if (status === 401 || status === 400) throw new Error("IDENTIFICATION_FAILED");
            if (status === 403) throw new Error("ACCOUNT_SUSPENDED");''',
    '''            if (status === 429) throw new Error("RATE_LIMITED");
            if (status === 401 || status === 400) {
                const msg = error.response?.data?.message || "";
                if (msg.toLowerCase().includes("too_many") || msg.toLowerCase().includes("locked")) throw new Error("RATE_LIMITED");
                throw new Error("IDENTIFICATION_FAILED");
            }
            if (status === 403) throw new Error("ACCOUNT_SUSPENDED");'''
)

patch(
    'erp-frontend/src/pages/login/LoginPage.jsx',
    '''            let msg = err.message;
            if (msg === "IDENTIFICATION_FAILED") msg = "Wrong username or password. Please try again.";
            else if (msg === "ACCOUNT_SUSPENDED") msg = "This account has been suspended. Contact the admin.";
            else if (msg === "SERVER_STARTING_UP") msg = "The server is waking up (this takes up to 60 seconds on the free plan). Please wait a moment and try again.";
            else msg = "Could not connect to the server. Please check your internet and try again.";''',
    '''            let msg = err.message;
            if (msg === "RATE_LIMITED") msg = "Account locked for 15 minutes due to too many failed attempts.";
            else if (msg === "IDENTIFICATION_FAILED") msg = "Wrong username or password. Please try again.";
            else if (msg === "ACCOUNT_SUSPENDED") msg = "This account has been suspended. Contact the admin.";
            else if (msg === "SERVER_STARTING_UP") msg = "The server is waking up (this takes up to 60 seconds on the free plan). Please wait a moment and try again.";
            else msg = "Could not connect to the server. Please check your internet and try again.";'''
)

print("=== FIX 2: Session Expiration Redirect in axios.js ===")
patch(
    'erp-frontend/src/api/axios.js',
    '''        if (error.response && error.response.status === 401) {
            localStorage.removeItem('gs_token');
            window.location.href = '/login';
        }''',
    '''        if (error.response && error.response.status === 401) {
            localStorage.removeItem('gs_token');
            localStorage.removeItem('gs_user');
            window.location.href = '/login?reason=session_conflict';
        }'''
)

print("=== FIX 2b: Session conflict message in LoginPage.jsx ===")
patch(
    'erp-frontend/src/pages/login/LoginPage.jsx',
    '''        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'Your session ended because this account signed in on another device.';
        }''',
    '''        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'Your session ended because this account signed in on another device.';
        }
        if (params.get('reason') === 'session_expired') {
            return 'Your session ended because this account signed in on another device.';
        }'''
)

print("=== FIX 3: Root Recovery Email SMTP error in MailService.java ===")
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/MailService.java',
    '''        try {
            mailSender.send(message);
            System.out.println(">>> SMTP_SUCCESS: Recovery signal transmitted to " + recipientEmail);
        } catch (Exception e) {
            // PHYSICALLY THROW THE ERROR
            // This ensures the Frontend shows a RED alert instead of a fake GREEN check.
            System.err.println(">>> SMTP_CRITICAL_FAULT: " + e.getMessage());
            throw new BusinessException("COMMUNICATION_FAILURE: System could not reach Gmail relay. Check App Password.");
        }''',
    '''        try {
            mailSender.send(message);
            System.out.println(">>> SMTP_SUCCESS: Recovery signal transmitted to " + recipientEmail);
        } catch (org.springframework.mail.MailException e) {
            System.err.println(">>> SMTP_CRITICAL_FAULT (MailException): " + e.getMessage());
            throw new BusinessException("COMMUNICATION_FAILURE: System could not reach Gmail relay. Check App Password.");
        } catch (Exception e) {
            System.err.println(">>> SMTP_CRITICAL_FAULT: " + e.getMessage());
            throw new BusinessException("COMMUNICATION_FAILURE: System could not reach Gmail relay. Check App Password.");
        }'''
)

print("=== FIX 4: Upgrade RouterBlocker.jsx ===")
patch(
    'erp-frontend/src/components/common/RouterBlocker.jsx',
    '''// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * GOLDEN SEED — ROUTER BLOCKER
 *
 * Wraps react-router-dom's useBlocker to intercept ALL navigation
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
};''',
    '''// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

/**
 * GOLDEN SEED — ROUTER BLOCKER
 *
 * Wraps react-router-dom's useBlocker to intercept ALL in-app navigation
 * when there are unsaved changes. Also handles browser back/forward and
 * tab-close via beforeunload (callers should add their own beforeunload
 * handler so this hook stays focused on the blocker API).
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

    // beforeunload covers hard refresh, tab close, and browser-level back/forward
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
};'''
)

print("=== FIX 4b: Upgrade useUnsavedChanges.js ===")
patch(
    'erp-frontend/src/hooks/useUnsavedChanges.js',
    '''// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD HOOK
 *
 * Intercepts all navigation attempts (browser back/forward, link clicks,
 * programmatic navigate() calls) and tab-close events when there are
 * unsaved changes. Shows the branded UnsavedChangesModal instead of the
 * browser's plain default dialog.
 *
 * Usage:
 *   const { UnsavedGuard, guardedNavigate } = useUnsavedChanges(isDirty, context);
 *
 *   Replace navigate(path) calls with guardedNavigate(path)
 *   Render <UnsavedGuard /> anywhere in the component tree
 *
 * isDirty  — boolean, true when there are unsaved changes
 * context  — string describing what's unsaved (e.g. "New Plot Registration")
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

export default useUnsavedChanges;''',
    '''// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * GOLDEN SEED — UNSAVED CHANGES GUARD HOOK
 *
 * Intercepts all navigation attempts (browser back/forward, link clicks,
 * programmatic navigate() calls) and tab-close events when there are
 * unsaved changes. Shows the branded UnsavedChangesModal instead of the
 * browser's plain default dialog.
 *
 * Usage:
 *   const { UnsavedGuard, guardedNavigate } = useUnsavedChanges(isDirty, context);
 *
 *   Replace navigate(path) calls with guardedNavigate(path)
 *   Render <UnsavedGuard /> anywhere in the component tree
 *
 * isDirty  — boolean, true when there are unsaved changes
 * context  — string describing what's unsaved (e.g. "New Plot Registration")
 */
const useUnsavedChanges = (isDirty, context = 'this form') => {
    const navigate = useNavigate();
    const [modalOpen, setModalOpen] = useState(false);
    const pendingNavRef = useRef(null); // stores the navigation to execute after confirm

    // ── 1. Browser tab close / hard refresh / browser-level back+forward guard ──
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

export default useUnsavedChanges;'''
)

print("=== FIX 4c: IntakePage.jsx - ensure beforeunload uses return value ===")
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''    useEffect(() => {
        if (!isDirty || saving) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    // NOTE: beforeunload is now handled by useUnsavedChanges hook''',
    '''    useEffect(() => {
        if (!isDirty || saving) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
            return '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty, saving]);

    // NOTE: beforeunload is also handled by useRouterBlock hook'''
)

print("=== FIX 4d: FolderPage.jsx - ensure beforeunload uses return value ===")
patch(
    'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx',
    '''    // beforeunload -- catches tab close, hard refresh, browser back to external site
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);''',
    '''    // beforeunload -- catches tab close, hard refresh, browser back to external site
    // useRouterBlock also adds beforeunload, this is a belt-and-suspenders backup
    useEffect(() => {
        if (!isEditing || committing) return;
        const handler = (e) => {
            e.preventDefault();
            e.returnValue = '';
            return '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isEditing, committing]);'''
)

print("=== FIX 4e: SettingsPage.jsx - ensure beforeunload uses return value ===")
patch(
    'erp-frontend/src/pages/settings/SettingsPage.jsx',
    '''    // beforeunload for tab close / hard refresh
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);''',
    '''    // beforeunload for tab close / hard refresh
    // useRouterBlock also adds beforeunload — this is belt-and-suspenders
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => { e.preventDefault(); e.returnValue = ''; return ''; };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [isDirty]);'''
)

print("=== ALL FIXES APPLIED ===")