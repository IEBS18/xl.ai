import React, { useState, useCallback, useRef, useEffect } from "react"
import MessageTimeline from "./MessageTimeline"
import InputArea from "./InputArea"
import FileInfo from "./FileInfo"
import SampleQuestions from "./SampleQuestions"
import UploadProgress from "./UploadProgress"
import SidePanel from "./SidePanel"
import { useTheme } from "@/context/ThemeProvider"

const ChatInterface = ({
  messages,
  isAnalyzing,
  isConnected,
  fileUploaded,
  fileInfo,
  onSendMessage,
  messagesEndRef,
  expandedMessages,
  toggleMessageExpansion,
  uploadProgress,
  fileInputRef,
  handleFileUpload,
  triggerFileUpload,
  debugSession,
  manualSessionSync,
  onUpdateMessage,
  sessionId,
  currentQueryCategory // Add this prop to track current analysis type
}) => {
  const [activeSidePanel, setActiveSidePanel] = useState(null)
  const [selectedChatMessage, setSelectedChatMessage] = useState(null)
  const [chatPanelWidth, setChatPanelWidth] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const [previewMessage, setPreviewMessage] = useState(null)
  const containerRef = useRef(null)
  const { themeClasses } = useTheme()

  // Enhanced message processing for different query types
  const processMessagesForDisplay = (messages) => {
    return messages.map(message => {
      // Add query category context to messages
      if (message.queryCategory) {
        return { ...message, queryCategory: message.queryCategory }
      }
      
      // Infer category from message type for backwards compatibility
      if (message.type === "conversational") {
        return { ...message, queryCategory: "conversational" }
      }
      if (message.type === "textual_analytical") {
        return { ...message, queryCategory: "textual_analytical" }
      }
      
      return message
    })
  }

  const processedMessages = processMessagesForDisplay(messages)

  // Determine which messages should show in side panel based on query category
  const getSidePanelItems = () => {
    const sidePanelTypes = ['code', 'image', 'dataframe', 'report']
    
    // Only show side panel items for fully analytical queries
    const analyticalMessages = processedMessages.filter(msg => {
      // Check if message is from a fully analytical query
      const isAnalyticalQuery = msg.queryCategory === "fully_analytical" || 
                               (!msg.queryCategory && sidePanelTypes.includes(msg.type))
      
      return isAnalyticalQuery && sidePanelTypes.includes(msg.type)
    })
    
    // Add preview message if it exists
    if (previewMessage) {
      return [previewMessage, ...analyticalMessages]
    }
    
    return analyticalMessages
  }

  // Get side panel items for a specific chat message/query
  const getSidePanelItemsForMessage = (messageId) => {
    if (!messageId) return []
    
    // Find the user message and get items that came after it until the next user message
    const messageIndex = processedMessages.findIndex(msg => msg.id === messageId)
    if (messageIndex === -1) return []
    
    const userMessage = processedMessages[messageIndex]
    
    // Only show side panel for fully analytical queries
    if (userMessage.queryCategory !== "fully_analytical" && 
        !processedMessages.slice(messageIndex + 1).some(msg => 
          ['code', 'image', 'dataframe', 'report'].includes(msg.type)
        )) {
      return []
    }
    
    const nextUserMessageIndex = processedMessages.findIndex((msg, idx) => 
      idx > messageIndex && msg.isUser
    )
    
    const endIndex = nextUserMessageIndex !== -1 ? nextUserMessageIndex : processedMessages.length
    
    const messageItems = processedMessages
      .slice(messageIndex + 1, endIndex)
      .filter(msg => ['code', 'image', 'dataframe', 'report'].includes(msg.type))
    
    // Add preview message if it exists and no specific chat message is selected
    if (previewMessage && !selectedChatMessage) {
      return [previewMessage, ...messageItems]
    }
    
    return messageItems
  }

  const sidePanelItems = selectedChatMessage 
    ? getSidePanelItemsForMessage(selectedChatMessage)
    : getSidePanelItems()

  // Handle updating a specific message/item content
  const handleUpdateItem = useCallback((itemId, newContent) => {
    if (onUpdateMessage) {
      onUpdateMessage(itemId, { content: newContent })
    }
  }, [onUpdateMessage])

  // Handle showing file preview
  const handleShowPreview = useCallback((previewData) => {
    setPreviewMessage(previewData)
    setSelectedChatMessage(null)
    setActiveSidePanel(previewData.id)
  }, [])

  // Auto-select the latest analytical user message when no message is selected
  React.useEffect(() => {
    if (!selectedChatMessage && processedMessages.length > 0 && !previewMessage) {
      // Find the latest user message that has analytical content
      const analyticalUserMessages = processedMessages
        .filter(msg => msg.isUser)
        .filter(msgId => getSidePanelItemsForMessage(msgId.id).length > 0)
      
      if (analyticalUserMessages.length > 0) {
        const latestAnalyticalMessage = analyticalUserMessages.slice(-1)[0]
        setSelectedChatMessage(latestAnalyticalMessage.id)
      }
    }
  }, [processedMessages, selectedChatMessage, previewMessage])

  // Auto-select first item when side panel items are available
  React.useEffect(() => {
    if (sidePanelItems.length > 0 && !activeSidePanel) {
      setActiveSidePanel(sidePanelItems[0].id)
    } else if (sidePanelItems.length === 0) {
      setActiveSidePanel(null)
    }
  }, [sidePanelItems, activeSidePanel])

  // Handle chat message selection
  const handleChatMessageClick = (messageId) => {
    const itemsForMessage = getSidePanelItemsForMessage(messageId)
    
    // Only set selection if message has analytical content
    if (itemsForMessage.length > 0) {
      setSelectedChatMessage(messageId)
      setActiveSidePanel(null)
      setPreviewMessage(null)
    }
  }

  // Handle clear selection
  const handleClearSelection = () => {
    setSelectedChatMessage(null)
    setPreviewMessage(null)
  }

  // Enhanced sample questions based on query categories
  const enhancedSampleQuestions = [
    // Conversational
    { 
      question: "Hi, what can you help me with?",
      category: "conversational",
      description: "Start a conversation"
    },
    { 
      question: "What capabilities do you have?",
      category: "conversational", 
      description: "Learn about features"
    },
    
    // Textual Analytical
    { 
      question: "What is the average sales value?",
      category: "textual_analytical",
      description: "Quick data answer"
    },
    { 
      question: "How many rows are in my dataset?",
      category: "textual_analytical",
      description: "Simple data query"
    },
    { 
      question: "What's the maximum revenue?",
      category: "textual_analytical",
      description: "Find maximum value"
    },
    
    // Fully Analytical  
    { 
      question: "Generate a comprehensive sales analysis",
      category: "fully_analytical",
      description: "Detailed analysis with charts"
    },
    { 
      question: "Create a 12-month forecast model",
      category: "fully_analytical",
      description: "Predictive modeling"
    },
    { 
      question: "Show me trends and correlations in the data",
      category: "fully_analytical",
      description: "Pattern analysis"
    }
  ]

  // Handle mouse down on resize handle
  const handleMouseDown = useCallback((e) => {
    setIsDragging(true)
    e.preventDefault()
  }, [])

  // Handle mouse move during drag
  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !containerRef.current) return

    const containerRect = containerRef.current.getBoundingClientRect()
    const newChatWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100

    const constrainedWidth = Math.min(Math.max(newChatWidth, 35), 65)
    setChatPanelWidth(constrainedWidth)
  }, [isDragging])

  // Handle mouse up to stop dragging
  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Add event listeners for mouse move and up
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  // Filter timeline messages (exclude side panel items for conversational/textual queries)
  const getTimelineMessages = () => {
    return processedMessages.filter(msg => {
      // Always show user messages
      if (msg.isUser) return true
      
      // For conversational and textual analytical, exclude code/dataframe/image/report
      if (msg.queryCategory === "conversational" || msg.queryCategory === "textual_analytical") {
        return !['code', 'dataframe', 'image', 'report'].includes(msg.type)
      }
      
      // For fully analytical, show all messages in timeline but they'll also appear in side panel
      return true
    })
  }

  return (
    <div ref={containerRef} className={`flex h-full ${themeClasses.bg} transition-colors`}>
      {/* Main Chat Area */}
      <div 
        className="flex flex-col transition-all duration-300"
        style={{ 
          width: sidePanelItems.length > 0 ? `${chatPanelWidth}%` : '100%' 
        }}
      >
        {/* Messages Area - Scrollable with explicit height */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {/* Header padding to prevent content being covered */}
          <div className="h-16"></div>
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <MessageTimeline
              messages={getTimelineMessages()}
              isAnalyzing={isAnalyzing}
              expandedMessages={expandedMessages}
              toggleMessageExpansion={toggleMessageExpansion}
              messagesEndRef={messagesEndRef}
              onChatMessageClick={handleChatMessageClick}
              selectedChatMessage={selectedChatMessage}
              currentQueryCategory={currentQueryCategory}
            />
          </div>
        </div>

        {/* Bottom UI Elements - Fixed at bottom */}
        <div className={`flex-shrink-0 ${themeClasses.border} border-t transition-colors`}>
          {/* Enhanced Sample Questions */}
          {fileUploaded && messages.filter((m) => m.isUser).length === 0 && (
            <EnhancedSampleQuestions 
              questions={enhancedSampleQuestions}
              onSelectQuestion={(question) => onSendMessage(question)} 
            />
          )}

          {/* Upload Progress */}
          {uploadProgress > 0 && <UploadProgress progress={uploadProgress} />}

          {/* File Info */}
          {fileUploaded && fileInfo && (
            <FileInfo
              fileInfo={fileInfo}
              onDebug={debugSession}
              onSync={manualSessionSync}
              onShowPreview={handleShowPreview}
              sessionId={sessionId}
            />
          )}

          {/* Input Area - Always visible at bottom */}
          {fileUploaded && (
            <InputArea
              isConnected={isConnected}
              isAnalyzing={isAnalyzing}
              onSendMessage={onSendMessage}
              onFileUpload={triggerFileUpload}
            />
          )}
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      {/* Resize Handle */}
      {sidePanelItems.length > 0 && (
        <div
          className={`w-1 ${themeClasses.border} border-l hover:bg-blue-500/20 cursor-col-resize flex-shrink-0 relative group transition-colors duration-200`}
          onMouseDown={handleMouseDown}
        >
          {/* Visual indicator for the resize handle */}
          <div className="absolute inset-y-0 left-1/2 w-0.5 bg-transparent group-hover:bg-blue-500/40 transition-colors duration-200 transform -translate-x-1/2"></div>
          
          {/* Expanded hover area for easier grabbing */}
          <div className="absolute inset-y-0 -left-2 -right-2 cursor-col-resize"></div>
        </div>
      )}

      {/* Side Panel - Only for fully analytical queries */}
      {sidePanelItems.length > 0 && (
        <div 
          className={`${themeClasses.border} transition-all duration-300 ${themeClasses.bg} flex-shrink-0`}
          style={{ 
            width: `${100 - chatPanelWidth}%` 
          }}
        >
          <SidePanel
            items={sidePanelItems}
            activeItem={activeSidePanel}
            onItemChange={setActiveSidePanel}
            selectedMessage={selectedChatMessage}
            onClearSelection={handleClearSelection}
            onUpdateItem={handleUpdateItem}
          />
        </div>
      )}
    </div>
  )
}

