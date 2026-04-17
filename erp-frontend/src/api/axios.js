// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V12 - HARD-WIRED CLOUD)
 * 
 * Physically points the interface to the Render Engine Room.
 * This kills the 'ERR_CONNECTION_REFUSED' bug by removing localhost fallbacks.
 */
const api = axios.create({
    // VITAL: Hard-wired to your Cloud Backend
    baseURL: 'https://ge-solutions-api.onrender.com/api/v1',
    headers: {
        'Content-Type': 'application/json'
    }
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