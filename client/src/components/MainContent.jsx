
import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import { BACKEND_URL } from "../utils/constants"
import Header from "./Header"
import LandingPage from "./LandingPage"
import DatabaseConnectionModal from "./DatabaseConnectionModal"

const MainContent = () => {
  const { themeClasses } = useTheme()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [showDatabaseModal, setShowDatabaseModal] = useState(false)

  const handleFileUpload = async (files) => {
    if (!files || (Array.isArray(files) && files.length === 0)) return

    // Check authentication first
    if (!isAuthenticated) {
      alert("Please sign in to upload files")
      return
    }

    // Convert single file to array for consistency
    const fileArray = Array.isArray(files) ? files : [files]

    const validTypes = [".csv", ".xlsx", ".xls"]
    const MAX_FILE_SIZE_MB = 128;
    const maxSize = MAX_FILE_SIZE_MB * 1024 * 1024; // bytes

    // Validate all files
    for (const file of fileArray) {
      const fileExtension = "." + file.name.split(".").pop().toLowerCase()
      if (!validTypes.includes(fileExtension)) {
        alert(`Invalid file type for "${file.name}". Please upload CSV or Excel files only (.csv, .xlsx, .xls)`)
        return
      }

      if (file.size > maxSize) {
        alert(`File "${file.name}" is too large. Please upload files smaller than ${MAX_FILE_SIZE_MB} MB.`);
        return;
      }
    }

    const formData = new FormData()
    fileArray.forEach(file => {
      formData.append("files", file)
    })

    try {
      setIsUploading(true)
      setUploadProgress(10)

      const response = await fetch(`${BACKEND_URL}/api/upload-files`, {
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
      if (result.success && result.session_id) {
        setUploadProgress(100)

        // Small delay to show 100% before redirect
        setTimeout(() => {
          navigate(`/chat/${result.session_id}`)
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
    input.multiple = true
    input.onchange = (e) => {
      const selectedFiles = Array.from(e.target.files)
      if (selectedFiles.length > 0) {
        handleFileUpload(selectedFiles)
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

  const handleDatabaseConnect = () => {
    if (!isAuthenticated) {
      alert("Please sign in to connect to a database")
      return
    }
    setShowDatabaseModal(true)
  }

  const handleDatabaseConnectionSuccess = (sessionId) => {
    navigate(`/chat/${sessionId}?type=database`)
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
            onDatabaseConnect={handleDatabaseConnect}
            uploadProgress={uploadProgress}
            isUploading={isUploading}
          />
        </div>
      </div>

      {/* Database Connection Modal */}
      <DatabaseConnectionModal
        isOpen={showDatabaseModal}
        onClose={() => setShowDatabaseModal(false)}
        onSuccess={handleDatabaseConnectionSuccess}
      />
    </div>
  )
}

export default MainContent