// Enhanced Sample Questions Component with Categories
const EnhancedSampleQuestions = ({ questions, onSelectQuestion }) => {
  const { themeClasses } = useTheme()
  const [selectedCategory, setSelectedCategory] = useState("all")

  const categories = [
    { id: "all", label: "All", icon: "🎯" },
    { id: "conversational", label: "Chat", icon: "💬" },
    { id: "textual_analytical", label: "Quick Q&A", icon: "⚡" },
    { id: "fully_analytical", label: "Deep Analysis", icon: "🧠" }
  ]

  const filteredQuestions = selectedCategory === "all" 
    ? questions 
    : questions.filter(q => q.category === selectedCategory)

  return (
    <div className={`p-4 ${themeClasses.surface} ${themeClasses.border} border-b`}>
      <div className="max-w-4xl mx-auto">
        <div className="mb-4">
          <h3 className={`text-sm font-medium ${themeClasses.text} mb-2`}>
            Try these example queries:
          </h3>
          
          {/* Category Filters */}
          <div className="flex gap-2 mb-3">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedCategory === category.id
                    ? `${themeClasses.button} ${themeClasses.text}`
                    : `${themeClasses.surface} ${themeClasses.textSecondary} hover:${themeClasses.text}`
                }`}
              >
                <span className="mr-1">{category.icon}</span>
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Questions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {filteredQuestions.map((item, index) => (
            <button
              key={index}
              onClick={() => onSelectQuestion(item.question)}
              className={`text-left p-3 rounded-lg border ${themeClasses.border} ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group`}
            >
              <div className="flex items-start gap-2">
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  item.category === "conversational" 
                    ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                    : item.category === "textual_analytical"
                    ? "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                    : "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400"
                }`}>
                  {item.category === "conversational" ? "💬" : 
                   item.category === "textual_analytical" ? "⚡" : "🧠"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm ${themeClasses.text} font-medium mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors`}>
                    {item.question}
                  </div>
                  <div className={`text-xs ${themeClasses.textSecondary}`}>
                    {item.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ChatInterface