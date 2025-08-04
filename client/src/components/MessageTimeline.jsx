import React from "react"
import { Loader2, MessageSquare, Zap, Brain } from "lucide-react"
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
  currentQueryCategory // Add this prop to track current analysis type
}) => {
  const { themeClasses } = useTheme()

  // Get the appropriate analyzing message based on query category
  const getAnalyzingMessage = (category) => {
    switch (category) {
      case "conversational":
        return {
          icon: <MessageSquare size={14} className="animate-pulse" />,
          text: "Thinking about your message...",
          color: "bg-green-500"
        }
      case "textual_analytical":
        return {
          icon: <Zap size={14} className="animate-pulse" />,
          text: "Analyzing your data quickly...",
          color: "bg-blue-500"
        }
      case "fully_analytical":
        return {
          icon: <Brain size={14} className="animate-pulse" />,
          text: "Performing comprehensive analysis...",
          color: "bg-purple-500"
        }
      default:
        return {
          icon: <Loader2 size={14} className="animate-spin" />,
          text: "Processing your request...",
          color: "bg-blue-500"
        }
    }
  }

  const analyzingInfo = getAnalyzingMessage(currentQueryCategory)

  // Helper function to sort messages with output messages last for each user query
  const sortMessagesWithOutputLastPerQuery = (messages) => {
    const result = []
    let currentQueryMessages = []
    
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i]
      
      if (message.isUser) {
        // If we have accumulated messages from previous query, sort and add them
        if (currentQueryMessages.length > 0) {
          const sortedQueryMessages = sortSingleQueryMessages(currentQueryMessages)
          result.push(...sortedQueryMessages)
          currentQueryMessages = []
        }
        // Add the user message
        result.push(message)
      } else {
        // Accumulate system messages for current query
        currentQueryMessages.push(message)
      }
    }
    
    // Handle remaining messages after the last user query
    if (currentQueryMessages.length > 0) {
      const sortedQueryMessages = sortSingleQueryMessages(currentQueryMessages)
      result.push(...sortedQueryMessages)
    }
    
    return result
  }

  // Helper function to sort messages within a single query response
  const sortSingleQueryMessages = (messages) => {
    const outputMessages = []
    const nonOutputMessages = []
    
    messages.forEach(message => {
      if (message.type === "output") {
        outputMessages.push(message)
      } else {
        nonOutputMessages.push(message)
      }
    })
    
    // Return non-output messages first, then output messages
    return [...nonOutputMessages, ...outputMessages]
  }

  // Filter messages for cleaner Claude-like experience
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
          // For fully analytical: show all messages (existing behavior)
          cleaned.push(message)
          i++
        }
      }
    }
    
    return cleaned
  }

  // Helper function to find final conversational response
  const findFinalConversationalResponse = (messages, startIndex) => {
    for (let j = startIndex; j < messages.length; j++) {
      const msg = messages[j]
      if (msg.isUser) break // Stop at next user message
      
      if (msg.type === "output" || msg.type === "conversational" || 
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
      
      if (msg.type === "output" || msg.type === "textual_analytical") {
        return msg
      }
    }
    return null
  }

  // First clean the messages, then sort them with output messages last per query
  const cleanedMessages = getCleanedMessages(messages)
  const sortedMessages = sortMessagesWithOutputLastPerQuery(cleanedMessages)

  return (
    <div className="space-y-6 pb-6">
      {/* Add some top padding for better visual spacing */}
      <div className="h-4"></div>
      
      {sortedMessages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          isExpanded={expandedMessages.has(message.id)}
          onToggleExpansion={toggleMessageExpansion}
          onChatMessageClick={onChatMessageClick}
          isSelected={selectedChatMessage === message.id}
        />
      ))}
      
      {isAnalyzing && (
        <div className="animate-in slide-in-from-left duration-300">
          {/* Claude-like analyzing indicator - minimal and clean */}
          <div className="flex justify-start mb-6">
            <div className="flex items-start gap-3 max-w-2xl">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center`}>
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
              </div>
              <div className={`px-4 py-3 rounded-2xl shadow-sm border bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 ${themeClasses.text}`}>
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Bottom spacer to ensure last message is visible above input */}
      <div className="h-8"></div>
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageTimeline