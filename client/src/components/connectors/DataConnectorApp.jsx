// import React, { useState } from 'react';
// import { X, Plus, ExternalLink, Check, AlertCircle } from 'lucide-react';

// const DataConnectorApp = () => {
//   const [selectedConnector, setSelectedConnector] = useState(null);
//   const [showModal, setShowModal] = useState(false);
//   const [connectedServices, setConnectedServices] = useState([]);
//   const [formData, setFormData] = useState({});
//   const [errors, setErrors] = useState({});

//   const connectors = {
//     integrations: [
//       {
//         id: 'google-drive',
//         name: 'Google Drive',
//         description: 'Analyze your Google Drive files and folders',
//         icon: '🔺',
//         color: 'bg-yellow-500',
//         category: 'Integration',
//         authType: 'oauth'
//       },
//     ],
//     mcps: [
//       {
//         id: 'github',
//         name: 'Github',
//         description: 'Search repositories, issues, and pull requests with actionable summaries',
//         icon: '🐙',
//         color: 'bg-gray-800',
//         category: 'MCP'
//       },
  
//     ],
//     databases: [
//       {
//         id: 'postgres',
//         name: 'Postgres',
//         description: 'Open source relational database',
//         icon: '🐘',
//         color: 'bg-blue-700',
//         category: 'Database',
//         fields: ['host', 'port', 'database', 'user', 'password', 'ssl']
//       },
//       {
//         id: 'mongodb',
//         name: 'MongoDB',
//         description: 'NoSQL document database',
//         icon: '🍃',
//         color: 'bg-green-600',
//         category: 'Database',
//         fields: ['connectionString', 'database', 'collection']
//       },
//       {
//         id: 'mysql',
//         name: 'MySQL',
//         description: 'Open source relational database',
//         icon: '🐬',
//         color: 'bg-orange-600',
//         category: 'Database',
//         fields: ['host', 'port', 'database', 'user', 'password']
//       },
//       {
//         id: 'elasticsearch',
//         name: 'Elasticsearch',
//         description: 'Distributed search and analytics engine',
//         icon: '🔍',
//         color: 'bg-yellow-600',
//         category: 'Database',
//         fields: ['host', 'port', 'username', 'password', 'index']
//       }
//     ]
//   };

//   const allConnectors = [...connectors.integrations, ...connectors.mcps, ...connectors.databases];

//   const handleConnectorClick = (connector) => {
//     setSelectedConnector(connector);
//     setShowModal(true);
//     setFormData({});
//     setErrors({});
//   };

//   const validateForm = () => {
//     const newErrors = {};
    
//     if (selectedConnector?.fields) {
//       selectedConnector.fields.forEach(field => {
//         if (!formData[field] && field !== 'ssl') {
//           newErrors[field] = `${field.charAt(0).toUpperCase() + field.slice(1)} is required`;
//         }
//       });
//     }

//     if (selectedConnector?.category === 'Database' && !formData.connectionName) {
//       newErrors.connectionName = 'Connection name is required';
//     }

//     setErrors(newErrors);
//     return Object.keys(newErrors).length === 0;
//   };

//   const handleConnect = () => {
//     if (!validateForm()) return;

//     const newConnection = {
//       ...selectedConnector,
//       ...formData,
//       connectedAt: new Date().toISOString()
//     };

//     setConnectedServices([...connectedServices, newConnection]);
//     setShowModal(false);
//     setFormData({});
//     setErrors({});
//   };

//   const handleOAuthConnect = () => {
//     // Simulate OAuth flow
//     console.log(`Initiating OAuth for ${selectedConnector.name}`);
//     alert(`Redirecting to ${selectedConnector.name} OAuth login...`);
    
//     setTimeout(() => {
//       const newConnection = {
//         ...selectedConnector,
//         connectedAt: new Date().toISOString()
//       };
//       setConnectedServices([...connectedServices, newConnection]);
//       setShowModal(false);
//     }, 1000);
//   };

//   const handleInputChange = (field, value) => {
//     setFormData({ ...formData, [field]: value });
//     if (errors[field]) {
//       setErrors({ ...errors, [field]: '' });
//     }
//   };

//   const renderDatabaseForm = () => {
//     const fieldLabels = {
//       host: 'Host',
//       port: 'Port',
//       database: 'Database',
//       user: 'Username',
//       password: 'Password',
//       ssl: 'Use SSL',
//       connectionString: 'Connection String',
//       collection: 'Collection',
//       account: 'Account',
//       warehouse: 'Warehouse',
//       schema: 'Schema',
//       role: 'Role',
//       projectId: 'Project ID',
//       datasetId: 'Dataset ID',
//       privateKey: 'Private Key',
//       url: 'Project URL',
//       anonKey: 'Anon Key',
//       serviceKey: 'Service Key',
//       username: 'Username',
//       index: 'Index'
//     };

