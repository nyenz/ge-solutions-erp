import api from '../api/axios';
export const folderPortalService = {
  getPortfolio:  (id) => api.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter:    (id, reason) => api.post(`/land/portal/${id}/receivable/enter`, { reason }).then(r => r.data),
  exit: (id, action, reason) => api.post(`/land/portal/${id}/receivable/exit`, reason ? { action, reason } : { action }).then(r => r.data),
  reduceFees: (id, newFees, reason) => api.post(`/land/portal/${id}/receivable/reduce-fees`, { newFees: String(newFees), reason }).then(r => r.data),
  settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
  // fix167: says what is WANTED (flag true = flag, false = clear) so two clicks at once cannot undo each other
  toggleProblem: (id, note, flag) => api.post(`/land/portal/${id}/toggle-problem`, null, { params: { note, flag } }).then(r => r.data),
};
export default folderPortalService;
