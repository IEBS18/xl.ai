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

  const addMessage = useCallback((type, content, isUser = false) => {
    const message = {
      id: Date.now() + Math.random(),
      type,
      content,
      isUser,
      timestamp: new Date().toISOString(),
      isCompleted: type !== "status",
    }

    setMessages((prev) => {
      const lastMessage = prev[prev.length - 1]

      // Enhanced duplicate prevention with better object comparison
      if (lastMessage && !isUser && Date.now() - new Date(lastMessage.timestamp).getTime() < 3000) {
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

      // FIXED: Better handling for output messages - prevent duplication
      if (type === "output" && !isUser) {
        // Find the last output message in the array
        const lastOutputIndex = prev.findLastIndex((msg) => msg.type === "output")

        if (lastOutputIndex !== -1) {
          const existingContent = prev[lastOutputIndex].content
          
          // Check if the new content is already included in existing content
          if (existingContent.includes(content)) {
            console.log("Preventing duplicate output content")
            return prev
          }
          
          // Only append if it's truly new content
          const updatedMessages = [...prev]
          updatedMessages[lastOutputIndex] = {
            ...updatedMessages[lastOutputIndex],
            content: existingContent + "\n" + content,
            timestamp: new Date().toISOString(),
          }
          return updatedMessages
        }
        // If no previous output message found, add as new message (will fall through to end)
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
        return [...updatedMessages, message]
      }

      // For success, error, or other completion types, mark previous status as completed
      if (
        (type === "success" ||
          type === "error" ||
          type === "code" ||
          type === "dataframe" ||
          type === "image" ||
          type === "report") &&
        !isUser
      ) {
        const updatedMessages = prev.map((msg) => {
          if (msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, message]
      }

      return [...prev, message]
    })
  }, [])

  const updateMessage = useCallback((messageId, updates) => {
    setMessages((prev) => 
      prev.map((msg) => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    )
  }, [])

  const removeMessage = useCallback((messageId) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== messageId))
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setExpandedMessages(new Set())
  }, [])

  const toggleMessageExpansion = useCallback((messageId) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }, [])

  const handleStreamData = useCallback((data) => {
    const { type, data: content, timestamp, sessionId } = data
    
    // Log received stream data for debugging
    console.log(`📨 Stream data received:`, { type, sessionId, timestamp })
    
    switch (type) {
      case "status":
        addMessage("status", content)
        break
      case "code":
        addMessage("code", content)
        break
      case "dataframe":
        addMessage("dataframe", content)
        break
      case "image":
        addMessage("image", content)
        break
      case "report":
        addMessage("report", content)
        break
      case "success":
        addMessage("success", content)
        break
      case "error":
        addMessage("error", content)
        break
      case "output":
        addMessage("output", content)
        break
      case "completion":
        addMessage("success", content)
        break
      case "warning":
        addMessage("warning", content)
        break
      case "system":
        addMessage("system", content)
        break
      default:
        console.warn(`Unknown stream data type: ${type}`)
        addMessage("system", content)
        break
    }
  }, [addMessage])

  const getMessagesByType = useCallback((type) => {
    return messages.filter((msg) => msg.type === type)
  }, [messages])

  const getLastMessage = useCallback((type = null) => {
    if (type) {
      const filtered = messages.filter((msg) => msg.type === type)
      return filtered[filtered.length - 1] || null
    }
    return messages[messages.length - 1] || null
  }, [messages])

  const getMessageCount = useCallback((type = null) => {
    if (type) {
      return messages.filter((msg) => msg.type === type).length
    }
    return messages.length
  }, [messages])

  const getUserMessages = useCallback(() => {
    return messages.filter((msg) => msg.isUser)
  }, [messages])

  const getSystemMessages = useCallback(() => {
    return messages.filter((msg) => !msg.isUser)
  }, [messages])

  const hasMessagesOfType = useCallback((type) => {
    return messages.some((msg) => msg.type === type)
  }, [messages])

  const getMessagesInTimeRange = useCallback((startTime, endTime) => {
    return messages.filter((msg) => {
      const msgTime = new Date(msg.timestamp)
      return msgTime >= startTime && msgTime <= endTime
    })
  }, [messages])

  const exportMessages = useCallback((format = 'json') => {
    if (format === 'json') {
      return JSON.stringify(messages, null, 2)
    }
    
    if (format === 'text') {
      return messages.map((msg) => {
        const timestamp = new Date(msg.timestamp).toLocaleString()
        const prefix = msg.isUser ? 'USER' : msg.type.toUpperCase()
        const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
        return `[${timestamp}] ${prefix}: ${content}`
      }).join('\n')
    }
    
    if (format === 'csv') {
      const headers = ['timestamp', 'type', 'isUser', 'content']
      const rows = messages.map((msg) => [
        msg.timestamp,
        msg.type,
        msg.isUser,
        typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
      ])
      
      return [headers, ...rows].map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
      ).join('\n')
    }
    
    return messages
  }, [messages])

  return {
    messages,
    expandedMessages,
    messagesEndRef,
    addMessage,
    updateMessage,
    removeMessage,
    clearMessages,
    toggleMessageExpansion,
    handleStreamData,
    getMessagesByType,
    getLastMessage,
    getMessageCount,
    getUserMessages,
    getSystemMessages,
    hasMessagesOfType,
    getMessagesInTimeRange,
    exportMessages
  }
}