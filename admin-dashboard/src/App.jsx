import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Recipients from './pages/Recipients'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'
import { getStoredToken } from './api/api'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = getStoredToken()
    setIsAuthenticated(!!token)
  }, [])

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
