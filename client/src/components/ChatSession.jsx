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
import Sidebar from "./Sidebar"
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
  const [currentQueryCategory, setCurrentQueryCategory] = useState(null)
  
  // Sidebar state - Default to collapsed
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true)
  const [chatHistory, setChatHistory] = useState([])
  
  const { messages, addMessage, handleStreamData, ...messageProps } = useMessages()
  
  // Enhanced socket handling for different query types
  const { socket, isConnected, sendMessage } = useSocket(
    BACKEND_URL,
    (data) => {
      console.log('Socket data received:', data)
      
      handleStreamData(data)
      
      if (data.type === "completion" || 
          data.type === "analysis_complete" ||
          data.type === "conversational_complete") {
        
        setIsAnalyzing(false)
        
        if (data.result && data.result.query_category) {
          console.log('Query completed with category:', data.result.query_category)
        }
        
        setCurrentQueryCategory(null)
        
        // Update chat history when conversation completes
        updateChatHistory()
      }
      
      if (data.type === "output") {
        setIsAnalyzing(false)
        setCurrentQueryCategory(null)
        updateChatHistory()
      }
      
      if (data.type === "error") {
        setIsAnalyzing(false)
        setCurrentQueryCategory(null)
      }
      
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

  // Load chat history from localStorage or API
  const loadChatHistory = async () => {
    try {
      // First try to load from localStorage
      const savedHistory = localStorage.getItem('chatHistory')
      if (savedHistory) {
        setChatHistory(JSON.parse(savedHistory))
      }
      
      // Then try to load from API if authenticated
      if (isAuthenticated) {
        // You can implement an API call here to fetch user's chat history
        // const response = await fetch(`${BACKEND_URL}/api/chat-history`, {
        //   credentials: 'include'
        // })
        // if (response.ok) {
        //   const data = await response.json()
        //   setChatHistory(data.history)
        // }
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  // Update chat history when messages change
  const updateChatHistory = () => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages].reverse().find(msg => msg.type === 'user')
      const lastAssistantMessage = [...messages].reverse().find(msg => msg.type === 'assistant' || msg.type === 'output')
      
      if (lastUserMessage) {
        const chatEntry = {
          id: sessionId,
          title: lastUserMessage.content.slice(0, 50) + (lastUserMessage.content.length > 50 ? '...' : ''),
          lastMessage: lastAssistantMessage ? lastAssistantMessage.content.slice(0, 100) : 'Processing...',
          createdAt: new Date().toISOString(),
          attachedFiles: fileInfo ? [fileInfo.filename] : []
        }
        
        setChatHistory(prev => {
          const updated = prev.filter(chat => chat.id !== sessionId)
          const newHistory = [chatEntry, ...updated].slice(0, 50) // Keep last 50 chats
          
          // Save to localStorage
          localStorage.setItem('chatHistory', JSON.stringify(newHistory))
          
          return newHistory
        })
      }
    }
  }

  // Check authentication first, then validate session
  useEffect(() => {
    const checkSessionAndAuth = async () => {
      if (isLoading) return

      if (!isAuthenticated) {
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
          // Load chat history after session validation
          loadChatHistory()
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

  // Update chat history when messages change
  useEffect(() => {
    if (messages.length > 0 && sessionValid) {
      // Debounce the update to avoid too frequent calls
      const timeoutId = setTimeout(updateChatHistory, 1000)
      return () => clearTimeout(timeoutId)
    }
  }, [messages, sessionValid])

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

    const classifyQueryLocally = (query) => {
      const lowerQuery = query.toLowerCase().trim()
      
      if (lowerQuery.match(/^(hi|hello|hey|what can you|what do you|help|thanks|thank you|bye|goodbye)/)) {
        return "conversational"
      } else if (lowerQuery.match(/(what is|what's|how many|average|maximum|minimum|sum|count|total)/)) {
        return "textual_analytical"
      } else if (lowerQuery.match(/(generate|create|analyze|forecast|predict|report|comprehensive|detailed)/)) {
        return "fully_analytical"
      }
      
      return "unknown"
    }

    const estimatedCategory = classifyQueryLocally(message)
    console.log('Estimated query category:', estimatedCategory)
    
    if (estimatedCategory !== "unknown") {
      setCurrentQueryCategory(estimatedCategory)
    }

    addMessage("user", message, true, estimatedCategory)
    setIsAnalyzing(true)
    
    sendMessage(message)
  }

  // Handle new chat creation
  const handleNewChat = async () => {
    try {
      // Create new session by calling upload endpoint without file (or redirect to home)
      navigate('/')
    } catch (error) {
      console.error('Error creating new chat:', error)
    }
  }

  // Handle chat selection
  const handleChatSelect = (chatId) => {
    if (chatId !== sessionId) {
      navigate(`/chat/${chatId}`)
    }
  }

  // Handle chat deletion
  const handleDeleteChat = (chatId) => {
    setChatHistory(prev => {
      const updated = prev.filter(chat => chat.id !== chatId)
      localStorage.setItem('chatHistory', JSON.stringify(updated))
      return updated
    })
    
    // If deleting current chat, go to home
    if (chatId === sessionId) {
      navigate('/')
    }
  }

  // Handle sidebar collapse toggle
  const handleSidebarToggle = (collapsed) => {
    setIsSidebarCollapsed(collapsed)
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
      <div className={`h-screen flex transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
        {/* Sidebar */}
        <Sidebar
          isConnected={isConnected}
          currentChatId={sessionId}
          onNewChat={handleNewChat}
          onChatSelect={handleChatSelect}
          onDeleteChat={handleDeleteChat}
          chatHistory={chatHistory}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={handleSidebarToggle}
        />
        
        {/* Main Content Area - No header in chat session */}
        <div 
          className="flex-1 flex flex-col transition-all duration-400 ease-[cubic-bezier(0.4,0,0.2,1)]"
          style={{
            marginLeft: isSidebarCollapsed ? '64px' : '320px'
          }}
        >
          {/* No Header component rendered here since we're in session */}
          
          {/* Chat Interface - Full height since no header */}
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
                currentQueryCategory={currentQueryCategory}
                {...messageProps}
                {...fileProps}
              />
            </div>
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