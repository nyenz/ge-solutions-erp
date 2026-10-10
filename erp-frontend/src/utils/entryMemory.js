// PATH: erp-frontend/src/utils/entryMemory.js
// fix188: DATA ENTRY HELPERS -- the app remembers what was typed before and offers it again, so staff type less
// and spell places and names the same way every time. These are the plain rules (no screen code); the box that
// shows the suggestions is components/common/SuggestInput.jsx and the data comes from hooks/useEntryMemory.js.
//
// THREE PROMISES:
//   1. A suggestion is only ever an OFFER. Nothing is filled in until the person picks it. Typing is never changed.
//   2. A suggestion is built only from lists the signed-in person may already open (the Ledger, the Client list).
//      A rank that cannot open those lists gets no suggestions.
//   3. It is fast: the lists are worked out once and each lookup is a short loop over a small array.

export const PLACE_FIELDS = ['district', 'county', 'subCounty', 'parish', 'village'];
const PLACE_LABEL = { district: 'District', county: 'County', subCounty: 'Sub-county', parish: 'Parish', village: 'Village' };

/** One way of writing a value for comparing: trimmed, single spaces, capitals (the form saves places in capitals). */
export const norm = (v) => String(v == null ? '' : v).trim().replace(/\s+/g, ' ').toUpperCase();

/** Every different place (district ... village) used by past projects, with how many projects use it. */
export function buildPlaces(projects) {
    const map = new Map();
    for (const p of (projects || [])) {
        if (!p) continue;
        const row = {};
        let any = false;
        for (const f of PLACE_FIELDS) { row[f] = norm(p[f]); if (row[f]) any = true; }
        if (!any) continue;
        const key = PLACE_FIELDS.map(f => row[f]).join('|');
        const hit = map.get(key);
        if (hit) hit.count += 1; else map.set(key, { ...row, count: 1 });
    }
    return [...map.values()];
}

/** How well `value` answers what was typed: 0 = starts with it, 1 = a later word starts with it, 2 = contains it, -1 = no. */
export function matchRank(value, typed) {
    const v = norm(value), t = norm(typed);
    if (!v) return -1;
    if (!t) return 0;
    if (v.startsWith(t)) return 0;
    if (v.split(/[\s/-]+/).some(w => w.startsWith(t))) return 1;
    if (v.includes(t)) return 2;
    return -1;
}

/**
 * Suggestions for ONE location field.
 *   places  = buildPlaces(...)      field = 'village' | 'parish' | ...      typed = what is in the box now
 *   context = the other location boxes ({ district, county, ... }); a box that is already filled narrows the list
 * Each suggestion: { key, value, detail, fill, count }
 *   fill = the OTHER location fields, only when every past project with this value agrees on them
 *          (typing a village then offers its parish, sub-county, county and district in one pick).
 */
export function suggestPlace(places, field, typed, context = {}, limit = 8) {
    if (!PLACE_FIELDS.includes(field)) return [];
    const groups = new Map();
    for (const pl of (places || [])) {
        const value = pl[field];
        const rank = matchRank(value, typed);
        if (rank < 0) continue;
        // a parent box that is filled must agree (a village typed while District says JINJA only offers Jinja's villages)
        let ok = true;
        for (const f of PLACE_FIELDS) {
            if (f === field) continue;
            const want = norm(context[f]);
            if (want && pl[f] && pl[f] !== want) { ok = false; break; }
        }
        if (!ok) continue;
        const g = groups.get(value) || { value, rank, count: 0, rows: [] };
        g.count += pl.count; g.rows.push(pl); g.rank = Math.min(g.rank, rank);
        groups.set(value, g);
    }
    const out = [];
    for (const g of groups.values()) {
        const fill = {};
        for (const f of PLACE_FIELDS) {
            if (f === field) continue;
            const seen = new Set(g.rows.map(r => r[f]).filter(Boolean));
            if (seen.size === 1) fill[f] = [...seen][0];
        }
        const detail = PLACE_FIELDS.filter(f => f !== field && fill[f]).map(f => fill[f]).reverse().join(' / ');
        out.push({ key: field + ':' + g.value, value: g.value, detail, fill, count: g.count, rank: g.rank });
    }
    out.sort((a, b) => a.rank - b.rank || b.count - a.count || a.value.localeCompare(b.value));
    // an exact match with nothing more to offer is not worth a list
    const t = norm(typed);
    const useful = out.filter(s => !(s.value === t && PLACE_FIELDS.every(f => f === field || !s.fill[f] || norm(context[f]) === s.fill[f])));
    return useful.slice(0, limit);
}

/** Classic edit distance (how many single letters differ), stopped early when it passes `max`. */
export function editDistance(a, b, max = 3) {
    const s = norm(a), t = norm(b);
    if (s === t) return 0;
    if (Math.abs(s.length - t.length) > max) return max + 1;
    let prev = Array.from({ length: t.length + 1 }, (_, i) => i);
    for (let i = 1; i <= s.length; i += 1) {
        const cur = [i];
        let best = i;
        for (let j = 1; j <= t.length; j += 1) {
            const v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (s[i - 1] === t[j - 1] ? 0 : 1));
            cur.push(v); if (v < best) best = v;
        }
        if (best > max) return max + 1;
        prev = cur;
    }
    return prev[t.length];
}

/**
 * A LIKELY TYPO: the typed word is not a known value, but it is one or two letters away from one that is used often.
 * Returns that known value ("did you mean NAMULESA?") or null. Short words are left alone (too many false alarms).
 */
