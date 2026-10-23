// PATH: erp-frontend/src/services/statusTemplateService.js
import api from '../api/axios';
import { retrying } from '../utils/retry';   // fix210

/**
 * GOLDEN SEED - STATUS TEMPLATE SERVICE (fix180: was stageTemplateService)
 *
 * Every project type has its own ordered status list (the master template). Adding a status -- to a type's list or
 * to one project -- is for Admin, Manager and Director only; the server refuses it for Secretary.
 */
const statusTemplateService = {

    // the master list of one project type (no type = every type's list)
    getTemplate: async (projectType) => {
        const response = await retrying(() => api.get('/status-templates', { params: projectType ? { projectType } : {} }));
        return response.data;
    },

    addTemplateStatus: async (projectType, statusName, defaultCost, displayOrder) => {
        const response = await api.post('/status-templates', { projectType, statusName, defaultCost, displayOrder });
        return response.data;
    },

    updateTemplateStatus: async (id, statusName, defaultCost, displayOrder) => {
        const response = await api.put(`/status-templates/${id}`, { statusName, defaultCost, displayOrder });
        return response.data;
    },

    // one round trip to persist a whole new ordering
    reorderTemplateStatuses: async (orderedIds) => {
        const response = await api.put('/status-templates/reorder', { orderedIds });
        return response.data;
    },

    // one project type's list back to its fixed defaults, in a single server step
    restoreDefaultStatuses: async (projectType) => {
        const response = await api.post('/status-templates/restore-defaults', null, { params: { projectType } });
        return response.data;
    },

    deactivateTemplateStatus: async (id) => {
        await api.delete(`/status-templates/${id}`);
    },

    getProjectStatuses: async (projectId) => {
        const response = await retrying(() => api.get(`/land/projects/${projectId}/statuses`));
        return response.data;
    },

    // fix167: RESTORE DEFAULTS for one project in one server step (director only)
    restoreProjectDefaults: async (projectId) => {
        const response = await api.post(`/land/projects/${projectId}/statuses/restore-defaults`);
        return response.data;
    },

    attachStatuses: async (projectId, statusRequests) => {
        const response = await api.post(`/land/projects/${projectId}/statuses`, statusRequests);
        return response.data;
    },

    // fix197: tick the "Titled" stage of a project that has no Title Details yet -- the details are saved first
    // fix202 (test note 26): the Title Details and the title scan(s) in one step
    completeTitledWithScans: async (projectId, statusId, details, files) => {
        const fd = new FormData();
        fd.append('data', JSON.stringify(details || {}));
        (files || []).forEach(f => fd.append('scans', f));
        const response = await api.post(`/land/projects/${projectId}/statuses/${statusId}/complete-titled-scans`, fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 180000 });
        return response.data;
    },

    completeTitledStage: async (projectId, statusId, details) => {
        const response = await api.post(`/land/projects/${projectId}/statuses/${statusId}/complete-titled`, details || {});
        return response.data;
    },

    toggleStatusCompletion: async (projectId, statusId, completed) => {
        const response = await api.patch(
            `/land/projects/${projectId}/statuses/${statusId}/complete`,
            null,
            { params: { completed } }
        );
        return response.data;
    },

    reorderProjectStatuses: async (projectId, orderedIds) => {
        const response = await api.put(`/land/projects/${projectId}/statuses/reorder`, orderedIds);
        return response.data;
    },

    removeStatus: async (projectId, statusId, reason) => {   // fix223: reason needed
        await api.delete(`/land/projects/${projectId}/statuses/${statusId}`, { params: { reason } });
    },
};

export default statusTemplateService;