//     return (
//       <div className="space-y-4">
//         <div>
//           <label className="block text-sm font-medium text-gray-700 mb-1">
//             Connection Name *
//           </label>
//           <input
//             type="text"
//             className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//               errors.connectionName ? 'border-red-500' : 'border-gray-300'
//             }`}
//             placeholder="Enter a name for this connection"
//             value={formData.connectionName || ''}
//             onChange={(e) => handleInputChange('connectionName', e.target.value)}
//           />
//           {errors.connectionName && (
//             <p className="text-red-500 text-sm mt-1">{errors.connectionName}</p>
//           )}
//         </div>

//         {selectedConnector?.fields?.map((field) => (
//           <div key={field}>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               {fieldLabels[field] || field} {field !== 'ssl' && '*'}
//             </label>
//             {field === 'ssl' ? (
//               <label className="flex items-center">
//                 <input
//                   type="checkbox"
//                   className="mr-2"
//                   checked={formData[field] || false}
//                   onChange={(e) => handleInputChange(field, e.target.checked)}
//                 />
//                 <span className="text-sm">Enable SSL connection</span>
//               </label>
//             ) : field === 'password' || field === 'privateKey' || field === 'serviceKey' ? (
//               <input
//                 type="password"
//                 className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                   errors[field] ? 'border-red-500' : 'border-gray-300'
//                 }`}
//                 placeholder={`Enter your ${fieldLabels[field].toLowerCase()}`}
//                 value={formData[field] || ''}
//                 onChange={(e) => handleInputChange(field, e.target.value)}
//               />
//             ) : field === 'port' || field === 'database' ? (
//               <input
//                 type={field === 'port' ? 'number' : 'text'}
//                 className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                   errors[field] ? 'border-red-500' : 'border-gray-300'
//                 }`}
//                 placeholder={field === 'port' ? '5432' : `Enter your ${fieldLabels[field].toLowerCase()}`}
//                 value={formData[field] || ''}
//                 onChange={(e) => handleInputChange(field, e.target.value)}
//               />
//             ) : (
//               <input
//                 type="text"
//                 className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                   errors[field] ? 'border-red-500' : 'border-gray-300'
//                 }`}
//                 placeholder={`Enter your ${fieldLabels[field].toLowerCase()}`}
//                 value={formData[field] || ''}
//                 onChange={(e) => handleInputChange(field, e.target.value)}
//               />
//             )}
//             {errors[field] && (
//               <p className="text-red-500 text-sm mt-1">{errors[field]}</p>
//             )}
//           </div>
//         ))}

//         <div className="flex items-center space-x-2 text-sm text-gray-600">
//           <AlertCircle className="w-4 h-4" />
//           <span>Your credentials are encrypted and stored securely</span>
//         </div>
//       </div>
//     );
//   };

//   const isConnected = (connectorId) => {
//     return connectedServices.some(service => service.id === connectorId);
//   };

//   return (
//     <div className="min-h-screen bg-gray-50 p-8">
//       <div className="max-w-7xl mx-auto">
//         <div className="mb-8">
//           <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Connectors & MCPs</h1>
//           <p className="text-gray-600">You can connect Julius to your data stores and business tools here</p>
//         </div>

//         {connectedServices.length > 0 && (
//           <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-lg">
//             <h3 className="text-sm font-semibold text-green-800 mb-2">Connected Services ({connectedServices.length})</h3>
//             <div className="flex flex-wrap gap-2">
//               {connectedServices.map((service, index) => (
//                 <span key={index} className="inline-flex items-center px-3 py-1 bg-white border border-green-300 rounded-full text-sm">
//                   <Check className="w-3 h-3 text-green-600 mr-1" />
//                   {service.name}
//                 </span>
//               ))}
//             </div>
//           </div>
//         )}

//         <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
//           <h2 className="text-xl font-semibold mb-6">Add connectors</h2>
          
//           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//             {allConnectors.map((connector) => (
//               <div
//                 key={connector.id}
//                 onClick={() => !isConnected(connector.id) && handleConnectorClick(connector)}
//                 className={`relative p-4 border rounded-lg transition-all ${
//                   isConnected(connector.id)
//                     ? 'bg-gray-50 border-green-400 cursor-not-allowed'
//                     : 'hover:shadow-md cursor-pointer border-gray-200'
//                 }`}
//               >
//                 {isConnected(connector.id) && (
//                   <div className="absolute top-2 right-2">
//                     <Check className="w-5 h-5 text-green-600" />
//                   </div>
//                 )}
                
