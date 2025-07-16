import { useState, useEffect, useCallback } from "react"
import { io } from "socket.io-client"

export const useSocket = (backendUrl, onStreamData, onStatusUpdate) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionRetries, setConnectionRetries] = useState(0)

  const initializeConnection = useCallback(() => {
    if (socket) {
      socket.removeAllListeners()
      socket.close()
    }

    const newSocket = io(backendUrl, {
      transports: ["polling", "websocket"],
      withCredentials: true,
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      autoConnect: true,
    })

    newSocket.on("connect", () => {
      setIsConnected(true)
      setConnectionRetries(0)
      console.log("Connected to server")
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

    setSocket(newSocket)
  }, [backendUrl, connectionRetries, onStreamData, onStatusUpdate, socket])

  useEffect(() => {
    initializeConnection()
    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [])

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.emit("send_message", { message })
    }
  }, [socket, isConnected])

  return {
    socket,
    isConnected,
    connectionRetries,
    sendMessage,
    initializeConnection
  }
}