// PATH: erp-frontend/src/context/prefsStore.js
// fix181 (15.1d, 15.1i, 15.1j): where the appearance choices are kept and how they are read.
//  - per person on the device: goldenseed.prefs.v1.<username>; the plain key goldenseed.prefs.v1 is the device default
//    (used on the login page and for anyone who has not chosen yet). Devices are shared, so one person's 125% / SLATE /
//    start page never reaches the next person.
//  - a stored value is accepted only when it is in that setting's own list; anything else falls back to the default.
//  - index.html has a tiny inline copy of these rules that runs before the first paint (keep the two in step).
import { DEFAULT_PREFS, PREF_ALLOWED } from './PreferencesContext';

export const DEVICE_KEY = 'goldenseed.prefs.v1';

export const currentUsername = () => {
    try { return JSON.parse(window.localStorage.getItem('gs_user') || 'null')?.username || null; }
    catch { return null; }
};

export const keyFor = (username) => (username ? `${DEVICE_KEY}.${String(username).toLowerCase()}` : DEVICE_KEY);

const deviceReducesMotion = () => {
    try { return !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches; } catch { return false; }
};

/** Keeps only known settings with allowed values; anything missing or damaged is the default. */
export const sanitizePrefs = (raw) => {
    const out = { ...DEFAULT_PREFS };
    if (raw && typeof raw === 'object') {
        for (const k of Object.keys(DEFAULT_PREFS)) {
            const v = raw[k] == null ? null : String(raw[k]);
            if (v != null && PREF_ALLOWED[k]?.includes(v)) out[k] = v;
        }
    }
    return out;
};

const readKey = (key) => {
    try {
        const raw = window.localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
};

/** The choices of the person signed in on this device (or the device default when nobody is). */
export const readPrefsFor = (username = currentUsername()) => {
    const own = username ? readKey(keyFor(username)) : null;
    const base = own || readKey(DEVICE_KEY);
    if (!base) return sanitizePrefs({ motion: deviceReducesMotion() ? 'reduced' : 'full' });
    // the start page is personal: never inherited from the device default
    return sanitizePrefs(own ? base : { ...base, landing: undefined });
};

export const writePrefsFor = (username, prefs) => {
    try {
        window.localStorage.setItem(keyFor(username), JSON.stringify(prefs));
        // the first choices made on a device also become its default (login page), without a start page
        if (username && !window.localStorage.getItem(DEVICE_KEY)) {
            window.localStorage.setItem(DEVICE_KEY, JSON.stringify({ ...prefs, landing: undefined }));
        }
    } catch { /* private mode */ }
};

export const THEME_COLOR = { light: '#1a2e30', dark: '#16292b' };
