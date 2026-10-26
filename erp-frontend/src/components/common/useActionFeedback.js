// PATH: erp-frontend/src/components/common/useActionFeedback.js
// A button that makes the person SEE that it worked: while the work runs the phase is 'working' (arrows spin),
// for a moment after it is 'done' (a tick), then 'idle'. The spin lasts at least MIN ms even when the server
// answers at once, so a quick refresh is still seen. If the click handler returns a promise, 'working' waits for it.
import { useState, useRef, useEffect, useCallback } from 'react';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

export default function useActionFeedback(fn, { min = 700, doneMs = 1000 } = {}) {
    const [phase, setPhase] = useState('idle');
    const alive = useRef(true);
    const running = useRef(false);
    useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
    const run = useCallback(async (...args) => {
        if (running.current) return;
        running.current = true;
        setPhase('working');
        const t0 = Date.now();
        try { await Promise.resolve(fn ? fn(...args) : null); } catch { /* the page shows its own error */ }
        await sleep(Math.max(0, min - (Date.now() - t0)));
        running.current = false;
        if (!alive.current) return;
        setPhase('done');
        await sleep(doneMs);
        if (alive.current) setPhase('idle');
    }, [fn, min, doneMs]);
    return [phase, run];
}
