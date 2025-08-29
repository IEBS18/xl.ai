// "use client"

// import { useState, useRef, useEffect } from "react"
// import { Send, Paperclip, Loader2, X, FileText } from "lucide-react"
// import { useTheme } from "@/context/ThemeProvider"

// const InputArea = ({
//   isConnected,
//   isAnalyzing,
//   onSendMessage,
//   onFileUpload,
//   fileInfo,
//   onShowFilePreview,
//   onRemoveFile,
//   isFileProcessing = false, // New prop for file processing state
// }) => {
//   const [inputMessage, setInputMessage] = useState("")
//   const { themeClasses, isDark } = useTheme()
//   const textareaRef = useRef(null)

//   // Debug logging
//   useEffect(() => {
//     console.log('🔍 InputArea Debug:', {
//       isFileProcessing,
//       fileInfo: fileInfo ? { filename: fileInfo.filename } : null,
//       isConnected,
//       isAnalyzing
//     })
//   }, [isFileProcessing, fileInfo, isConnected, isAnalyzing])

//   const handleSendMessage = () => {
//     console.log('🚀 Send button clicked:', {
//       hasMessage: !!inputMessage.trim(),
//       isAnalyzing,
//       isFileProcessing,
//       isConnected
//     })

//     if (!inputMessage.trim() || isAnalyzing || isFileProcessing) {
//       if (isFileProcessing) {
//         console.log('❌ Blocked: File is still processing')
//       }
//       return
//     }

//     onSendMessage(inputMessage)
//     setInputMessage("")
//     if (textareaRef.current) {
//       textareaRef.current.style.height = "auto"
//       textareaRef.current.style.height = "56px"
//     }
//   }

//   const handleKeyPress = (e) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault()
//       handleSendMessage()
//     }
//   }

//   const handleFilePreview = () => {
//     console.log('👁️ File preview clicked:', {
//       hasFileInfo: !!fileInfo,
//       isFileProcessing,
//       hasPreviewHandler: !!onShowFilePreview
//     })

//     if (onShowFilePreview && fileInfo && !isFileProcessing) {
//       onShowFilePreview()
//     }
//   }

//   const handleRemoveFile = (e) => {
//     e.stopPropagation()
//     console.log('🗑️ Remove file clicked:', { isFileProcessing })
//     if (onRemoveFile) {
//       onRemoveFile()
//     }
//   }

//   const handleFileUpload = () => {
//     console.log('📎 File upload clicked:', { isFileProcessing })
//     if (!isFileProcessing && onFileUpload) {
//       onFileUpload()
//     }
//   }

//   // Calculate if send button should be disabled
//   const isSendDisabled = !inputMessage.trim() || isAnalyzing || !isConnected || isFileProcessing

//   console.log('🎛️ InputArea State:', {
//     isFileProcessing,
//     isSendDisabled,
//     inputDisabled: isAnalyzing || !isConnected || isFileProcessing
//   })

//   return (
//     <div className={`${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
//       <div className="max-w-4xl mx-auto px-4 py-2">
//         <div className={`${themeClasses.glass} rounded-3xl shadow-lg`}>
//           <div className="flex flex-col">
//             {fileInfo && (
//               <div className="px-6 pt-4 pb-2">
//                 <button
//                   onClick={handleFilePreview}
//                   disabled={isFileProcessing}
//                   className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group border ${themeClasses.border} shadow-sm ${isFileProcessing ? 'cursor-default opacity-75' : 'cursor-pointer'}`}
//                   title={isFileProcessing ? "Preprocessing file for analysis..." : "Click to view file preview"}
//                 >
//                   {isFileProcessing ? (
//                     <>
//                       <Loader2 size={14} className={`${themeClasses.textSecondary} flex-shrink-0 animate-spin`} />
//                       <span className={`text-xs ${themeClasses.textSecondary} font-medium ${isDark ? 'text-orange-400' : 'text-orange-600'}`}>
//                         PROCESSING
//                       </span>
//                     </>
//                   ) : (
//                     <FileText size={14} className={`${themeClasses.textSecondary} flex-shrink-0`} />
//                   )}
//                   <span
//                     className={`text-sm ${themeClasses.text} truncate max-w-[200px] ${!isFileProcessing ? (isDark ? 'group-hover:text-blue-400' : 'group-hover:text-blue-600') : ''}`}
//                   >
//                     {fileInfo.filename}
//                   </span>
//                   {isFileProcessing && (
//                     <span className={`text-xs ${themeClasses.textSecondary} whitespace-nowrap animate-pulse`}>
//                       Processing...
//                     </span>
//                   )}
//                   <button
//                     onClick={handleRemoveFile}
//                     className={`p-0.5 rounded-full ${isDark ? 'hover:bg-red-900/30' : 'hover:bg-red-100'} ${themeClasses.textSecondary} hover:text-red-600 transition-colors ml-1`}
//                     title="Remove file"
//                   >
//                     <X size={12} />
//                   </button>
//                 </button>
//               </div>
//             )}

