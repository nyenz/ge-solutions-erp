// PATH: erp-frontend/src/api/axios.js

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 60000,
});

// ── IDLE TIMEOUT: sign out after 30 minutes with no real input ──
// fix181 (14.2, 15.2a): the clock is ONE time kept in localStorage and shared by every tab, so a busy tab keeps the
// whole browser signed in and an idle tab no longer signs a busy person out. Only real input (click, key, touch,
// scroll, mouse movement) moves it; API calls never do (the bell polls would otherwise keep a session open all night).
const IDLE_MINUTES = 30;
const ACTIVITY_KEY = 'gs_last_activity';
let lastWrite = 0;

export function markActivity(force = false) {
    const t = Date.now();
    if (!force && t - lastWrite < 15000) return;   // at most once every 15 seconds
    lastWrite = t;
    try { localStorage.setItem(ACTIVITY_KEY, String(t)); } catch { /* storage blocked */ }
    hideIdleWarning();
}

function lastActivity() {
    try { return Number(localStorage.getItem(ACTIVITY_KEY)) || Date.now(); } catch { return Date.now(); }
}

let warnBox = null;
function hideIdleWarning() { if (warnBox) { warnBox.remove(); warnBox = null; } }
function showIdleWarning() {
    if (warnBox || typeof document === 'undefined') return;
    warnBox = document.createElement('div');
    warnBox.setAttribute('role', 'alertdialog');
    warnBox.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:99999;background:#0f172a;color:#f8fafc;'
        + 'border:1px solid #f59e0b;border-radius:10px;padding:14px 18px;font:14px system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.4);'
        + 'display:flex;gap:14px;align-items:center;max-width:calc(100vw - 32px)';
    const text = document.createElement('span');
    text.textContent = 'You will be signed out in 1 minute. Stay signed in?';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Stay signed in';
    btn.style.cssText = 'background:#f59e0b;color:#111827;border:0;border-radius:6px;padding:6px 12px;font-weight:700;cursor:pointer';
    btn.onclick = () => markActivity(true);
    warnBox.append(text, btn);
    document.body.appendChild(warnBox);
}

function idleLogout() {
    hideIdleWarning();
    console.warn('[GS-ERP] Idle timeout -- logging out.');
    // remove only the sign-in, never the saved appearance choices (localStorage.clear() wiped them)
    try { api.post('/auth/logout').catch(() => {}); } catch { /* ignore */ }
    localStorage.removeItem('gs_token');
    localStorage.removeItem('gs_user');
    window.location.href = '/login?reason=idle_timeout';
}

if (typeof window !== 'undefined') {
    const poke = () => markActivity();
    ['click', 'keydown', 'touchstart', 'scroll', 'mousemove'].forEach(ev => window.addEventListener(ev, poke, { passive: true, capture: true }));
    if (!localStorage.getItem(ACTIVITY_KEY)) markActivity(true);
    setInterval(() => {
        if (!localStorage.getItem('gs_token')) { hideIdleWarning(); return; }
        const idleMs = Date.now() - lastActivity();
        if (idleMs >= IDLE_MINUTES * 60 * 1000) idleLogout();
        else if (idleMs >= (IDLE_MINUTES - 1) * 60 * 1000) showIdleWarning();
        else hideIdleWarning();
    }, 10000);
}

// REQUEST INTERCEPTOR: attach token + reset idle clock on every call
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('gs_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// RESPONSE INTERCEPTOR: handle 401 (expired/invalid token)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401 && !String(error.config?.url || '').includes('/auth/')) {
            // fix181: say WHY (another sign-in, expired, suspended) instead of always "session conflict"
            const code = error.response.data && error.response.data.error;
            const reason = code === 'ACCOUNT_SUSPENDED' ? 'suspended' : code === 'INVALID_TOKEN' ? 'session_expired' : 'session_conflict';
            localStorage.removeItem('gs_token');
            localStorage.removeItem('gs_user');
            window.location.href = '/login?reason=' + reason;
        }
        return Promise.reject(error);
    }
);

export default api;
