// import React, { useState } from "react"
// import { X, Database, Loader2, TestTube, CheckCircle, AlertCircle } from "lucide-react"
// import { useTheme } from "../context/ThemeProvider"
// import { BACKEND_URL } from "../utils/constants"

// const DatabaseConnectionModal = ({ isOpen, onClose, onSuccess }) => {
//   const { isDark, themeClasses } = useTheme()
//   const [formData, setFormData] = useState({
//     connection_type: 'postgresql',
//     host: 'localhost',
//     port: '5432',
//     database: '',
//     username: '',
//     password: ''
//   })
//   const [isConnecting, setIsConnecting] = useState(false)
//   const [isTestingConnection, setIsTestingConnection] = useState(false)
//   const [connectionError, setConnectionError] = useState('')
//   const [testResult, setTestResult] = useState(null)

//   const databaseTypes = {
//     postgresql: { name: 'PostgreSQL', defaultPort: '5432' },
//     mysql: { name: 'MySQL', defaultPort: '3306' },
//     sqlite: { name: 'SQLite', defaultPort: '' },
//     mssql: { name: 'SQL Server', defaultPort: '1433' }
//   }

//   const handleInputChange = (field, value) => {
//     setFormData(prev => ({
//       ...prev,
//       [field]: value
//     }))
    
//     // Auto-update port when database type changes
//     if (field === 'connection_type') {
//       setFormData(prev => ({
//         ...prev,
//         port: databaseTypes[value].defaultPort
//       }))
//     }
    
//     // Clear previous test results and errors when form changes
//     setTestResult(null)
//     setConnectionError('')
//   }

//   const handleTestConnection = async () => {
//     setIsTestingConnection(true)
//     setConnectionError('')
//     setTestResult(null)
    
//     try {
//       const response = await fetch(`${BACKEND_URL}/api/database/test-connection`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(formData),
//         credentials: 'include'
//       })
      
//       const result = await response.json()
      
//       if (result.success) {
//         setTestResult({
//           success: true,
//           message: result.message,
//           tablesCount: result.tables_count
//         })
//       } else {
//         setTestResult({
//           success: false,
//           message: result.message
//         })
//       }
      
//     } catch (error) {
//       setTestResult({
//         success: false,
//         message: error.message || 'Connection test failed'
//       })
//     } finally {
//       setIsTestingConnection(false)
//     }
//   }

//   const handleConnect = async () => {
//     setIsConnecting(true)
//     setConnectionError('')
    
//     try {
//       const connectResponse = await fetch(`${BACKEND_URL}/api/database/connect`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(formData),
//         credentials: 'include'
//       })
      
//       const result = await connectResponse.json()
      
//       if (result.success) {
//         onSuccess(result.session_id)
//         onClose()
//       } else {
//         throw new Error(result.error || 'Connection failed')
//       }
      
//     } catch (error) {
//       setConnectionError(error.message)
//     } finally {
//       setIsConnecting(false)
//     }
//   }

//   const isFormValid = () => {
//     return formData.host && formData.database && formData.username && formData.password
//   }

//   if (!isOpen) return null

//   return (
//     <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
//       <div className={`${isDark ? 'bg-black/90 border-white/20' : 'bg-white/95 border-black/20'} 
//         rounded-2xl shadow-2xl border backdrop-blur-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto`}>
        
//         <div className="flex items-center justify-between mb-6">
//           <div className="flex items-center space-x-3">
//             <Database size={24} className={themeClasses.text} />
//             <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Connect Database</h2>
//           </div>
//           <button 
//             onClick={onClose} 
//             className={`${themeClasses.textMuted} hover:${themeClasses.text} p-1 rounded-lg transition-colors`}
//           >
//             <X size={20} />
//           </button>
//         </div>

