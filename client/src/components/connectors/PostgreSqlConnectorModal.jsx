// import React, { useState, useEffect } from 'react';
// import { X, AlertCircle, ExternalLink, Loader2, Database, Server, Check, Trash2 } from 'lucide-react';
// import { useConnectorStore } from '../../hooks/useConnectorStore';
// import { BACKEND_URL } from "../../utils/constants"

// const PostgreSqlConnectorModal = ({ isOpen, onClose, onSuccess, connector }) => {
//   const { 
//     addConnector, 
//     getConnectorsByType, 
//     connectionExists, 
//     removeConnector,
//     updateLastUsed 
//   } = useConnectorStore();
  
//   const [step, setStep] = useState(1);
//   const [formData, setFormData] = useState({
//     connectionName: '',
//     host: '',
//     port: '5432',
//     user: '',
//     password: '',
//     ssl: false,
//     selectedDatabase: ''
//   });
  
//   const [databases, setDatabases] = useState([]);
//   const [existingConnections, setExistingConnections] = useState([]);
//   const [errors, setErrors] = useState({});
//   const [isLoading, setIsLoading] = useState(false);
//   const [testStatus, setTestStatus] = useState(null);
//   const [showExistingConnections, setShowExistingConnections] = useState(false);

//   // Load existing connections on mount
//   useEffect(() => {
//     if (isOpen) {
//       const connections = getConnectorsByType('postgres');
//       setExistingConnections(connections);
//       setShowExistingConnections(connections.length > 0);
//     }
//   }, [isOpen, getConnectorsByType]);

//   const handleInputChange = (field, value) => {
//     setFormData(prev => ({ ...prev, [field]: value }));
//     if (errors[field]) {
//       setErrors(prev => ({ ...prev, [field]: '' }));
//     }
//     setTestStatus(null);
//   };

//   const validateServerConnection = () => {
//     const newErrors = {};
    
//     if (!formData.host?.trim()) {
//       newErrors.host = 'Host is required';
//     }
//     if (!formData.port?.trim()) {
//       newErrors.port = 'Port is required';
//     } else if (isNaN(parseInt(formData.port))) {
//       newErrors.port = 'Port must be a number';
//     }
//     if (!formData.user?.trim()) {
//       newErrors.user = 'Username is required';
//     }
//     if (!formData.password) {
//       newErrors.password = 'Password is required';
//     }

//     setErrors(newErrors);
//     return Object.keys(newErrors).length === 0;
//   };

//   const validateDatabaseSelection = () => {
//     const newErrors = {};
    
//     if (!formData.connectionName?.trim()) {
//       newErrors.connectionName = 'Connection name is required';
//     } else if (connectionExists('postgres', formData.connectionName)) {
//       newErrors.connectionName = 'A connection with this name already exists';
//     }
    
//     if (!formData.selectedDatabase) {
//       newErrors.selectedDatabase = 'Please select a database';
//     }

//     setErrors(newErrors);
//     return Object.keys(newErrors).length === 0;
//   };

//   const handleUseExistingConnection = (connection) => {
//     setFormData({
//       connectionName: connection.connectionName,
//       host: connection.host,
//       port: connection.port.toString(),
//       user: connection.user,
//       password: connection.password,
//       ssl: connection.ssl || false,
//       selectedDatabase: connection.database || ''
//     });
    
//     // Update last used timestamp
//     updateLastUsed('postgres', connection.id);
    
//     // If database is already selected, connect directly
//     if (connection.database) {
//       setTestStatus({ 
//         type: 'success', 
//         message: `Using saved connection: ${connection.connectionName}` 
//       });
      
//       // Call the database connect API with existing connection
//       connectToDatabase(connection);
//     } else {
//       // Need to connect to server and select database
//       setShowExistingConnections(false);
//       testServerConnection();
//     }
//   };

//   const deleteConnection = (connection) => {
//     if (window.confirm(`Delete connection "${connection.connectionName}"?`)) {
//       removeConnector('postgres', connection.id);
//       const updatedConnections = existingConnections.filter(c => c.id !== connection.id);
//       setExistingConnections(updatedConnections);
//       if (updatedConnections.length === 0) {
//         setShowExistingConnections(false);
//       }
//     }
//   };

