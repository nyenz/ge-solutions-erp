// PATH: erp-frontend/src/services/recoveryService.js
import api from '../api/axios';

const recoveryService = {

    getTaskCount: async () => {
        try {
            const response = await api.get('/recovery/count');
            return response.data.staleCount;
        } catch {
            return 0;
        }
    },

    getMissionQueue: async () => {
        const response = await api.get('/recovery/queue');
        return response.data;
    },

    getRecoverySchedule: async () => {
        const response = await api.get('/recovery/schedule');
        return response.data;
    },

    getHistory: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/notes`);
        return response.data;
    },

    getPaymentHistory: async (projectId) => {
        const response = await api.get(`/recovery/projects/${projectId}/payments`);
        return response.data;
    },

    logRecoveryCall: async (projectId, text) => {
        await api.post(`/land/projects/${projectId}/follow-up`, null, {
            params: { content: text }
        });
        return true;
    },

    recordPayment: async (projectId, amount, notes) => {
        await api.post(`/recovery/projects/${projectId}/payment`, null, {
            params: { amount, notes }
        });
        return true;
    },

    moveToBacklog: async (projectId) => {
        await api.post(`/land/projects/${projectId}/backlog`);
        return true;
    },

    exitBacklog: async (projectId) => {
        await api.post(`/land/projects/${projectId}/exit-backlog`);
        return true;
    },

    pauseStorageFees: async (projectId, paused) => {
        await api.patch(`/land/projects/${projectId}/storage-pause`, null, {
            params: { paused }
        });
    },

    setStorageRate: async (projectId, rate) => {
        await api.patch(`/land/projects/${projectId}/storage-rate`, null, {
            params: { rate }
        });
    },

    setAccumulatedFees: async (projectId, amount) => {
        await api.patch(`/land/projects/${projectId}/storage-fees`, null, {
            params: { amount }
        });
    },

    setNegotiationDeadline: async (projectId, deadline) => {
        await api.patch(`/land/projects/${projectId}/negotiation-deadline`, null, {
            params: deadline ? { deadline } : {}
        });
    },

    setBacklogStartOverride: async (projectId, startDate) => {
        await api.patch(`/land/projects/${projectId}/backlog-start`, null, {
            params: { startDate }
        });
    }
};

export default recoveryService;