export function nearMiss(knownValues, typed) {
    const t = norm(typed);
    if (t.length < 5) return null;
    const known = new Map();
    for (const k of (knownValues || [])) { const v = typeof k === 'string' ? norm(k) : norm(k.value); const c = typeof k === 'string' ? 1 : (k.count || 1); if (v) known.set(v, (known.get(v) || 0) + c); }
    if (known.has(t)) return null;
    const max = t.length >= 8 ? 2 : 1;
    let best = null;
    for (const [v, count] of known) {
        const d = editDistance(v, t, max);
        if (d > max) continue;
        if (!best || d < best.d || (d === best.d && count > best.count)) best = { value: v, d, count };
    }
    return best ? best.value : null;
}

/** All the values one location field has, with counts (for nearMiss). */
export function placeValues(places, field) {
    const m = new Map();
    for (const pl of (places || [])) { const v = pl[field]; if (v) m.set(v, (m.get(v) || 0) + pl.count); }
    return [...m.entries()].map(([value, count]) => ({ value, count }));
}

const digits = (v) => String(v == null ? '' : v).replace(/\D+/g, '');

/** The people of the Client list as plain rows: { id, name, nin, phone, email }. One row per National ID. */
export function buildPeople(clientRows) {
    const seen = new Set();
    const out = [];
    for (const c of (clientRows || [])) {
        if (!c) continue;
        const nin = norm(c.nin ?? c.nationalId);
        const name = norm(c.name ?? c.fullName);
        if (!nin && !name) continue;
        const key = nin || name;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push({ id: c.id, name, nin, phone: String(c.phone ?? c.phoneNumber ?? '').trim(), email: String(c.email ?? '').trim() });
    }
    return out;
}

/**
 * Known people for a name, National ID or phone box. At least 3 characters must be typed (2 for a National ID), so a
 * single letter never lists half the client register.
 * Each suggestion: { key, value, detail, person }
 */
export function suggestPeople(people, field, typed, limit = 6) {
    const raw = String(typed == null ? '' : typed).trim();
    const out = [];
    if (field === 'phone') {
        const d = digits(raw).replace(/^(256|0)/, '');
        if (d.length < 4) return [];
        for (const p of (people || [])) if (digits(p.phone).includes(d)) out.push({ rank: 0, p });
    } else if (field === 'nationalId') {
        const t = norm(raw);
        if (t.length < 2) return [];
        for (const p of (people || [])) { if (p.nin && p.nin.startsWith(t)) out.push({ rank: 0, p }); else if (t.length >= 4 && p.nin && p.nin.includes(t)) out.push({ rank: 1, p }); }
    } else {
        if (norm(raw).length < 3) return [];
        for (const p of (people || [])) { const r = matchRank(p.name, raw); if (r >= 0) out.push({ rank: r, p }); }
    }
    out.sort((a, b) => a.rank - b.rank || a.p.name.localeCompare(b.p.name));
    return out.slice(0, limit).map(({ p }) => personSuggestion(p, field));
}

const personSuggestion = (p, field) => ({
    key: 'person:' + (p.nin || p.name),
    value: field === 'phone' ? p.phone : field === 'nationalId' ? p.nin : p.name,
    label: p.name || p.nin,
    detail: [p.nin, p.phone].filter(Boolean).join('  -  '),
    person: p,
});

/**
 * fix199 (David, test note 20): suggestions for one box of a client / owner ROW, using the boxes already filled.
 * Before, a filled NIN made the name box hide that very person. Now the person the row already points at (by its NIN,
 * or by its exact name when there is no NIN yet) is offered FIRST in the other boxes -- even before 3 letters are
 * typed -- so one pick fills the rest. It is not offered once the row already has that person's NIN, name and phone.
 */
export function suggestForRow(people, field, row, limit = 6) {
    const r = row || {};
    const ninNow = norm(r.nationalId), nameNow = norm(r.fullName);
    const list = suggestPeople(people, field, r[field], limit);
    const anchor = (ninNow && (people || []).find(p => p.nin === ninNow))
        || (!ninNow && nameNow && (people || []).find(p => p.name === nameNow)) || null;
    if (!anchor) return list;
    const rest = list.filter(s => s.person !== anchor);
    const complete = anchor.nin === ninNow && anchor.name === nameNow && digits(anchor.phone) === digits(r.phone);
    return complete ? rest : [personSuggestion(anchor, field), ...rest].slice(0, limit);
}

/**
 * Plain "you typed this before" suggestions for a free-text box (an expense category, who spent the money).
 * values = strings (repeats allowed: a value used more often comes first).
 */
export function suggestValues(values, typed, limit = 8) {
    const counts = new Map();
    const shown = new Map();
    for (const v of (values || [])) {
        const k = norm(v);
        if (!k) continue;
        counts.set(k, (counts.get(k) || 0) + 1);
        if (!shown.has(k)) shown.set(k, String(v).trim());
    }
    const t = norm(typed);
    const out = [];
    for (const [k, count] of counts) {
        if (k === t) continue;                       // already typed in full
        const rank = matchRank(k, typed);
        if (rank >= 0) out.push({ key: 'v:' + k, value: shown.get(k), count, rank });
    }
    out.sort((a, b) => a.rank - b.rank || b.count - a.count || a.value.localeCompare(b.value));
    return out.slice(0, limit);
}

export const placeLabel = (field) => PLACE_LABEL[field] || field;
