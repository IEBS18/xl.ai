import React, { useState, useEffect } from "react"
import { useTheme } from "../context/ThemeProvider"
import { useSocket } from "../hooks/useSocket"
// import { useMessages } from "../hooks/useMessages"
import { useMessages } from "@/hooks/useMesssages"
import { useFileUpload } from "@/hooks/useFileUpload"
import { BACKEND_URL } from "@/utils/constants"
import Header from "./Header"
import ChatInterface from "./ChatInterface"
import LandingPage from "./LandingPage"

const MainContent = () => {
  const { themeClasses } = useTheme()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  
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
    addMessage
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

    addMessage("user", message, true)
    setIsAnalyzing(true)
    sendMessage(message)
  }

  return (
    <div className={`min-h-screen transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      <Header isConnected={isConnected} />
      
      {fileUploaded || messages.length > 0 ? (
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
      ) : (
        <LandingPage
          isConnected={isConnected}
          onSendMessage={handleSendMessage}
          {...fileProps}
        />
      )}
    </div>
  )
}

export default MainContent