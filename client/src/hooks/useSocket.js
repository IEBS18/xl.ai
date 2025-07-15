"use client"

import { useEffect, useState } from "react"
import { io } from "socket.io-client"

export function useSocket() {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // Initialize socket connection
    const socketInstance = io("http://localhost:5000", {
      transports: ["websocket"],
    })

    socketInstance.on("connect", () => {
      console.log("Connected to server")
      setConnected(true)
    })

    socketInstance.on("disconnect", () => {
      console.log("Disconnected from server")
      setConnected(false)
    })

    socketInstance.on("connected", (data) => {
      console.log("Server confirmation:", data.message)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [])

  return { socket, connected }
}
