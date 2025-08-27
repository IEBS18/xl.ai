import React, { useState } from "react"
import { X, Database, Loader2, TestTube, CheckCircle, AlertCircle } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import { BACKEND_URL } from "../utils/constants"

const DatabaseConnectionModal = ({ isOpen, onClose, onSuccess }) => {
  const { isDark, themeClasses } = useTheme()
  const [formData, setFormData] = useState({
    connection_type: 'postgresql',
    host: 'localhost',
    port: '5432',
    database: '',
    username: '',
    password: ''
  })
  const [isConnecting, setIsConnecting] = useState(false)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [connectionError, setConnectionError] = useState('')
  const [testResult, setTestResult] = useState(null)

  const databaseTypes = {
    postgresql: { name: 'PostgreSQL', defaultPort: '5432' },
    mysql: { name: 'MySQL', defaultPort: '3306' },
    sqlite: { name: 'SQLite', defaultPort: '' },
    mssql: { name: 'SQL Server', defaultPort: '1433' }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Auto-update port when database type changes
    if (field === 'connection_type') {
      setFormData(prev => ({
        ...prev,
        port: databaseTypes[value].defaultPort
      }))
    }
    
    // Clear previous test results and errors when form changes
    setTestResult(null)
    setConnectionError('')
  }

  const handleTestConnection = async () => {
    setIsTestingConnection(true)
    setConnectionError('')
    setTestResult(null)
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/database/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        credentials: 'include'
      })
      
      const result = await response.json()
      
      if (result.success) {
        setTestResult({
          success: true,
          message: result.message,
          tablesCount: result.tables_count
        })
      } else {
        setTestResult({
          success: false,
          message: result.message
        })
      }
      
    } catch (error) {
      setTestResult({
        success: false,
        message: error.message || 'Connection test failed'
      })
    } finally {
      setIsTestingConnection(false)
    }
  }

  const handleConnect = async () => {
    setIsConnecting(true)
    setConnectionError('')
    
    try {
      const connectResponse = await fetch(`${BACKEND_URL}/api/database/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        credentials: 'include'
      })
      
      const result = await connectResponse.json()
      
      if (result.success) {
        onSuccess(result.session_id)
        onClose()
      } else {
        throw new Error(result.error || 'Connection failed')
      }
      
    } catch (error) {
      setConnectionError(error.message)
    } finally {
      setIsConnecting(false)
    }
  }

  const isFormValid = () => {
    return formData.host && formData.database && formData.username && formData.password
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className={`${isDark ? 'bg-black/90 border-white/20' : 'bg-white/95 border-black/20'} 
        rounded-2xl shadow-2xl border backdrop-blur-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto`}>
        
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Database size={24} className={themeClasses.text} />
            <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Connect Database</h2>
          </div>
          <button 
            onClick={onClose} 
            className={`${themeClasses.textMuted} hover:${themeClasses.text} p-1 rounded-lg transition-colors`}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); handleConnect(); }} className="space-y-4">
          <div>
            <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
              Database Type
            </label>
            <select 
              value={formData.connection_type}
              onChange={(e) => handleInputChange('connection_type', e.target.value)}
              className={`w-full p-3 rounded-xl ${isDark 
                ? 'bg-white/10 border-white/20 text-white' 
                : 'bg-black/5 border-black/20 text-black'
              } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
            >
              {Object.entries(databaseTypes).map(([key, { name }]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
                Host
              </label>
              <input
                type="text"
                value={formData.host}
                onChange={(e) => handleInputChange('host', e.target.value)}
                placeholder="localhost"
                className={`w-full p-3 rounded-xl ${isDark 
                  ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
                  : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
                } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
                required
              />
            </div>
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
                Port
              </label>
              <input
                type="text"
                value={formData.port}
                onChange={(e) => handleInputChange('port', e.target.value)}
                placeholder={databaseTypes[formData.connection_type].defaultPort}
                className={`w-full p-3 rounded-xl ${isDark 
                  ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
                  : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
                } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
                required
              />
            </div>
          </div>

          <div>
            <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
              Database Name
            </label>
            <input
              type="text"
              value={formData.database}
              onChange={(e) => handleInputChange('database', e.target.value)}
              placeholder="my_database"
              className={`w-full p-3 rounded-xl ${isDark 
                ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
                : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
              } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
              required
            />
          </div>

          <div>
            <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
              Username
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              placeholder="username"
              className={`w-full p-3 rounded-xl ${isDark 
                ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
                : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
              } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
              required
            />
          </div>

          <div>
            <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
              Password
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder="password"
              className={`w-full p-3 rounded-xl ${isDark 
                ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
                : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
              } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
              required
            />
          </div>

          {/* Test Connection Button */}
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={!isFormValid() || isTestingConnection || isConnecting}
            className={`w-full py-2.5 px-4 ${isDark 
              ? 'bg-blue-600/20 hover:bg-blue-600/30 border-blue-500/30 text-blue-300' 
              : 'bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700'
            } border rounded-xl font-medium transition-all duration-200 
              disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2`}
          >
            {isTestingConnection ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Testing Connection...</span>
              </>
            ) : (
              <>
                <TestTube size={16} />
                <span>Test Connection</span>
              </>
            )}
          </button>

          {/* Test Result */}
          {testResult && (
            <div className={`p-3 rounded-xl border ${testResult.success 
              ? 'bg-green-500/20 border-green-500/30' 
              : 'bg-red-500/20 border-red-500/30'
            }`}>
              <div className="flex items-center space-x-2">
                {testResult.success ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <AlertCircle size={16} className="text-red-400" />
                )}
                <p className={`text-sm ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                  {testResult.message}
                </p>
              </div>
              {testResult.success && testResult.tablesCount && (
                <p className={`text-xs ${themeClasses.textMuted} mt-1`}>
                  Found {testResult.tablesCount} tables in database
                </p>
              )}
            </div>
          )}

          {/* Connection Error */}
          {connectionError && (
            <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-xl">
              <div className="flex items-center space-x-2">
                <AlertCircle size={16} className="text-red-400" />
                <p className="text-red-400 text-sm">{connectionError}</p>
              </div>
            </div>
          )}

          {/* Connect Button */}
          <button
            type="submit"
            disabled={!isFormValid() || isConnecting || isTestingConnection || (testResult && !testResult.success)}
            className={`w-full py-3 px-6 ${themeClasses.button} rounded-xl font-medium transition-all duration-200 
              disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2`}
          >
            {isConnecting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <Database size={16} />
                <span>Connect & Start Analysis</span>
              </>
            )}
          </button>
        </form>

        <div className={`mt-4 p-3 rounded-xl ${isDark ? 'bg-blue-600/10' : 'bg-blue-50'}`}>
          <p className={`text-xs ${themeClasses.textMuted}`}>
            💡 <strong>Tip:</strong> Test your connection first to ensure it's working before proceeding with analysis.
          </p>
        </div>
      </div>
    </div>
  )
}

export default DatabaseConnectionModal