"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Paperclip, Loader2, X, FileText, Files } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"

const InputArea = ({
  isConnected,
  isAnalyzing,
  onSendMessage,
  onFileUpload,
  fileInfo,
  onShowFilePreview,
  onRemoveFile,
  isFileProcessing = false, // New prop for file processing state
}) => {
  const [showAllFiles, setShowAllFiles] = useState(false)
  const [inputMessage, setInputMessage] = useState("")
  const { themeClasses, isDark } = useTheme()
  const textareaRef = useRef(null)

  // Debug logging
  useEffect(() => {
    console.log('🔍 InputArea Debug:', {
      isFileProcessing,
      fileInfo: fileInfo ? { filename: fileInfo.filename } : null,
      isConnected,
      isAnalyzing
    })
  }, [isFileProcessing, fileInfo, isConnected, isAnalyzing])

  const handleSendMessage = () => {
    console.log('🚀 Send button clicked:', {
      hasMessage: !!inputMessage.trim(),
      isAnalyzing,
      isFileProcessing,
      isConnected
    })

    if (!inputMessage.trim() || isAnalyzing || isFileProcessing) {
      if (isFileProcessing) {
        console.log('❌ Blocked: File is still processing')
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

  const handleFilePreview = (specificFile = null) => {
    console.log('👁️ File preview clicked:', {
      hasFileInfo: !!fileInfo,
      isFileProcessing,
      hasPreviewHandler: !!onShowFilePreview,
      specificFile: specificFile ? specificFile.filename : 'default'
    })

    if (onShowFilePreview && fileInfo && !isFileProcessing) {
      onShowFilePreview(specificFile)
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
                {/* Multiple Files Display */}
                {fileInfo.files && fileInfo.files.length > 1 ? (
                  <div className="space-y-2">
                    {/* Header showing total count */}
                    <div className="flex items-center space-x-2">
                      <Files size={14} className={`${themeClasses.textSecondary} flex-shrink-0`} />
                      <span className={`text-xs ${themeClasses.textSecondary} font-medium`}>
                        {fileInfo.files.length} files uploaded
                      </span>
                      <button
                        onClick={handleRemoveFile}
                        className={`p-1 rounded-full ${isDark ? 'hover:bg-red-900/30' : 'hover:bg-red-100'} ${themeClasses.textSecondary} hover:text-red-600 transition-colors`}
                        title="Remove all files"
                      >
                        <X size={12} />
                      </button>
                    </div>
                    
                    {/* Individual file buttons - show first 3 or all based on showAllFiles */}
                    <div className="flex flex-wrap gap-2">
                      {(showAllFiles ? fileInfo.files : fileInfo.files.slice(0, 3)).map((file, index) => (
                        <button
                          key={index}
                          onClick={() => handleFilePreview(file)}
                          disabled={isFileProcessing || file.assistant_upload_status === 'pending'}
                          className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group border ${themeClasses.border} shadow-sm ${isFileProcessing || file.assistant_upload_status === 'pending' ? 'cursor-default opacity-75' : 'cursor-pointer'}`}
                          title={file.assistant_upload_status === 'pending' ? "Processing file..." : `Click to preview ${file.filename}`}
                        >
                          {file.assistant_upload_status === 'pending' ? (
                            <Loader2 size={12} className={`${themeClasses.textSecondary} flex-shrink-0 animate-spin`} />
                          ) : (
                            <FileText size={12} className={`${themeClasses.textSecondary} flex-shrink-0`} />
                          )}
                          <span
                            className={`text-xs ${themeClasses.text} truncate max-w-[120px] ${file.assistant_upload_status !== 'pending' ? (isDark ? 'group-hover:text-blue-400' : 'group-hover:text-blue-600') : ''}`}
                          >
                            {file.filename}
                          </span>
                        </button>
                      ))}
                      
                      {/* Show/Hide toggle for multiple files */}
                      {fileInfo.files.length > 3 && (
                        <button
                          onClick={() => setShowAllFiles(!showAllFiles)}
                          className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded-full ${themeClasses.surfaceSecondary} hover:${themeClasses.surface} transition-colors border ${themeClasses.border} shadow-sm`}
                          title={showAllFiles ? "Show fewer files" : "Show all files"}
                        >
                          <span className={`text-xs ${themeClasses.textSecondary}`}>
                            {showAllFiles ? 'Show less' : `+${fileInfo.files.length - 3} more`}
                          </span>
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  /* Single File Display (fallback) */
                  <button
                    onClick={() => handleFilePreview()}
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
                )}
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
      {process.env.NODE_ENV === 'development' && (
        <div className="max-w-4xl mx-auto px-4 py-1">
          <div className={`text-xs ${themeClasses.textSecondary} ${themeClasses.surface} rounded px-2 py-1`}>
            Debug: isFileProcessing={String(isFileProcessing)} | isAnalyzing={String(isAnalyzing)} | isConnected={String(isConnected)}
          </div>
        </div>
      )}
    </div>
  )
}

export default InputArea