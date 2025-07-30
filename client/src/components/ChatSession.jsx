import React, { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import { useSocket } from "../hooks/useSocket"
import { useMessages } from "@/hooks"
import { useSessionFileUpload } from "../hooks/useSessionFileUpload"
import { BACKEND_URL } from "../utils/constants"
import Header from "./Header"
import ChatInterface from "./ChatInterface"
import AuthModal from "./AuthModal"

const ChatSession = () => {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const { themeClasses } = useTheme()
  const { isAuthenticated, isLoading } = useAuth()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [sessionValid, setSessionValid] = useState(false)
  const [loading, setLoading] = useState(true)
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
  const [currentQueryCategory, setCurrentQueryCategory] = useState(null) // Track current query type
  
  const { messages, addMessage, handleStreamData, ...messageProps } = useMessages()
  
  // Enhanced socket handling for different query types
  const { socket, isConnected, sendMessage } = useSocket(
    BACKEND_URL,
    (data) => {
      console.log('Socket data received:', data) // Debug log
      
      // Handle different types of streaming data from enhanced backend
      handleStreamData(data)
      
      // Enhanced completion handling for different query categories
      if (data.type === "completion" || 
          data.type === "analysis_complete" ||
          data.type === "conversational_complete") {
        
        setIsAnalyzing(false)
        
        // Extract query category from completion data
        if (data.result && data.result.query_category) {
          console.log('Query completed with category:', data.result.query_category)
        }
        
        setCurrentQueryCategory(null) // Reset after completion
      }
      
      // Handle quick responses for conversational and textual analytical
      if (data.type === "output") {
        setIsAnalyzing(false)
        setCurrentQueryCategory(null)
      }
      
      // Handle errors
      if (data.type === "error") {
        setIsAnalyzing(false)
        setCurrentQueryCategory(null)
      }
      
      // Track analysis start with category
      if (data.type === "analysis_started") {
        console.log('Analysis started')
        setIsAnalyzing(true)
      }
    },
    addMessage,
    sessionId
  )

  const { 
    fileUploaded, 
    fileInfo, 
    validateSession,
    ...fileProps 
  } = useSessionFileUpload(
    BACKEND_URL,
    sessionId,
    (type, content) => {
      addMessage(type, content)
    }
  )

  // Check authentication first, then validate session
  useEffect(() => {
    const checkSessionAndAuth = async () => {
      if (isLoading) return // Wait for auth to load

      if (!isAuthenticated) {
        // Redirect to home if not authenticated
        navigate('/')
        return
      }

      if (!sessionId) {
        navigate('/')
        return
      }

      try {
        const isValid = await validateSession()
        if (isValid) {
          setSessionValid(true)
          console.log(`Valid session: ${sessionId}`)
        } else {
          console.log(`Invalid session: ${sessionId}, redirecting to home`)
          navigate('/')
        }
      } catch (error) {
        console.error('Session validation failed:', error)
        navigate('/')
      } finally {
        setLoading(false)
      }
    }

    checkSessionAndAuth()
  }, [sessionId, validateSession, navigate, isAuthenticated, isLoading])

  // Enhanced message sending with query classification support
  const handleSendMessage = (message) => {
    if (!message.trim() || isAnalyzing) return

    if (!isConnected) {
      addMessage("error", "Not connected to server. Please check your connection.")
      return
    }

    if (!fileUploaded) {
      addMessage("system", "Session file not found. Please go back to home and upload a file.")
      return
    }

    // Classify query locally for immediate UI feedback (optional)
    const classifyQueryLocally = (query) => {
      const lowerQuery = query.toLowerCase().trim()
      
      // Simple local classification for immediate UI feedback
      if (lowerQuery.match(/^(hi|hello|hey|what can you|what do you|help|thanks|thank you|bye|goodbye)/)) {
        return "conversational"
      } else if (lowerQuery.match(/(what is|what's|how many|average|maximum|minimum|sum|count|total)/)) {
        return "textual_analytical"
      } else if (lowerQuery.match(/(generate|create|analyze|forecast|predict|report|comprehensive|detailed)/)) {
        return "fully_analytical"
      }
      
      return "unknown" // Let backend classify
    }

    const estimatedCategory = classifyQueryLocally(message)
    console.log('Estimated query category:', estimatedCategory)
    
    // Set current query category for UI feedback
    if (estimatedCategory !== "unknown") {
      setCurrentQueryCategory(estimatedCategory)
    }

    // Add user message with estimated category
    addMessage("user", message, true, estimatedCategory)
    setIsAnalyzing(true)
    
    // Send message to enhanced backend
    sendMessage(message)
  }

  const handleGoHome = () => {
    navigate('/')
  }

  const openAuthModal = (mode = "login") => {
    setAuthModal({ isOpen: true, mode })
  }

  const closeAuthModal = () => {
    setAuthModal({ isOpen: false, mode: "login" })
  }

  // Show loading while checking auth or session
  if (isLoading || loading) {
    return (
      <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
        <Header isConnected={isConnected} sessionId={sessionId} onGoHome={handleGoHome} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-lg">
              {isLoading ? "Checking authentication..." : "Validating session..."}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Show auth modal if not authenticated
  if (!isAuthenticated) {
    return (
      <>
        <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
          <Header isConnected={isConnected} />
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Please sign in to access your analysis session.
              </p>
              <button
                onClick={() => openAuthModal('login')}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors mr-4"
              >
                Sign In
              </button>
              <button
                onClick={handleGoHome}
                className="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
        
        <AuthModal
          isOpen={authModal.isOpen}
          mode={authModal.mode}
          onClose={closeAuthModal}
          onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
        />
      </>
    )
  }

  // Show session not found if invalid
  if (!sessionValid) {
    return (
      <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
        <Header isConnected={isConnected} sessionId={sessionId} onGoHome={handleGoHome} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Session Not Found</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The session you're looking for doesn't exist or has expired.
            </p>
            <button
              onClick={handleGoHome}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
        <Header 
          isConnected={isConnected} 
          sessionId={sessionId} 
          onGoHome={handleGoHome}
          currentQueryCategory={currentQueryCategory} // Pass query category to header
        />
          
        <div className="flex-1 min-h-0">
          <div className="h-full pt-2">
            <ChatInterface
              messages={messages}
              isAnalyzing={isAnalyzing}
              isConnected={isConnected}
              fileUploaded={fileUploaded}
              fileInfo={fileInfo}
              onSendMessage={handleSendMessage}
              sessionId={sessionId}
              currentQueryCategory={currentQueryCategory} // Pass to chat interface
              {...messageProps}
              {...fileProps}
            />
          </div>
        </div>
      </div>

      <AuthModal
        isOpen={authModal.isOpen}
        mode={authModal.mode}
        onClose={closeAuthModal}
        onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
      />
    </>
  )
}

export default ChatSession