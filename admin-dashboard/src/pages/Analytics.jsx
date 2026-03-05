import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyticsApi, clearAuth } from '../api/api'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function Analytics() {
  const [summary, setSummary] = useState(null)
  const [events, setEvents] = useState([])
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [summaryRes, eventsRes, clientsRes] = await Promise.all([
        analyticsApi.getSummary(),
        analyticsApi.getEvents({ range: '7d' }),
        analyticsApi.getClients()
      ])
      setSummary(summaryRes.data)
      setEvents(eventsRes.data)
      setClients(clientsRes.data)
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

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
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="ml-4 px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 focus:outline-none"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-2xl font-bold mb-6">Analytics</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Tracking Events Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={events}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#8884d8" name="Events" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Email Clients</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={clients}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {clients.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Summary Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">Total Events</p>
                <p className="text-2xl font-bold">{summary?.total_events || 0}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Unique Recipients</p>
                <p className="text-2xl font-bold">{summary?.unique_recipients || 0}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg. Opens per Day</p>
                <p className="text-2xl font-bold">{summary?.avg_daily_opens || 0}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Top Country</p>
                <p className="text-2xl font-bold">{summary?.top_country || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Analytics