//             <div className="flex items-center space-x-3">
//               <div className="flex-1 relative">
//                 <textarea
//                   ref={textareaRef}
//                   value={inputMessage}
//                   onChange={(e) => {
//                     setInputMessage(e.target.value)
//                     // Auto-resize textarea
//                     e.target.style.height = "auto"
//                     e.target.style.height = e.target.scrollHeight + "px"
//                   }}
//                   onKeyPress={handleKeyPress}
//                   placeholder={
//                     !isConnected
//                       ? "Connecting to server..."
//                       : isFileProcessing
//                         ? "⏳ Processing file... Please wait"
//                       : fileInfo
//                         ? "Ask a follow-up..."
//                         : "Upload a file or describe what you'd like to analyze..."
//                   }
//                   disabled={isAnalyzing || !isConnected || isFileProcessing}
//                   className={`w-full px-6 ${fileInfo ? "py-2 pb-4" : "py-4"} bg-transparent ${themeClasses.text} placeholder-gray-500 focus:outline-none text-base transition-all duration-200 resize-none ${
//                     isFileProcessing ? 'opacity-60 cursor-not-allowed' : ''
//                   }`}
//                   style={{ minHeight: fileInfo ? "40px" : "56px", maxHeight: "200px" }}
//                   rows={1}
//                 />
                
//                 {/* Processing overlay */}
//                 {isFileProcessing && (
//                   <div className={`absolute inset-0 ${isDark ? 'bg-gray-800/50' : 'bg-gray-100/50'} rounded-3xl flex items-center justify-center pointer-events-none`}>
//                     <div className={`flex items-center space-x-2 text-sm ${themeClasses.textSecondary}`}>
//                       <Loader2 size={16} className="animate-spin" />
//                       <span>Processing file...</span>
//                     </div>
//                   </div>
//                 )}
//               </div>

//               <div className="flex items-center space-x-2">
//                 <button
//                   onClick={handleFileUpload}
//                   disabled={isFileProcessing}
//                   className={`p-3 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors rounded-2xl hover:${themeClasses.surfaceSecondary} flex-shrink-0 ${isFileProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
//                   title={isFileProcessing ? "Processing current file..." : "Upload file"}
//                 >
//                   {isFileProcessing ? (
//                     <Loader2 size={20} className="animate-spin" />
//                   ) : (
//                     <Paperclip size={20} />
//                   )}
//                 </button>

//                 <button
//                   onClick={handleSendMessage}
//                   disabled={isSendDisabled}
//                   className={`${themeClasses.button} p-3 rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md transform hover:scale-105 disabled:transform-none flex-shrink-0 ${
//                     isFileProcessing ? `${themeClasses.surface} cursor-not-allowed` : ''
//                   }`}
//                   title={
//                     !isConnected 
//                       ? "Not connected" 
//                       : isFileProcessing 
//                         ? "⏳ Processing file... Please wait" 
//                         : isAnalyzing
//                           ? "Analyzing..."
//                           : "Send message"
//                   }
//                 >
//                   {isAnalyzing ? (
//                     <Loader2 size={20} className="animate-spin" />
//                   ) : isFileProcessing ? (
//                     <div className="flex items-center space-x-1">
//                       <Loader2 size={16} className="animate-spin" />
//                     </div>
//                   ) : (
//                     <Send size={20} />
//                   )}
//                 </button>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
      
