// PATH: erp-frontend/src/services/companyExpenseService.js
import api from '../api/axios';

/**
 * GE SOLUTIONS - COMPANY FINANCIALS SERVICE (PHASE 5)
 * Talks to /finance/company-expenses. Restricted server-side to
 * ROLE_ADMIN and ROLE_DIRECTOR.
 */
const companyExpenseService = {
    getAll: async (page = 0, size = 50) => {
        const response = await api.get('/finance/company-expenses', { params: { page, size } });
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get('/finance/company-expenses/categories');
        return response.data;
    },

    getSummary: async () => {
        const response = await api.get('/finance/company-expenses/summary');
        return response.data;
    },

    create: async (data) => {
        const response = await api.post('/finance/company-expenses', data);
        return response.data;
    },

    recordPayment: async (id, amount, notes) => {
        const response = await api.post(`/finance/company-expenses/${id}/payment`, { amount, notes });
        return response.data;
    },

    remove: async (id) => {
        await api.delete(`/finance/company-expenses/${id}`);
    },
};

export default companyExpenseService;
