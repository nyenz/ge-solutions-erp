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
};

export function errorText(err) {
    const status = err && err.response && err.response.status;
    if (!status) return 'No reply from the server (the internet is down, or the server is waking up). Nothing was saved. Try again in a few seconds.';
    if (status === 403 && !(err.response.data && (err.response.data.message || err.response.data.error))) {
        return 'You do not have permission to do that.';
    }
    const d = err.response.data;
    let raw = '';
    if (d && typeof d === 'object') raw = d.message || d.error || '';
    else if (typeof d === 'string' && d.length < 400) raw = d;
    if (!raw) return 'Something went wrong (HTTP ' + status + ').';
    const m = String(raw).match(/^([A-Z][A-Z0-9_]{2,}):\s*(.*)$/s);
    if (!m) return raw;
    const known = PLAIN[m[1]];
    if (known) return known;
    const rest = m[2].trim();
    return rest || m[1].replace(/_/g, ' ').toLowerCase();
}

export default errorText;
