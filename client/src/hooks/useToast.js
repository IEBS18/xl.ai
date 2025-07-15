"use client"

import { useState, useCallback } from "react"

export function useToast() {
  const [toasts, setToasts] = useState([])

  const toast = useCallback(({ type = "info", title, message, duration = 5000 }) => {
    const id = Date.now().toString()
    const newToast = { id, type, title, message, duration }

    setToasts((prev) => [...prev, newToast])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return { toast, toasts, removeToast }
}
