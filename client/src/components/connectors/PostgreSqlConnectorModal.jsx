import React, { useState } from 'react';
import { X, AlertCircle, ExternalLink, Loader2, Database, Server } from 'lucide-react';
import axios from 'axios';

const PostgreSqlConnectorModal = ({ isOpen, onClose, onSuccess, connector }) => {
  const [step, setStep] = useState(1); // Step 1: Server connection, Step 2: Database selection
  const [formData, setFormData] = useState({
    connectionName: '',
    host: '',
    port: '5432',
    user: '',
    password: '',
    ssl: false,
    selectedDatabase: ''
  });
  
  const [databases, setDatabases] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [testStatus, setTestStatus] = useState(null);

  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' });
    }
    setTestStatus(null);
  };

  const validateServerConnection = () => {
    const newErrors = {};
    
    if (!formData.host) {
      newErrors.host = 'Host is required';
    }
    if (!formData.port) {
      newErrors.port = 'Port is required';
    }
    if (!formData.user) {
      newErrors.user = 'Username is required';
    }
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateDatabaseSelection = () => {
    const newErrors = {};
    
    if (!formData.connectionName) {
      newErrors.connectionName = 'Connection name is required';
    }
    if (!formData.selectedDatabase) {
      newErrors.selectedDatabase = 'Please select a database';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const testServerConnection = async () => {
    if (!validateServerConnection()) return;

    setIsLoading(true);
    setTestStatus(null);

    try {
      const response = await axios.post('http://localhost:5000/api/connectors/postgres/test', {
        host: formData.host,
        port: parseInt(formData.port),
        user: formData.user,
        password: formData.password
      });

      if (response.data.success) {
        setDatabases(response.data.databases);
        setTestStatus({ 
          type: 'success', 
          message: `Connected! Found ${response.data.databases.length} databases` 
        });
        
        // Auto-advance to step 2 after successful connection
        setTimeout(() => {
          setStep(2);
          setTestStatus(null);
        }, 1500);
      } else {
        setTestStatus({ type: 'error', message: response.data.message || 'Connection failed' });
      }
    } catch (error) {
      setTestStatus({ 
        type: 'error', 
        message: error.response?.data?.message || 'Failed to connect to server' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const connectToDatabase = async () => {
    if (!validateDatabaseSelection()) return;

    setIsLoading(true);
    setTestStatus(null);

    try {
      const response = await axios.post('http://localhost:5000/api/connectors/postgres/connect', {
        connectionName: formData.connectionName,
        host: formData.host,
        port: parseInt(formData.port),
        user: formData.user,
        password: formData.password,
        database: formData.selectedDatabase,
        ssl: formData.ssl
      });

      if (response.data.success) {
        setTestStatus({ 
          type: 'success', 
          message: `Connected to ${response.data.database}! Found ${response.data.tableCount} tables` 
        });
        
        // Pass connection details to parent
        setTimeout(() => {
          onSuccess({
            connectionName: formData.connectionName,
            connectionId: response.data.connectionId,
            database: response.data.database,
            tables: response.data.tables
          });
        }, 1000);
      } else {
        setTestStatus({ type: 'error', message: response.data.message || 'Connection failed' });
      }
    } catch (error) {
      setTestStatus({ 
        type: 'error', 
        message: error.response?.data?.message || 'Failed to connect to database' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setTestStatus(null);
    setErrors({});
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {step === 1 ? 'Connect to PostgreSQL Server' : 'Select Database'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={isLoading}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          {/* Progress indicator */}
          <div className="mt-4 flex items-center space-x-2">
            <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
              <Server className="w-4 h-4 mr-1" />
              <span className="text-sm">Server</span>
            </div>
            <div className={`flex-1 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
              <Database className="w-4 h-4 mr-1" />
              <span className="text-sm">Database</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-blue-50 rounded-xl flex items-center justify-center">
              <img 
                src="/connector/Postgre_logo.png" 
                alt="PostgreSQL logo"
                className="w-16 h-16 object-contain"
              />
            </div>
          </div>

          {step === 1 ? (
            <>
              <div className="text-center mb-6">
                <h3 className="text-2xl font-semibold mb-2">PostgreSQL Server</h3>
                <p className="text-gray-600">Connect to your PostgreSQL server to view available databases</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Host *
                  </label>
                  <input
                    type="text"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.host ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="localhost or your server address"
                    value={formData.host}
                    onChange={(e) => handleInputChange('host', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.host && (
                    <p className="text-red-500 text-sm mt-1">{errors.host}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Port *
                  </label>
                  <input
                    type="number"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.port ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="5432"
                    value={formData.port}
                    onChange={(e) => handleInputChange('port', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.port && (
                    <p className="text-red-500 text-sm mt-1">{errors.port}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.user ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="postgres"
                    value={formData.user}
                    onChange={(e) => handleInputChange('user', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.user && (
                    <p className="text-red-500 text-sm mt-1">{errors.user}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password *
                  </label>
                  <input
                    type="password"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.password ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.password && (
                    <p className="text-red-500 text-sm mt-1">{errors.password}</p>
                  )}
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={formData.ssl}
                      onChange={(e) => handleInputChange('ssl', e.target.checked)}
                      disabled={isLoading}
                    />
                    <span className="text-sm">Use SSL connection</span>
                  </label>
                </div>

                {testStatus && (
                  <div className={`p-3 rounded-lg ${
                    testStatus.type === 'success' 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <p className={`text-sm ${
                      testStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {testStatus.message}
                    </p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="text-center mb-6">
                <h3 className="text-2xl font-semibold mb-2">Select Database</h3>
                <p className="text-gray-600">Choose a database to connect and embed for AI queries</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Connection Name *
                  </label>
                  <input
                    type="text"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.connectionName ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter a name for this connection"
                    value={formData.connectionName}
                    onChange={(e) => handleInputChange('connectionName', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.connectionName && (
                    <p className="text-red-500 text-sm mt-1">{errors.connectionName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Database *
                  </label>
                  <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-lg">
                    {databases.map((db) => (
                      <label
                        key={db}
                        className={`flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer ${
                          formData.selectedDatabase === db ? 'bg-blue-50' : ''
                        }`}
                      >
                        <input
                          type="radio"
                          name="database"
                          value={db}
                          checked={formData.selectedDatabase === db}
                          onChange={(e) => handleInputChange('selectedDatabase', e.target.value)}
                          disabled={isLoading}
                          className="mr-2"
                        />
                        <Database className="w-4 h-4 mr-2 text-gray-500" />
                        <span className="text-sm">{db}</span>
                      </label>
                    ))}
                  </div>
                  {errors.selectedDatabase && (
                    <p className="text-red-500 text-sm mt-1">{errors.selectedDatabase}</p>
                  )}
                </div>

                {testStatus && (
                  <div className={`p-3 rounded-lg ${
                    testStatus.type === 'success' 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <p className={`text-sm ${
                      testStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {testStatus.message}
                    </p>
                  </div>
                )}

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    The selected database will be embedded and indexed for natural language queries using AI.
                  </p>
                  <p className="text-sm text-blue-800 mt-2">
                    Server: {formData.host}:{formData.port} | User: {formData.user}
                  </p>
                </div>
              </div>
            </>
          )}

          <div className="flex items-center space-x-2 text-sm text-gray-600 mt-4">
            <AlertCircle className="w-4 h-4" />
            <span>Your credentials are encrypted and stored securely</span>
          </div>

          <div className="mt-6 flex items-center space-x-2 text-sm">
            <a href="#" className="text-blue-600 hover:underline flex items-center">
              Read the Documentation
              <ExternalLink className="w-3 h-3 ml-1" />
            </a>
            <span className="text-gray-400">|</span>
            <a href="#" className="text-blue-600 hover:underline flex items-center">
              Security & Trust Center
              <ExternalLink className="w-3 h-3 ml-1" />
            </a>
          </div>

          <div className="mt-8 flex justify-end space-x-3">
            {step === 2 && (
              <button
                onClick={handleBack}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isLoading}
              >
                Back
              </button>
            )}
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancel
            </button>
            {step === 1 ? (
              <button
                onClick={testServerConnection}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Connecting...
                  </span>
                ) : (
                  'Connect to Server'
                )}
              </button>
            ) : (
              <button
                onClick={connectToDatabase}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={isLoading || !formData.selectedDatabase}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Connecting...
                  </span>
                ) : (
                  'Connect to Database'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostgreSqlConnectorModal;