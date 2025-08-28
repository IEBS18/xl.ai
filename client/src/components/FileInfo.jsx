import React from "react"
import { FileText, Database, CheckCircle, Bug, RefreshCw, Files } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
import { BACKEND_URL } from "../utils/constants"

const FileInfo = ({ fileInfo, onDebug, onSync, onShowPreview, sessionId }) => {
  const { themeClasses } = useTheme()

  const handleFilenameClick = async () => {
    if (!onShowPreview || !fileInfo || !sessionId) return

    try {
      // If preview data is already available, use it
      if (fileInfo.preview && fileInfo.data) {
        const previewMessage = {
          id: `file-preview-${Date.now()}`,
          type: "dataframe",
          content: {
            name: fileInfo.filename,
            shape: fileInfo.shape,
            columns: fileInfo.columns || [],
            preview: fileInfo.preview,
            data: fileInfo.data
          },
          timestamp: new Date().toISOString()
        }
        onShowPreview(previewMessage)
        return
      }

      // If preview data is not available, fetch it from session info
      console.log("Fetching session data for preview...")
      const response = await fetch(`${BACKEND_URL}/session/${sessionId}/info`, {
        method: 'GET',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch session info: ${response.status}`)
      }

      const sessionData = await response.json()
      
      if (sessionData.success && sessionData.dataPreview) {
        const previewMessage = {
          id: `file-preview-${Date.now()}`,
          type: "dataframe",
          content: {
            name: fileInfo.filename,
            shape: fileInfo.shape,
            columns: fileInfo.columns || [],
            preview: sessionData.dataPreview,
            data: sessionData.fileInfo?.data || [] // Use data if available
          },
          timestamp: new Date().toISOString()
        }
        onShowPreview(previewMessage)
      } else {
        console.error("No preview data available")
        alert("Preview data not available")
      }
    } catch (error) {
      console.error("Error fetching preview:", error)
      alert("Failed to load preview data")
    }
  }

  const files = fileInfo.files || []
  const hasMultipleFiles = files.length > 1

  return (
    <div className={`px-4 py-4 ${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className={`${themeClasses.glass} rounded-2xl p-4 shadow-sm`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4">
          {/* File Information Section */}
          <div className="flex items-center space-x-3 min-w-0 flex-1 flex-wrap">
            <div className={`p-2 ${themeClasses.surface} rounded-lg flex-shrink-0`}>
              {hasMultipleFiles ? (
                <Files size={16} className={themeClasses.textSecondary} />
              ) : (
                <FileText size={16} className={themeClasses.textSecondary} />
              )}
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              {hasMultipleFiles ? (
                <div className="space-y-1">
                  <div className={`text-sm font-medium ${themeClasses.text}`}>
                    {fileInfo.totalFiles || files.length} Files Uploaded
                  </div>
                  <div className="space-y-1 max-h-20 overflow-y-auto">
                    {files.slice(0, 3).map((file, index) => (
                      <div key={index} className={`text-xs ${themeClasses.textSecondary} truncate`}>
                        • {file.filename}
                      </div>
                    ))}
                    {files.length > 3 && (
                      <div className={`text-xs ${themeClasses.textMuted} italic`}>
                        +{files.length - 3} more files
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleFilenameClick}
                  className={`text-sm font-medium ${themeClasses.text} truncate text-left hover:text-blue-600 dark:hover:text-blue-400 hover:underline transition-colors cursor-pointer`}
                  title="Click to view data preview"
                >
                  {fileInfo.filename}
                </button>
              )}
              <div className="flex items-center flex-wrap gap-2 mt-1">
                <div className={`flex items-center space-x-1 text-xs ${themeClasses.textSecondary} ${themeClasses.surface} px-2 py-1 rounded-full flex-shrink-0`}>
                  <Database size={12} />
                  <span>{fileInfo.shape[0]} rows × {fileInfo.shape[1]} columns</span>
                </div>
                <div className="flex items-center space-x-1 text-xs text-green-700 bg-green-50 px-2 py-1 rounded-full border border-green-200 flex-shrink-0">
                  <CheckCircle size={12} />
                  <span className="font-medium">Loaded</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileInfo