import React, { useState } from "react"
import { Send, Paperclip, Loader2 } from "lucide-react"

const InputArea = ({ isConnected, isAnalyzing, onSendMessage, onFileUpload }) => {
  const [inputMessage, setInputMessage] = useState("")

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

  return (
    <div className="p-4 bg-gray-900 border-t border-gray-800 shadow-xl">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center space-x-3">
          <button
            onClick={onFileUpload}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors rounded-lg border border-gray-700"
            title="Upload new file"
          >
            <Paperclip size={18} />
          </button>
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={!isConnected ? "Connecting to server..." : "Ask me anything about your data..."}
              disabled={isAnalyzing || !isConnected}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-900 disabled:text-gray-500 text-sm shadow-sm text-white placeholder-gray-500"
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isAnalyzing || !isConnected}
            className="bg-white text-gray-900 p-3 rounded-xl hover:bg-gray-100 transition-all duration-200 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            title={!isConnected ? "Not connected" : "Send message"}
          >
            {isAnalyzing ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </div>
    </div>
  )
}

export default InputArea