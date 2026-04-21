// PATH: erp-frontend/src/api/axios.js
import axios from 'axios';

const api = axios.create({
    // VITAL: Hard-wiring the exact secure cloud link
    baseURL: 'https://ge-solutions-api.onrender.com/api/v1',
    headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('gs_token'); 
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
    },
    (error) => Promise.reject(error)
);

export default api;