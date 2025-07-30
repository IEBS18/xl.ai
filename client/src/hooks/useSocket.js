import { useState, useEffect, useCallback } from "react"
import { io } from "socket.io-client"

export const useSocket = (backendUrl, onStreamData, onStatusUpdate, sessionId = null) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionRetries, setConnectionRetries] = useState(0)

  const initializeConnection = useCallback(() => {
    if (socket) {
      socket.removeAllListeners()
      socket.close()
    }

    const socketOptions = {
      transports: ["polling", "websocket"],
      withCredentials: true,
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      autoConnect: true,
    }

    // Add session ID to connection query if provided
    if (sessionId) {
      socketOptions.query = { sessionId }
    }

    const newSocket = io(backendUrl, socketOptions)

    newSocket.on("connect", () => {
      setIsConnected(true)
      setConnectionRetries(0)
      console.log(`✅ Connected to enhanced backend${sessionId ? ` with session ${sessionId}` : ''}`)
      
      // Join session room if sessionId is provided
      if (sessionId) {
        newSocket.emit('join_session', { sessionId })
        console.log(`🏠 Joining session room: ${sessionId}`)
      }

      // Enhanced connection message
      if (onStatusUpdate) {
        onStatusUpdate("system", "🤖 Connected to enhanced AI analysis server - conversational features enabled!")
      }
    })

    newSocket.on("disconnect", (reason) => {
      setIsConnected(false)
      console.log("❌ Disconnected from enhanced backend:", reason)
      if (reason !== "io client disconnect" && onStatusUpdate) {
        onStatusUpdate("error", `Disconnected from server: ${reason}`)
      }
    })

    newSocket.on("connect_error", (error) => {
      console.error("🔴 Enhanced backend connection error:", error)
      setConnectionRetries((prev) => prev + 1)
      if (onStatusUpdate) {
        if (connectionRetries < 3) {
          onStatusUpdate("error", `Connection failed, retrying... (${connectionRetries + 1}/3)`)
        } else {
          onStatusUpdate("error", "Unable to connect to enhanced backend. Please check if enhanced_app.py is running on localhost:5000")
        }
      }
    })

    // Enhanced stream data handler for the new backend
    newSocket.on("stream_data", (data) => {
      console.log("🌊 Enhanced stream data received:", { 
        type: data.type, 
        sessionId: data.sessionId, 
        timestamp: data.timestamp,
        hasData: !!data.data
      })
      
      if (onStreamData) {
        onStreamData(data)
      }
    })

    // Enhanced status handler
    newSocket.on("status", (data) => {
      console.log("📊 Enhanced status:", data)
      
      // Check for enhanced features confirmation
      if (data.features) {
        console.log("🚀 Enhanced features available:", data.features)
      }
      
      if (onStatusUpdate) {
        onStatusUpdate("system", data.message || data)
      }
    })

    // Handle session termination
    newSocket.on("session_terminated", (data) => {
      console.log("🛑 Session terminated:", data)
      if (onStatusUpdate) {
        onStatusUpdate("error", "Session was terminated")
      }
    })

    // Handle analysis completion with enhanced data
    newSocket.on("analysis_complete", (data) => {
      console.log("✅ Enhanced analysis complete:", data)
      if (onStreamData) {
        onStreamData({
          type: "analysis_complete",
          data: data.message || "Analysis completed",
          result: data.result,
          timestamp: data.timestamp,
          sessionId: data.sessionId
        })
      }
    })

    // Handle errors from enhanced backend
    newSocket.on("error", (error) => {
      console.error("❌ Enhanced backend error:", error)
      if (onStatusUpdate) {
        onStatusUpdate("error", error.message || error)
      }
    })

    setSocket(newSocket)
  }, [backendUrl, connectionRetries, onStreamData, onStatusUpdate, sessionId])

  useEffect(() => {
    initializeConnection()
    return () => {
      if (socket) {
        console.log("🔌 Closing enhanced backend connection")
        socket.close()
      }
    }
  }, [sessionId]) // Reconnect when sessionId changes

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      console.log(`📤 Sending enhanced message with sessionId: ${sessionId}`, {
        message: message.substring(0, 50) + (message.length > 50 ? '...' : ''),
        sessionId
      })
      
      if (sessionId) {
        // Use session-aware handler for enhanced backend
        socket.emit("send_message_with_session", { 
          message,
          sessionId 
        })
      } else {
        // Use original handler for landing page (legacy support)
        socket.emit("send_message", { message })
      }
    } else {
      console.warn("⚠️ Cannot send message - socket not connected", { 
        hasSocket: !!socket, 
        isConnected,
        sessionId 
      })
    }
  }, [socket, isConnected, sessionId])

  // Enhanced method to stop analysis
  const stopAnalysis = useCallback((stopType = 'query') => {
    if (socket && isConnected && sessionId) {
      console.log(`🛑 Stopping ${stopType} for session: ${sessionId}`)
      socket.emit("stop_analysis", { 
        sessionId,
        type: stopType // 'query' or 'session'
      })
    }
  }, [socket, isConnected, sessionId])

  // Enhanced method to terminate session
  const terminateSession = useCallback(() => {
    if (socket && isConnected && sessionId) {
      console.log(`🗑️ Terminating session: ${sessionId}`)
      socket.emit("terminate_session", { sessionId })
    }
  }, [socket, isConnected, sessionId])

  return {
    socket,
    isConnected,
    connectionRetries,
    sendMessage,
    stopAnalysis,
    terminateSession,
    initializeConnection
  }
}