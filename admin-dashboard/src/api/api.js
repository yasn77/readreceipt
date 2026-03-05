import axios from 'axios'

const API_BASE_URL = '/api'

// SECURITY FIX #101: Cookie-based authentication
// Configure axios to automatically send cookies with requests
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // Send cookies automatically
})

// SECURITY FIX #101: Remove localStorage usage for tokens
// Tokens are now stored in httpOnly cookies, inaccessible to JavaScript
// This prevents XSS attacks from stealing authentication tokens

// Keep these functions for backwards compatibility but they no longer store tokens
const TOKEN_STORAGE_KEY = 'adminToken'

const getStoredToken = () => {
  // No longer used - authentication is via httpOnly cookies
  return null
}

const setStoredToken = (token) => {
  // No longer used - tokens are set via httpOnly cookies from backend
  console.warn('setStoredToken is deprecated - using cookie-based auth')
}

const clearAuth = () => {
  // Clear any legacy localStorage items
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

// Add CSRF token to requests for state-changing operations
api.interceptors.request.use((config) => {
  // For state-changing requests, include CSRF token from cookie
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase())) {
    const csrfToken = getCookie('csrf_token')
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }
  }
  return config
})

// Helper function to get cookie value
const getCookie = (name) => {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
  return null
}

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
  logout: () => api.post('/admin/logout')  // Now calls backend logout endpoint
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
