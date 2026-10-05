// PATH: erp-frontend/src/hooks/useUnsavedChanges.js
import { useEffect, useCallback, useId } from 'react';
import { useBlocker } from 'react-router-dom';
import { setDirty, isLeaving } from '../utils/dirtyRegistry';

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
    const key = useId();
    useEffect(() => { setDirty(key, !!isDirty); return () => setDirty(key, false); }, [key, isDirty]);
    const blocker = useBlocker(
        ({ currentLocation, nextLocation }) =>
            isDirty && currentLocation.pathname !== nextLocation.pathname
    );
    
    // beforeunload — tab close, hard refresh, browser-level back to external
    useEffect(() => {
        if (!isDirty) return;
        const handler = (e) => {
            if (isLeaving()) return;   // the person already confirmed (sign out with unsaved changes)
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
