// PATH: erp-frontend/src/api/axios.js

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 15000,
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
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login?reason=idle_timeout';
        }
    }, IDLE_MINUTES * 60 * 1000);
}

// Start the timer immediately when the module loads (user is already logged in)
resetIdleTimer();

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
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('gs_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
