
import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import { BACKEND_URL } from "../utils/constants"
import Header from "./Header"
import LandingPage from "./LandingPage"

const MainContent = () => {
  const { themeClasses } = useTheme()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileUpload = async (file) => {
    if (!file) return

    // Check authentication first
    if (!isAuthenticated) {
      alert("Please sign in to upload files")
      return
    }

    const validTypes = [".csv", ".xlsx", ".xls"]
    const fileExtension = "." + file.name.split(".").pop().toLowerCase()
    if (!validTypes.includes(fileExtension)) {
      alert("Please upload a CSV or Excel file (.csv, .xlsx, .xls)")
      return
    }

    const MAX_FILE_SIZE_MB = 128;
    const maxSize = MAX_FILE_SIZE_MB * 1024 * 1024; // bytes

    if (file.size > maxSize) {
      alert(`File size too large. Please upload a file smaller than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    const formData = new FormData()
    formData.append("file", file)

    try {
      setIsUploading(true)
      setUploadProgress(10)

      const response = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData,
        credentials: "include",
      })

      setUploadProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Upload failed with status ${response.status}`)
      }

      const result = await response.json()
      if (result.success && result.sessionId) {
        setUploadProgress(100)

        // Small delay to show 100% before redirect
        setTimeout(() => {
          navigate(`/chat/${result.sessionId}`)
        }, 500)
      } else {
        throw new Error(result.error || "Upload failed")
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert(`Upload failed: ${error.message}`)
      setUploadProgress(0)
    } finally {
      // Reset upload state after a delay
      setTimeout(() => {
        setIsUploading(false)
        setUploadProgress(0)
      }, 2000)
    }
  }

  const triggerFileUpload = () => {
    // Check authentication first
    if (!isAuthenticated) {
      alert("Please sign in to upload files")
      return
    }

    // Don't allow new uploads while one is in progress
    if (isUploading) {
      return
    }

    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.csv,.xlsx,.xls'
    input.onchange = (e) => {
      const selectedFile = e.target.files[0]
      if (selectedFile) {
        handleFileUpload(selectedFile)
      }
    }
    input.click()
  }

  const handleSendMessage = (message) => {
    // For landing page, we don't have file context yet
    if (!isAuthenticated) {
      alert("Please sign in to analyze data")
      return
    }

    alert("Please upload a file first to start analyzing your data")
  }

  return (
    <div className={`min-h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      {/* Header - Fixed positioning */}
      <Header isConnected={true} />

      {/* Main Content - Account for fixed header */}
      <div className="flex-1 pt-16 overflow-hidden"> {/* pt-16 accounts for fixed header height */}
        <div className="h-full overflow-y-auto">
          <LandingPage
            isConnected={true}
            onSendMessage={handleSendMessage}
            onFileUpload={triggerFileUpload}
            uploadProgress={uploadProgress}
            isUploading={isUploading}
          />
        </div>
      </div>
    </div>
  )
}

export default MainContent