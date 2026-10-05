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
  // fix181: clientRequestId = one id per payment window; a retried send with the same id is refused by the server
  // fix181 (16.9): paidOn (YYYY-MM-DD) only when the money came on an earlier day
  recordPayment: (projectId, amount, notes, receipt, payerId, allocation, clientRequestId, paidOn) => {
    const fd = new FormData();
    if (paidOn) fd.append('paidOn', paidOn);
    if (clientRequestId) fd.append('clientRequestId', clientRequestId);
    fd.append('amount', String(amount));
    if (notes) fd.append('notes', notes);
    if (payerId) fd.append('payerId', payerId);
    if (allocation) fd.append('allocation', allocation);
    if (receipt) fd.append('receipt', receipt, receipt.name);
    return api.post(`/land/projects/${projectId}/payment`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  // fix181 (17.6, 21.1): before = the createdAt of the last row shown (older page)
  getNotifications: (before) => api.get('/notifications', { params: before ? { before } : {} }).then(r => r.data),
  getSummary: () => api.get('/notifications/summary').then(r => r.data),
  getUnreadCount: () => api.get('/notifications/unread-count').then(r => r.data.unread),
  markRead: (id) => api.post('/notifications/' + id + '/read'),
  // fix181 (17.4(3), 17.18b): one call, one group, only alerts up to the newest one shown
  markAllRead: (group, upTo) => api.post('/notifications/read-all', null, { params: { ...(group ? { group } : {}), ...(upTo ? { upTo } : {}) } }),
};
export default recoveryService;
