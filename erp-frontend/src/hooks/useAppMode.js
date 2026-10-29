// PATH: erp-frontend/src/hooks/useAppMode.js
// fix278: asks the server once whether this is the practice (DEMO) copy or the real one.
// demo = true  -> the header shows a DEMO strip and Settings offers FRESH START.
// demo = false -> the real app: no strip, no FRESH START. While unknown (or if the server does not answer) demo is false,
// so the real app is never shown as a demo by mistake.
import { useEffect, useState } from 'react';
import api from '../api/axios';

let cached = null;      // 'true' | 'false' once known
let pending = null;

function load() {
    if (!pending) {
        pending = api.get('/auth/health')
            .then(r => { cached = String(r?.data?.demo) === 'true'; return cached; })
            .catch(() => { pending = null; return false; });
    }
    return pending;
}

export default function useAppMode() {
    const [demo, setDemo] = useState(cached === true);
    useEffect(() => {
        let alive = true;
        if (cached !== null) return undefined;   // already known: the first render used it
        load().then(v => { if (alive) setDemo(v === true); });
        return () => { alive = false; };
    }, []);
    return { demo };
}
