// PATH: erp-frontend/src/services/pendingService.js
// fix181 (12.1 to 12.3): Pending projects. The Employee's own routes and the office's START / REJECT.
import api from '../api/axios';

const pendingService = {
    create: async (data, scans, categories = []) => {
        const fd = new FormData();
        const payload = { ...data };
        delete payload.fileQueue;
        fd.append('data', JSON.stringify(payload));
        if (scans) scans.forEach(f => fd.append('scans', f));
        if (scans && categories.length === scans.length) categories.forEach(c => fd.append('categories', c || ''));
        return (await api.post('/land/pending', fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
    },
    mine: async () => (await api.get('/land/pending/mine')).data,
    view: async (id) => (await api.get(`/land/pending/${id}`)).data,
    update: async (id, data) => (await api.put(`/land/pending/${id}`, data)).data,
    addNote: async (id, content) => (await api.post(`/land/pending/${id}/notes`, { content })).data,
    addDocuments: async (id, files, categories = []) => {
        const fd = new FormData();
        files.forEach(f => fd.append('scans', f));
        if (categories.length === files.length) categories.forEach(c => fd.append('categories', c || ''));
        return (await api.post(`/land/pending/${id}/documents`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
    },
    start: async (id, data) => (await api.post(`/land/pending/${id}/start`, data)).data,
    // fix199 (test note 9): save the numbers / price one at a time; the answer says { started, missing }
    saveParts: async (id, data) => (await api.post(`/land/pending/${id}/save`, data)).data,
    reject: async (id, reason) => (await api.post(`/land/pending/${id}/reject`, { reason })).data,
    count: async () => (await api.get('/land/pending/count')).data,
};

export default pendingService;
