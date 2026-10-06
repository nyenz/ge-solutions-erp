// PATH: erp-frontend/src/hooks/useEntryMemory.js
// fix188: where the data entry helpers get their memory from.
//   places = every location used by past projects      (from the Ledger list)
//   people = the known clients                          (from the Client list)
// RANK RULE: the lists are asked for ONLY when the signed-in person may open those pages anyway (Secretary and above).
// An Employee gets empty lists, so no suggestion can show them a client or a project they are not allowed to see.
// The answers are shared with the Ledger and Client pages through utils/pageCache.js (no second download when one of
// those pages was open in the last 10 minutes). A failed load simply means "no suggestions"; the form still works.
import { useEffect, useMemo, useState } from 'react';
import landService from '../services/landService';
import recoveryService from '../services/recoveryService';
import { cached, remember } from '../utils/pageCache';
import { roleFlags } from '../utils/roles';
import { useAuth } from './useAuth';
import { buildPlaces, buildPeople } from '../utils/entryMemory';

async function loadProjects() {
    const hit = cached('ledger');
    if (hit) return hit;
    const all = [];
    const seen = new Set();
    for (let p = 0; p < 20; p += 1) {
        const data = await landService.getGlobalLedger(p, 500);
        const rows = (data && data.content) || [];
        rows.forEach(r => { if (!seen.has(r.id)) { seen.add(r.id); all.push(r); } });
        if (rows.length < 500 || (data && data.last)) break;
    }
    return remember('ledger', all);
}

async function loadClients() {
    const hit = cached('clients');
    if (hit) return hit;
    return remember('clients', (await recoveryService.getClientLedger()) || []);
}

export default function useEntryMemory({ wantPlaces = true, wantPeople = true } = {}) {
    const { user } = useAuth();
    const allowed = roleFlags(user).isStaff;
    const [projects, setProjects] = useState(() => (allowed && wantPlaces ? cached('ledger') : null) || []);
    const [clients, setClients] = useState(() => (allowed && wantPeople ? cached('clients') : null) || []);

    useEffect(() => {
        if (!allowed) return undefined;
        let alive = true;
        if (wantPlaces) loadProjects().then(d => { if (alive) setProjects(d || []); }).catch(() => { /* no suggestions */ });
        if (wantPeople) loadClients().then(d => { if (alive) setClients(d || []); }).catch(() => { /* no suggestions */ });
        return () => { alive = false; };
    }, [allowed, wantPlaces, wantPeople]);

    // Pending entries are not in any list an office page shows as real data; they do not teach the helpers either.
    const places = useMemo(() => buildPlaces((projects || []).filter(p => p && !p.pending)), [projects]);
    const people = useMemo(() => buildPeople(clients), [clients]);
    return { places, people, allowed };
}
