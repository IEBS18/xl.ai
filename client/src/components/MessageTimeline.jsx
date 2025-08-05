import React from "react"
import { Loader2, MessageSquare, Zap, Brain, Bot, Code, Database, Play } from "lucide-react"
import MessageItem from "./MessageItem"
import { useTheme } from "@/context/ThemeProvider"

const MessageTimeline = ({ 
  messages, 
  isAnalyzing, 
  expandedMessages, 
  toggleMessageExpansion, 
  messagesEndRef,
  onChatMessageClick,
  selectedChatMessage,
  currentQueryCategory // Track current analysis type
}) => {
  const { themeClasses } = useTheme()

  // Get the appropriate analyzing message based on query category
  const getAnalyzingMessage = (category) => {
    switch (category) {
      case "conversational":
        return {
          icon: <MessageSquare size={14} className="animate-pulse" />,
          text: "Thinking about your message...",
          color: "bg-green-500",
          description: "Processing conversational query"
        }
      case "textual_analytical":
        return {
          icon: <Zap size={14} className="animate-pulse" />,
          text: "Analyzing your data quickly...",
          color: "bg-blue-500",
          description: "Running quick data analysis"
        }
      case "fully_analytical":
        return {
          icon: <Brain size={14} className="animate-pulse" />,
          text: "Performing comprehensive analysis...",
          color: "bg-purple-500",
          description: "Running complex analysis with code execution"
        }
      default:
        return {
          icon: <Loader2 size={14} className="animate-spin" />,
          text: "Processing your request...",
          color: "bg-blue-500",
          description: "Determining best approach"
        }
    }
  }

  const analyzingInfo = getAnalyzingMessage(currentQueryCategory)

  // Enhanced message cleaning for better Claude-like experience
  const getCleanedMessages = (messages) => {
    const cleaned = []
    let i = 0
    
    while (i < messages.length) {
      const message = messages[i]
      
      if (message.isUser) {
        // Always include user messages
        cleaned.push(message)
        i++
      } else {
        // For system responses, find the conversation flow
        const userMessageIndex = cleaned.findLastIndex(msg => msg.isUser)
        if (userMessageIndex === -1) {
          i++
          continue
        }
        
        const userMessage = cleaned[userMessageIndex]
        const queryCategory = message.queryCategory || userMessage.queryCategory

        // Different handling based on query category
        if (queryCategory === "conversational") {
          // For conversational: only show final response, skip all status messages
          const finalResponse = findFinalConversationalResponse(messages, i)
          if (finalResponse) {
            cleaned.push({
              ...finalResponse,
              queryCategory: "conversational"
            })
            i = messages.indexOf(finalResponse) + 1
          } else {
            i++
          }
        } else if (queryCategory === "textual_analytical") {
          // For textual analytical: skip status/code, only show final output
          const finalOutput = findFinalTextualResponse(messages, i)
          if (finalOutput) {
            cleaned.push({
              ...finalOutput,
              queryCategory: "textual_analytical"
            })
            i = messages.indexOf(finalOutput) + 1
          } else {
            i++
          }
        } else {
          // For fully analytical: show relevant messages (enhanced filtering)
          if (shouldShowMessageInTimeline(message, queryCategory)) {
            cleaned.push(message)
          }
          i++
        }
      }
    }
    
    return cleaned
  }

  // Helper function to determine if message should show in timeline
  const shouldShowMessageInTimeline = (message, queryCategory) => {
    const { type } = message
    
    // Always show these types
    const alwaysShow = [
      'output', 'response', 'code', 'dataframe', 'image', 'file', 
      'report', 'error', 'success', 'function_call'
    ]
    
    if (alwaysShow.includes(type)) {
      return true
    }
    
    // Show status for complex analysis only
    if (type === 'status' && queryCategory === 'fully_analytical') {
      return true
    }
    
    // Show step_start for detailed tracking
    if (type === 'step_start') {
      return true
    }
    
    // Show warnings and system messages
    if (['warning', 'system'].includes(type)) {
      return true
    }
    
    // Hide completion messages (they're redundant)
    if (['completion', 'simple_completion'].includes(type)) {
      return false
    }
    
    // Show unknown types for debugging
    if (type === 'unknown') {
      return true
    }
    
    return false
  }

  // Helper function to find final conversational response
  const findFinalConversationalResponse = (messages, startIndex) => {
    for (let j = startIndex; j < messages.length; j++) {
      const msg = messages[j]
      if (msg.isUser) break // Stop at next user message
      
      if (msg.type === "output" || msg.type === "response" || msg.type === "conversational" || 
          (msg.type === "success" && msg.content && !msg.content.includes("Analysis completed"))) {
        return msg
      }
    }
    return null
  }

  // Helper function to find final textual analytical response  
  const findFinalTextualResponse = (messages, startIndex) => {
    for (let j = startIndex; j < messages.length; j++) {
      const msg = messages[j]
      if (msg.isUser) break // Stop at next user message
      
      if (msg.type === "output" || msg.type === "response" || msg.type === "textual_analytical") {
        return msg
      }
    }
    return null
  }

  const cleanedMessages = getCleanedMessages(messages)

  // Enhanced analyzing indicator based on current activity
  const renderAnalyzingIndicator = () => {
    if (!isAnalyzing) return null

    return (
      <div className="animate-in slide-in-from-left duration-300">
        <div className="flex justify-start mb-6">
          <div className="flex items-start gap-3 max-w-2xl">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center`}>
              {analyzingInfo.icon}
            </div>
            <div className={`px-4 py-3 rounded-2xl shadow-sm border bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 ${themeClasses.text}`}>
              <div className="flex items-center gap-2 mb-1">
                {analyzingInfo.icon}
                <span className="text-sm text-gray-600 dark:text-gray-400">{analyzingInfo.text}</span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-500">
                {analyzingInfo.description}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Helper to get activity indicators during analysis
  const getActivityIndicators = () => {
    if (!isAnalyzing || !currentQueryCategory) return null

    const indicators = []
    
    if (currentQueryCategory === "fully_analytical") {
      indicators.push(
        { icon: <Code size={12} />, label: "Code Generation", active: true },
        { icon: <Database size={12} />, label: "Data Processing", active: false },
        { icon: <Bot size={12} />, label: "Result Analysis", active: false }
      )
    } else if (currentQueryCategory === "textual_analytical") {
      indicators.push(
        { icon: <Zap size={12} />, label: "Quick Analysis", active: true },
        { icon: <Database size={12} />, label: "Data Lookup", active: false }
      )
    } else if (currentQueryCategory === "conversational") {
      indicators.push(
        { icon: <MessageSquare size={12} />, label: "Understanding", active: true },
        { icon: <Bot size={12} />, label: "Responding", active: false }
      )
    }

    return (
      <div className="flex justify-start mb-4">
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
          {indicators.map((indicator, index) => (
            <div key={index} className="flex items-center gap-1">
              <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                indicator.active ? 'bg-blue-500 text-white' : 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
              }`}>
                {indicator.icon}
              </div>
              <span className={`text-xs ${
                indicator.active ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
              }`}>
                {indicator.label}
              </span>
              {index < indicators.length - 1 && (
                <div className="w-2 h-px bg-gray-300 dark:bg-gray-600 mx-1" />
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-6">
      {/* Top padding for better visual spacing */}
      <div className="h-4"></div>
      
      {/* Render all cleaned messages */}
      {cleanedMessages.map((message, index) => (
        <MessageItem
          key={message.id}
          message={message}
          isExpanded={expandedMessages.has(message.id)}
          onToggleExpansion={toggleMessageExpansion}
          onChatMessageClick={onChatMessageClick}
          isSelected={selectedChatMessage === message.id}
        />
      ))}
      
      {/* Enhanced analyzing indicator */}
      {renderAnalyzingIndicator()}
      
      {/* Activity indicators for complex analysis */}
      {getActivityIndicators()}
      
      {/* Bottom spacer to ensure last message is visible above input */}
      <div className="h-8"></div>
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageTimeline