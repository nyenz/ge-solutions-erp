// PATH: erp-frontend/src/components/common/RouterBlocker.jsx
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
};
