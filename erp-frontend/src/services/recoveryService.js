import api from '../api/axios';
// RECOVERY COCKPIT v2 - cards, priority, locked tray, numbers-only
const recoveryService = {
getClientLedger: () => api.get('/recovery/clients/ledger').then(r => r.data),
getClientDossier: (clientId) => api.get('/recovery/clients/' + clientId + '/dossier').then(r => r.data),
  getQueue:  (q) => api.get('/recovery/queue', { params: { queue: q || 'ALL' } }),
getQueues: (q) => api.get('/recovery/queues', { params: q ? { q } : {} }),
  getLocked: () => api.get('/recovery/locked'),
  getTags:   () => api.get('/recovery/tags'),
  getStats:  () => api.get('/recovery/stats'),
  getTaskCount: () => api.get('/recovery/stats').then(r => r.data.dueNow),
  getNotes:  (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:   (payload) => api.post('/recovery/notes', payload),
  deleteNote: (noteId) => api.delete('/recovery/notes/' + noteId),
  // fix165: a payment is sent TOGETHER with its receipt file; the server refuses it without one.
  // fix167: also WHO paid (payerId) and what for (allocation TITLE or STORAGE)
  recordPayment: (projectId, amount, notes, receipt, payerId, allocation) => {
    const fd = new FormData();
    fd.append('amount', String(amount));
    if (notes) fd.append('notes', notes);
    if (payerId) fd.append('payerId', payerId);
    if (allocation) fd.append('allocation', allocation);
    if (receipt) fd.append('receipt', receipt, receipt.name);
    return api.post(`/land/projects/${projectId}/payment`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  getNotifications: () => api.get('/notifications').then(r => r.data),
  getUnreadCount: () => api.get('/notifications/unread-count').then(r => r.data.unread),
  markRead: (id) => api.post('/notifications/' + id + '/read'),
  markAllRead: () => api.post('/notifications/read-all'),
};
export default recoveryService;
