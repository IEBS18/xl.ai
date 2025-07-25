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

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      alert("File size too large. Please upload a file smaller than 50MB.")
      return
    }

    const formData = new FormData()
    formData.append("file", file)

    try {
      setUploadProgress(10)
      
      const response = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData,
        credentials: "include",
      })
      
      setUploadProgress(90)

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
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
      alert(`Upload failed: ${error.message}`)
      setUploadProgress(0)
    }
  }

  const triggerFileUpload = () => {
    // Check authentication first
    if (!isAuthenticated) {
      alert("Please sign in to upload files")
      return
    }

    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.csv,.xlsx,.xls'
    input.onchange = (e) => handleFileUpload(e.target.files[0])
    input.click()
  }

  const handleSendMessage = (message) => {
    // For landing page, we don't have file context yet
    // This would typically show a message to upload a file first
    if (!isAuthenticated) {
      alert("Please sign in to analyze data")
      return
    }
    
    alert("Please upload a file first to start analyzing your data")
  }

  return (
    <div className={`h-screen flex flex-col transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      <Header isConnected={true} />
        
      <div className="flex-1 min-h-0">
        <div className="h-full overflow-y-auto">
          <LandingPage
            isConnected={true}
            onSendMessage={handleSendMessage}
            onFileUpload={triggerFileUpload}
            uploadProgress={uploadProgress}
          />
        </div>
      </div>
    </div>
  )
}

export default MainContent