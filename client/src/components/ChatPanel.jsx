"use client"

import { useState, useEffect, useRef } from "react"
import { Send, X, Bot, User, Loader2, CheckCircle, AlertCircle, Sparkles } from "lucide-react"

export function ChatPanel({ socket, connected, hasData, onClose }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const scrollAreaRef = useRef(null)

  const addMessage = (message) => {
    setMessages((prev) => [...prev, { ...message, id: Date.now().toString() }])
  }

  const handleSendMessage = () => {
    if (!inputValue.trim() || !socket || !hasData || isAnalyzing) return

    const userMessage = inputValue.trim()
    addMessage({
      type: "user",
      content: userMessage,
      timestamp: new Date(),
    })

    setInputValue("")
    setIsAnalyzing(true)

    socket.emit("analyze_query", {
      query: userMessage,
      session_id: Date.now().toString(),
    })
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  useEffect(() => {
    if (!socket) return

    const handleAnalysisUpdate = (update) => {
      const { type, data, timestamp } = update

      switch (type) {
        case "status":
          addMessage({
            type: "status",
            content: data.message,
            timestamp: new Date(timestamp),
          })
          break
        case "error":
          addMessage({
            type: "error",
            content: data.message,
            timestamp: new Date(timestamp),
          })
          setIsAnalyzing(false)
          break
        case "code_generation":
          addMessage({
            type: "status",
            content: "Generating analysis code...",
            timestamp: new Date(timestamp),
          })
          break
        case "execution_success":
          addMessage({
            type: "success",
            content: "Analysis completed successfully!",
            timestamp: new Date(timestamp),
          })
          break
        case "chart":
          addMessage({
            type: "success",
            content: `Generated chart: ${data.filename}`,
            timestamp: new Date(timestamp),
          })
          break
        case "report":
          addMessage({
            type: "success",
            content: "Generated comprehensive report",
            timestamp: new Date(timestamp),
          })
          break
      }
    }

    const handleAnalysisComplete = (result) => {
      setIsAnalyzing(false)

      if (result.result?.error) {
        addMessage({
          type: "error",
          content: result.result.error,
          timestamp: new Date(result.timestamp),
        })
      } else if (result.result?.message) {
        addMessage({
          type: "bot",
          content: result.result.message,
          timestamp: new Date(result.timestamp),
        })
      } else {
        addMessage({
          type: "success",
          content: "Analysis completed",
          timestamp: new Date(result.timestamp),
        })
      }
    }

    socket.on("analysis_update", handleAnalysisUpdate)
    socket.on("analysis_complete", handleAnalysisComplete)

    return () => {
      socket.off("analysis_update", handleAnalysisUpdate)
      socket.off("analysis_complete", handleAnalysisComplete)
    }
  }, [socket])

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const getMessageIcon = (type) => {
    switch (type) {
      case "user":
        return <User className="w-4 h-4" />
      case "bot":
        return <Bot className="w-4 h-4" />
      case "success":
        return <CheckCircle className="w-4 h-4" />
      case "error":
        return <AlertCircle className="w-4 h-4" />
      case "status":
        return <Loader2 className="w-4 h-4 animate-spin" />
      default:
        return <Bot className="w-4 h-4" />
    }
  }

  const getMessageStyle = (type) => {
    switch (type) {
      case "user":
        return "bg-primary-600 text-white ml-8"
      case "bot":
        return "bg-gray-100 text-gray-900 mr-8"
      case "success":
        return "bg-green-50 text-green-800 border border-green-200 mr-8"
      case "error":
        return "bg-red-50 text-red-800 border border-red-200 mr-8"
      case "status":
        return "bg-blue-50 text-blue-800 border border-blue-200 mr-8"
      default:
        return "bg-gray-100 text-gray-900 mr-8"
    }
  }

  const suggestions = [
    "What is the average of sales?",
    "Show me a chart of revenue by month",
    "Generate a summary report",
    "Find the maximum value in price column",
    "Create a correlation analysis",
  ]

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Sparkles className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">AI Assistant</h2>
              <p className="text-xs text-gray-600">{connected ? "Ready to analyze your data" : "Connecting..."}</p>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <div ref={scrollAreaRef} className="h-full overflow-y-auto custom-scrollbar p-4">
          <div className="space-y-4">
            {!hasData && (
              <div className="card p-4 bg-blue-50 border-blue-200">
                <div className="flex items-start space-x-3">
                  <Bot className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm text-blue-800 font-medium mb-2">Welcome to DataFlow Pro!</p>
                    <p className="text-xs text-blue-700">
                      Upload a CSV or Excel file to start analyzing your data with AI-powered insights.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {hasData && messages.length === 0 && (
              <div className="space-y-3">
                <div className="card p-4 bg-gradient-to-br from-primary-50 to-blue-50 border-primary-200">
                  <div className="flex items-start space-x-3">
                    <Bot className="w-5 h-5 text-primary-600 mt-0.5" />
                    <div>
                      <p className="text-sm text-primary-800 font-medium mb-2">Ready to analyze your data!</p>
                      <p className="text-xs text-primary-700 mb-3">
                        Try asking me questions about your dataset. Here are some suggestions:
                      </p>
                      <div className="space-y-2">
                        {suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => setInputValue(suggestion)}
                            className="block w-full text-left text-xs text-primary-700 hover:text-primary-800 bg-white bg-opacity-50 hover:bg-opacity-75 rounded px-2 py-1 transition-colors"
                          >
                            "{suggestion}"
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div key={message.id} className="flex items-start space-x-3">
                <div
                  className={`flex-shrink-0 p-1.5 rounded-full ${
                    message.type === "user" ? "bg-primary-100" : "bg-gray-100"
                  }`}
                >
                  <div className={message.type === "user" ? "text-primary-600" : "text-gray-600"}>
                    {getMessageIcon(message.type)}
                  </div>
                </div>
                <div className={`rounded-lg px-3 py-2 text-sm max-w-full ${getMessageStyle(message.type)}`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">{message.timestamp.toLocaleTimeString()}</p>
                </div>
              </div>
            ))}

            {isAnalyzing && (
              <div className="flex items-center space-x-3 text-sm text-gray-600">
                <div className="p-1.5 bg-blue-100 rounded-full">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                </div>
                <span>Analyzing your query...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex space-x-2">
          <input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={hasData ? "Ask about your data..." : "Upload data first"}
            disabled={!hasData || isAnalyzing || !connected}
            className="input flex-1"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || !hasData || isAnalyzing || !connected}
            className="btn btn-primary px-4 py-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {hasData && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">Ask questions, request charts, or generate reports from your data</p>
          </div>
        )}
      </div>
    </div>
  )
}
