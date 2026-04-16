// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V9 - CLOUD PRODUCTION)
 * 
 * Physically synchronized with the Render environment variables.
 */
const api = axios.create({
    // VITAL: Now strictly uses the baked-in variable
    baseURL: import.meta.env.VITE_API_BASE_URL,
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