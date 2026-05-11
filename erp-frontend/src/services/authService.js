// PATH: erp-frontend/src/services/authService.js

// VITAL FIX: We now import the pre-configured 'api' instance from axios.js
// instead of raw axios. That instance already has the correct cloud URL
// (VITE_API_BASE_URL from render.yaml) baked in at build time.
// The old version imported plain axios and called localhost:8080 directly —
// which works on your laptop but fails completely in the cloud.
import api from '../api/axios';

/**
 * NYENZ ERP - AUTHENTICATION PIPELINE (V2.1 - CLOUD FIXED)
 */
const authService = {

    /**
     * AUTHORIZE OPERATOR
     * Sends credentials to the cloud engine and stores the identity token.
     */
    login: async (username, password) => {
        try {
            // 'api' already knows the base URL. We only need the path suffix.
            const response = await api.post('/auth/login', { username, password });

            if (response.data && response.data.token) {
                const { token, user } = response.data;
                localStorage.setItem('gs_token', token);
                localStorage.setItem('gs_user', JSON.stringify(user));
                return { token, user };
            }
            throw new Error("PROTOCOL_FAULT: INCOMPLETE_HANDSHAKE");

        } catch (error) {
            const status = error.response?.status;
            if (status === 401 || status === 400) throw new Error("IDENTIFICATION_FAILED");
            if (status === 403) throw new Error("ACCOUNT_SUSPENDED");
                        // Check if it was a timeout (server waking up on Render free tier)
            if (error.code === 'ECONNABORTED' || (error.message && error.message.toLowerCase().includes('timeout'))) {
                throw new Error('SERVER_STARTING_UP');
            }
            throw new Error(error.message || "COMMUNICATION_FAULT");
        }
    },

    /**
     * ROOT RECOVERY TRIGGER (The Panic Button)
     */
    recoverPassword: async (email) => {
        try {
            const response = await api.post('/auth/recover-owner', { email });
            return response.data.message;
        } catch (error) {
            const msg = error.response?.data?.message || "RECOVERY_FAULT: UNKNOWN";
            throw new Error(msg.toUpperCase());
        }
    },

    logout: () => {
        localStorage.removeItem('gs_token');
        localStorage.removeItem('gs_user');
        window.location.href = '/login';
    }
};

export default authService;