//                 <div className="flex items-start space-x-3">
//                   <div className={`w-10 h-10 ${connector.color} rounded-lg flex items-center justify-center text-white text-xl`}>
//                     {connector.icon}
//                   </div>
//                   <div className="flex-1">
//                     <div className="flex items-center space-x-2">
//                       <h3 className="font-semibold text-gray-900">{connector.name}</h3>
//                       {connector.status === 'new' && (
//                         <span className="px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full">New</span>
//                       )}
//                     </div>
//                     <p className="text-sm text-gray-600 mt-1">{connector.description}</p>
//                     <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
//                       {connector.category}
//                     </span>
//                   </div>
//                 </div>
//               </div>
//             ))}
//           </div>

//           <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
//             <div className="flex items-center justify-between">
//               <div className="flex items-center space-x-2">
//                 <Plus className="w-5 h-5 text-blue-600" />
//                 <div>
//                   <p className="font-semibold text-blue-900">Need another connection?</p>
//                   <p className="text-sm text-blue-700">Let us know what data you'd like to use in Julius</p>
//                 </div>
//               </div>
//               <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
//                 Request connector
//               </button>
//             </div>
//           </div>

//           <div className="mt-4 flex items-center space-x-2 text-sm text-blue-600">
//             <AlertCircle className="w-4 h-4" />
//             <a href="#" className="hover:underline flex items-center">
//               Whitelist IP Address for Database Connections
//               <ExternalLink className="w-3 h-3 ml-1" />
//             </a>
//           </div>
//         </div>
//       </div>

//       {/* Connection Modal */}
//       {showModal && selectedConnector && (
//         <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//           <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
//             <div className="p-6 border-b border-gray-200">
//               <div className="flex items-center justify-between">
//                 <h2 className="text-xl font-semibold">Create {selectedConnector.name} Connector</h2>
//                 <button
//                   onClick={() => setShowModal(false)}
//                   className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
//                 >
//                   <X className="w-5 h-5" />
//                 </button>
//               </div>
//             </div>

//             <div className="p-6">
//               <div className="flex justify-center mb-6">
//                 <div className={`w-20 h-20 ${selectedConnector.color} rounded-xl flex items-center justify-center text-white text-4xl`}>
//                   {selectedConnector.icon}
//                 </div>
//               </div>

//               <div className="text-center mb-6">
//                 <h3 className="text-2xl font-semibold mb-2">{selectedConnector.name}</h3>
//                 <p className="text-gray-600">{selectedConnector.description}</p>
//               </div>

//               {selectedConnector.category === 'Database' ? (
//                 <>
//                   <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
//                     <p className="text-sm text-blue-800">
//                       Data Connectors allows you to connect to data sources like {selectedConnector.name} by securely providing your credentials to the AI.
//                     </p>
//                     <p className="text-sm text-blue-800 mt-2">
//                       Once a connector is enabled, it is available for the entire chat, allowing the AI to access and query your data contextually across interactions.
//                     </p>
//                   </div>

//                   {renderDatabaseForm()}

//                   <div className="mt-6 flex items-center space-x-2 text-sm">
//                     <a href="#" className="text-blue-600 hover:underline flex items-center">
//                       Read the Documentation
//                       <ExternalLink className="w-3 h-3 ml-1" />
//                     </a>
//                     <span className="text-gray-400">|</span>
//                     <a href="#" className="text-blue-600 hover:underline flex items-center">
//                       Security & Trust Center
//                       <ExternalLink className="w-3 h-3 ml-1" />
//                     </a>
//                   </div>
//                 </>
//               ) : selectedConnector.authType === 'oauth' ? (
//                 <div className="text-center space-y-4">
//                   <p className="text-gray-600">
//                     Click the button below to authenticate with {selectedConnector.name} and grant Julius access to your data.
//                   </p>
//                   <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
//                     <p className="text-sm text-yellow-800">
//                       You will be redirected to {selectedConnector.name} to complete the authentication process.
//                     </p>
//                   </div>
//                 </div>
//               ) : (
//                 <div className="space-y-4">
//                   <div className="p-4 bg-gray-50 rounded-lg">
//                     <p className="text-sm text-gray-600">
//                       Configure your {selectedConnector.name} integration settings.
//                     </p>
//                   </div>
//                   <div>
//                     <label className="block text-sm font-medium text-gray-700 mb-1">
//                       API Key
//                     </label>
//                     <input
//                       type="password"
//                       className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
//                       placeholder="Enter your API key"
//                       value={formData.apiKey || ''}
//                       onChange={(e) => handleInputChange('apiKey', e.target.value)}
//                     />
//                   </div>
//                 </div>
//               )}

//               <div className="mt-8 flex justify-end space-x-3">
//                 <button
//                   onClick={() => setShowModal(false)}
//                   className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
//                 >
//                   Cancel
//                 </button>
//                 <button
//                   onClick={selectedConnector.authType === 'oauth' ? handleOAuthConnect : handleConnect}
//                   className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
//                 >
//                   {selectedConnector.authType === 'oauth' ? 'Connect with ' + selectedConnector.name : 'Add Connection'}
//                 </button>
//               </div>
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// };