//         <form onSubmit={(e) => { e.preventDefault(); handleConnect(); }} className="space-y-4">
//           <div>
//             <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//               Database Type
//             </label>
//             <select 
//               value={formData.connection_type}
//               onChange={(e) => handleInputChange('connection_type', e.target.value)}
//               className={`w-full p-3 rounded-xl ${isDark 
//                 ? 'bg-white/10 border-white/20 text-white' 
//                 : 'bg-black/5 border-black/20 text-black'
//               } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//             >
//               {Object.entries(databaseTypes).map(([key, { name }]) => (
//                 <option key={key} value={key}>{name}</option>
//               ))}
//             </select>
//           </div>

//           <div className="grid grid-cols-2 gap-4">
//             <div>
//               <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//                 Host
//               </label>
//               <input
//                 type="text"
//                 value={formData.host}
//                 onChange={(e) => handleInputChange('host', e.target.value)}
//                 placeholder="localhost"
//                 className={`w-full p-3 rounded-xl ${isDark 
//                   ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
//                   : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
//                 } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//                 required
//               />
//             </div>
//             <div>
//               <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//                 Port
//               </label>
//               <input
//                 type="text"
//                 value={formData.port}
//                 onChange={(e) => handleInputChange('port', e.target.value)}
//                 placeholder={databaseTypes[formData.connection_type].defaultPort}
//                 className={`w-full p-3 rounded-xl ${isDark 
//                   ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
//                   : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
//                 } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//                 required
//               />
//             </div>
//           </div>

//           <div>
//             <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//               Database Name
//             </label>
//             <input
//               type="text"
//               value={formData.database}
//               onChange={(e) => handleInputChange('database', e.target.value)}
//               placeholder="my_database"
//               className={`w-full p-3 rounded-xl ${isDark 
//                 ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
//                 : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
//               } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//               required
//             />
//           </div>

//           <div>
//             <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//               Username
//             </label>
//             <input
//               type="text"
//               value={formData.username}
//               onChange={(e) => handleInputChange('username', e.target.value)}
//               placeholder="username"
//               className={`w-full p-3 rounded-xl ${isDark 
//                 ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
//                 : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
//               } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//               required
//             />
//           </div>

//           <div>
//             <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
//               Password
//             </label>
//             <input
//               type="password"
//               value={formData.password}
//               onChange={(e) => handleInputChange('password', e.target.value)}
//               placeholder="password"
//               className={`w-full p-3 rounded-xl ${isDark 
//                 ? 'bg-white/10 border-white/20 text-white placeholder-gray-400' 
//                 : 'bg-black/5 border-black/20 text-black placeholder-gray-600'
//               } border backdrop-blur-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
//               required
//             />
//           </div>

//           {/* Test Connection Button */}
//           <button
//             type="button"
//             onClick={handleTestConnection}
//             disabled={!isFormValid() || isTestingConnection || isConnecting}
//             className={`w-full py-2.5 px-4 ${isDark 
//               ? 'bg-blue-600/20 hover:bg-blue-600/30 border-blue-500/30 text-blue-300' 
//               : 'bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700'
//             } border rounded-xl font-medium transition-all duration-200 
//               disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2`}
//           >
//             {isTestingConnection ? (
//               <>
//                 <Loader2 size={16} className="animate-spin" />
//                 <span>Testing Connection...</span>
//               </>
//             ) : (
//               <>
//                 <TestTube size={16} />
//                 <span>Test Connection</span>
//               </>
//             )}
//           </button>

//           {/* Test Result */}
//           {testResult && (
//             <div className={`p-3 rounded-xl border ${testResult.success 
//               ? 'bg-green-500/20 border-green-500/30' 
//               : 'bg-red-500/20 border-red-500/30'
//             }`}>
//               <div className="flex items-center space-x-2">
//                 {testResult.success ? (
//                   <CheckCircle size={16} className="text-green-400" />
//                 ) : (
//                   <AlertCircle size={16} className="text-red-400" />
//                 )}
//                 <p className={`text-sm ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
//                   {testResult.message}
//                 </p>
//               </div>
//               {testResult.success && testResult.tablesCount && (
//                 <p className={`text-xs ${themeClasses.textMuted} mt-1`}>
//                   Found {testResult.tablesCount} tables in database
//                 </p>
//               )}
//             </div>
//           )}

