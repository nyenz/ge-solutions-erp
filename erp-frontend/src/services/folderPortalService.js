// PATH: erp-frontend/src/services/landService.js
import api from '../api/axios';


export const folderPortalService = {
  getReceivable: (id) => api.get(`/land/portal/${id}/receivable`).then(r => r.data),
  getPortfolio: (id) => api.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter: (id) => api.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),
  exit: (id, action) => api.post(`/land/portal/${id}/receivable/exit`, { action }).then(r => r.data),
  settings: (id, payload) => api.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
};
export default folderPortalService;
