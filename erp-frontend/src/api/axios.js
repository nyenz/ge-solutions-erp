// PATH: erp-frontend/src/api/axios.js

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 60000,
});

// ── IDLE TIMEOUT: log out after 30 minutes of no API activity ──
const IDLE_MINUTES = 30;
let idleTimer = null;

function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        const token = localStorage.getItem('gs_token');
        if (token) {
            console.warn('[GS-ERP] Idle timeout -- logging out.');
            // fix181: remove only the sign-in, never the saved appearance choices (localStorage.clear() wiped them)
            try { api.post('/auth/logout').catch(() => {}); } catch { /* ignore */ }
            localStorage.removeItem('gs_token');
            localStorage.removeItem('gs_user');
            window.location.href = '/login?reason=idle_timeout';
        }
    }, IDLE_MINUTES * 60 * 1000);
}

// Timer resets on every API call via the request interceptor below.
// fix167: ...and on every click or key press, so someone typing a long edit is not logged out (losing it)
// just because the page has not talked to the server for 30 minutes.
if (typeof window !== 'undefined') {
    let lastPoke = 0;
    const poke = () => { const t = Date.now(); if (t - lastPoke > 15000) { lastPoke = t; resetIdleTimer(); } };
    window.addEventListener('click', poke, { passive: true });
    window.addEventListener('keydown', poke, { passive: true });
}

// REQUEST INTERCEPTOR: attach token + reset idle clock on every call
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('gs_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        resetIdleTimer(); // any API call resets the 30-min clock
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
