import { useState, useCallback, useRef, useEffect } from "react"

export const useMessages = () => {
  const [messages, setMessages] = useState([])
  const [expandedMessages, setExpandedMessages] = useState(new Set())
  const [currentQueryCategory, setCurrentQueryCategory] = useState(null)
  const [isFileProcessing, setIsFileProcessing] = useState(false) // New state for file processing
  const messagesEndRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Set file processing state when file upload starts
  const setFileProcessingState = useCallback((isProcessing) => {
    setIsFileProcessing(isProcessing)
  }, [])

  // Enhanced message addition with query category support and duplicate prevention
  const addMessage = useCallback((type, content, isUser = false, queryCategory = null, additionalData = {}) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      type,
      content,
      isUser,
      queryCategory,
      timestamp: new Date().toISOString(),
      isCompleted: type !== "status",
      ...additionalData
    }

    setMessages((prev) => {
      const lastMessage = prev[prev.length - 1]

      // Enhanced duplicate prevention
      if (lastMessage && !isUser && Date.now() - new Date(lastMessage.timestamp).getTime() < 1000) {
        // For simple string content
        if (typeof content === "string" && typeof lastMessage.content === "string") {
          if (lastMessage.type === type && lastMessage.content === content) {
            console.log("Preventing duplicate string message:", content.substring(0, 50))
            return prev
          }
        }

        // For complex objects
        if (typeof content === "object" && typeof lastMessage.content === "object" && content && lastMessage.content) {
          if (lastMessage.type === type) {
            // For dataframe objects
            if (
              type === "dataframe" &&
              content.name === lastMessage.content.name &&
              JSON.stringify(content.shape) === JSON.stringify(lastMessage.content.shape)
            ) {
              console.log("Preventing duplicate dataframe message:", content.name)
              return prev
            }

            // For image objects
            if (type === "image" && content.filename === lastMessage.content.filename) {
              console.log("Preventing duplicate image message:", content.filename)
              return prev
            }

            // For file objects
            if (type === "file" && content.filename === lastMessage.content.filename) {
              console.log("Preventing duplicate file message:", content.filename)
              return prev
            }
          }
        }
      }

      // Always create new messages for output to prevent mixing queries
      if (type === "output" && !isUser) {
        console.log(`Creating new output message with category: ${queryCategory}`)
        return [...prev, newMessage]
      }

      if (type === "response" && !isUser) {
        console.log(`Creating new output message with category: ${queryCategory}`)
        return [...prev, newMessage]
      }

      // Special handling for status messages
      if (type === "status" && !isUser) {
        const updatedMessages = prev.map((msg, index) => {
          if (index === prev.length - 1 && msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, newMessage]
      }

      // For completion types, mark previous status as completed
      if (
        (type === "success" ||
          type === "error" ||
          type === "code" ||
          type === "dataframe" ||
          type === "image" ||
          type === "file" ||
          type === "report" ||
          type === "conversational" ||
          type === "textual_analytical" ||
          type === "response" ||
          type === "function_call" ||
          type === "step_start" ||
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

  // Enhanced stream data handler for ALL backend stream types
  const handleStreamData = useCallback((data) => {
    const { type, data: content, timestamp, sessionId, ...additionalInfo } = data
    
    console.log(`📨 Stream data received:`, { type, sessionId, timestamp, additionalInfo })
    
    switch (type) {
      case "analysis_started":
        // Track current query category for UI
        const startCategory = additionalInfo.query_category || detectQueryCategoryFromContent(content)
        setCurrentQueryCategory(startCategory)
        
        if (!startCategory || startCategory === "fully_analytical") {
          addMessage("status", content || "Starting analysis...", false, startCategory, {
            isCompleted: false,
            analysisType: additionalInfo.analysis_type
          })
        }
        break

      case "assistant_upload_complete":
        // Handle file upload completion
        console.log("📁 File processing completed:", { 
          fileId: additionalInfo.file_id,
          uploadTime: additionalInfo.upload_time 
        })
        
        // Extra debugging for healthcare files
        if (content && content.toLowerCase().includes('healthcare')) {
          console.log("🏥 HEALTHCARE FILE - Frontend received assistant_upload_complete:", {
            content,
            additionalInfo,
            timestamp: new Date().toISOString()
          })
        }
        
        // Mark file processing as complete
        setIsFileProcessing(false)
        
        // Add a success message for file upload completion
        addMessage("success", content || "File processed successfully!", false, null, {
          isCompleted: true,
          fileUploadComplete: true,
          fileId: additionalInfo.file_id,
          uploadTime: additionalInfo.upload_time
        })
        break

      case "status":
        const statusCategory = additionalInfo.query_category || detectQueryCategoryFromContent(content)
        setCurrentQueryCategory(statusCategory)
        
        // Only show status for complex analysis
        if (statusCategory === "fully_analytical" || !statusCategory) {
          addMessage("status", content, false, statusCategory, {
            isCompleted: false
          })
        }
        break

      case "step_start":
        // New: Handle step start events
        const stepCategory = additionalInfo.query_category || "fully_analytical"
        addMessage("step_start", `Starting ${content.type || 'step'}: ${content.step_id || ''}`, false, stepCategory, {
          isCompleted: false,
          stepInfo: content
        })
        break

      case "code":
        // Handle code execution
        addMessage("code", content, false, "fully_analytical", {
          isCompleted: true,
          generatedCode: content
        })
        break

      case "output":
        // Main response - always show as separate messages
        const queryCategory = additionalInfo.query_category || 
                             additionalInfo.result?.query_category ||
                             detectQueryCategoryFromContent(content)
        
        console.log(`Output message with category: ${queryCategory}`)
        
        if (queryCategory === "conversational" && content) {
          const parts = splitResponseIntoParts(content)
          parts.forEach((part, index) => {
            setTimeout(() => {
              addMessage("output", part.trim(), false, queryCategory, {
                isCompleted: true,
                responseType: "output",
                partIndex: index,
                totalParts: parts.length
              })
            }, index * 100)
          })
        } else {
          addMessage("output", content, false, queryCategory, {
            isCompleted: true,
            responseType: "output"
          })
        }
        break

      case "response":
        // New: Direct assistant response
        const responseCategory = additionalInfo.query_category || detectQueryCategoryFromContent(content)
        setCurrentQueryCategory(responseCategory)
        
        addMessage("response", content, false, responseCategory, {
          isCompleted: true,
          responseType: "assistant_response"
        })
        break

      case "conversational":
      case "conversational_response":
      case "conversational_complete":
        setCurrentQueryCategory("conversational")
        addMessage("output", content, false, "conversational", {
          isCompleted: true,
          responseType: "conversational"
        })
        break

      case "textual_analytical":
      case "textual_analytical_complete":
        setCurrentQueryCategory("textual_analytical")
        addMessage("output", content, false, "textual_analytical", {
          isCompleted: true,
          responseType: "textual_analytical"
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
            path: content.path,
            file_id: content.file_id,
            type: content.type
          }
        })
        break

      case "file":
        // New: Handle any file type (.txt, .pdf, .csv, etc.)
        addMessage("file", content, false, "fully_analytical", {
          isCompleted: true,
          fileInfo: {
            filename: content.filename,
            data: content.data,
            path: content.path,
            file_id: content.file_id,
            type: content.type,
            size: content.size,
            mime_type: content.mime_type
          }
        })
        break

      case "function_call":
        // New: Handle function calls
        addMessage("function_call", `Function: ${content.name}`, false, "fully_analytical", {
          isCompleted: true,
          functionInfo: {
            name: content.name,
            arguments: content.arguments
          }
        })
        break

      case "report":
        console.log(content);
        addMessage("report", content.html, false, "fully_analytical", {
          isCompleted: true,
          reportData: content.html
        })
        break

      case "success":
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
      case "simple_completion":
      case "analysis_complete":
        const completionCategory = additionalInfo.result?.query_category || 
                                  additionalInfo.result?.type ||
                                  "unknown"
        
        console.log('Analysis completed with category:', completionCategory)
        
        // Show completion for complex analysis or simple responses
        if (type === "simple_completion") {
          // Simple completion - no analysis was performed
          console.log("Simple query completed - no analysis needed")
        } else if (completionCategory === "fully_analytical") {
          addMessage("completion", content || "Analysis completed!", false, completionCategory, {
            isCompleted: true,
            completionInfo: additionalInfo.result
          })
        }
        
        // Clear current query category
        setCurrentQueryCategory(null)
        break

      case "stop_requested":
      case "stopped":
        addMessage("error", "Analysis stopped by user", false, null, {
          isCompleted: true,
          wasStopped: true
        })
        setCurrentQueryCategory(null)
        break

      case "session_terminated":
        addMessage("error", "Session was terminated", false, null, {
          isCompleted: true,
          sessionTerminated: true
        })
        setCurrentQueryCategory(null)
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

      case "assistant_upload_progress":
        console.log("⏳ Upload progress:", { content, additionalInfo })
        // Could show progress indicator here
        break

      case "assistant_upload_timeout":
        console.warn("⏰ Upload timeout:", { content, additionalInfo })
        // Mark file processing as complete even on timeout
        setIsFileProcessing(false)
        addMessage("warning", content || "File upload timed out - file may be too large", false, null, {
          isCompleted: true,
          fileUploadTimeout: true
        })
        break

      case "healthcare_test":
        console.log("🏥 HEALTHCARE TEST EVENT received on frontend:", {
          content,
          additionalInfo,
          timestamp: new Date().toISOString()
        })
        break

      default:
        console.warn(`Unknown stream data type: ${type}`, { content, additionalInfo })
        // Add unknown types for debugging but mark them clearly
        addMessage("unknown", `Unknown type: ${type} - ${content}`, false, null, {
          isCompleted: true,
          unknownType: type,
          originalData: data
        })
        break
    }
  }, [addMessage])

  // Helper function to split long conversational responses into logical parts
  const splitResponseIntoParts = (content) => {
    if (!content || typeof content !== 'string') return [content]
    
    const parts = content.split(/\n\n+|\. (?=[A-Z])|(?<=\?)\s+(?=[A-Z])|(?<=!)\s+(?=[A-Z])/)
      .filter(part => part.trim().length > 0)
      .map(part => part.trim())
    
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

  // Helper function to detect query category from content
  const detectQueryCategoryFromContent = (content) => {
    if (!content || typeof content !== 'string') return null
    
    const lowerContent = content.toLowerCase()
    
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
        lowerContent.includes('the highest') ||
        lowerContent.includes('the average') ||
        lowerContent.includes('total of')) {
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

  // Update a specific message
  const updateMessage = useCallback((messageId, updates) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ))
  }, [])

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([])
    setExpandedMessages(new Set())
    setCurrentQueryCategory(null)
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

  // Get messages for a specific user query
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
    currentQueryCategory, // Export current query category for UI
    isFileProcessing, // Export file processing state
    setFileProcessingState, // Export function to control file processing state
    getMessagesByCategory,
    getLatestUserMessage,
    getMessagesForQuery
  }
}