//           {/* Connection Error */}
//           {connectionError && (
//             <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-xl">
//               <div className="flex items-center space-x-2">
//                 <AlertCircle size={16} className="text-red-400" />
//                 <p className="text-red-400 text-sm">{connectionError}</p>
//               </div>
//             </div>
//           )}

//           {/* Connect Button */}
//           <button
//             type="submit"
//             disabled={!isFormValid() || isConnecting || isTestingConnection || (testResult && !testResult.success)}
//             className={`w-full py-3 px-6 ${themeClasses.button} rounded-xl font-medium transition-all duration-200 
//               disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2`}
//           >
//             {isConnecting ? (
//               <>
//                 <Loader2 size={16} className="animate-spin" />
//                 <span>Connecting...</span>
//               </>
//             ) : (
//               <>
//                 <Database size={16} />
//                 <span>Connect & Start Analysis</span>
//               </>
//             )}
//           </button>
//         </form>

//         <div className={`mt-4 p-3 rounded-xl ${isDark ? 'bg-blue-600/10' : 'bg-blue-50'}`}>
//           <p className={`text-xs ${themeClasses.textMuted}`}>
//             💡 <strong>Tip:</strong> Test your connection first to ensure it's working before proceeding with analysis.
//           </p>
//         </div>
//       </div>
//     </div>
//   )
// }

// export default DatabaseConnectionModal

