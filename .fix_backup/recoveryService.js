import api from '../api/axios';

// RECOVERY COCKPIT v2 - cards, priority, locked tray, numbers-only
const recoveryService = {
  getQueue:  () => api.get('/recovery/queue'),
  getLocked: () => api.get('/recovery/locked'),
  getTags:   () => api.get('/recovery/tags'),
  getStats:  () => api.get('/recovery/stats'),
  getTaskCount: () => api.get('/recovery/stats').then(r => r.data.dueNow),
  getNotes:  (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:   (payload) => api.post('/recovery/notes', payload),
};
export default recoveryService;
