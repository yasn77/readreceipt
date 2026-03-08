import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * IP Filtering Management Page
 * Issue #151 - IP-Based Own-Open Filtering
 */
function IPFiltering() {
  const navigate = useNavigate();
  const [ipBlocklist, setIpBlocklist] = useState([]);
  const [newIp, setNewIp] = useState('');
  const [validationError, setValidationError] = useState('');
  const [validationSuccess, setValidationSuccess] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Auth token from localStorage
  const authToken = localStorage.getItem('authToken');

  useEffect(() => {
    // Check if authenticated
    if (!authToken) {
      navigate('/login');
      return;
    }

    fetchIpBlocklist();
  }, [authToken, navigate]);

  /**
   * Fetch current IP blocklist
   */
  const fetchIpBlocklist = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/ip-blocklist', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          navigate('/login');
          return;
        }
        throw new Error('Failed to fetch IP blocklist');
      }

      const data = await response.json();
      setIpBlocklist(data.ip_blocklist || []);
    } catch (error) {
      console.error('Error fetching IP blocklist:', error);
      setMessage({ type: 'error', text: 'Failed to load IP blocklist' });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Validate IP address format
   */
  const validateIp = async (ip) => {
    try {
      const response = await fetch('/api/admin/ip-blocklist/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ ip_address: ip }),
      });

      const data = await response.json();
      return { valid: data.valid, message: data.error || data.normalized };
    } catch (error) {
      console.error('Error validating IP:', error);
      return { valid: false, message: 'Validation failed' };
    }
  };

  /**
   * Add IP to blocklist
   */
  const handleAddIp = async (e) => {
    e.preventDefault();
    setSaving(true);
    setValidationError('');
    setValidationSuccess(null);

    try {
      // First validate the IP
      const validation = await validateIp(newIp.trim());
      
      if (!validation.valid) {
        setValidationError(validation.message);
        setSaving(false);
        return;
      }

      setValidationSuccess(`Normalized IP: ${validation.message}`);

      // Add to blocklist
      const response = await fetch('/api/admin/ip-blocklist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ ip_address: newIp.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to add IP');
      }

      setMessage({ type: 'success', text: `IP ${newIp.trim()} added to blocklist` });
      setNewIp('');
      fetchIpBlocklist();
    } catch (error) {
      console.error('Error adding IP:', error);
      setMessage({ type: 'error', text: error.message });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    }
  };

  /**
   * Remove IP from blocklist
   */
  const handleRemoveIp = async (ip) => {
    if (!window.confirm(`Remove ${ip} from blocklist?`)) {
      return;
    }

    setSaving(true);

    try {
      const response = await fetch(`/api/admin/ip-blocklist/${encodeURIComponent(ip)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to remove IP');
      }

      setMessage({ type: 'success', text: `IP ${ip} removed from blocklist` });
      fetchIpBlocklist();
    } catch (error) {
      console.error('Error removing IP:', error);
      setMessage({ type: 'error', text: error.message });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    }
  };

  /**
   * Handle IP input change
   */
  const handleIpChange = (e) => {
    setNewIp(e.target.value);
    setValidationError('');
    setValidationSuccess(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading IP blocklist...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">IP Filtering</h1>
        <p className="text-gray-600 mt-1">
          Block tracking from specific IP addresses to prevent recording your own email opens.
        </p>
      </div>

      {message.text && (
        <div className={`mb-4 p-4 rounded-md ${
          message.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-800' 
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add IP Form */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Add IP to Blocklist
          </h2>
          
          <form onSubmit={handleAddIp}>
            <div className="mb-4">
              <label htmlFor="ipAddress" className="block text-sm font-medium text-gray-700 mb-2">
                IP Address (IPv4 or IPv6)
              </label>
              <input
                type="text"
                id="ipAddress"
                value={newIp}
                onChange={handleIpChange}
                placeholder="e.g., 192.168.1.1 or 2001:db8::1"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                  validationError
                    ? 'border-red-300 focus:ring-red-200'
                    : 'border-gray-300 focus:ring-blue-200'
                }`}
              />
              
              {validationError && (
                <p className="mt-2 text-sm text-red-600">{validationError}</p>
              )}
              
              {validationSuccess && (
                <p className="mt-2 text-sm text-green-600">{validationSuccess}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={saving || !newIp.trim()}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Adding...' : 'Add IP Address'}
            </button>
          </form>

          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <h3 className="text-sm font-medium text-blue-900 mb-1">What does this do?</h3>
            <p className="text-sm text-blue-700">
              When you view your sent emails, tracking pixels will be blocked if the request 
              comes from a blocked IP address. This prevents your own opens from being recorded.
            </p>
          </div>
        </div>

        {/* IP Blocklist */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Current Blocklist ({ipBlocklist.length})
          </h2>

          {ipBlocklist.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <p className="mt-2">No IP addresses blocked yet</p>
              <p className="text-sm">Add an IP address to start filtering</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {ipBlocklist.map((ip, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-mono text-gray-700">{ip}</span>
                    <span className="text-xs text-gray-500">
                      {ip.includes(':') ? 'IPv6' : 'IPv4'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleRemoveIp(ip)}
                    disabled={saving}
                    className="text-red-600 hover:text-red-800 disabled:text-gray-400 transition-colors"
                    title="Remove from blocklist"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Help & Information</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-2">How it works</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Add IP addresses you want to block</li>
              <li>• Supports both IPv4 and IPv6 formats</li>
              <li>• Blocking is applied immediately</li>
              <li>• All blocklist changes are audited</li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-2">Example IPs</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Home network: 192.168.1.1</li>
              <li>• Office network: 10.0.0.1</li>
              <li>• VPN endpoint: 203.0.113.1</li>
              <li>• IPv6: 2001:db8::1</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default IPFiltering;
