import { useState, useCallback, useRef, useEffect } from "react"

export const useSessionFileUpload = (backendUrl, sessionId, onMessage, setFileProcessingState) => {
  const [fileUploaded, setFileUploaded] = useState(false)
  const [fileInfo, setFileInfo] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  // Validate that the session exists and has a file
  const validateSession = useCallback(async () => {
    if (!sessionId) return false

    try {
      const response = await fetch(`${backendUrl}/api/session/${sessionId}/info`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        return false
      }

      const data = await response.json()
      if (data.success && data.fileInfo) {
        setFileUploaded(true)
        setFileInfo(data.fileInfo)
        
        // Check assistant upload status and set file processing state accordingly
        if (setFileProcessingState) {
          const assistantUploadStatus = data.assistant_upload_status || "pending"
          const isUploadComplete = data.is_assistant_upload_complete || false
          
          console.log('🔍 Session validation - Assistant upload status:', {
            assistantUploadStatus,
            isUploadComplete,
            sessionId
          })
          
          // Set processing state based on upload status
          if (assistantUploadStatus === "pending" || assistantUploadStatus === "uploading") {
            setFileProcessingState(true)
            console.log('⏳ File still processing for session:', sessionId)
          } else if (assistantUploadStatus === "completed") {
            setFileProcessingState(false)
            console.log('✅ File processing completed for session:', sessionId)
            
            // Force a small delay to ensure state propagation
            setTimeout(() => {
              console.log('🔄 Double-checking file processing state after completion')
              setFileProcessingState(false)
            }, 100)
          } else if (assistantUploadStatus === "failed") {
            setFileProcessingState(false)
            console.log('❌ File processing failed for session:', sessionId)
          }
        }
        
        return true
      }

      return false
    } catch (error) {
      console.error("Session validation failed:", error)
      return false
    }
  }, [backendUrl, sessionId, setFileProcessingState])

  // Load session info on mount
  useEffect(() => {
    if (sessionId) {
      validateSession()
    }
  }, [sessionId, validateSession])

  const handleFileUpload = useCallback(async (filesOrEvent) => {
    let files = []
    
    // Handle both file array from dropzone and event from file input
    if (Array.isArray(filesOrEvent)) {
      files = filesOrEvent
    } else if (filesOrEvent.target && filesOrEvent.target.files) {
      files = Array.from(filesOrEvent.target.files)
    } else {
      return
    }
    
    if (!files.length || !sessionId) return

    const validTypes = [".csv", ".xlsx", ".xls"]
    const maxSize = 128 * 1024 * 1024

    // Validate all files
    for (const file of files) {
      const fileExtension = "." + file.name.split(".").pop().toLowerCase()
      if (!validTypes.includes(fileExtension)) {
        onMessage("error", `Invalid file type for "${file.name}". Please upload CSV or Excel files only.`)
        return
      }
      if (file.size > maxSize) {
        onMessage("error", `File "${file.name}" is too large. Please upload files smaller than 128MB.`)
        return
      }
    }

    const formData = new FormData()
    files.forEach((file) => {
      formData.append("files", file)
    })

    try {
      setUploadProgress(10)
      onMessage("status", `Uploading ${files.length} file(s) to session ${sessionId}...`)
      
      const response = await fetch(`${backendUrl}/api/session/${sessionId}/upload-files`, {
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
        setFileInfo({
          ...result.data,
          files: result.files,
          totalFiles: result.total_files
        })
        setUploadProgress(100)
        onMessage(
          "success",
          `Successfully loaded ${files.length} file(s) in session ${sessionId}!`,
        )

        setTimeout(() => setUploadProgress(0), 1000)
      } else {
        onMessage("error", `${result.error || "Upload failed"}`)
        setUploadProgress(0)
      }
    } catch (error) {
      onMessage("error", `Upload failed: ${error.message}`)
      setUploadProgress(0)
    }
  }, [backendUrl, sessionId, onMessage])

  const triggerFileUpload = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const getSessionHistory = useCallback(async () => {
    if (!sessionId) return []

    try {
      const response = await fetch(`${backendUrl}/api/session/${sessionId}/history`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        return data.history || []
      }
    } catch (error) {
      console.error("Failed to get session history:", error)
    }
    
    return []
  }, [backendUrl, sessionId])

  const debugSession = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await fetch(`${backendUrl}/api/session/${sessionId}/debug`, {
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
          `Debug Info for Session ${sessionId}:\nValid: ${data.valid}\nHas File: ${data.hasFile}\nFile: ${data.filename || "None"}`,
        )
      }
    } catch (error) {
      console.error("Debug failed:", error)
    }
  }, [backendUrl, sessionId, onMessage])

  const deleteSession = useCallback(async () => {
    if (!sessionId) return false

    try {
      const response = await fetch(`${backendUrl}/api/session/${sessionId}/delete`, {
        method: "DELETE",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        setFileUploaded(false)
        setFileInfo(null)
        onMessage("success", "Session deleted successfully")
        return true
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
      onMessage("error", "Failed to delete session")
    }
    
    return false
  }, [backendUrl, sessionId, onMessage])

  return {
    fileUploaded,
    fileInfo,
    uploadProgress,
    fileInputRef,
    sessionId,
    handleFileUpload,
    triggerFileUpload,
    validateSession,
    getSessionHistory,
    debugSession,
    deleteSession
  }
}