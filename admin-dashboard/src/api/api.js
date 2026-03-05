import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

const TOKEN_STORAGE_KEY = 'adminToken'
const TOKEN_EXPIRY_KEY = 'adminTokenExpiry'
const TOKEN_EXPIRY_MS = 24 * 60 * 60 * 1000

const getStoredToken = () => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)

  if (!token || !expiry) {
    return null
  }

  if (Date.now() > parseInt(expiry)) {
    clearAuth()
    return null
  }

  return token
}

const setStoredToken = (token) => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
  localStorage.setItem(TOKEN_EXPIRY_KEY, Date.now() + TOKEN_EXPIRY_MS)
}

const clearAuth = () => {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(TOKEN_EXPIRY_KEY)
}

api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
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
  updateSettings: (data) => api.put('/admin/settings', data),
  logout: () => clearAuth()
}

export const analyticsApi = {
  getSummary: () => api.get('/analytics/summary'),
  getEvents: (params) => api.get('/analytics/events', { params }),
  getRecipients: () => api.get('/analytics/recipients'),
  getGeo: () => api.get('/analytics/geo'),
  getClients: () => api.get('/analytics/clients'),
  export: () => api.get('/analytics/export')
}

export { getStoredToken, setStoredToken, clearAuth }
export default api
