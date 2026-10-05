// PATH: erp-frontend/src/services/landService.js
import api from '../api/axios';

// fix173: the system default monthly storage fee is fetched once and shared by every page
let storageFeeDefaultPromise = null;

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

    // fix166: deleting a project needs a written reason (5+ characters)
    purgeAsset: async (projectId, reason) => {
        await api.delete(`/land/projects/${projectId}`, { params: { reason } });
    },

    getDeletedProjects: async () => {
        const response = await api.get('/land/projects/deleted');
        return response.data;
    },

    // fix181 (14.7c): without force the server refuses a restore that clashes with a live project on the same plot
    restoreProject: async (projectId, force = false) => {
        await api.post(`/land/projects/${projectId}/restore`, null, { params: { force } });
    },

    // fix180: statusId = the project status the files are attached to (leave empty for general documents)
    addExtraDocuments: async (projectId, scans, categories = [], statusId = null) => {
        const formData = new FormData();
        scans.forEach(file => formData.append('scans', file));
        // fix136: one category code per file, same order as scans
        if (categories.length === scans.length) categories.forEach(c => formData.append('categories', c || ''));
        if (statusId) formData.append('statusId', statusId);
        await api.post(`/land/projects/${projectId}/documents`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },

    getDocumentCategories: async () => {
        const response = await api.get('/land/document-categories');
        return response.data;
    },

    addDocumentCategory: async (label) => {
        const response = await api.post('/land/document-categories', { label });
        return response.data;
    },

    deleteDocument: async (docId) => {
        await api.delete(`/land/documents/${docId}`);
    },

    addStandaloneNote: async (projectId, content) => {
        // fix165: the note travels in the request body (a long note in the web address was refused by the server)
        await api.post(`/land/projects/${projectId}/notes`, { content });
    },

    editStandaloneNote: async (noteId, content) => {
        await api.put(`/land/notes/${noteId}`, { content });
    },

    deleteStandaloneNote: async (noteId) => {
        await api.delete(`/land/notes/${noteId}`);
    },

    getGlobalLedger: async (page = 0, size = 50) => {
        const response = await api.get('/land/ledger', { params: { page, size } });
        return response.data;
    },

    getStatusesBulk: async (projectIds) => {
        const response = await api.post('/land/ledger/statuses-bulk', projectIds);
        return response.data;
    },

    bulkMarkTitleProduced: async (projectIds) => {
        const response = await api.post('/land/projects/bulk-mark-title-produced', projectIds);
        return response.data;
    },

    createAtomicEntry: async (data, scans, categories = []) => {
        const formData = new FormData();
        const payload = { ...data };
        delete payload.fileQueue;
        formData.append('data', JSON.stringify(payload));
        if (scans) scans.forEach(file => formData.append('scans', file));
        // fix174: one document type (category code) per file, same order as scans
        if (scans && categories.length === scans.length) categories.forEach(c => formData.append('categories', c || ''));
        const response = await api.post('/land/ingest', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // fix167: moveToReceivable / exitReceivable / getPaymentHistory / setRealityStatus removed (unused; the old
    // receivable endpoints are gone -- receivable moves go through folderPortalService).

    // fix167: a hand-over needs a note (who collected the title): 5+ characters
    authorizeRelease: async (projectId, managerNote) => {
        await api.patch(`/land/projects/${projectId}/release`, null, { params: { managerNote } });
    },

    // fix162: money safety
    reversePayment: async (projectId, paymentId, reason) => {
        await api.post(`/land/projects/${projectId}/payments/${paymentId}/reverse`, null, { params: { reason } });
    },

    undoRelease: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/undo-release`, null, { params: { reason } });
    },

    // fix163: take a saved title off the project (fix180: Topographic Survey and older projects only)
    revertTitle: async (projectId, reason) => {
        await api.patch(`/land/projects/${projectId}/revert-title`, null, { params: { reason } });
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
    },

    // fix173: the system default monthly storage fee (the server holds the only copy of the number)
    getStorageFeeDefault: () => {
        if (!storageFeeDefaultPromise) {
            storageFeeDefaultPromise = api.get('/land/storage-fee-default')
                .then(r => Number(r.data && r.data.defaultMonthlyFee) || 0)
                .catch(e => { storageFeeDefaultPromise = null; throw e; });
        }
        return storageFeeDefaultPromise;
    }
};

export default landService;

