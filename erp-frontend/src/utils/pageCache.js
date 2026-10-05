// PATH: erp-frontend/src/utils/pageCache.js
// fix182 (speed): the last answer of a list page, kept in memory for this tab. Coming back to the Ledger, Clients or
// Recovery then draws at once from what was on screen a moment ago, and the page refreshes it behind the scenes (no
// full-page spinner, no blank table). Nothing is written to the device; signing out or reloading the tab clears it.
// Entries older than MAX_AGE are not shown at all (the page loads normally).
const MAX_AGE = 10 * 60 * 1000;
const store = new Map();

/** The saved answer for this key, or null when there is none or it is too old. */
export function cached(key) {
    const hit = store.get(key);
    if (!hit) return null;
    if (Date.now() - hit.at > MAX_AGE) { store.delete(key); return null; }
    return hit.data;
}

export function remember(key, data) {
    store.set(key, { data, at: Date.now() });
    return data;
}

/** Forget one key, every key starting with a prefix, or (no argument) everything -- e.g. after a save or sign-out. */
export function forget(prefix) {
    if (prefix == null) { store.clear(); return; }
    for (const k of [...store.keys()]) if (k === prefix || k.startsWith(prefix)) store.delete(k);
}
