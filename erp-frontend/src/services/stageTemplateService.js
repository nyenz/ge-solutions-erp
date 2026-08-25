// PATH: erp-frontend/src/services/stageTemplateService.js
import api from '../api/axios';

/**
 * GOLDEN SEED - STAGE TEMPLATE SERVICE (PHASE 4A)
 *
 * Backend API wrapper only. The Intake checkbox/cost UI and the FolderPage
 * dynamic stage display that consume this are built in Phase 4B.
 */
const stageTemplateService = {

    getTemplate: async () => {
        const response = await api.get('/stage-templates');
        return response.data;
    },

    addTemplateStage: async (stageName, defaultCost, displayOrder) => {
        const response = await api.post('/stage-templates', { stageName, defaultCost, displayOrder });
        return response.data;
    },

    updateTemplateStage: async (id, stageName, defaultCost) => {
        const response = await api.put(`/stage-templates/${id}`, { stageName, defaultCost });
        return response.data;
    },

    deactivateTemplateStage: async (id) => {
        await api.delete(`/stage-templates/${id}`);
    },

    getProjectStages: async (projectId) => {
        const response = await api.get(`/land/projects/${projectId}/stages`);
        return response.data;
    },

    attachStages: async (projectId, stageRequests) => {
        const response = await api.post(`/land/projects/${projectId}/stages`, stageRequests);
        return response.data;
    },

    toggleStageCompletion: async (projectId, stageId, completed) => {
        const response = await api.patch(
            `/land/projects/${projectId}/stages/${stageId}/complete`,
            null,
            { params: { completed } }
        );
        return response.data;
    },

    updateStageCost: async (projectId, stageId, cost, notes) => {
        const response = await api.patch(
            `/land/projects/${projectId}/stages/${stageId}/cost`,
            { cost, notes }
        );
        return response.data;
    },

    removeStage: async (projectId, stageId) => {
        await api.delete(`/land/projects/${projectId}/stages/${stageId}`);
    },
    deleteTemplateStage: async (id) => {
        await api.delete(`/stage-templates/${id}`);
    },

};

export default stageTemplateService;
