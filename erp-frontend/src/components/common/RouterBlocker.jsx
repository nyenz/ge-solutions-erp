// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
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
};
