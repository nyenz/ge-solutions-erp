// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V7 - NUCLEAR READY)
 * 
 * FIX: Standardised error extraction to prevent generic 'REWRITE_FAILURE' 
 * and reveal the actual logic fault from the Backend.
 */
const api = axios.create({
    baseURL: 'http://localhost:8080/api/v1',
    headers: { 'Content-Type': 'application/json' }
});

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

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response ? error.response.status : null;
        
        // --- INDUSTRIAL SENSOR ---
        // If the backend sent a 'BusinessException' message, we log it to console
        const serverMsg = error.response?.data?.message;
        if (serverMsg) console.error(`>>> SERVER_SAYS: ${serverMsg}`);

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