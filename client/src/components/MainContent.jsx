import React, { useState, useEffect } from "react"
import { useTheme } from "../context/ThemeProvider"
import { useSocket } from "../hooks/useSocket"
import { useMessages } from "@/hooks"
import { useFileUpload } from "../hooks/useFileUpload"
import { BACKEND_URL } from "../utils/constants"
import Header from "./Header"
import ChatInterface from "./ChatInterface"
import LandingPage from "./LandingPage"

const MainContent = () => {
  const { themeClasses } = useTheme()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [hasUserInteraction, setHasUserInteraction] = useState(false)
  
  const { messages, addMessage, handleStreamData, ...messageProps } = useMessages()
  
  const { socket, isConnected, sendMessage } = useSocket(
    BACKEND_URL,
    (data) => {
      handleStreamData(data)
      if (data.type === "success" || data.type === "error") {
        setIsAnalyzing(false)
      }
    },
    addMessage
  )

  const { fileUploaded, fileInfo, checkSessionInfo, ...fileProps } = useFileUpload(
    BACKEND_URL,
    (type, content) => {
      addMessage(type, content)
      // Only set user interaction for actual user actions, not system messages
      if (type === "success" && content.includes("Successfully loaded")) {
        setHasUserInteraction(true)
      }
    }
  )

  useEffect(() => {
    checkSessionInfo()
  }, [checkSessionInfo])

  const handleSendMessage = (message) => {
    if (!message.trim() || isAnalyzing) return

    if (!isConnected) {
      addMessage("error", "Not connected to server. Please check your connection.")
      return
    }

    if (!fileUploaded) {
      addMessage("system", "Please upload a CSV or Excel file first to start analyzing your data.")
      return
    }

    setHasUserInteraction(true)
    addMessage("user", message, true)
    setIsAnalyzing(true)
    sendMessage(message)
  }

  const handleFileUpload = () => {
    setHasUserInteraction(true)
    fileProps.triggerFileUpload()
  }

  // Determine if we should show chat interface
  // Only show chat if user has actually interacted (uploaded file or sent message)
  const userMessages = messages.filter(msg => msg.isUser)
  const shouldShowChat = (fileUploaded && hasUserInteraction) || userMessages.length > 0

  return (
    <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      <Header isConnected={isConnected} />
      
      {/* Main Content Area - Takes remaining height after header */}
      <div className="flex-1 min-h-0">
        {shouldShowChat ? (
          <div className="h-full pt-2">
            <ChatInterface
              messages={messages}
              isAnalyzing={isAnalyzing}
              isConnected={isConnected}
              fileUploaded={fileUploaded}
              fileInfo={fileInfo}
              onSendMessage={handleSendMessage}
              {...messageProps}
              {...fileProps}
            />
          </div>
        ) : (
          <div className="h-full overflow-y-auto">
            <LandingPage
              isConnected={isConnected}
              onSendMessage={handleSendMessage}
              onFileUpload={handleFileUpload}
              {...fileProps}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default MainContent