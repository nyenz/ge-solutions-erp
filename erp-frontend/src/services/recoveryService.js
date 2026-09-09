import api from '../api/axios';
// RECOVERY COCKPIT v2 - cards, priority, locked tray, numbers-only
const recoveryService = {
  getQueue:  (q) => api.get('/recovery/queue', { params: { queue: q || 'ALL' } }),
getQueues: (q) => api.get('/recovery/queues', { params: q ? { q } : {} }),
  getLocked: () => api.get('/recovery/locked'),
  getTags:   () => api.get('/recovery/tags'),
  getStats:  () => api.get('/recovery/stats'),
  getTaskCount: () => api.get('/recovery/stats').then(r => r.data.dueNow),
  getNotes:  (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:   (payload) => api.post('/recovery/notes', payload),
  deleteNote: (noteId) => api.delete('/recovery/notes/' + noteId),
  recordPayment: (projectId, amount, notes) => api.post(`/land/projects/${projectId}/payment`, null, { params: { amount, notes } }),
  getNotifications: () => api.get('/notifications').then(r => r.data),
  getUnreadCount: () => api.get('/notifications/unread-count').then(r => r.data.unread),
  markRead: (id) => api.post('/notifications/' + id + '/read'),
  markAllRead: () => api.post('/notifications/read-all'),
};
export default recoveryService;