//       {/* Debug info in development */}
//       {process.env.NODE_ENV === 'development' && (
//         <div className="max-w-4xl mx-auto px-4 py-1">
//           <div className={`text-xs ${themeClasses.textSecondary} ${themeClasses.surface} rounded px-2 py-1`}>
//             Debug: isFileProcessing={String(isFileProcessing)} | isAnalyzing={String(isAnalyzing)} | isConnected={String(isConnected)}
//           </div>
//         </div>
//       )}
//     </div>
//   )
// }

// export default InputArea


import { useState, useRef, useEffect } from "react"
import { Send, Paperclip, Loader2, X, FileText, Plus, Database, Folder } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
import PostgreSqlConnectorModal from '@/components/connectors/PostgreSqlConnectorModal'

const InputArea = ({
  isConnected,
  isAnalyzing,
  onSendMessage,
  onFileUpload,
  fileInfo,
  onShowFilePreview,
  onRemoveFile,
  isFileProcessing = false,
  onNavigateToDataConnector, // New prop for navigation
}) => {
  const [inputMessage, setInputMessage] = useState("")
  const [showConnectorDropdown, setShowConnectorDropdown] = useState(false)
  const [showPostgreSqlModal, setShowPostgreSqlModal] = useState(false)
  const { themeClasses, isDark } = useTheme()
  const textareaRef = useRef(null)
  const dropdownRef = useRef(null)

  // Debug logging
  useEffect(() => {
    console.log('🔍 InputArea Debug:', {
      isFileProcessing,
      fileInfo: fileInfo ? { filename: fileInfo.filename } : null,
      isConnected,
      isAnalyzing
    })
  }, [isFileProcessing, fileInfo, isConnected, isAnalyzing])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowConnectorDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handleSendMessage = () => {
    console.log('🚀 Send button clicked:', {
      hasMessage: !!inputMessage.trim(),
      isAnalyzing,
      isFileProcessing,
      isConnected
    })

    if (!inputMessage.trim() || isAnalyzing || isFileProcessing) {
      if (isFileProcessing) {
        console.log('⛔ Blocked: File is still processing')
      }
      return
    }

    onSendMessage(inputMessage)
    setInputMessage("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = "56px"
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleFilePreview = () => {
    console.log('👁️ File preview clicked:', {
      hasFileInfo: !!fileInfo,
      isFileProcessing,
      hasPreviewHandler: !!onShowFilePreview
    })

    if (onShowFilePreview && fileInfo && !isFileProcessing) {
      onShowFilePreview()
    }
  }

  const handleRemoveFile = (e) => {
    e.stopPropagation()
    console.log('🗑️ Remove file clicked:', { isFileProcessing })
    if (onRemoveFile) {
      onRemoveFile()
    }
  }

  const handleFileUpload = () => {
    console.log('📎 File upload clicked:', { isFileProcessing })
    if (!isFileProcessing && onFileUpload) {
      onFileUpload()
    }
  }

  const handleConnectorClick = () => {
    setShowConnectorDropdown(!showConnectorDropdown)
  }

  const handleGoogleDriveConnect = () => {
    console.log('Connecting to Google Drive...')
    setShowConnectorDropdown(false)
    // Add Google Drive OAuth logic here
    alert('Google Drive OAuth flow would start here')
  }

  const handlePostgreSqlConnect = () => {
    setShowConnectorDropdown(false)
    setShowPostgreSqlModal(true)
  }

  const handleViewAllConnectors = () => {
    setShowConnectorDropdown(false)
    if (onNavigateToDataConnector) {
      onNavigateToDataConnector()
    }
  }

  const handlePostgreSqlSuccess = (connectionData) => {
    console.log('PostgreSQL connected successfully:', connectionData)
    setShowPostgreSqlModal(false)
    // Handle successful connection
  }

  // Calculate if send button should be disabled
  const isSendDisabled = !inputMessage.trim() || isAnalyzing || !isConnected || isFileProcessing

  console.log('🎛️ InputArea State:', {
    isFileProcessing,
    isSendDisabled,
    inputDisabled: isAnalyzing || !isConnected || isFileProcessing
  })

  return (
    <div className={`${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className="max-w-4xl mx-auto px-4 py-2">
        <div className={`${themeClasses.glass} rounded-3xl shadow-lg`}>
          <div className="flex flex-col">
            {fileInfo && (
              <div className="px-6 pt-4 pb-2">
                <button
                  onClick={handleFilePreview}
                  disabled={isFileProcessing}
                  className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group border ${themeClasses.border} shadow-sm ${isFileProcessing ? 'cursor-default opacity-75' : 'cursor-pointer'}`}
                  title={isFileProcessing ? "Preprocessing file for analysis..." : "Click to view file preview"}
                >
                  {isFileProcessing ? (
                    <>
                      <Loader2 size={14} className={`${themeClasses.textSecondary} flex-shrink-0 animate-spin`} />
                      <span className={`text-xs ${themeClasses.textSecondary} font-medium ${isDark ? 'text-orange-400' : 'text-orange-600'}`}>
                        PROCESSING
                      </span>
                    </>
                  ) : (
                    <FileText size={14} className={`${themeClasses.textSecondary} flex-shrink-0`} />
                  )}
                  <span
                    className={`text-sm ${themeClasses.text} truncate max-w-[200px] ${!isFileProcessing ? (isDark ? 'group-hover:text-blue-400' : 'group-hover:text-blue-600') : ''}`}
                  >
                    {fileInfo.filename}
                  </span>
                  {isFileProcessing && (
                    <span className={`text-xs ${themeClasses.textSecondary} whitespace-nowrap animate-pulse`}>
                      Processing...
                    </span>
                  )}
                  <button
                    onClick={handleRemoveFile}
                    className={`p-0.5 rounded-full ${isDark ? 'hover:bg-red-900/30' : 'hover:bg-red-100'} ${themeClasses.textSecondary} hover:text-red-600 transition-colors ml-1`}
                    title="Remove file"
                  >
                    <X size={12} />
                  </button>
                </button>
              </div>
            )}

            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={(e) => {
                    setInputMessage(e.target.value)
                    // Auto-resize textarea
                    e.target.style.height = "auto"
                    e.target.style.height = e.target.scrollHeight + "px"
                  }}
                  onKeyPress={handleKeyPress}
                  placeholder={
                    !isConnected
                      ? "Connecting to server..."
                      : isFileProcessing
                        ? "⏳ Processing file... Please wait"
                      : fileInfo
                        ? "Ask a follow-up..."
                        : "Upload a file or describe what you'd like to analyze..."
                  }
                  disabled={isAnalyzing || !isConnected || isFileProcessing}
                  className={`w-full px-6 ${fileInfo ? "py-2 pb-4" : "py-4"} bg-transparent ${themeClasses.text} placeholder-gray-500 focus:outline-none text-base transition-all duration-200 resize-none ${
                    isFileProcessing ? 'opacity-60 cursor-not-allowed' : ''
                  }`}
                  style={{ minHeight: fileInfo ? "40px" : "56px", maxHeight: "200px" }}
                  rows={1}
                />
                
                {/* Processing overlay */}
                {isFileProcessing && (
                  <div className={`absolute inset-0 ${isDark ? 'bg-gray-800/50' : 'bg-gray-100/50'} rounded-3xl flex items-center justify-center pointer-events-none`}>
                    <div className={`flex items-center space-x-2 text-sm ${themeClasses.textSecondary}`}>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Processing file...</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                {/* Connector Dropdown */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={handleConnectorClick}
                    disabled={isFileProcessing}
                    className={`p-3 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors rounded-2xl hover:${themeClasses.surfaceSecondary} flex-shrink-0 ${isFileProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={isFileProcessing ? "Processing current file..." : "Connect data sources"}
                  >
                    <Plus size={20} />
                  </button>

                  {showConnectorDropdown && (
                    <div className={`absolute bottom-full right-0 mb-2 w-64 ${themeClasses.surface} border ${themeClasses.border} rounded-lg shadow-lg z-50`}>
                      <div className="p-2">
                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                          Quick Connect
                        </div>
                        
                        <button
                          onClick={handleGoogleDriveConnect}
                          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:${themeClasses.surfaceSecondary} transition-colors text-left`}
                        >
                          <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                            <Folder className="w-4 h-4 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className={`text-sm font-medium ${themeClasses.text}`}>Google Drive</div>
                            <div className={`text-xs ${themeClasses.textSecondary}`}>Analyze your files and folders</div>
                          </div>
                        </button>

                        <button
                          onClick={handlePostgreSqlConnect}
                          className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:${themeClasses.surfaceSecondary} transition-colors text-left`}
                        >
                          <div className="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center">
                            <Database className="w-4 h-4 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className={`text-sm font-medium ${themeClasses.text}`}>PostgreSQL</div>
                            <div className={`text-xs ${themeClasses.textSecondary}`}>Connect to your database</div>
                          </div>
                        </button>

                        <div className="border-t border-gray-200 mt-2 pt-2">
                          <button
                            onClick={handleViewAllConnectors}
                            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:${themeClasses.surfaceSecondary} transition-colors text-left`}
                          >
                            <div className={`w-8 h-8 ${themeClasses.surface} border ${themeClasses.border} rounded-lg flex items-center justify-center`}>
                              <Plus className={`w-4 h-4 ${themeClasses.textSecondary}`} />
                            </div>
                            <div className="flex-1">
                              <div className={`text-sm font-medium ${themeClasses.text}`}>View All Connectors</div>
                              <div className={`text-xs ${themeClasses.textSecondary}`}>Browse all available connections</div>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleFileUpload}
                  disabled={isFileProcessing}
                  className={`p-3 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors rounded-2xl hover:${themeClasses.surfaceSecondary} flex-shrink-0 ${isFileProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title={isFileProcessing ? "Processing current file..." : "Upload file"}
                >
                  {isFileProcessing ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : (
                    <Paperclip size={20} />
                  )}
                </button>

                <button
                  onClick={handleSendMessage}
                  disabled={isSendDisabled}
                  className={`${themeClasses.button} p-3 rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md transform hover:scale-105 disabled:transform-none flex-shrink-0 ${
                    isFileProcessing ? `${themeClasses.surface} cursor-not-allowed` : ''
                  }`}
                  title={
                    !isConnected 
                      ? "Not connected" 
                      : isFileProcessing 
                        ? "⏳ Processing file... Please wait" 
                        : isAnalyzing
                          ? "Analyzing..."
                          : "Send message"
                  }
                >
                  {isAnalyzing ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : isFileProcessing ? (
                    <div className="flex items-center space-x-1">
                      <Loader2 size={16} className="animate-spin" />
                    </div>
                  ) : (
                    <Send size={20} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Debug info in development */}
      {import.meta.env.NODE_ENV === 'development' && (
        <div className="max-w-4xl mx-auto px-4 py-1">
          <div className={`text-xs ${themeClasses.textSecondary} ${themeClasses.surface} rounded px-2 py-1`}>
            Debug: isFileProcessing={String(isFileProcessing)} | isAnalyzing={String(isAnalyzing)} | isConnected={String(isConnected)}
          </div>
        </div>
      )}

      {/* PostgreSQL Modal */}
      <PostgreSqlConnectorModal
        isOpen={showPostgreSqlModal}
        onClose={() => setShowPostgreSqlModal(false)}
        onSuccess={handlePostgreSqlSuccess}
        connector={{
          id: 'postgres',
          name: 'PostgreSQL',
          description: 'Open source relational database'
        }}
      />
    </div>
  )
}

export default InputArea