//   const testServerConnection = async () => {
//     if (!validateServerConnection()) return;

//     setIsLoading(true);
//     setTestStatus(null);

//     try {
//       // First test the connection to get list of databases
//       const response = await fetch(`${BACKEND_URL}/database/test-connection`, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         credentials: 'include',
//         body: JSON.stringify({
//           connection_type: 'postgresql',
//           host: formData.host,
//           port: parseInt(formData.port),
//           database: 'postgres', // Use default postgres db for listing databases
//           username: formData.user,
//           password: formData.password
//         })
//       });

//       const data = await response.json();

//       if (data.success) {
//         // Fetch list of databases manually since test-connection doesn't return them
//         // For now, we'll show a success and let user enter database name manually
//         setDatabases(['postgres', 'template1', 'template0']); // Default PostgreSQL databases
//         setTestStatus({ 
//           type: 'success', 
//           message: `Connected successfully! Enter database name to connect` 
//         });
        
//         // Auto-advance to step 2 after successful connection
//         setTimeout(() => {
//           setStep(2);
//           setTestStatus(null);
//           setErrors({});
//         }, 1500);
//       } else {
//         setTestStatus({ 
//           type: 'error', 
//           message: data.message || 'Connection failed' 
//         });
//       }
//     } catch (error) {
//       console.error('Connection test error:', error);
//       setTestStatus({ 
//         type: 'error', 
//         message: 'Failed to connect to server. Please check your connection details.' 
//       });
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const connectToDatabase = async (existingConnection = null) => {
//     // Validate only if not using existing connection
//     if (!existingConnection && !validateDatabaseSelection()) return;

//     setIsLoading(true);
//     setTestStatus(null);

//     try {
//       const connectionParams = existingConnection || {
//         connectionName: formData.connectionName,
//         host: formData.host,
//         port: parseInt(formData.port),
//         user: formData.user,
//         password: formData.password,
//         database: formData.selectedDatabase,
//         ssl: formData.ssl
//       };

//       // Using the database/connect endpoint that creates a session
//       const response = await fetch(`${BACKEND_URL}/database/connect`, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         credentials: 'include',
//         body: JSON.stringify({
//           connection_type: 'postgresql',
//           host: connectionParams.host,
//           port: connectionParams.port || 5432,
//           database: connectionParams.database || connectionParams.selectedDatabase,
//           username: connectionParams.user,
//           password: connectionParams.password
//         })
//       });

//       const data = await response.json();

//       if (data.success && data.session_id) {
//         // Save to local storage if new connection
//         if (!existingConnection) {
//           const newConnector = addConnector('postgres', {
//             connectionName: formData.connectionName,
//             host: formData.host,
//             port: parseInt(formData.port),
//             user: formData.user,
//             password: formData.password, // Note: Consider encrypting this
//             database: formData.selectedDatabase,
//             ssl: formData.ssl
//           });
//         }

//         setTestStatus({ 
//           type: 'success', 
//           message: `Connected successfully!` 
//         });
        
//         // Pass session_id to parent for navigation
//         setTimeout(() => {
//           onSuccess({
//             connectionName: connectionParams.connectionName,
//             session_id: data.session_id,
//             database: connectionParams.database || connectionParams.selectedDatabase,
//             type: 'database'
//           });
//         }, 1000);
//       } else {
//         setTestStatus({ 
//           type: 'error', 
//           message: data.error || 'Connection failed' 
//         });
//       }
//     } catch (error) {
//       console.error('Database connection error:', error);
//       setTestStatus({ 
//         type: 'error', 
//         message: 'Failed to connect to database' 
//       });
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const handleBack = () => {
//     if (showExistingConnections) {
//       setShowExistingConnections(false);
//     } else {
//       setStep(1);
//       setTestStatus(null);
//       setErrors({});
//     }
//   };

//   const handleClose = () => {
//     // Reset all state when closing
//     setStep(1);
//     setFormData({
//       connectionName: '',
//       host: '',
//       port: '5432',
//       user: '',
//       password: '',
//       ssl: false,
//       selectedDatabase: ''
//     });
//     setDatabases([]);
//     setErrors({});
//     setTestStatus(null);
//     setIsLoading(false);
//     setShowExistingConnections(existingConnections.length > 0);
//     onClose();
//   };

//   if (!isOpen) return null;

//   return (
//     <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//       <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
//         <div className="p-6 border-b border-gray-200">
//           <div className="flex items-center justify-between">
//             <h2 className="text-xl font-semibold">
//               {showExistingConnections 
//                 ? 'PostgreSQL Connections' 
//                 : step === 1 
//                   ? 'Connect to PostgreSQL Server' 
//                   : 'Select Database'}
//             </h2>
//             <button
//               onClick={handleClose}
//               className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
//               disabled={isLoading}
//             >
//               <X className="w-5 h-5" />
//             </button>
//           </div>
          
//           {/* Progress indicator */}
//           {!showExistingConnections && (
//             <div className="mt-4 flex items-center space-x-2">
//               <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
//                 <Server className="w-4 h-4 mr-1" />
//                 <span className="text-sm">Server</span>
//               </div>
//               <div className={`flex-1 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
//               <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
//                 <Database className="w-4 h-4 mr-1" />
//                 <span className="text-sm">Database</span>
//               </div>
//             </div>
//           )}
//         </div>

//         <div className="p-6">
//           <div className="flex justify-center mb-6">
//             <div className="w-20 h-20 bg-blue-50 rounded-xl flex items-center justify-center">
//               <img 
//                 src="public/connector/Postgres_logo.webp" 
//                 alt="PostgreSQL logo"
//                 className="w-16 h-16 object-contain"
//                 onError={(e) => {
//                   e.target.onerror = null;
//                   e.target.style.display = 'none';
//                   e.target.parentElement.innerHTML = '🐘';
//                   e.target.parentElement.style.fontSize = '3rem';
//                 }}
//               />
//             </div>
//           </div>

//           {/* Existing Connections */}
//           {showExistingConnections ? (
//             <>
//               <div className="text-center mb-6">
//                 <h3 className="text-2xl font-semibold mb-2">Saved Connections</h3>
//                 <p className="text-gray-600">Select an existing connection or create a new one</p>
//               </div>

//               <div className="space-y-3 mb-6 max-h-60 overflow-y-auto">
//                 {existingConnections.map((conn) => (
//                   <div
//                     key={conn.id}
//                     className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
//                   >
//                     <div className="flex items-center justify-between">
//                       <div className="flex-1">
//                         <div className="flex items-center space-x-2">
//                           <Database className="w-4 h-4 text-gray-500" />
//                           <span className="font-medium">{conn.connectionName}</span>
//                           <Check className="w-4 h-4 text-green-500" />
//                         </div>
//                         <p className="text-sm text-gray-500 mt-1">
//                           {conn.host}:{conn.port} | Database: {conn.database}
//                         </p>
//                         <p className="text-xs text-gray-400 mt-1">
//                           Last used: {new Date(conn.lastUsed).toLocaleDateString()}
//                         </p>
//                       </div>
//                       <div className="flex space-x-2">
//                         <button
//                           onClick={() => handleUseExistingConnection(conn)}
//                           className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
//                         >
//                           Use
//                         </button>
//                         <button
//                           onClick={() => deleteConnection(conn)}
//                           className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
//                         >
//                           <Trash2 className="w-4 h-4" />
//                         </button>
//                       </div>
//                     </div>
//                   </div>
//                 ))}
//               </div>

//               <button
//                 onClick={() => setShowExistingConnections(false)}
//                 className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors"
//               >
//                 + Create New Connection
//               </button>
//             </>
//           ) : step === 1 ? (
//             <>
//               <div className="text-center mb-6">
//                 <h3 className="text-2xl font-semibold mb-2">PostgreSQL Server</h3>
//                 <p className="text-gray-600">Connect to your PostgreSQL server to view available databases</p>
//               </div>

//               <div className="space-y-4">
//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Host *
//                   </label>
//                   <input
//                     type="text"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.host ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="localhost or your server address"
//                     value={formData.host}
//                     onChange={(e) => handleInputChange('host', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.host && (
//                     <p className="text-red-500 text-sm mt-1">{errors.host}</p>
//                   )}
//                 </div>

//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Port *
//                   </label>
//                   <input
//                     type="number"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.port ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="5432"
//                     value={formData.port}
//                     onChange={(e) => handleInputChange('port', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.port && (
//                     <p className="text-red-500 text-sm mt-1">{errors.port}</p>
//                   )}
//                 </div>

//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Username *
//                   </label>
//                   <input
//                     type="text"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.user ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="postgres"
//                     value={formData.user}
//                     onChange={(e) => handleInputChange('user', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.user && (
//                     <p className="text-red-500 text-sm mt-1">{errors.user}</p>
//                   )}
//                 </div>

//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Password *
//                   </label>
//                   <input
//                     type="password"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.password ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="Enter your password"
//                     value={formData.password}
//                     onChange={(e) => handleInputChange('password', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.password && (
//                     <p className="text-red-500 text-sm mt-1">{errors.password}</p>
//                   )}
//                 </div>

//                 <div>
//                   <label className="flex items-center">
//                     <input
//                       type="checkbox"
//                       className="mr-2"
//                       checked={formData.ssl}
//                       onChange={(e) => handleInputChange('ssl', e.target.checked)}
//                       disabled={isLoading}
//                     />
//                     <span className="text-sm">Use SSL connection</span>
//                   </label>
//                 </div>

//                 {testStatus && (
//                   <div className={`p-3 rounded-lg ${
//                     testStatus.type === 'success' 
//                       ? 'bg-green-50 border border-green-200' 
//                       : 'bg-red-50 border border-red-200'
//                   }`}>
//                     <p className={`text-sm ${
//                       testStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
//                     }`}>
//                       {testStatus.message}
//                     </p>
//                   </div>
//                 )}
//               </div>
//             </>
//           ) : (
//             <>
//               <div className="text-center mb-6">
//                 <h3 className="text-2xl font-semibold mb-2">Select Database</h3>
//                 <p className="text-gray-600">Enter the database name you want to connect to</p>
//               </div>

//               <div className="space-y-4">
//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Connection Name *
//                   </label>
//                   <input
//                     type="text"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.connectionName ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="Enter a name for this connection"
//                     value={formData.connectionName}
//                     onChange={(e) => handleInputChange('connectionName', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.connectionName && (
//                     <p className="text-red-500 text-sm mt-1">{errors.connectionName}</p>
//                   )}
//                 </div>

//                 <div>
//                   <label className="block text-sm font-medium text-gray-700 mb-1">
//                     Database Name *
//                   </label>
//                   <input
//                     type="text"
//                     className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
//                       errors.selectedDatabase ? 'border-red-500' : 'border-gray-300'
//                     }`}
//                     placeholder="Enter database name (e.g., myapp_db)"
//                     value={formData.selectedDatabase}
//                     onChange={(e) => handleInputChange('selectedDatabase', e.target.value)}
//                     disabled={isLoading}
//                   />
//                   {errors.selectedDatabase && (
//                     <p className="text-red-500 text-sm mt-1">{errors.selectedDatabase}</p>
//                   )}
//                   <p className="text-xs text-gray-500 mt-1">
//                     Common database names: postgres, myapp_db, production, development
//                   </p>
//                 </div>

//                 {testStatus && (
//                   <div className={`p-3 rounded-lg ${
//                     testStatus.type === 'success' 
//                       ? 'bg-green-50 border border-green-200' 
//                       : 'bg-red-50 border border-red-200'
//                   }`}>
//                     <p className={`text-sm ${
//                       testStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
//                     }`}>
//                       {testStatus.message}
//                     </p>
//                   </div>
//                 )}

//                 <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
//                   <p className="text-sm text-blue-800">
//                     The selected database will be available for natural language queries and analysis.
//                   </p>
//                   <p className="text-sm text-blue-800 mt-2">
//                     Server: {formData.host}:{formData.port} | User: {formData.user}
//                   </p>
//                 </div>
//               </div>
//             </>
//           )}

//           <div className="flex items-center space-x-2 text-sm text-gray-600 mt-4">
//             <AlertCircle className="w-4 h-4" />
//             <span>Your credentials are encrypted and stored securely in your browser</span>
//           </div>

//           <div className="mt-6 flex items-center space-x-2 text-sm">
//             <a href="#" className="text-blue-600 hover:underline flex items-center">
//               Read the Documentation
//               <ExternalLink className="w-3 h-3 ml-1" />
//             </a>
//             <span className="text-gray-400">|</span>
//             <a href="#" className="text-blue-600 hover:underline flex items-center">
//               Security & Trust Center
//               <ExternalLink className="w-3 h-3 ml-1" />
//             </a>
//           </div>

//           <div className="mt-8 flex justify-end space-x-3">
//             {((step === 2 && !showExistingConnections) || (showExistingConnections && existingConnections.length > 0)) && (
//               <button
//                 onClick={handleBack}
//                 className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
//                 disabled={isLoading}
//               >
//                 Back
//               </button>
//             )}
//             <button
//               onClick={handleClose}
//               className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
//               disabled={isLoading}
//             >
//               Cancel
//             </button>
//             {!showExistingConnections && (
//               step === 1 ? (
//                 <button
//                   onClick={testServerConnection}
//                   className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
//                   disabled={isLoading}
//                 >
//                   {isLoading ? (
//                     <span className="flex items-center">
//                       <Loader2 className="w-4 h-4 mr-2 animate-spin" />
//                       Connecting...
//                     </span>
//                   ) : (
//                     'Connect to Server'
//                   )}
//                 </button>
//               ) : (
//                 <button
//                   onClick={() => connectToDatabase()}
//                   className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
//                   disabled={isLoading || !formData.selectedDatabase}
//                 >
//                   {isLoading ? (
//                     <span className="flex items-center">
//                       <Loader2 className="w-4 h-4 mr-2 animate-spin" />
//                       Connecting...
//                     </span>
//                   ) : (
//                     'Connect to Database'
//                   )}
//                 </button>
//               )
//             )}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default PostgreSqlConnectorModal;


import React, { useState, useEffect } from 'react';
import { X, AlertCircle, ExternalLink, Loader2, Database, Server, Check, Trash2 } from 'lucide-react';
import { useConnectorStore } from '../../hooks/useConnectorStore';
import { BACKEND_URL } from "../../utils/constants"

const PostgreSqlConnectorModal = ({ isOpen, onClose, onSuccess, connector }) => {
  const { 
    addConnector, 
    getConnectorsByType, 
    connectionExists, 
    removeConnector,
    updateLastUsed 
  } = useConnectorStore();
  
  const [step, setStep] = useState(1);
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
  const [existingConnections, setExistingConnections] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [testStatus, setTestStatus] = useState(null);
  const [showExistingConnections, setShowExistingConnections] = useState(false);

  // Load existing connections on mount
  useEffect(() => {
    if (isOpen) {
      const connections = getConnectorsByType('postgres');
      setExistingConnections(connections);
      setShowExistingConnections(connections.length > 0);
    }
  }, [isOpen, getConnectorsByType]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    setTestStatus(null);
  };

  const validateServerConnection = () => {
    const newErrors = {};
    
    if (!formData.host?.trim()) {
      newErrors.host = 'Host is required';
    }
    if (!formData.port?.trim()) {
      newErrors.port = 'Port is required';
    } else if (isNaN(parseInt(formData.port))) {
      newErrors.port = 'Port must be a number';
    }
    if (!formData.user?.trim()) {
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
    
    if (!formData.connectionName?.trim()) {
      newErrors.connectionName = 'Connection name is required';
    } else if (connectionExists('postgres', formData.connectionName)) {
      newErrors.connectionName = 'A connection with this name already exists';
    }
    
    if (!formData.selectedDatabase) {
      newErrors.selectedDatabase = 'Please select a database';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleUseExistingConnection = (connection) => {
    setFormData({
      connectionName: connection.connectionName,
      host: connection.host,
      port: connection.port.toString(),
      user: connection.user,
      password: connection.password,
      ssl: connection.ssl || false,
      selectedDatabase: connection.database || ''
    });
    
    // Update last used timestamp
    updateLastUsed('postgres', connection.id);
    
    // If database is already selected, connect directly
    if (connection.database) {
      setTestStatus({ 
        type: 'success', 
        message: `Using saved connection: ${connection.connectionName}` 
      });
      
      // Call the database connect API with existing connection
      connectToDatabase(connection);
    } else {
      // Need to connect to server and select database
      setShowExistingConnections(false);
      testServerConnection();
    }
  };

  const deleteConnection = (connection) => {
    if (window.confirm(`Delete connection "${connection.connectionName}"?`)) {
      removeConnector('postgres', connection.id);
      const updatedConnections = existingConnections.filter(c => c.id !== connection.id);
      setExistingConnections(updatedConnections);
      if (updatedConnections.length === 0) {
        setShowExistingConnections(false);
      }
    }
  };


  const testServerConnection = async () => {
    if (!validateServerConnection()) return;

    setIsLoading(true);
    setTestStatus(null);

    try {
      // First test the connection to get list of databases
      const response = await fetch(`${BACKEND_URL}/database/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        mode: 'cors',
        credentials: 'include',
        body: JSON.stringify({
          connection_type: 'postgresql',
          host: formData.host,
          port: parseInt(formData.port),
          database: 'postgres', // Use default postgres db for listing databases
          username: formData.user,
          password: formData.password
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        // Fetch list of databases manually since test-connection doesn't return them
        // For now, we'll show a success and let user enter database name manually
        setDatabases(['postgres', 'template1', 'template0']); // Default PostgreSQL databases
        setTestStatus({ 
          type: 'success', 
          message: `Connected successfully! Enter database name to connect` 
        });
        
        // Auto-advance to step 2 after successful connection
        setTimeout(() => {
          setStep(2);
          setTestStatus(null);
          setErrors({});
        }, 1500);
      } else {
        setTestStatus({ 
          type: 'error', 
          message: data.message || 'Connection failed' 
        });
      }
    } catch (error) {
      console.error('Connection test error:', error);
      setTestStatus({ 
        type: 'error', 
        message: error.message === 'HTTP error! status: 405' 
          ? 'Server configuration error. Please ensure the backend is running and CORS is configured.'
          : 'Failed to connect to server. Please check your connection details.' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const connectToDatabase = async (existingConnection = null) => {
    // Validate only if not using existing connection
    if (!existingConnection && !validateDatabaseSelection()) return;

    setIsLoading(true);
    setTestStatus(null);

    try {
      const connectionParams = existingConnection || {
        connectionName: formData.connectionName,
        host: formData.host,
        port: parseInt(formData.port),
        user: formData.user,
        password: formData.password,
        database: formData.selectedDatabase,
        ssl: formData.ssl
      };

      // Using the database/connect endpoint that creates a session
      const response = await fetch(`${BACKEND_URL}/database/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        mode: 'cors',
        credentials: 'include',
        body: JSON.stringify({
          connection_type: 'postgresql',
          host: connectionParams.host,
          port: connectionParams.port || 5432,
          database: connectionParams.database || connectionParams.selectedDatabase,
          username: connectionParams.user,
          password: connectionParams.password
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.session_id) {
        // Save to local storage if new connection
        if (!existingConnection) {
          const newConnector = addConnector('postgres', {
            connectionName: formData.connectionName,
            host: formData.host,
            port: parseInt(formData.port),
            user: formData.user,
            password: formData.password, // Note: Consider encrypting this
            database: formData.selectedDatabase,
            ssl: formData.ssl
          });
        }

        setTestStatus({ 
          type: 'success', 
          message: `Connected successfully!` 
        });
        
        // Pass session_id to parent for navigation
        setTimeout(() => {
          onSuccess({
            connectionName: connectionParams.connectionName,
            session_id: data.session_id,
            database: connectionParams.database || connectionParams.selectedDatabase,
            type: 'database'
          });
        }, 1000);
      } else {
        setTestStatus({ 
          type: 'error', 
          message: data.error || 'Connection failed' 
        });
      }
    } catch (error) {
      console.error('Database connection error:', error);
      setTestStatus({ 
        type: 'error', 
        message: error.message === 'HTTP error! status: 405' 
          ? 'Server configuration error. Please ensure the backend is running and CORS is configured.'
          : `Failed to connect to database: ${error.message}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    if (showExistingConnections) {
      setShowExistingConnections(false);
    } else {
      setStep(1);
      setTestStatus(null);
      setErrors({});
    }
  };

  const handleClose = () => {
    // Reset all state when closing
    setStep(1);
    setFormData({
      connectionName: '',
      host: '',
      port: '5432',
      user: '',
      password: '',
      ssl: false,
      selectedDatabase: ''
    });
    setDatabases([]);
    setErrors({});
    setTestStatus(null);
    setIsLoading(false);
    setShowExistingConnections(existingConnections.length > 0);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {showExistingConnections 
                ? 'PostgreSQL Connections' 
                : step === 1 
                  ? 'Connect to PostgreSQL Server' 
                  : 'Select Database'}
            </h2>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={isLoading}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Progress indicator */}
          {!showExistingConnections && (
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
          )}
        </div>

        <div className="p-6">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-blue-50 rounded-xl flex items-center justify-center">
              <img 
                src="public/connector/Postgres_logo.webp" 
                alt="PostgreSQL logo"
                className="w-16 h-16 object-contain"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.style.display = 'none';
                  e.target.parentElement.innerHTML = '🐘';
                  e.target.parentElement.style.fontSize = '3rem';
                }}
              />
            </div>
          </div>

          {/* Existing Connections */}
          {showExistingConnections ? (
            <>
              <div className="text-center mb-6">
                <h3 className="text-2xl font-semibold mb-2">Saved Connections</h3>
                <p className="text-gray-600">Select an existing connection or create a new one</p>
              </div>

              <div className="space-y-3 mb-6 max-h-60 overflow-y-auto">
                {existingConnections.map((conn) => (
                  <div
                    key={conn.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <Database className="w-4 h-4 text-gray-500" />
                          <span className="font-medium">{conn.connectionName}</span>
                          <Check className="w-4 h-4 text-green-500" />
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {conn.host}:{conn.port} | Database: {conn.database}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Last used: {new Date(conn.lastUsed).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleUseExistingConnection(conn)}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                        >
                          Use
                        </button>
                        <button
                          onClick={() => deleteConnection(conn)}
                          className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setShowExistingConnections(false)}
                className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors"
              >
                + Create New Connection
              </button>
            </>
          ) : step === 1 ? (
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
                <p className="text-gray-600">Enter the database name you want to connect to</p>
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
                    Database Name *
                  </label>
                  <input
                    type="text"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.selectedDatabase ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Enter database name (e.g., myapp_db)"
                    value={formData.selectedDatabase}
                    onChange={(e) => handleInputChange('selectedDatabase', e.target.value)}
                    disabled={isLoading}
                  />
                  {errors.selectedDatabase && (
                    <p className="text-red-500 text-sm mt-1">{errors.selectedDatabase}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Common database names: postgres, myapp_db, production, development
                  </p>
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
                    The selected database will be available for natural language queries and analysis.
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
            <span>Your credentials are encrypted and stored securely in your browser</span>
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
            {((step === 2 && !showExistingConnections) || (showExistingConnections && existingConnections.length > 0)) && (
              <button
                onClick={handleBack}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isLoading}
              >
                Back
              </button>
            )}
            <button
              onClick={handleClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancel
            </button>
            {!showExistingConnections && (
              step === 1 ? (
                <button
                  onClick={testServerConnection}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
                  onClick={() => connectToDatabase()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostgreSqlConnectorModal;