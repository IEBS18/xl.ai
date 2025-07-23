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
  onUpdateMessage // Add this prop to handle message updates
}) => {
  const [activeSidePanel, setActiveSidePanel] = useState(null)
  const [selectedChatMessage, setSelectedChatMessage] = useState(null)
  const [chatPanelWidth, setChatPanelWidth] = useState(50) // Percentage width
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef(null)
  const { themeClasses } = useTheme()

  // Handle updating a specific message/item content
  const handleUpdateItem = useCallback((itemId, newContent) => {
    if (onUpdateMessage) {
      onUpdateMessage(itemId, { content: newContent })
    }
  }, [onUpdateMessage])

  // Get side panel items (code, image, dataframe, report)
  const getSidePanelItems = () => {
    return messages.filter(msg => ['code', 'image', 'dataframe', 'report'].includes(msg.type))
  }

  // Get side panel items for a specific chat message/query
  const getSidePanelItemsForMessage = (messageId) => {
    if (!messageId) return []
    
    // Find the user message and get items that came after it until the next user message
    const messageIndex = messages.findIndex(msg => msg.id === messageId)
    if (messageIndex === -1) return []
    
    const nextUserMessageIndex = messages.findIndex((msg, idx) => 
      idx > messageIndex && msg.isUser
    )
    
    const endIndex = nextUserMessageIndex !== -1 ? nextUserMessageIndex : messages.length
    
    return messages
      .slice(messageIndex + 1, endIndex)
      .filter(msg => ['code', 'image', 'dataframe', 'report'].includes(msg.type))
  }

  const sidePanelItems = selectedChatMessage 
    ? getSidePanelItemsForMessage(selectedChatMessage)
    : getSidePanelItems()

  // Auto-select the latest user message when no message is selected
  React.useEffect(() => {
    if (!selectedChatMessage && messages.length > 0) {
      // Find the latest user message
      const latestUserMessage = messages
        .filter(msg => msg.isUser)
        .slice(-1)[0]
      
      if (latestUserMessage) {
        setSelectedChatMessage(latestUserMessage.id)
      }
    }
  }, [messages, selectedChatMessage])

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
    setSelectedChatMessage(messageId)
    setActiveSidePanel(null) // Reset active side panel when switching messages
  }

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

    // Constrain the width between 25% and 75%
    const constrainedWidth = Math.min(Math.max(newChatWidth, 35), 65)
    setChatPanelWidth(constrainedWidth)
  }, [isDragging])
  console.log(chatPanelWidth);
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
              messages={messages.filter(msg => !['code', 'image', 'dataframe', 'report'].includes(msg.type))}
              isAnalyzing={isAnalyzing}
              expandedMessages={expandedMessages}
              toggleMessageExpansion={toggleMessageExpansion}
              messagesEndRef={messagesEndRef}
              onChatMessageClick={handleChatMessageClick}
              selectedChatMessage={selectedChatMessage}
            />
          </div>
        </div>

        {/* Bottom UI Elements - Fixed at bottom */}
        <div className={`flex-shrink-0 ${themeClasses.border} border-t transition-colors`}>
          {/* Sample Questions */}
          {fileUploaded && messages.filter((m) => m.isUser).length === 0 && (
            <SampleQuestions onSelectQuestion={(question) => onSendMessage(question)} />
          )}

          {/* Upload Progress */}
          {uploadProgress > 0 && <UploadProgress progress={uploadProgress} />}

          {/* File Info */}
          {fileUploaded && fileInfo && (
            <FileInfo
              fileInfo={fileInfo}
              onDebug={debugSession}
              onSync={manualSessionSync}
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

      {/* Side Panel */}
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
            onClearSelection={() => setSelectedChatMessage(null)}
            onUpdateItem={handleUpdateItem}
          />
        </div>
      )}
    </div>
  )
}

export default ChatInterface