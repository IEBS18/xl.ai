import { useState, useCallback, useRef, useEffect } from "react"

export const useMessages = () => {
  const [messages, setMessages] = useState([])
  const [expandedMessages, setExpandedMessages] = useState(new Set())
  const messagesEndRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Enhanced message addition with query category support and duplicate prevention
  const addMessage = useCallback((type, content, isUser = false, queryCategory = null, additionalData = {}) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      type,
      content,
      isUser,
      queryCategory, // Add query category tracking
      timestamp: new Date().toISOString(),
      isCompleted: type !== "status",
      ...additionalData
    }

    setMessages((prev) => {
      const lastMessage = prev[prev.length - 1]

      // Enhanced duplicate prevention with better object comparison
      if (lastMessage && !isUser && Date.now() - new Date(lastMessage.timestamp).getTime() < 1000) {
        // For simple string content
        if (typeof content === "string" && typeof lastMessage.content === "string") {
          if (lastMessage.type === type && lastMessage.content === content) {
            console.log("Preventing duplicate string message:", content.substring(0, 50))
            return prev
          }
        }

        // For complex objects (dataframe, image)
        if (typeof content === "object" && typeof lastMessage.content === "object" && content && lastMessage.content) {
          if (lastMessage.type === type) {
            // For dataframe objects, compare by name and shape
            if (
              type === "dataframe" &&
              content.name === lastMessage.content.name &&
              JSON.stringify(content.shape) === JSON.stringify(lastMessage.content.shape)
            ) {
              console.log("Preventing duplicate dataframe message:", content.name)
              return prev
            }

            // For image objects, compare by filename
            if (type === "image" && content.filename === lastMessage.content.filename) {
              console.log("Preventing duplicate image message:", content.filename)
              return prev
            }
          }
        }
      }

      // CRITICAL FIX: NEVER aggregate output messages - always create separate messages
      if (type === "output" && !isUser) {
        // Always create a new message for ANY query category to prevent mixing queries
        console.log(`Creating new output message with category: ${queryCategory}`)
        return [...prev, newMessage]
      }

      // Special handling for status messages - mark previous status as completed when new one arrives
      if (type === "status" && !isUser) {
        const updatedMessages = prev.map((msg, index) => {
          // Mark the last status message as completed
          if (index === prev.length - 1 && msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, newMessage]
      }

      // For success, error, or other completion types, mark previous status as completed
      if (
        (type === "success" ||
          type === "error" ||
          type === "code" ||
          type === "dataframe" ||
          type === "image" ||
          type === "report" ||
          type === "conversational" ||
          type === "textual_analytical" ||
          type === "completion") &&
        !isUser
      ) {
        const updatedMessages = prev.map((msg) => {
          if (msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, newMessage]
      }

      return [...prev, newMessage]
    })

    return newMessage.id
  }, [])

  // Enhanced stream data handler for Claude-like experience
  const handleStreamData = useCallback((data) => {
    const { type, data: content, timestamp, sessionId, ...additionalInfo } = data
    
    // Log received stream data for debugging
    console.log(`📨 Stream data received:`, { type, sessionId, timestamp })
    
    switch (type) {
      case "analysis_started":
        // Don't show "analysis started" for conversational queries
        if (!additionalInfo.query_category || additionalInfo.query_category === "fully_analytical") {
          addMessage("status", content || "Starting analysis...", false, null, {
            isCompleted: false,
            analysisType: additionalInfo.analysis_type
          })
        }
        break

      case "status":
        // Only show status for complex analysis, skip for conversational/textual
        const category = additionalInfo.query_category || detectQueryCategoryFromContent(content)
        if (category === "fully_analytical" || !category) {
          addMessage("status", content, false, category, {
            isCompleted: false
          })
        }
        break

      case "output":
        // This is the main response - always show as separate messages
        const queryCategory = additionalInfo.query_category || 
                             additionalInfo.result?.query_category ||
                             detectQueryCategoryFromContent(content)
        
        console.log(`Output message with category: ${queryCategory}`)
        
        // Split content into separate logical parts for better chat experience
        if (queryCategory === "conversational" && content) {
          const parts = splitResponseIntoParts(content)
          parts.forEach((part, index) => {
            setTimeout(() => {
              addMessage("output", part.trim(), false, queryCategory, {
                isCompleted: true,
                responseType: additionalInfo.response_type || "output",
                partIndex: index,
                totalParts: parts.length
              })
            }, index * 100) // Small delay between parts for natural feel
          })
        } else {
          addMessage("output", content, false, queryCategory, {
            isCompleted: true,
            responseType: additionalInfo.response_type || "output"
          })
        }
        break

      case "conversational":
      case "conversational_complete":
        addMessage("output", content, false, "conversational", {
          isCompleted: true,
          responseType: "conversational"
        })
        break

      case "textual_analytical":
      case "textual_analytical_complete":
        addMessage("output", content, false, "textual_analytical", {
          isCompleted: true,
          responseType: "textual_analytical"
        })
        break

      case "code":
        addMessage("code", content, false, "fully_analytical", {
          isCompleted: true,
          generatedCode: content
        })
        break

      case "dataframe":
        addMessage("dataframe", content, false, "fully_analytical", {
          isCompleted: true,
          dataInfo: {
            name: content.name,
            shape: content.shape,
            columns: content.columns,
            preview: content.preview,
            data: content.data
          }
        })
        break

      case "image":
        addMessage("image", content, false, "fully_analytical", {
          isCompleted: true,
          imageInfo: {
            filename: content.filename,
            data: content.data,
            path: content.path
          }
        })
        break

      case "report":
        addMessage("report", content, false, "fully_analytical", {
          isCompleted: true,
          reportData: content
        })
        break

      case "success":
        // Only show success for complex analysis
        if (content && !content.includes("Analysis completed")) {
          addMessage("success", content, false, null, {
            isCompleted: true
          })
        }
        break

      case "error":
        addMessage("error", content, false, null, {
          isCompleted: true,
          isError: true
        })
        break

      case "completion":
      case "analysis_complete":
        // Don't show completion messages for simple queries
        const completionCategory = additionalInfo.result?.query_category || 
                                  additionalInfo.result?.type ||
                                  "unknown"
        
        console.log('Analysis completed with category:', completionCategory)
        
        // Only show completion for complex analysis
        if (completionCategory === "fully_analytical") {
          addMessage("completion", content || "Analysis completed!", false, completionCategory, {
            isCompleted: true,
            completionInfo: additionalInfo.result
          })
        }
        break

      case "stop_requested":
      case "stopped":
        addMessage("error", "Analysis stopped by user", false, null, {
          isCompleted: true,
          wasStopped: true
        })
        break

      case "session_terminated":
        addMessage("error", "Session was terminated", false, null, {
          isCompleted: true,
          sessionTerminated: true
        })
        break

      case "warning":
        addMessage("warning", content, false, null, {
          isCompleted: true
        })
        break

      case "system":
        addMessage("system", content, false, null, {
          isCompleted: true
        })
        break

      default:
        console.warn(`Unknown stream data type: ${type}`)
        // Don't add unknown types to avoid clutter
        break
    }
  }, [addMessage])

  // Helper function to split long conversational responses into logical parts
  const splitResponseIntoParts = (content) => {
    if (!content || typeof content !== 'string') return [content]
    
    // Split by double newlines (paragraph breaks) or specific patterns
    const parts = content.split(/\n\n+|\. (?=[A-Z])|(?<=\?)\s+(?=[A-Z])|(?<=!)\s+(?=[A-Z])/)
      .filter(part => part.trim().length > 0)
      .map(part => part.trim())
    
    // If splitting created too many small parts, join them back
    if (parts.length > 4) {
      const merged = []
      let current = ""
      
      parts.forEach((part, index) => {
        if (current.length + part.length > 200 || index === parts.length - 1) {
          merged.push((current + " " + part).trim())
          current = ""
        } else {
          current += (current ? " " : "") + part
        }
      })
      
      return merged.filter(part => part.length > 0)
    }
    
    return parts.length > 1 ? parts : [content]
  }

  // Helper function to detect query category from content (fallback)
  const detectQueryCategoryFromContent = (content) => {
    if (!content || typeof content !== 'string') return null
    
    const lowerContent = content.toLowerCase()
    
    // Look for indicators of different response types
    if (lowerContent.includes('hello') || 
        lowerContent.includes('hi there') || 
        lowerContent.includes('i\'m here to help') ||
        lowerContent.includes('what can i do') ||
        lowerContent.includes('i\'m your ai') ||
        lowerContent.includes('ready to help')) {
      return "conversational"
    }
    
    if (lowerContent.includes('📈') || 
        lowerContent.includes('📊') || 
        lowerContent.includes('📉') ||
        lowerContent.includes('📋') ||
        lowerContent.includes('🔢') ||
        lowerContent.includes('the highest') ||
        lowerContent.includes('the average') ||
        lowerContent.includes('the maximum') ||
        lowerContent.includes('the minimum') ||
        lowerContent.includes('total of') ||
        lowerContent.includes('count of')) {
      return "textual_analytical"
    }
    
    return null
  }

  // Toggle message expansion
  const toggleMessageExpansion = useCallback((messageId) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }, [])

  // Update a specific message (for editing reports, etc.)
  const updateMessage = useCallback((messageId, updates) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ))
  }, [])

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([])
    setExpandedMessages(new Set())
  }, [])

  // Get messages by category
  const getMessagesByCategory = useCallback((category) => {
    return messages.filter(msg => msg.queryCategory === category)
  }, [messages])

  // Get latest user message
  const getLatestUserMessage = useCallback(() => {
    const userMessages = messages.filter(msg => msg.isUser)
    return userMessages.length > 0 ? userMessages[userMessages.length - 1] : null
  }, [messages])

  // Get messages for a specific user query (all responses after a user message)
  const getMessagesForQuery = useCallback((userMessageId) => {
    const messageIndex = messages.findIndex(msg => msg.id === userMessageId)
    if (messageIndex === -1) return []
    
    const nextUserMessageIndex = messages.findIndex((msg, idx) => 
      idx > messageIndex && msg.isUser
    )
    
    const endIndex = nextUserMessageIndex !== -1 ? nextUserMessageIndex : messages.length
    
    return messages.slice(messageIndex + 1, endIndex)
  }, [messages])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (!lastMessage.isUser) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
        }, 100)
      }
    }
  }, [messages])

  return {
    messages,
    addMessage,
    handleStreamData,
    expandedMessages,
    toggleMessageExpansion,
    updateMessage,
    clearMessages,
    messagesEndRef,
    getMessagesByCategory,
    getLatestUserMessage,
    getMessagesForQuery
  }
}