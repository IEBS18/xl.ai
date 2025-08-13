import React, { useState } from "react"
import { Send, Paperclip, Loader2, X } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"

const InputArea = ({ 
  isConnected, 
  isAnalyzing, 
  onSendMessage, 
  onFileUpload, 
  fileInfo, 
  onShowFilePreview, 
  onRemoveFile 
}) => {
  const [inputMessage, setInputMessage] = useState("")
  const { themeClasses } = useTheme()

  const handleSendMessage = () => {
    if (!inputMessage.trim() || isAnalyzing) return
    onSendMessage(inputMessage)
    setInputMessage("")
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleFilePreview = () => {
    if (onShowFilePreview && fileInfo) {
      onShowFilePreview()
    }
  }

  const handleRemoveFile = (e) => {
    e.stopPropagation()
    if (onRemoveFile) {
      onRemoveFile()
    }
  }

  return (
    <div className={`${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className="max-w-4xl mx-auto px-4 py-2">
        <div className={`${themeClasses.glass} rounded-3xl shadow-lg`}>
          <div className="flex items-center space-x-3">
            {/* File indicator section */}
            {fileInfo && (
              <div className="flex-shrink-0 pl-2">
                <button
                  onClick={handleFilePreview}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-2xl ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group`}
                  title="Click to view file preview"
                >
                  <div className={`w-2 h-2 rounded-full bg-green-500 flex-shrink-0`}></div>
                  <span className={`text-sm ${themeClasses.text} truncate max-w-[150px] group-hover:text-blue-600 dark:group-hover:text-blue-400`}>
                    {fileInfo.filename}
                  </span>
                  <button
                    onClick={handleRemoveFile}
                    className={`p-1 rounded-full hover:bg-red-100 dark:hover:bg-red-900/30 ${themeClasses.textSecondary} hover:text-red-600 transition-colors`}
                    title="Remove file"
                  >
                    <X size={12} />
                  </button>
                </button>
              </div>
            )}

            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => {
                  setInputMessage(e.target.value);
                  // Auto-resize textarea
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onKeyPress={handleKeyPress}
                placeholder={
                  !isConnected 
                    ? "Connecting to server..." 
                    : fileInfo 
                      ? "Ask a question about your data..."
                      : "Upload a file or describe what you'd like to analyze..."
                }
                disabled={isAnalyzing || !isConnected}
                className={`w-full px-6 py-4 bg-transparent ${themeClasses.text} placeholder-gray-500 focus:outline-none text-base transition-all duration-200 resize-none`}
                style={{ minHeight: '56px', maxHeight: '200px' }}
                rows={1}
              />
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={onFileUpload}
                className={`p-3 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors rounded-2xl hover:${themeClasses.surfaceSecondary} flex-shrink-0`}
                title="Upload file"
              >
                <Paperclip size={20} />
              </button>

              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isAnalyzing || !isConnected}
                className={`${themeClasses.button} p-3 rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md transform hover:scale-105 disabled:transform-none flex-shrink-0`}
                title={!isConnected ? "Not connected" : "Send message"}
              >
                {isAnalyzing ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InputArea