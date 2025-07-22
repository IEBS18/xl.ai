import React, { useState } from "react"
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
  manualSessionSync
}) => {
  const [activeSidePanel, setActiveSidePanel] = useState(null)
  const [selectedChatMessage, setSelectedChatMessage] = useState(null)
  const { themeClasses } = useTheme()

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

  // Auto-select latest user message when new messages are added
  React.useEffect(() => {
    const userMessages = messages.filter(msg => msg.isUser)
    if (userMessages.length > 0) {
      const latestUserMessage = userMessages[userMessages.length - 1]
      setSelectedChatMessage(latestUserMessage.id)
    }
  }, [messages])

  const sidePanelItems = selectedChatMessage 
    ? getSidePanelItemsForMessage(selectedChatMessage)
    : getSidePanelItems()

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

  return (
    <div className={`flex h-full ${themeClasses.bg} transition-colors`}>
      {/* Main Chat Area */}
      <div className={`flex flex-col transition-all duration-300 ${
        sidePanelItems.length > 0 ? 'w-1/2' : 'flex-1'
      }`}>
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

      {/* Side Panel */}
      {sidePanelItems.length > 0 && (
        <div className={`w-1/2 ${themeClasses.border} border-l transition-all duration-300 ${themeClasses.bg}`}>
          <SidePanel
            items={sidePanelItems}
            activeItem={activeSidePanel}
            onItemChange={setActiveSidePanel}
            selectedMessage={selectedChatMessage}
            onClearSelection={() => setSelectedChatMessage(null)}
          />
        </div>
      )}
    </div>
  )
}

export default ChatInterface