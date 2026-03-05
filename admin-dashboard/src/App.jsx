import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Recipients from './pages/Recipients'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'
import api from './api/api'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // SECURITY FIX #101: Cookie-based authentication
    // Check authentication status by making a test request
    // The browser will automatically send cookies
    const checkAuth = async () => {
      try {
        // Try to fetch stats - if cookie is valid, will succeed
        await api.get('/admin/stats')
        setIsAuthenticated(true)
      } catch (error) {
        // 401 means not authenticated
        setIsAuthenticated(false)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={<Login onLogin={() => setIsAuthenticated(true)} />}
      />
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Dashboard />
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
  )
}

export default App
