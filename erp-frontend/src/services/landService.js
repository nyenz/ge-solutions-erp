// PATH: erp-frontend/src/services/landService.js
import api from '../api/axios';

const landService = {

    getDashboardSummary: async () => {
        const response = await api.get('/dashboard/summary');
        return response.data;
    },

    getDeepBinder: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/deep`);
        return response.data;
    },

    logDossierUnlock: async (projectId) => {
        await api.post(`/land/projects/${projectId}/unlock-log`);
    },

    updateMasterFolder: async (projectId, data) => {
        const response = await api.put(`/land/projects/${projectId}/full-update`, data);
        return response.data;
    },

    purgeAsset: async (projectId) => {
        await api.delete(`/land/projects/${projectId}`);
    },

    getDeletedProjects: async () => {
        const response = await api.get('/land/projects/deleted');
        return response.data;
    },

    restoreProject: async (projectId) => {
        await api.post(`/land/projects/${projectId}/restore`);
    },

    addExtraDocuments: async (projectId, scans) => {
        const formData = new FormData();
        scans.forEach(file => formData.append('scans', file));
        await api.post(`/land/projects/${projectId}/documents`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    deleteDocument: async (docId) => {
        await api.delete(`/land/documents/${docId}`);
    },

    addStandaloneNote: async (projectId, content) => {
        await api.post(`/land/projects/${projectId}/notes`, null, { params: { content } });
    },

    editStandaloneNote: async (noteId, content) => {
        await api.put(`/land/notes/${noteId}`, null, { params: { content } });
    },

    deleteStandaloneNote: async (noteId) => {
        await api.delete(`/land/notes/${noteId}`);
    },

    setRealityStage: async (projectId, targetStage) => {
        await api.patch(`/land/projects/${projectId}/reality-override`, null, {
            params: { targetStage }
        });
    },

    getGlobalLedger: async (page = 0, size = 50) => {
        const response = await api.get('/land/ledger', { params: { page, size } });
        return response.data;
    },

    bulkMarkTitleProduced: async (projectIds) => {
        const response = await api.post('/land/projects/bulk-mark-title-produced', projectIds);
        return response.data;
    },

    createAtomicEntry: async (data, scans) => {
        const formData = new FormData();
        const payload = { ...data };
        delete payload.fileQueue;
        formData.append('data', JSON.stringify(payload));
        if (scans) scans.forEach(file => formData.append('scans', file));
        const response = await api.post('/land/ingest', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    moveToReceivable: async (projectId) => {
        await api.post(`/land/projects/${projectId}/receivable`);
    },

    exitReceivable: async (projectId) => {
        await api.post(`/land/projects/${projectId}/exit-receivable`);
    },

    getPaymentHistory: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/payments`);
        return response.data;
    },

    authorizeRelease: async (projectId, managerNote) => {
        await api.patch(`/land/projects/${projectId}/release`, null, {
            params: managerNote ? { managerNote } : {}
        });
    },

    // PHASE 7: Director's Dashboard -- period is 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'
    getDirectorDashboard: async (period = 'WEEK') => {
        const response = await api.get('/dashboard/director', { params: { period } });
        return response.data;
    },

    // INTAKE: preview the next project index (001A format) before saving
    getNextIndex: async () => {
        const response = await api.get('/land/next-index');
        return response.data;
    }
};

export default landService;

