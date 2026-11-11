// PATH: erp-frontend/src/utils/installApp.js
// fix293 (David): "Download app". The browser offers to install the app once (the beforeinstallprompt event); we keep that
// offer here so the header button can use it later. Loaded first thing in main.jsx, before the offer can arrive.
let offer = null;
const listeners = new Set();
const tell = () => listeners.forEach((f) => { try { f(); } catch { /* a closed page */ } });

if (typeof window !== 'undefined') {
    window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); offer = e; tell(); });
    window.addEventListener('appinstalled', () => { offer = null; tell(); });
}

/** True when the app is already running as the installed app (from its own icon). */
export const isInstalled = () => {
    try {
        return !!((window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone);
    } catch { return false; }
};

/** True when the browser can show its own install popup right now. */
export const canPrompt = () => !!offer;

/** Shows the browser's install popup. Returns 'accepted', 'dismissed' or 'none' (no popup available). */
export const promptInstall = async () => {
    if (!offer) return 'none';
    const o = offer;
    offer = null;
    try { o.prompt(); const r = await o.userChoice; tell(); return (r && r.outcome) || 'dismissed'; }
    catch { tell(); return 'dismissed'; }
};

/** Call f whenever the install state changes. Returns the function that stops it. */
export const onInstallChange = (f) => { listeners.add(f); return () => listeners.delete(f); };

/** Which device the steps are written for. */
export const deviceKind = () => {
    const ua = (typeof navigator !== 'undefined' && navigator.userAgent) || '';
    if (/iphone|ipad|ipod/i.test(ua) || (/macintosh/i.test(ua) && typeof navigator !== 'undefined' && navigator.maxTouchPoints > 1)) return 'ios';
    if (/android/i.test(ua)) return 'android';
    return 'laptop';
};

/** Registers the small helper (public/sw.js) that makes the app installable. Only on the real (built) app. */
export const registerInstallHelper = () => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator) || !import.meta.env.PROD) return;
    window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => { /* the app works without it */ }); });
};
