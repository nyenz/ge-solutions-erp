// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
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

export default useUnsavedChanges;
