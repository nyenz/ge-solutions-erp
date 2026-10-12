// PATH: erp-frontend/src/utils/errorText.js
// fix181 (15.2i): ONE place that turns a server error into a plain sentence. The server answers "CODE: sentence".
// Known codes get a friendly sentence; an unknown code shows the server's sentence without the code, in normal case
// (never shouted in capitals).
const PLAIN = {
    IDENTIFICATION_FAILED: 'Wrong username or key.',
    ACCOUNT_SUSPENDED: 'This account is suspended. Ask the Director.',
    TOO_MANY_ATTEMPTS: null,               // the server sentence already says how long to wait
    SESSION_CONFLICT: 'You were signed out because this account signed in somewhere else.',
    INVALID_TOKEN: 'Your sign-in expired. Please sign in again.',
    PASSWORD_CHANGE_REQUIRED: 'Change your temporary key first (Settings, Security).',
    KEY_EXPIRED: 'Your temporary key has expired. Ask the Director for a new one.',
    OLD_PASSWORD_INCORRECT: 'The current key is not right.',
    RANK_DENIED: null,
    PRICING_NOT_ALLOWED: null,
    NOT_YOUR_ENTRY: 'You can only open the projects you entered.',
    ALREADY_STARTED: 'The office has already started this project. Ask a Secretary.',
    SERVER_STARTING_UP: 'The server is waking up (up to 60 seconds on the free plan). Wait a moment and try again.',   // fix205
    COMMUNICATION_FAULT: 'Could not reach the server. Check the internet and try again.',
    PROTOCOL_FAULT: 'The server gave an incomplete answer. Try again.',
};

// fix205 (David): a message a person reads NEVER shows a status number ("HTTP 400", "status code 500") or a code word
// ("PLOT_TAKEN:"). The server's own sentence is kept; anything technical is replaced by a plain sentence.
const BY_STATUS = {
    400: 'That could not be saved. Check the boxes and try again.',
    403: 'You do not have permission to do that.',
    404: 'That item could not be found. It may have been removed. Refresh the page.',
    409: 'Someone else changed this at the same time. Refresh the page and try again.',
    413: 'The file is too big.',
    429: 'Too many tries. Wait a moment and try again.',
};
const SERVER_TROUBLE = 'The server had a problem, so nothing was saved. Try again in a minute.';
const TECHNICAL = /(not authori[sz]ed|access is denied|forbidden|request failed with status code|internal server error|exception|stack ?trace|null ?pointer|jdbc|sql|hibernate|status code)/i;

/** Takes a code word off the front and any "(HTTP 400)" / status number off a sentence. */
export function cleanMessage(text) {
    let t = String(text == null ? '' : text).trim();
    t = t.replace(/\s*\((?:HTTP|status)\s*\d{3}\)\s*/gi, ' ').replace(/\bHTTP\s*\d{3}\b/gi, '').trim();
    const m = t.match(/^([A-Z][A-Z0-9_]{2,}):\s*(.*)$/s);
    if (m) t = (PLAIN[m[1]] || m[2].trim() || m[1].replace(/_/g, ' ').toLowerCase());
    else if (/^[A-Z][A-Z0-9_]{2,}$/.test(t)) t = PLAIN[t] || t.replace(/_/g, ' ').toLowerCase();
    return t.replace(/\s{2,}/g, ' ').trim();
}

export function errorText(err) {
    const status = err && err.response && err.response.status;
    if (!status) return 'No reply from the server (the internet is down, or the server is waking up). Nothing was saved. Try again in a few seconds.';
    const d = err.response.data;
    let raw = '';
    if (d && typeof d === 'object') raw = d.message || d.error || '';
    else if (typeof d === 'string' && d.length < 400 && !/<html|<!doctype/i.test(d)) raw = d;
    if (status === 403 && (!raw || TECHNICAL.test(raw))) return BY_STATUS[403];
    const coded = /^[A-Z][A-Z0-9_]{2,}:/.test(String(raw));
    if (status >= 500 && !coded) return SERVER_TROUBLE;   // a crash text is never shown
    if (!raw || TECHNICAL.test(raw)) return status >= 500 ? SERVER_TROUBLE : (BY_STATUS[status] || 'Something went wrong. Nothing was saved. Try again.');
    const code = (String(raw).match(/^([A-Z][A-Z0-9_]{2,}):/) || [])[1];
    if (code && PLAIN[code]) return PLAIN[code];
    return cleanMessage(raw) || (status >= 500 ? SERVER_TROUBLE : 'Something went wrong. Nothing was saved. Try again.');
}

export default errorText;
