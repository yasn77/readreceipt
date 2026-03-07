import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { AuthProvider } from 'react-oidc-context'
import { userManager } from './api/api'
import Login from './pages/Login'
import Callback from './pages/Callback'
import Dashboard from './pages/Dashboard'
import Recipients from './pages/Recipients'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'

// OIDC configuration
const oidcConfig = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY || 'http://localhost:8000',
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID || 'admin-dashboard',
  redirect_uri: `${window.location.origin}/callback`,
  response_type: 'code',
  scope: 'openid profile email',
  post_logout_redirect_uri: window.location.origin,
  automaticSilentRenew: true,
  validateSubOnSilentRenew: true
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is already authenticated via OIDC
    const checkAuth = async () => {
      try {
        const user = await userManager.getUser()
        setIsAuthenticated(!!user && !user.expired)
      } catch (error) {
        console.error('Error checking auth status:', error)
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <AuthProvider {...oidcConfig}>
      <Routes>
        <Route
          path="/login"
          element={<Login onLogin={handleLogin} onLogout={handleLogout} />}
        />
        <Route
          path="/callback"
          element={<Callback />}
        />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Dashboard onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/recipients"
          element={
            isAuthenticated ? (
              <Recipients />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/analytics"
          element={
            isAuthenticated ? (
              <Analytics />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/settings"
          element={
            isAuthenticated ? (
              <Settings />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
