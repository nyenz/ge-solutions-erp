// PATH: erp-frontend/src/api/axios.js

import axios from 'axios';

// VITAL FIX: We no longer hardcode the URL.
// Instead, we read it from the environment variable set in render.yaml.
//
// How this works:
//   - In PRODUCTION (Render): Vite reads VITE_API_BASE_URL from render.yaml
//     and bakes it into the built files automatically.
//   - In LOCAL DEV: Create a file called '.env.local' in your erp-frontend/
//     folder and add this one line:
//     VITE_API_BASE_URL=http://localhost:8080/api/v1
//
// This means the same code works in both environments without any changes.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ge-solutions-api.onrender.com/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    // ADDED: If the server takes more than 15 seconds to respond,
    // show an error instead of hanging forever. Important for the
    // Render free tier which can be slow on first wake-up.
    timeout: 15000,
});

// REQUEST INTERCEPTOR: Automatically attach the saved login token
// to every request so the user doesn't have to log in repeatedly.
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

// RESPONSE INTERCEPTOR: If the server says our token is expired (401),
// automatically log the user out and send them back to the login screen.
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token is expired or invalid — clear it and redirect
            localStorage.removeItem('gs_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;