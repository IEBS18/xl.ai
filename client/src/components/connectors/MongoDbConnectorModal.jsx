import React, { useState } from 'react';
import { X, AlertCircle, ExternalLink, Loader2 } from 'lucide-react';
import axios from 'axios';

const MongoDbConnectorModal = ({ isOpen, onClose, onSuccess, connector }) => {
  const [formData, setFormData] = useState({
    connectionName: '',
    connectionString: '',
    database: '',
    collection: ''
  });
  
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

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.connectionName) {
      newErrors.connectionName = 'Connection name is required';
    }
    if (!formData.connectionString) {
      newErrors.connectionString = 'Connection string is required';
    }
    if (!formData.database) {
      newErrors.database = 'Database is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const testConnection = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setTestStatus(null);

    try {
      const response = await axios.post('/api/connectors/mongodb/test', {
        connectionString: formData.connectionString,
        database: formData.database,
        collection: formData.collection
      });

      if (response.data.success) {
        setTestStatus({ type: 'success', message: 'Connection successful!' });
      } else {
        setTestStatus({ type: 'error', message: response.data.message || 'Connection failed' });
      }
    } catch (error) {
      setTestStatus({ 
        type: 'error', 
        message: error.response?.data?.message || 'Failed to test connection' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsLoading(true);

    try {
      const response = await axios.post('/api/connectors/mongodb/connect', {
        connectionName: formData.connectionName,
        connectionString: formData.connectionString,
        database: formData.database,
        collection: formData.collection
      });

      if (response.data.success) {
        onSuccess({
          connectionName: formData.connectionName,
          connectionId: response.data.connectionId
        });
      } else {
        setTestStatus({ type: 'error', message: response.data.message || 'Connection failed' });
      }
    } catch (error) {
      setTestStatus({ 
        type: 'error', 
        message: error.response?.data?.message || 'Failed to create connection' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Create MongoDB Connector</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={isLoading}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-green-50 rounded-xl flex items-center justify-center">
              <img 
                src="/connector/mongodb_logo.png" 
                alt="MongoDB logo"
                className="w-16 h-16 object-contain"
              />
            </div>
          </div>

          <div className="text-center mb-6">
            <h3 className="text-2xl font-semibold mb-2">MongoDB</h3>
            <p className="text-gray-600">NoSQL document database</p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              Connect to your MongoDB database using a connection string. MongoDB Atlas users can find their connection string in the Atlas dashboard.
            </p>
            <p className="text-sm text-blue-800 mt-2">
              Format: mongodb+srv://username:password@cluster.mongodb.net/
            </p>
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
                Connection String *
              </label>
              <input
                type="password"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.connectionString ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="mongodb+srv://username:password@cluster.mongodb.net/"
                value={formData.connectionString}
                onChange={(e) => handleInputChange('connectionString', e.target.value)}
                disabled={isLoading}
              />
              {errors.connectionString && (
                <p className="text-red-500 text-sm mt-1">{errors.connectionString}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Database *
              </label>
              <input
                type="text"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.database ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter your database name"
                value={formData.database}
                onChange={(e) => handleInputChange('database', e.target.value)}
                disabled={isLoading}
              />
              {errors.database && (
                <p className="text-red-500 text-sm mt-1">{errors.database}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection (Optional)
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter a specific collection (leave empty for all)"
                value={formData.collection}
                onChange={(e) => handleInputChange('collection', e.target.value)}
                disabled={isLoading}
              />
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

            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <AlertCircle className="w-4 h-4" />
              <span>Your credentials are encrypted and stored securely</span>
            </div>
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
            <button
              onClick={testConnection}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              disabled={isLoading}
            >
              {isLoading && testStatus === null ? (
                <span className="flex items-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Testing...
                </span>
              ) : (
                'Test Connection'
              )}
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              disabled={isLoading || (testStatus && testStatus.type === 'error')}
            >
              {isLoading && testStatus !== null ? (
                <span className="flex items-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </span>
              ) : (
                'Add Connection'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MongoDbConnectorModal;