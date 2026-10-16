// PATH: erp-frontend/src/utils/typeAhead.js
// fix210 (David): "type the first letter and the list jumps to the words with that letter". Every pick-list in the app
// uses this one helper, so they all behave the same way, like a normal select box:
//  - typing "d" jumps to the first item starting with D; typing "d" again moves to the NEXT item starting with D;
//  - typing quickly ("de") matches "Deed Plan" by its first letters; a pause of 0.8 s starts a new search.
import { useCallback, useRef } from 'react';

const RESET_MS = 800;

const norm = (s) => String(s == null ? '' : s).toLowerCase().replace(/\s+/g, ' ').trimStart();

/**
 * The index of the item that matches query, searching from just after `from` and wrapping round; -1 when none does.
 * When the query is one letter repeated ("ddd"), it cycles through the items starting with that letter.
 */
export function findTypeAhead(labels, query, from = -1) {
    const list = labels || [];
    const q = norm(query);
    if (!q || !list.length) return -1;
    const repeated = q.length > 1 && q.split('').every(ch => ch === q[0]);
    const needle = repeated ? q[0] : q;
    // a longer query keeps the current item if it still matches; a single letter moves on to the next match
    const start = needle.length > 1 ? Math.max(0, from) : from + 1;
    for (let k = 0; k < list.length; k++) {
        const i = (start + k + list.length) % list.length;
        if (norm(list[i]).startsWith(needle)) return i;
    }
    return -1;
}

/** true for a key press that should feed the search (a letter, digit or sign; no Ctrl/Alt/Meta) */
export function isTypeAheadKey(e, searching = false) {
    if (!e || e.ctrlKey || e.metaKey || e.altKey) return false;
    if (typeof e.key !== 'string' || e.key.length !== 1) return false;
    if (e.key === ' ') return searching;   // a space only counts in the middle of a word ("deed p")
    return true;
}

/** React hook: returns (event, labels, currentIndex) => matched index or -1 (the event is used only when it matches). */
export function useTypeAhead() {
    const buf = useRef('');
    const at = useRef(0);
    return useCallback((e, labels, current = -1) => {
        const now = Date.now();
        if (now - at.current > RESET_MS) buf.current = '';
        if (!isTypeAheadKey(e, buf.current.length > 0)) return -1;
        at.current = now;
        buf.current += e.key;
        return findTypeAhead(labels, buf.current, current);
    }, []);
}
