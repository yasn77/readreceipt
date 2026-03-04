import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('adminToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('adminToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const adminApi = {
  login: (token) => api.post('/admin/login', { token }),
  getRecipients: (params) => api.get('/admin/recipients', { params }),
  createRecipient: (data) => api.post('/admin/recipients', data),
  updateRecipient: (id, data) => api.put(`/admin/recipients/${id}`, data),
  deleteRecipient: (id) => api.delete(`/admin/recipients/${id}`),
  getStats: () => api.get('/admin/stats'),
  getSettings: () => api.get('/admin/settings'),
  updateSettings: (data) => api.put('/admin/settings', data)
}

export const analyticsApi = {
  getSummary: () => api.get('/analytics/summary'),
  getEvents: (params) => api.get('/analytics/events', { params }),
  getRecipients: () => api.get('/analytics/recipients'),
  getGeo: () => api.get('/analytics/geo'),
  getClients: () => api.get('/analytics/clients'),
  export: () => api.get('/analytics/export')
}

export default api
