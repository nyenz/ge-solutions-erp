import api from '../api/axios';

// RECOVERY COCKPIT service - numbers-only, tag-driven
const recoveryService = {
  getQueue: () => api.get('/recovery/queue'),
  getTags:  () => api.get('/recovery/tags'),
  getStats: () => api.get('/recovery/stats'),
  getNotes: (clientId) => api.get('/recovery/clients/' + clientId + '/notes'),
  logNote:  (payload) => api.post('/recovery/notes', payload),
};
export default recoveryService;
