import React, { useState, useEffect, useCallback } from "react"
import { X, FileText, Download } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"

const FilePreviewModal = ({ 
  isOpen, 
  onClose, 
  fileInfo 
}) => {
  const { themeClasses, isDark } = useTheme()
  const [activeSheet, setActiveSheet] = useState(0)

  // Reset active sheet when modal opens or file changes
  useEffect(() => {
    if (isOpen) {
      setActiveSheet(0)
    }
  }, [isOpen, fileInfo])

  const handleOverlayClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }, [onClose])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen || !fileInfo) return null

  // Handle multiple sheets (for Excel files) or single sheet (for CSV)
  const sheets = fileInfo.sheets || [{ 
    name: fileInfo.filename || 'Sheet1', 
    preview: fileInfo.preview,
    data: fileInfo.data,
    shape: fileInfo.shape,
    columns: fileInfo.columns
  }]

  const currentSheet = sheets[activeSheet] || sheets[0]

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleOverlayClick}
    >
      <div className={`${themeClasses.bg} ${themeClasses.border} border rounded-2xl shadow-2xl max-w-6xl max-h-[90vh] w-full mx-4 flex flex-col`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-6 ${themeClasses.border} border-b`}>
          <div className="flex items-center space-x-3">
            <FileText className={`w-6 h-6 ${themeClasses.text}`} />
            <div>
              <h2 className={`text-lg font-semibold ${themeClasses.text}`}>
                {fileInfo.filename}
              </h2>
              {fileInfo.shape && (
                <p className={`text-sm ${themeClasses.textSecondary}`}>
                  {fileInfo.shape[0]} rows × {fileInfo.shape[1]} columns
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors`}
            title="Close preview"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sheet tabs (if multiple sheets) */}
        {sheets.length > 1 && (
          <div className={`flex space-x-1 p-4 ${themeClasses.border} border-b bg-gray-50 dark:bg-gray-800/50`}>
            {sheets.map((sheet, index) => (
              <button
                key={index}
                onClick={() => setActiveSheet(index)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeSheet === index
                    ? `${themeClasses.button} text-white shadow-sm`
                    : `${themeClasses.surface} ${themeClasses.text} hover:${themeClasses.surfaceSecondary}`
                }`}
              >
                {sheet.name || `Sheet ${index + 1}`}
              </button>
            ))}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden p-6">
          <div className="h-full flex flex-col space-y-4">
            {/* Sheet info */}
            {currentSheet.shape && (
              <div className={`text-sm ${themeClasses.textSecondary}`}>
                Current sheet: {currentSheet.shape[0]} rows × {currentSheet.shape[1]} columns
              </div>
            )}

            {/* Data preview */}
            <div className="flex-1 overflow-auto">
              {currentSheet.preview ? (
                <div
                  className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-auto`}
                  dangerouslySetInnerHTML={{ __html: currentSheet.preview }}
                  style={{ 
                    maxHeight: 'calc(90vh - 200px)',
                    fontSize: '11px'
                  }}
                />
              ) : currentSheet.data && currentSheet.data.length > 0 ? (
                <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-auto`} style={{ maxHeight: 'calc(90vh - 200px)' }}>
                  <table className="min-w-full text-xs">
                    <thead className={`${themeClasses.surfaceSecondary} sticky top-0`}>
                      <tr>
                        {currentSheet.columns && currentSheet.columns.map((col, index) => (
                          <th key={index} className={`px-2 py-1 text-left font-medium ${themeClasses.text} border-r ${themeClasses.border} last:border-r-0 whitespace-nowrap`}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {currentSheet.data.map((row, rowIndex) => (
                        <tr key={rowIndex} className={`hover:${themeClasses.surfaceSecondary} transition-colors`}>
                          {currentSheet.columns && currentSheet.columns.map((col, colIndex) => (
                            <td key={colIndex} className={`px-2 py-1 ${themeClasses.text} border-r ${themeClasses.border} last:border-r-0 border-b ${themeClasses.border} max-w-xs truncate`} title={String(row[col] || '')}>
                              {String(row[col] || '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-8 text-center`}>
                  <p className={`${themeClasses.textSecondary}`}>No preview data available</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`p-4 ${themeClasses.border} border-t ${themeClasses.surface} rounded-b-2xl`}>
          <div className="flex items-center justify-between">
            <div className={`text-xs ${themeClasses.textSecondary}`}>
              Press Esc to close • Showing preview of data
            </div>
            {/* <div className="flex space-x-2">
              <button
                onClick={onClose}
                className={`px-4 py-2 text-sm ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
              >
                Close
              </button>
            </div> */}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FilePreviewModal