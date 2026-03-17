// PATH: erp-frontend/src/services/recoveryService.js
import api from '../api/axios';

/**
 * NYENZ ERP - RECOVERY PIPELINE (V5.1 - SENSOR SYNC)
 */
const recoveryService = {

    /**
     * SENSOR: HEADER NOTIFICATION COUNT
     */
    getTaskCount: async () => {
        try {
            const response = await api.get('/recovery/count');
            // Backend returns { "staleCount": X }
            return response.data.staleCount;
        } catch {
            return 0;
        }
    },

    /**
     * QUEUE: ACTION MODE
     */
    getMissionQueue: async () => {
        const response = await api.get('/recovery/queue');
        return response.data;
    },

    /**
     * SCHEDULE: FORECAST MODE
     */
    getRecoverySchedule: async () => {
        const response = await api.get('/recovery/schedule');
        return response.data;
    },

    /**
     * HISTORY: INTEL STREAM
     */
    getHistory: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/notes`);
        return response.data;
    },

    /**
     * LOG INTERACTION
     */
    logRecoveryCall: async (projectId, text) => {
        await api.post(`/land/projects/${projectId}/follow-up`, null, {
            params: { content: text }
        });
        return true;
    }
};

export default recoveryService;