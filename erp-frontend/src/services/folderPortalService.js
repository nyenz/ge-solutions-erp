import api from '../api/axios';
export const folderPortalService = {
  getReceivable: (id) => api.get(`/land/portal/${id}/receivable`).then(r => r.data),
  getPortfolio:  (id) => api.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter:    (id) => api.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),
  exit: (id, action, reason) => api.post(`/land/portal/${id}/receivable/exit`, reason ? { action, reason } : { action }).then(r => r.data),
  reduceFees: (id, newFees, reason) => api.post(`/land/portal/${id}/receivable/reduce-fees`, { newFees: String(newFees), reason }).then(r => r.data),
  settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
  toggleProblem: (id, note) => api.post(`/land/portal/${id}/toggle-problem`, null, { params: note ? { note } : {} }).then(r => r.data),
};
export default folderPortalService;
