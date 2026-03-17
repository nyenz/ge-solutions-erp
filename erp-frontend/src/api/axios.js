// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V6 - PRODUCTION READY)
 * 
 * Logic: Dynamically detects the environment to route traffic correctly
 * between local dev machines and the online production server.
 */
const api = axios.create({
    // VITAL: Uses the .env variable instead of a hardcoded string
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1',
    headers: {
        'Content-Type': 'application/json'
    }
});

/**
 * SECURITY INTERCEPTOR
 */
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

/**
 * AUTH WATCHDOG (SESSION EXPIRY)
 */
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response ? error.response.status : null;

        // TARGET: Scenario E (Broken or Expired Token)
        if (status === 401 || status === 403) {
            console.error(">>> SECURITY_ALERT: Session Expired. Purging storage.");
            localStorage.clear(); 
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;