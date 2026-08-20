// PATH: erp-frontend/src/services/expenseService.js
import api from '../api/axios';

/**
 * GE SOLUTIONS - EXPENSES SERVICE (EXPENSES REBUILD)
 * Talks to /finance/expenses. Logging/editing/presets are Manager+.
 * Delete, search, and summary are Director/Admin only (server-enforced).
 */
const expenseService = {
    getPresets: async () => {
        const response = await api.get('/finance/expenses/presets');
        return response.data;
    },

    createPreset: async (name) => {
        const response = await api.post('/finance/expenses/presets', { name });
        return response.data;
    },

    create: async ({ category, amount, note }) => {
        const response = await api.post('/finance/expenses', { category, amount, note });
        return response.data;
    },

    getRecent: async (hours = 24) => {
        const response = await api.get('/finance/expenses/recent', { params: { hours } });
        return response.data;
    },

    update: async (id, { category, amount, note }) => {
        const response = await api.put(`/finance/expenses/${id}`, { category, amount, note });
        return response.data;
    },

    remove: async (id) => {
        await api.delete(`/finance/expenses/${id}`);
    },

    search: async (filters = {}, page = 0, size = 50) => {
        const response = await api.get('/finance/expenses/search', {
            params: { ...filters, page, size }
        });
        return response.data;
    },

    getSummary: async (period = 'MONTH', from, to) => {
        const response = await api.get('/finance/expenses/summary', {
            params: { period, from, to }
        });
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get('/finance/expenses/categories');
        return response.data;
    },

    getByStaff: async (period = 'MONTH', from, to) => {
        const response = await api.get('/finance/expenses/analytics/by-staff', {
            params: { period, from, to }
        });
        return response.data;
    },

    getTimeSeries: async (period = 'MONTH', from, to, bucket = 'DAY') => {
        const response = await api.get('/finance/expenses/analytics/timeseries', {
            params: { period, from, to, bucket }
        });
        return response.data;
    },
};

export default expenseService;
