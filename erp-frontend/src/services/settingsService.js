// PATH: erp-frontend/src/services/settingsService.js
import api from '../api/axios';

/**
 * GOLDEN SEED ERP - SECURITY & GOVERNANCE SERVICE (V5)
 * 
 * Physically manages operator lifecycles and security keys.
 * UPDATED: Transparent error handling to reveal root causes of failures.
 */
const settingsService = {

    /**
     * SELF-SERVICE: PASSWORD REWRITE
     */
    changePersonalPassword: async (oldPassword, newPassword) => {
        try {
            await api.put('/profile/change-password', { oldPassword, newPassword });
            return true;
        } catch (error) {
            // VITAL FIX: We pull the REAL reason from the response.
            // If it's a CORS block, this will likely say "Network Error".
            // If it's a logic error, it will say the backend message.
            const serverMsg = error.response?.data?.message || "COMMUNICATION_ERROR: Cannot reach engine.";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: FETCH REGISTRY (ROOT ONLY)
     */
    getAllOperators: async () => {
        try {
            const response = await api.get('/staff/all');
            return response.data;
        } catch (error) {
            const serverMsg = error.response?.data?.message || "REGISTRY_OFFLINE";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: PROVISION NEW MANAGER (ROOT ONLY)
     */
    registerManager: async (staffData) => {
        try {
            const payload = { ...staffData, role: staffData.role || 'ROLE_MANAGER' };
            const response = await api.post('/staff/create', payload);
            return response.data; 
        } catch (error) {
            const serverMsg = error.response?.data?.message || "REGISTRATION_DENIED";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: HIERARCHY ADJUSTMENT
     */
    updateOperatorRole: async (username, newRole) => {
        try {
            await api.patch(`/staff/${username}/role`, null, {
                params: { newRole }
            });
            return true;
        } catch (error) {
            const serverMsg = error.response?.data?.message || "RANK_ADJUSTMENT_FAILED";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: STATUS KILL-SWITCH
     */
    toggleOperator: async (username, isActive) => {
        try {
            await api.patch(`/staff/${username}/toggle`, null, {
                params: { active: isActive }
            });
            return true;
        } catch (error) {
            const serverMsg = error.response?.data?.message || "GOVERNANCE_FAULT";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * GOVERNANCE: EMERGENCY KEY RESET
     */
    resetOperatorKey: async (username) => {
        try {
            const response = await api.post('/staff/reset-password', { username });
            return response.data.temporaryPassword;
        } catch (error) {
            const serverMsg = error.response?.data?.message || "RESET_FAILED";
            throw new Error(serverMsg.toUpperCase());
        }
    },

    /**
     * DANGER ZONE: FULL SYSTEM WIPE (ROOT ONLY)
     * Permanently deletes every client, project, payment, and log, then
     * reseeds a clean root login, project index counter, and default
     * stage template. Cannot be undone.
     */
    wipeAllData: async () => {
        try {
            const response = await api.post('/admin/system/wipe-all-data', null, {
                params: { confirm: 'WIPE-EVERYTHING' }
            });
            return response.data;
        } catch (error) {
            const serverMsg = error.response?.data?.message || "WIPE_FAILED";
            throw new Error(serverMsg.toUpperCase());
        }
    }
};

export default settingsService;