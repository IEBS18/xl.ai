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
      console.log(`Connected to server${sessionId ? ` with session ${sessionId}` : ''}`)
      
      // Join session room if sessionId is provided
      if (sessionId) {
        newSocket.emit('join_session', { sessionId })
      }
    })

    newSocket.on("disconnect", (reason) => {
      setIsConnected(false)
      console.log("Disconnected from server:", reason)
      if (reason !== "io client disconnect" && onStatusUpdate) {
        onStatusUpdate("error", `Disconnected from server: ${reason}`)
      }
    })

    newSocket.on("connect_error", (error) => {
      console.error("Connection error:", error)
      setConnectionRetries((prev) => prev + 1)
      if (onStatusUpdate) {
        if (connectionRetries < 3) {
          onStatusUpdate("error", `Connection failed, retrying... (${connectionRetries + 1}/3)`)
        } else {
          onStatusUpdate("error", "Unable to connect to server. Please check if the backend is running on localhost:5000")
        }
      }
    })

    newSocket.on("stream_data", (data) => {
      if (onStreamData) {
        onStreamData(data)
      }
    })

    newSocket.on("status", (data) => {
      console.log("Status:", data.message)
    })

    newSocket.on("session_joined", (data) => {
      console.log("Successfully joined session:", data.sessionId)
    })

    newSocket.on("session_error", (data) => {
      console.error("Session error:", data.error)
      if (onStatusUpdate) {
        onStatusUpdate("error", `Session error: ${data.error}`)
      }
    })

    setSocket(newSocket)
  }, [backendUrl, connectionRetries, onStreamData, onStatusUpdate, sessionId])

  useEffect(() => {
    initializeConnection()
    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [sessionId]) // Reconnect when sessionId changes

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.emit("send_message", { 
        message,
        sessionId // Include sessionId in message
      })
    }
  }, [socket, isConnected, sessionId])

  const leaveSession = useCallback(() => {
    if (socket && isConnected && sessionId) {
      socket.emit("leave_session", { sessionId })
    }
  }, [socket, isConnected, sessionId])

  return {
    socket,
    isConnected,
    connectionRetries,
    sendMessage,
    leaveSession,
    initializeConnection
  }
}