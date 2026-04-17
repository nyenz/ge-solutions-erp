// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

/**
 * NYENZ ERP - MASTER API CLIENT (V10 - HARD-WIRED PRODUCTION)
 * 
 * FIX: Physically hard-coded the Render API URL to bypass 
 * environment variable build-time failures.
 */
const api = axios.create({
    // VITAL: Hard-wired to your Cloud Engine Room
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