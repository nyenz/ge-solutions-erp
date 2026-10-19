// fix215 (David): the rules of the Notes timeline on the page (pure, tested in tests/timeline.test.mjs).
// The server sends one list (TimelineService); the page only filters, groups and words it.

/** The filter pills, in order. MONEY only shows for people who can see money. */
export const KINDS = [
    { key: 'ALL', label: 'ALL', title: 'Everything that happened, newest first.' },
    { key: 'NOTE', label: 'NOTES', title: 'Notes typed by staff.' },
    { key: 'MONEY', label: 'MONEY', accent: 'green', title: 'Payments and reversals, with how they were paid. Manager and above.', money: true },
    { key: 'REASON', label: 'DECISIONS', accent: 'yellow', title: 'Every change that needed a reason: fees added to the cost, pauses, deletions and so on.' },
    { key: 'EVENT', label: 'EVENTS', accent: 'cyan', title: 'What the app recorded by itself: stages ticked, project started, problem flags, hand-overs.' },
    { key: 'CALL', label: 'CALLS', title: 'Recovery calls to the clients of this project.' },
];

/** One-tap topics for a new note. The money ones are quiet on purpose: a note is not a payment. */
export const TOPICS = ['Call with client', 'Site visit', 'Promise to pay', 'Money agreement', 'Waiting for client', 'Land office', 'Legal matter'];

export const kindWord = (k) => ({ NOTE: 'Note', MONEY: 'Money', REASON: 'Decision', EVENT: 'Event', CALL: 'Call' }[k] || 'Note');

/** "YYYY-MM-DD" of today on this device (never UTC: Uganda is 3 hours ahead) */
export const todayISO = (d = new Date()) => {
    const p = (n) => String(n).padStart(2, '0');
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
};

/** 'due' (today or late), 'soon' (later), or '' when there is no follow-up day */
export const followUpState = (day, today = todayISO()) => {
    if (!day) return '';
    const d = String(day).slice(0, 10);
    return d <= today ? 'due' : 'soon';
};

/** The rows for one filter + search; pinned notes are taken out and returned on their own (shown on top). */
export const visibleRows = (rows, kind = 'ALL', search = '', projectId = '') => {
    const q = String(search || '').trim().toLowerCase();
    const list = (rows || []).filter(r => (kind === 'ALL' || r.kind === kind)
        && (!projectId || r.projectId === projectId)
        && (!q || [r.title, r.text, r.detail, r.by, r.topic, r.projectIndex, r.clientName].some(v => v && String(v).toLowerCase().includes(q))));
    return { pinned: list.filter(r => r.pinned), rest: list.filter(r => !r.pinned) };
};

/** How many rows each pill holds (for the counts on the pills). */
export const countKinds = (rows) => {
    const c = { ALL: (rows || []).length };
    for (const r of rows || []) c[r.kind] = (c[r.kind] || 0) + 1;
    return c;
};

/** The one line shown before the row is opened. */
export const summaryOf = (r) => {
    // money lines lead with the amount and the method; the rest with the words typed
    const t = String((r.kind === 'MONEY' ? r.detail || r.text : r.text || r.detail) || '').replace(/\s+/g, ' ').trim();
    return t.length > 110 ? t.slice(0, 107) + '...' : t;
};

/** "19 Oct 2026" / "19 Oct 2026, 14:05" from the server's local date-time text (no time-zone guessing) */
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const fmtWhen = (s, withTime = false) => {
    const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/);
    if (!m) return '';
    const day = Number(m[3]) + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1];
    return withTime && m[4] ? day + ', ' + m[4] + ':' + m[5] : day;
};