// export default DataConnectorApp;



import React, { useState } from 'react';
import { Plus, ExternalLink, Check, AlertCircle } from 'lucide-react';
import PostgreSqlConnectorModal from './PostgreSqlConnectorModal';
import MongoDbConnectorModal from './MongoDbConnectorModal';
// import MySqlConnectorModal from './MySqlConnectorModal';
// import ElasticsearchConnectorModal from './ElasticsearchConnectorModal';
// import GoogleDriveConnectorModal from './GoogleDriveConnectorModal';
// import GithubConnectorModal from './GithubConnectorModal';

const DataConnectorApp = () => {
  const [selectedConnector, setSelectedConnector] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [connectedServices, setConnectedServices] = useState([]);

  const connectors = {
    integrations: [
      {
        id: 'google-drive',
        name: 'Google Drive',
        description: 'Analyze your Google Drive files and folders',
        logo: '/connector/g_drive_logo.png',
        category: 'Integration',
        authType: 'oauth',
        // modalComponent: GoogleDriveConnectorModal
      },
    ],
    mcps: [
      {
        id: 'github',
        name: 'Github',
        description: 'Search repositories, issues, and pull requests with actionable summaries',
        logo: '/connector/github_logo.png',
        category: 'MCP',
        // modalComponent: GithubConnectorModal
      },
    ],
    databases: [
      {
        id: 'postgres',
        name: 'PostgreSQL',
        description: 'Open source relational database',
        logo: '/connector/Postgre_logo.png',
        category: 'Database',
        modalComponent: PostgreSqlConnectorModal
      },
      {
        id: 'mongodb',
        name: 'MongoDB',
        description: 'NoSQL document database',
        logo: '/connector/mongodb_logo.png',
        category: 'Database',
        modalComponent: MongoDbConnectorModal
      },
      {
        id: 'mysql',
        name: 'MySQL',
        description: 'Open source relational database',
        logo: '/connector/mysql_logo.png',
        category: 'Database',
        // modalComponent: MySqlConnectorModal
      },
      {
        id: 'elasticsearch',
        name: 'Elasticsearch',
        description: 'Distributed search and analytics engine',
        logo: '/connector/elasticsearch_logo.png',
        category: 'Database',
        // modalComponent: ElasticsearchConnectorModal
      }
    ]
  };

  const allConnectors = [...connectors.integrations, ...connectors.mcps, ...connectors.databases];

  const handleConnectorClick = (connector) => {
    setSelectedConnector(connector);
    setShowModal(true);
  };

  const handleConnectionSuccess = (connectionData) => {
    const newConnection = {
      ...selectedConnector,
      ...connectionData,
      connectedAt: new Date().toISOString()
    };

    setConnectedServices([...connectedServices, newConnection]);
    setShowModal(false);
    setSelectedConnector(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedConnector(null);
  };

  const isConnected = (connectorId) => {
    return connectedServices.some(service => service.id === connectorId);
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
          <p className="text-gray-600">You can connect Julius to your data stores and business tools here</p>
        </div>

        {connectedServices.length > 0 && (
          <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-semibold text-green-800 mb-2">
              Connected Services ({connectedServices.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {connectedServices.map((service, index) => (
                <span 
                  key={index} 
                  className="inline-flex items-center px-3 py-1 bg-white border border-green-300 rounded-full text-sm"
                >
                  <Check className="w-3 h-3 text-green-600 mr-1" />
                  {service.name}
                  {service.connectionName && (
                    <span className="ml-1 text-gray-500">({service.connectionName})</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-6">Add connectors</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allConnectors.map((connector) => (
              <div
                key={connector.id}
                onClick={() => !isConnected(connector.id) && handleConnectorClick(connector)}
                className={`relative p-4 border rounded-lg transition-all ${
                  isConnected(connector.id)
                    ? 'bg-gray-50 border-green-400 cursor-not-allowed'
                    : 'hover:shadow-md cursor-pointer border-gray-200'
                }`}
              >
                {isConnected(connector.id) && (
                  <div className="absolute top-2 right-2">
                    <Check className="w-5 h-5 text-green-600" />
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
                    <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                      {connector.category}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Plus className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">Need another connection?</p>
                  <p className="text-sm text-blue-700">Let us know what data you'd like to use in Julius</p>
                </div>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Request connector
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center space-x-2 text-sm text-blue-600">
            <AlertCircle className="w-4 h-4" />
            <a href="#" className="hover:underline flex items-center">
              Whitelist IP Address for Database Connections
              <ExternalLink className="w-3 h-3 ml-1" />
            </a>
          </div>
        </div>
      </div>

      {/* Render the appropriate modal based on selected connector */}
      {renderModal()}
    </div>
  );
};

export default DataConnectorApp;
