import React, { useState, useEffect } from 'react';
import { Plus, ExternalLink, Check, AlertCircle, Trash2, Edit2, Database, Cloud, Code } from 'lucide-react';
import PostgreSqlConnectorModal from './PostgreSqlConnectorModal';
import MongoDbConnectorModal from './MongoDbConnectorModal';
import { useConnectorStore } from '../../hooks/useConnectorStore';

const DataConnectorApp = () => {
  const { 
    getAllConnectors, 
    removeConnector, 
    updateLastUsed 
  } = useConnectorStore();
  
  const [selectedConnector, setSelectedConnector] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [savedConnections, setSavedConnections] = useState([]);

  const connectors = {
    integrations: [
      {
        id: 'google-drive',
        name: 'Google Drive',
        description: 'Analyze your Google Drive files and folders',
        logo: 'public/connector/g_drive_logo.webp',
        category: 'Integration',
        authType: 'oauth',
        type: 'googleDrive',
        // modalComponent: GoogleDriveConnectorModal
      },
    ],
    mcps: [
      {
        id: 'github',
        name: 'Github',
        description: 'Search repositories, issues, and pull requests with actionable summaries',
        logo: 'public/connector/github.png',
        category: 'MCP',
        type: 'github',
        // modalComponent: GithubConnectorModal
      },
    ],
    databases: [
      {
        id: 'postgres',
        name: 'PostgreSQL',
        description: 'Open source relational database',
        logo: 'public/connector/Postgres_logo.webp',
        category: 'Database',
        type: 'postgres',
        modalComponent: PostgreSqlConnectorModal
      },
      {
        id: 'mongodb',
        name: 'MongoDB',
        description: 'NoSQL document database',
        logo: 'public/connector/mongo.png',
        category: 'Database',
        type: 'mongodb',
        modalComponent: MongoDbConnectorModal
      },
      {
        id: 'mysql',
        name: 'MySQL',
        description: 'Open source relational database',
        logo: 'public/connector/mysql.png',
        category: 'Database',
        type: 'mysql',
        // modalComponent: MySqlConnectorModal
      },
      {
        id: 'elasticsearch',
        name: 'Elasticsearch',
        description: 'Distributed search and analytics engine',
        logo: 'public/connector/elasticsearch.png',
        category: 'Database',
        type: 'elasticsearch',
        // modalComponent: ElasticsearchConnectorModal
      }
    ]
  };

  const allConnectors = [...connectors.integrations, ...connectors.mcps, ...connectors.databases];

  // Load saved connections from local storage
  useEffect(() => {
    loadSavedConnections();
  }, []);

  const loadSavedConnections = () => {
    const connections = getAllConnectors();
    setSavedConnections(connections);
  };

  const handleConnectorClick = (connector) => {
    if (connector.modalComponent) {
      setSelectedConnector(connector);
      setShowModal(true);
    } else {
      alert(`${connector.name} connector is coming soon!`);
    }
  };

  const handleConnectionSuccess = (connectionData) => {
    // Reload saved connections after successful connection
    loadSavedConnections();
    setShowModal(false);
    setSelectedConnector(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedConnector(null);
  };

  const handleEditConnection = (connection) => {
    // Update last used
    updateLastUsed(connection.type, connection.id);
    // Find the connector configuration
    const connector = allConnectors.find(c => c.type === connection.type);
    if (connector && connector.modalComponent) {
      setSelectedConnector(connector);
      setShowModal(true);
    }
  };

  const handleDeleteConnection = (connection) => {
    if (window.confirm(`Are you sure you want to delete "${connection.connectionName}"?`)) {
      removeConnector(connection.type, connection.id);
      loadSavedConnections();
    }
  };

  const isConnectorTypeConnected = (connectorType) => {
    return savedConnections.some(conn => conn.type === connectorType);
  };

  const getConnectorIcon = (category) => {
    switch(category) {
      case 'Database':
        return <Database className="w-4 h-4" />;
      case 'Integration':
        return <Cloud className="w-4 h-4" />;
      case 'MCP':
        return <Code className="w-4 h-4" />;
      default:
        return <Database className="w-4 h-4" />;
    }
  };

  const getConnectorInfo = (type) => {
    const connector = allConnectors.find(c => c.type === type);
    return connector || { name: type, category: 'Unknown' };
  };

  // Render the appropriate modal component
  const renderModal = () => {
    if (!showModal || !selectedConnector) return null;

    const ModalComponent = selectedConnector.modalComponent;
    if (!ModalComponent) return null;

    return (
      <ModalComponent
        isOpen={showModal}
        onClose={handleCloseModal}
        onSuccess={handleConnectionSuccess}
        connector={selectedConnector}
      />
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Connectors & MCPs</h1>
          <p className="text-gray-600">You can connect InsiPredict to your data stores and business tools here</p>
        </div>

        {/* My Connections Section */}
        {savedConnections.length > 0 && (
          <div className="mb-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">My Connections</h2>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Connector</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Created</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {savedConnections.map((connection) => {
                    const connectorInfo = getConnectorInfo(connection.type);
                    return (
                      <tr key={connection.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
                              {getConnectorIcon(connectorInfo.category)}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{connection.connectionName}</div>
                              {connection.database && (
                                <div className="text-xs text-gray-500">Database: {connection.database}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">{connectorInfo.name}</span>
                            <span className={`px-2 py-0.5 text-xs rounded-full ${
                              connectorInfo.category === 'Database' 
                                ? 'bg-blue-100 text-blue-700'
                                : connectorInfo.category === 'Integration'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-purple-100 text-purple-700'
                            }`}>
                              {connectorInfo.category}
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-600">
                            {new Date(connection.createdAt).toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric', 
                              year: 'numeric' 
                            })}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => handleEditConnection(connection)}
                              className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              title="Edit connection"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteConnection(connection)}
                              className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                              title="Delete connection"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Add Connectors Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-6">Add connectors</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allConnectors.map((connector) => {
              const isConnected = isConnectorTypeConnected(connector.type);
              
              return (
                <div
                  key={connector.id}
                  onClick={() => handleConnectorClick(connector)}
                  className={`relative p-4 border rounded-lg transition-all cursor-pointer ${
                    isConnected
                      ? 'border-green-400 hover:border-green-500 hover:shadow-md'
                      : 'border-gray-200 hover:shadow-md'
                  }`}
                >
                  {isConnected && (
                    <div className="absolute top-2 right-2">
                      <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 rounded-full">
                        <Check className="w-3 h-3 text-green-600" />
                        <span className="text-xs text-green-700 font-medium">Connected</span>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-50">
                      <img 
                        src={connector.logo} 
                        alt={`${connector.name} logo`}
                        className="w-8 h-8 object-contain"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '/connector/default_logo.png';
                        }}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-gray-900">{connector.name}</h3>
                        {connector.status === 'new' && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full">
                            New
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{connector.description}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {connector.category}
                        </span>
                        {isConnected && (
                          <span className="text-xs text-gray-500">
                            Click to add another
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Plus className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">Need another connection?</p>
                  <p className="text-sm text-blue-700">Let us know what data you'd like to use in InsiPredict</p>
                </div>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Request connector
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Render the appropriate modal based on selected connector */}
      {renderModal()}
    </div>
  );
};

export default DataConnectorApp;