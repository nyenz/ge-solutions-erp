// PATH: erp-frontend/src/services/settingsService.js
import api from '../api/axios';

/**
 * NYENZ ERP - SECURITY & GOVERNANCE SERVICE (V4)
 * 
 * Physically manages the communication between the Security Mastery UI 
 * and the Java Authentication Engine.
 * 
 * SECURITY: All methods are physically gated by the JWT Interceptor in axios.js.
 */
const settingsService = {

    /**
     * SELF-SERVICE: PASSWORD REWRITE
     * Used by any operator to update their personal master key.
     * Physically clears the 'mustChangePassword' handbrake on success.
     */
    changePersonalPassword: async (oldPassword, newPassword) => {
        try {
            await api.put('/profile/change-password', { oldPassword, newPassword });
            return true;
        } catch (error) {
            const msg = error.response?.data?.message || "REWRITE_PROTOCOL_FAILURE";
            throw new Error(msg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: FETCH REGISTRY (ROOT ONLY)
     * Retrieves all operators and their current status for Founder oversight.
     */
    getAllOperators: async () => {
        try {
            const response = await api.get('/staff/all');
            return response.data;
        } catch (error) {
            const msg = error.response?.data?.message || "REGISTRY_LOCKED";
            throw new Error(msg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: PROVISION NEW MANAGER (ROOT ONLY)
     * Creates a new identity and returns the temporary industrial key.
     */
    registerManager: async (staffData) => {
        try {
            // Default to ROLE_MANAGER if UI doesn't specify
            const payload = { ...staffData, role: staffData.role || 'ROLE_MANAGER' };
            const response = await api.post('/staff/create', payload);
            return response.data; 
        } catch (error) {
            const msg = error.response?.data?.message || "REGISTRATION_DENIED";
            throw new Error(msg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: HIERARCHY ADJUSTMENT (PROMOTION/DEMOTION)
     * Physically changes the security clearance level of an operator.
     */
    updateOperatorRole: async (username, newRole) => {
        try {
            await api.patch(`/staff/${username}/role`, null, {
                params: { newRole }
            });
            return true;
        } catch (error) {
            const msg = error.response?.data?.message || "RANK_ADJUSTMENT_FAILED";
            throw new Error(msg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: STATUS KILL-SWITCH
     * Physically suspends or restores access to the archive.
     */
    toggleOperator: async (username, isActive) => {
        try {
            await api.patch(`/staff/${username}/toggle`, null, {
                params: { active: isActive }
            });
            return true;
        } catch (error) {
            const msg = error.response?.data?.message || "GOVERNANCE_PROTOCOL_FAULT";
            throw new Error(msg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: EMERGENCY KEY RESET
     * Resets a secondary operator's password to a new temporary code.
     */
    resetOperatorKey: async (username) => {
        try {
            const response = await api.post('/staff/reset-password', { username });
            return response.data.temporaryPassword;
        } catch (error) {
            const msg = error.response?.data?.message || "RESET_PROTOCOL_REJECTED";
            throw new Error(msg.toUpperCase());
        }
    }
};

export default settingsService;