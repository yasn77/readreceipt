import { useAuth } from 'react-oidc-context'
import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

function Callback() {
  const auth = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (auth.isAuthenticated) {
      // Redirect to dashboard after successful authentication
      navigate('/')
    } else if (auth.error) {
      console.error('Callback error:', auth.error)
      navigate('/login')
    }
    // auth.isLoading is true while processing the callback
  }, [auth.isAuthenticated, auth.error, auth.isLoading, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Completing authentication...
        </h2>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-sm text-gray-600">
          Please wait while we complete your login
        </p>
      </div>
    </div>
  )
}

export default Callback
