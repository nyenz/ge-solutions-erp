// PATH: erp-frontend/src/services/statusTemplateService.js
import api from '../api/axios';

/**
 * GOLDEN SEED - STATUS TEMPLATE SERVICE (fix180: was stageTemplateService)
 *
 * Every project type has its own ordered status list (the master template). Adding a status -- to a type's list or
 * to one project -- is for Admin, Manager and Director only; the server refuses it for Secretary.
 */
const statusTemplateService = {

    // the master list of one project type (no type = every type's list)
    getTemplate: async (projectType) => {
        const response = await api.get('/status-templates', { params: projectType ? { projectType } : {} });
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
        const response = await api.get(`/land/projects/${projectId}/statuses`);
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

    removeStatus: async (projectId, statusId) => {
        await api.delete(`/land/projects/${projectId}/statuses/${statusId}`);
    },
};

export default statusTemplateService;
