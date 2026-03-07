import { useState, useEffect } from 'react'
import { adminApi } from '../api/api'

function Settings() {
  const [settings, setSettings] = useState({
    tracking_enabled: true,
    allowed_domains: '',
    log_level: 'INFO'
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await adminApi.getSettings()
      setSettings(response.data)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')

    try {
      await adminApi.updateSettings(settings)
      setMessage('Settings saved successfully!')
    } catch {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold">Read Receipt</h1>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-2xl font-bold mb-6">Settings</h2>

          <div className="bg-white shadow rounded-lg p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.tracking_enabled}
                    onChange={(e) => setSettings({ ...settings, tracking_enabled: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable tracking</span>
                </label>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={cookieSetting}
                    onChange={(e) => handleCookieToggle(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Ignore my own opens (cookie-based filtering)
                  </span>
                </label>
                <p className="ml-6 mt-1 text-xs text-gray-500">
                  Sets a cookie to prevent tracking when you view your sent folder.
                  This helps avoid false positives from your own email opens.
                </p>
              </div>

              <div>
                <label htmlFor="allowed_domains" className="block text-sm font-medium text-gray-700">
                  Allowed Domains (comma-separated)
                </label>
                <input
                  type="text"
                  id="allowed_domains"
                  value={settings.allowed_domains}
                  onChange={(e) => setSettings({ ...settings, allowed_domains: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
                  placeholder="gmail.com,outlook.com"
                />
              </div>

              <div>
                <label htmlFor="log_level" className="block text-sm font-medium text-gray-700">
                  Log Level
                </label>
                <select
                  id="log_level"
                  value={settings.log_level}
                  onChange={(e) => setSettings({ ...settings, log_level: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </div>

              {message && (
                <div className={`rounded-md p-4 ${message.includes('success') ? 'bg-green-50' : 'bg-red-50'}`}>
                  <p className={`text-sm ${message.includes('success') ? 'text-green-800' : 'text-red-800'}`}>
                    {message}
                  </p>
                </div>
              )}

              <div>
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Settings'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Settings
