// PATH: erp-frontend/src/pages/DigitalFolder/noteTags.js
/**
 * GOLDEN SEED -- NOTE TAGS
 *
 * THE PROBLEM THIS SOLVES
 *
 * The folder keeps two kinds of note in one timeline: ones a person typed,
 * and ones the system wrote on their behalf. The system ones were already
 * being marked with a bracketed prefix at the call site --
 *
 *     addStandaloneNote(id, '[PROBLEM] ' + text)
 *     recordPayment(id, '[STORAGE FEE PAYMENT] ' + notes)
 *
 * -- but nothing ever read those prefixes back. They rendered as literal
 * square brackets in the middle of the sentence, there was no way to filter
 * to them, and because the convention was invisible, each new call site
 * invented its own wording. That is how a subsystem drifts: the rule exists
 * only in the head of whoever wrote the last call.
 *
 * One registry now owns the convention. Parsing is tolerant -- an unknown tag
 * still renders as a chip rather than as raw text, so a prefix added later
 * from anywhere in the codebase is picked up without being listed here first.
 *
 * AUTO vs MANUAL is the distinction that matters when reading a file back:
 * "the system flagged this" and "Sarah decided this" are different kinds of
 * evidence, so the chip says which.
 */

export const NOTE_TAGS = {
    PROBLEM:               { label: 'PROBLEM',        tone: 'bad',  auto: true },
    'STORAGE FEE PAYMENT': { label: 'STORAGE FEE',    tone: 'info', auto: true },
    'STORAGE FEE':         { label: 'STORAGE FEE',    tone: 'info', auto: true },
    PAYMENT:               { label: 'PAYMENT',        tone: 'ok',   auto: true },
    RECEIVABLE:            { label: 'RECEIVABLE',     tone: 'warn', auto: true },
    STAGE:                 { label: 'STAGE',          tone: 'info', auto: true },
    CALL:                  { label: 'CALL',           tone: 'info', auto: false },
    VISIT:                 { label: 'SITE VISIT',     tone: 'warn', auto: false },
    PROMISE:               { label: 'PROMISE TO PAY', tone: 'ok',   auto: false },
    LEGAL:                 { label: 'LEGAL',          tone: 'bad',  auto: false },
    SYSTEM:                { label: 'SYSTEM',         tone: 'info', auto: true },
};

/* Offered as one-tap buttons in the add-note modal. Keeping the list short is
   the point -- a tag nobody uses is worse than no tag, because it makes the
   filter look broken. */
export const QUICK_TAGS = ['CALL', 'VISIT', 'PROMISE', 'LEGAL', 'PROBLEM'];

const TAG_RE = /^\s*\[([A-Z][A-Z \-_]{1,28})\]\s*/;

/**
 * Split a stored note into its tag and its body.
 * Returns { tag, meta, body } -- tag is null for a plain note.
 */
export const parseNote = (text) => {
    const raw = String(text || '');
    const m = raw.match(TAG_RE);
    if (!m) return { tag: null, meta: null, body: raw };

    const key = m[1].trim().toUpperCase();
    const known = NOTE_TAGS[key];
    return {
        tag: key,
        meta: known || { label: key, tone: 'info', auto: false },
        body: raw.slice(m[0].length),
    };
};

/** Write a tag onto a note without double-tagging one that already has one. */
export const applyTag = (text, tag) => {
    const { body } = parseNote(text);
    if (!tag) return body;
    return '[' + tag + '] ' + body;
};

/**
 * The filter list is built from what is actually in front of you, not from
 * the registry: offering PROMISE on a folder with no promises is a filter
 * that returns nothing and reads as a bug.
 */
export const tagsPresent = (notes) => {
    const seen = [];
    (notes || []).forEach(n => {
        const { tag } = parseNote(n.notes);
        const key = tag || 'UNTAGGED';
        if (!seen.includes(key)) seen.push(key);
    });
    return seen;
};

export const tagLabel = (key) =>
    (key === 'UNTAGGED' ? 'PLAIN' : (NOTE_TAGS[key]?.label || key));

export default NOTE_TAGS;
