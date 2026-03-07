import axios from 'axios'
import { UserManager } from 'oidc-client-ts'

const API_BASE_URL = '/api'

// OIDC configuration from environment variables
const oidcConfig = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY || 'http://localhost:8000',
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID || 'admin-dashboard',
  redirect_uri: `${window.location.origin}/callback`,
  response_type: 'code',
  scope: 'openid profile email',
  post_logout_redirect_uri: window.location.origin
}

// Create user manager for OIDC
export const userManager = new UserManager(oidcConfig)

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add OIDC access token
api.interceptors.request.use(async (config) => {
  try {
    const user = await userManager.getUser()
    if (user && user.access_token) {
      config.headers.Authorization = `Bearer ${user.access_token}`
    }
  } catch (error) {
    // No valid token, will be handled by response interceptor
  }
  return config
})

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear any stored session and redirect to login
      userManager.removeUser()
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

export const authApi = {
  login: () => api.post('/auth/login'),
  logout: () => api.post('/auth/logout'),
  callback: (code) => api.post('/auth/callback', { code })
}

export default api