import React, { useState, useCallback, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  X, 
  Database, 
  Loader2, 
  Server,
  Shield,
  Zap,
  Cloud,
  CheckCircle, 
  AlertCircle,
  TestTube,
  HardDrive,
  Globe,
  Lock
} from "lucide-react"
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
  const [successMessage, setSuccessMessage] = useState("")

  const databaseTypes = {
    postgresql: { name: 'PostgreSQL', defaultPort: '5432', icon: Database },
    mysql: { name: 'MySQL', defaultPort: '3306', icon: Database },
    sqlite: { name: 'SQLite', defaultPort: '', icon: HardDrive },
    mssql: { name: 'SQL Server', defaultPort: '1433', icon: Server }
  }

  // Features for left panel
  const features = [
    { icon: Shield, text: "Secure Connection", delay: 0 },
    { icon: Zap, text: "Real-time Sync", delay: 0.2 },
    { icon: Cloud, text: "Cloud & On-premise", delay: 0.4 },
    { icon: Database, text: "Multiple Databases", delay: 0.6 },
  ]

  // Memoized theme styles
  const themeStyles = useMemo(
    () => ({
      modal: `${themeClasses.surfaceCard} ${themeClasses.border}`,
      leftPanel: isDark
        ? "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900"
        : "bg-gradient-to-br from-gray-50 via-white to-gray-100",
      text: themeClasses.text,
      textSecondary: themeClasses.textSecondary,
      textMuted: themeClasses.textMuted,
      input: isDark
        ? "bg-gray-800/50 border-gray-700 text-white placeholder-gray-500"
        : "bg-gray-50/50 border-gray-300 text-gray-900 placeholder-gray-400",
      inputFocus: isDark
        ? "focus:ring-2 focus:ring-gray-500/30 focus:border-gray-400"
        : "focus:ring-2 focus:ring-gray-400/30 focus:border-gray-600",
      inputError: "border-red-500 focus:ring-red-500/30 focus:border-red-500",
      button: themeClasses.button,
      link: isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900",
      accent: themeClasses.text,
      success: themeClasses.success,
      warning: themeClasses.warning,
    }),
    [isDark, themeClasses],
  )

  const handleInputChange = useCallback((field, value) => {
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
    setSuccessMessage('')
  }, [])

  const handleTestConnection = useCallback(async () => {
    setIsTestingConnection(true)
    setConnectionError('')
    setTestResult(null)
    setSuccessMessage('')
    
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
        setSuccessMessage(`Connection successful! Found ${result.tables_count || 0} tables.`)
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
  }, [formData])

  const handleConnect = useCallback(async (e) => {
    e.preventDefault()
    if (!isFormValid()) return
    
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
        setSuccessMessage("Database connected successfully!")
        setTimeout(() => {
          onSuccess(result.session_id)
          handleClose()
        }, 1500)
      } else {
        throw new Error(result.error || 'Connection failed')
      }
      
    } catch (error) {
      setConnectionError(error.message)
    } finally {
      setIsConnecting(false)
    }
  }, [formData, onSuccess])

  const isFormValid = () => {
    if (formData.connection_type === 'sqlite') {
      return formData.database
    }
    return formData.host && formData.database && formData.username && formData.password
  }

  const resetForm = useCallback(() => {
    setFormData({
      connection_type: 'postgresql',
      host: 'localhost',
      port: '5432',
      database: '',
      username: '',
      password: ''
    })
    setConnectionError('')
    setTestResult(null)
    setSuccessMessage('')
  }, [])

  const handleClose = useCallback(() => {
    resetForm()
    onClose()
  }, [resetForm, onClose])

  // Animation variants
  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
  }

  const modalVariants = {
    hidden: {
      opacity: 0,
      x: "100%",
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: "spring",
        duration: 0.5,
        bounce: 0.1,
        staggerChildren: 0.1,
      },
    },
    exit: {
      opacity: 0,
      x: "100%",
      scale: 0.95,
      transition: { duration: 0.3 },
    },
  }

  const leftPanelVariants = {
    hidden: { opacity: 0, x: -50 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.6, ease: "easeOut" },
    },
  }

  const rightPanelVariants = {
    hidden: { opacity: 0, x: 50 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.6, ease: "easeOut", delay: 0.2 },
    },
  }

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut",
      },
    },
  }

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={handleClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={`w-full max-w-5xl h-[90vh] ${themeStyles.modal} border rounded-2xl shadow-2xl backdrop-blur-xl overflow-hidden flex`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Left Animated Panel */}
            <motion.div
              variants={leftPanelVariants}
              className={`hidden lg:flex lg:w-1/2 ${themeStyles.leftPanel} relative overflow-hidden`}
            >
              {/* Background Pattern */}
              <div className={`absolute inset-0 opacity-10 ${isDark ? "bg-white" : "bg-gray-900"}`}>
                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>
              </div>

              {/* Content */}
              <div className="relative z-10 p-12 flex flex-col justify-center">
                {/* Logo */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center space-x-3 mb-8"
                >
                  <Database className={`w-8 h-8 ${themeStyles.accent}`} />
                  <span className={`text-2xl font-bold ${themeStyles.text}`}>
                    Database Connection
                  </span>
                </motion.div>

                {/* Main Content */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="mb-8"
                >
                  <h2 className={`text-4xl font-bold ${themeStyles.text} mb-4 leading-tight`}>
                    Connect Your Data
                  </h2>
                  <p className={`text-lg ${themeStyles.textSecondary} leading-relaxed`}>
                    Securely connect to your database and unlock powerful analytics capabilities. 
                    Support for PostgreSQL, MySQL, SQLite, and SQL Server.
                  </p>
                </motion.div>

                {/* Animated Features */}
                <div className="space-y-4">
                  {features.map((feature, index) => (
                    <motion.div
                      key={feature.text}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + feature.delay }}
                      className="flex items-center space-x-3"
                    >
                      <motion.div
                        variants={floatingVariants}
                        animate="animate"
                        transition={{ delay: index * 0.5 }}
                        className={`p-2 rounded-lg ${isDark ? "bg-gray-800/50" : "bg-white/50"} backdrop-blur-sm`}
                      >
                        <feature.icon className={`w-5 h-5 ${themeStyles.accent}`} />
                      </motion.div>
                      <span className={`${themeStyles.textSecondary} font-medium`}>{feature.text}</span>
                    </motion.div>
                  ))}
                </div>

                {/* Floating Elements */}
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  className={`absolute top-20 right-20 w-20 h-20 rounded-full ${isDark ? "bg-gray-700/30" : "bg-gray-300/30"} backdrop-blur-sm`}
                />
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  transition={{ delay: 2 }}
                  className={`absolute bottom-32 right-16 w-12 h-12 rounded-full ${isDark ? "bg-gray-600/20" : "bg-gray-400/20"} backdrop-blur-sm`}
                />
              </div>
            </motion.div>

            {/* Right Form Panel */}
            <motion.div variants={rightPanelVariants} className="w-full lg:w-1/2 flex flex-col relative">
              {/* Close Button */}
              <button
                onClick={handleClose}
                className={`absolute top-6 right-6 z-20 p-2 rounded-lg transition-all duration-200 ${themeStyles.link}`}
              >
                <X className="w-5 h-5" />
              </button>

              {/* Scrollable Content */}
              <div
                className={`custom-scrollbar flex-1 overflow-y-auto p-8 ${isDark
                  ? "[&::-webkit-scrollbar-track]:bg-gray-800 [&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500"
                  : "[&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-400 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500"
                  } [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:rounded-sm`}
                style={{
                  scrollbarWidth: "thin",
                  scrollbarColor: isDark ? "#4B5563 #1F2937" : "#9CA3AF #F3F6F6",
                }}
              >
                <div className="max-w-md mx-auto">
                  {/* Form Header */}
                  <div className="mb-8 pt-8">
                    <h2 className={`text-3xl font-bold ${themeStyles.text} mb-2`}>Database Details</h2>
                    <p className={`${themeStyles.textSecondary}`}>Enter your database connection information</p>
                  </div>

                  {/* Success Message */}
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-lg border mb-5 ${isDark 
                        ? 'bg-green-500/10 border-green-500/20 text-green-400' 
                        : 'bg-green-50 border-green-200 text-green-700'}`}
                    >
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{successMessage}</p>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Form */}
                  <form onSubmit={handleConnect} className="space-y-5">
                    {/* Database Type */}
                    <div>
                      <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                        Database Type
                      </label>
                      <div className="relative">
                        <Database className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                        <select 
                          value={formData.connection_type}
                          onChange={(e) => handleInputChange('connection_type', e.target.value)}
                          className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus} appearance-none cursor-pointer`}
                          disabled={isConnecting || isTestingConnection}
                        >
                          {Object.entries(databaseTypes).map(([key, { name }]) => (
                            <option key={key} value={key}>{name}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Host and Port - Not for SQLite */}
                    {formData.connection_type !== 'sqlite' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            Host
                          </label>
                          <div className="relative">
                            <Globe className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                            <input
                              type="text"
                              value={formData.host}
                              onChange={(e) => handleInputChange('host', e.target.value)}
                              placeholder="localhost"
                              className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus}`}
                              required
                              disabled={isConnecting || isTestingConnection}
                            />
                          </div>
                        </div>
                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            Port
                          </label>
                          <input
                            type="text"
                            value={formData.port}
                            onChange={(e) => handleInputChange('port', e.target.value)}
                            placeholder={databaseTypes[formData.connection_type].defaultPort}
                            className={`w-full px-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus}`}
                            required
                            disabled={isConnecting || isTestingConnection}
                          />
                        </div>
                      </div>
                    )}

                    {/* Database Name */}
                    <div>
                      <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                        {formData.connection_type === 'sqlite' ? 'Database File Path' : 'Database Name'}
                      </label>
                      <div className="relative">
                        <HardDrive className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                        <input
                          type="text"
                          value={formData.database}
                          onChange={(e) => handleInputChange('database', e.target.value)}
                          placeholder={formData.connection_type === 'sqlite' ? '/path/to/database.db' : 'my_database'}
                          className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus}`}
                          required
                          disabled={isConnecting || isTestingConnection}
                        />
                      </div>
                    </div>

                    {/* Username and Password - Not for SQLite */}
                    {formData.connection_type !== 'sqlite' && (
                      <>
                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            Username
                          </label>
                          <div className="relative">
                            <Server className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                            <input
                              type="text"
                              value={formData.username}
                              onChange={(e) => handleInputChange('username', e.target.value)}
                              placeholder="username"
                              className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus}`}
                              required
                              disabled={isConnecting || isTestingConnection}
                            />
                          </div>
                        </div>

                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            Password
                          </label>
                          <div className="relative">
                            <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                            <input
                              type="password"
                              value={formData.password}
                              onChange={(e) => handleInputChange('password', e.target.value)}
                              placeholder="••••••••"
                              className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${themeStyles.input} ${themeStyles.inputFocus}`}
                              required
                              disabled={isConnecting || isTestingConnection}
                            />
                          </div>
                        </div>
                      </>
                    )}

                    {/* Test Result */}
                    {testResult && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`p-4 rounded-lg border ${testResult.success 
                          ? isDark ? 'bg-green-500/10 border-green-500/20' : 'bg-green-50 border-green-200'
                          : isDark ? 'bg-red-500/10 border-red-500/20' : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex items-start space-x-2">
                          {testResult.success ? (
                            <CheckCircle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                          ) : (
                            <AlertCircle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isDark ? 'text-red-400' : 'text-red-600'}`} />
                          )}
                          <div className="flex-1">
                            <p className={`text-sm font-medium ${testResult.success 
                              ? isDark ? 'text-green-400' : 'text-green-700'
                              : isDark ? 'text-red-400' : 'text-red-700'
                            }`}>
                              {testResult.message}
                            </p>
                            {testResult.success && testResult.tablesCount !== undefined && (
                              <p className={`text-xs mt-1 ${themeStyles.textMuted}`}>
                                Found {testResult.tablesCount} tables in database
                              </p>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Connection Error */}
                    {connectionError && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`p-4 rounded-lg border ${isDark 
                          ? 'bg-red-500/10 border-red-500/20' 
                          : 'bg-red-50 border-red-200'}`}
                      >
                        <div className="flex items-start space-x-2">
                          <AlertCircle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isDark ? 'text-red-400' : 'text-red-600'}`} />
                          <p className={`text-sm font-medium ${isDark ? 'text-red-400' : 'text-red-700'}`}>
                            {connectionError}
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Test Connection Button */}
                    <motion.button
                      type="button"
                      onClick={handleTestConnection}
                      disabled={!isFormValid() || isTestingConnection || isConnecting}
                      className={`w-full py-3 rounded-lg font-medium transition-all duration-200 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed border ${isDark 
                        ? 'bg-gray-800/50 border-gray-700 text-white hover:bg-gray-700/50' 
                        : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'}`}
                      whileHover={!isTestingConnection && !isConnecting ? { scale: 1.02 } : {}}
                      whileTap={!isTestingConnection && !isConnecting ? { scale: 0.98 } : {}}
                    >
                      {isTestingConnection ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className={`w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin`} />
                          <span>Testing Connection...</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center space-x-2">
                          <TestTube className="w-5 h-5" />
                          <span>Test Connection</span>
                        </div>
                      )}
                    </motion.button>

                    {/* Connect Button */}
                    <motion.button
                      type="submit"
                      disabled={!isFormValid() || isConnecting || isTestingConnection || (testResult && !testResult.success)}
                      className={`w-full py-3 rounded-lg font-medium transition-all duration-200 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${themeClasses.button}`}
                      whileHover={!isConnecting && !isTestingConnection ? { scale: 1.02 } : {}}
                      whileTap={!isConnecting && !isTestingConnection ? { scale: 0.98 } : {}}
                    >
                      {isConnecting ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className={`w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin`} />
                          <span>Connecting...</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center space-x-2">
                          <Database className="w-5 h-5" />
                          <span>Connect & Start Analysis</span>
                        </div>
                      )}
                    </motion.button>
                  </form>

                  {/* Tips */}
                  <div className={`mt-6 p-4 rounded-lg ${isDark 
                    ? 'bg-blue-500/10 border border-blue-500/20' 
                    : 'bg-blue-50 border border-blue-200'}`}>
                    <p className={`text-xs ${themeStyles.textSecondary} leading-relaxed`}>
                      <strong>💡 Tip:</strong> Test your connection first to ensure it's working before proceeding. 
                      Your connection details are encrypted and never stored permanently.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default DatabaseConnectionModal