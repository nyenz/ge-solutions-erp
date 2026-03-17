// PATH: erp-frontend/src/services/authService.js
import axios from 'axios';

const API_URL = 'http://localhost:8080/api/v1/auth';

/**
 * NYENZ ERP - AUTHENTICATION PIPELINE
 * Physically manages login and root recovery protocols.
 */
const authService = {
    /**
     * AUTHORIZE OPERATOR
     */
    login: async (username, password) => {
        try {
            const response = await axios.post(`${API_URL}/login`, { username, password });
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
            throw new Error(error.message || "COMMUNICATION_FAULT");
        }
    },

    /**
     * ROOT RECOVERY TRIGGER (The Panic Button)
     * Calls the SMTP relay engine in Java.
     */
    recoverPassword: async (email) => {
        try {
            const response = await axios.post(`${API_URL}/recover-owner`, { email });
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