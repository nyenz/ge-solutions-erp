// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V11 - FULL TRACING)
 */
const api = axios.create({
    baseURL: 'https://ge-solutions-api.onrender.com/api/v1',
    headers: { 'Content-Type': 'application/json' }
});

// --- REQUEST SENSOR ---
api.interceptors.request.use(
    (config) => {
        // LOGS EVERY CALL TO THE CONSOLE (F12)
        console.log(`%c>>> OUTGOING SIGNAL: ${config.method.toUpperCase()} ${config.url}`, 'color: #06b6d4; font-weight: bold;');
        
        const token = localStorage.getItem('gs_token'); 
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// --- RESPONSE SENSOR ---
api.interceptors.response.use(
    (response) => {
        console.log(`%c<<< SIGNAL RECEIVED: ${response.status} OK`, 'color: #10b981; font-weight: bold;');
        return response;
    },
    (error) => {
        const status = error.response ? error.response.status : 'OFFLINE';
        console.error(`%c!!! SIGNAL REJECTED: Status ${status}`, 'color: #ef4444; font-weight: bold;');
        
        if (status === 401 || status === 403) {
            if (!window.location.pathname.includes('/login')) {
                localStorage.clear(); 
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;