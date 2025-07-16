import { useState, useCallback, useRef } from "react"

export const useFileUpload = (backendUrl, onMessage) => {
  const [fileUploaded, setFileUploaded] = useState(false)
  const [fileInfo, setFileInfo] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const handleFileUpload = useCallback(async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const validTypes = [".csv", ".xlsx", ".xls"]
    const fileExtension = "." + file.name.split(".").pop().toLowerCase()
    if (!validTypes.includes(fileExtension)) {
      onMessage("error", "Please upload a CSV or Excel file (.csv, .xlsx, .xls)")
      return
    }

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      onMessage("error", "File size too large. Please upload a file smaller than 50MB.")
      return
    }

    const formData = new FormData()
    formData.append("file", file)

    try {
      setUploadProgress(10)
      onMessage("status", `Uploading "${file.name}"...`)
      const response = await fetch(`${backendUrl}/upload`, {
        method: "POST",
        body: formData,
        credentials: "include",
      })
      setUploadProgress(90)

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        setFileUploaded(true)
        setFileInfo(result.data)
        setUploadProgress(100)
        onMessage(
          "success",
          `Successfully loaded "${result.data.filename}"!\n\nDataset: ${result.data.shape[0]} rows × ${result.data.shape[1]} columns\nColumns: ${result.data.columns.slice(0, 5).join(", ")}${result.data.columns.length > 5 ? "..." : ""}\n\nWhat would you like to analyze?`,
        )

        if (result.data.preview) {
          onMessage("dataframe", {
            name: "Data Preview",
            shape: result.data.shape,
            columns: result.data.columns,
            preview: result.data.preview,
          })
        }

        setTimeout(() => setUploadProgress(0), 1000)
      } else {
        onMessage("error", `${result.error || "Upload failed"}`)
        setUploadProgress(0)
      }
    } catch (error) {
      onMessage("error", `Upload failed: ${error.message}`)
      setUploadProgress(0)
    }
  }, [backendUrl, onMessage])

  const triggerFileUpload = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const checkSessionInfo = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/session-info`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.connected && data.data) {
        // Set file state but don't add messages automatically
        // This prevents auto-switching to chat interface
        setFileUploaded(true)
        setFileInfo(data.data)
        
        // Only show session restored message in console, not in UI
        console.log(`Session restored: ${data.data.filename} with ${data.data.shape[0]} rows and ${data.data.shape[1]} columns`)
      }
    } catch (error) {
      console.log("No existing session or connection error:", error.message)
    }
  }, [backendUrl])

  const checkSessionSync = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/session-info`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.connected && data.data) {
        if (!fileUploaded) {
          setFileUploaded(true)
          setFileInfo(data.data)
          onMessage("success", "Session synced! File is ready for analysis.")
        } else {
          console.log("Session sync confirmed - file available in backend")
        }
      } else if (fileUploaded) {
        onMessage("error", "Session sync issue detected. Please re-upload your file.")
        setFileUploaded(false)
        setFileInfo(null)
      }
    } catch (error) {
      console.log("Session sync check failed:", error.message)
    }
  }, [backendUrl, fileUploaded, onMessage])

  const manualSessionSync = useCallback(async () => {
    onMessage("status", "Checking session sync...")
    await checkSessionSync()
  }, [checkSessionSync, onMessage])

  const debugSession = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/debug-session`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (response.ok) {
        const data = await response.json()
        console.log("Session Debug Info:", data)
        onMessage(
          "system",
          `Debug Info:\nSession ID: ${data.session_id || "None"}\nHas Analyzer: ${data.has_analyzer}\nHas Session Data: ${data.has_session_data}\nAnalyzers: ${data.analyzers_count}\nSessions: ${data.session_data_count}`,
        )
      }
    } catch (error) {
      console.error("Debug failed:", error)
    }
  }, [backendUrl, onMessage])

  return {
    fileUploaded,
    fileInfo,
    uploadProgress,
    fileInputRef,
    handleFileUpload,
    triggerFileUpload,
    checkSessionInfo,
    checkSessionSync,
    manualSessionSync,
    debugSession
  }
}