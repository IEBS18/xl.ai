import React from "react"
import { FileText, Database, CheckCircle, Bug, RefreshCw } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"

const FileInfo = ({ fileInfo, onDebug, onSync }) => {
  const { themeClasses } = useTheme()

  return (
    <div className={`px-4 py-4 ${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className={`${themeClasses.glass} rounded-2xl p-4 shadow-sm`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4">
          {/* File Information Section */}
          <div className="flex items-center space-x-3 min-w-0 flex-1 flex-wrap">
            <div className={`p-2 ${themeClasses.surface} rounded-lg flex-shrink-0`}>
              <FileText size={16} className={themeClasses.textSecondary} />
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <span className={`text-sm font-medium ${themeClasses.text} truncate`}>
                {fileInfo.filename}
              </span>
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

          {/* Buttons Section (Stacked below Loaded on small screens) */}
          <div className="flex flex-col sm:flex-row items-center gap-2 flex-shrink-0 w-full sm:w-auto mt-2 sm:mt-0">
            <button
              onClick={onDebug}
              className={`flex items-center space-x-2 text-xs ${themeClasses.buttonSecondary} border px-3 py-1.5 rounded-xl hover:scale-105 transition-all duration-200 shadow-sm hover:shadow-md font-medium`}
              title="Debug session info"
            >
              <Bug size={14} />
              <span>Debug</span>
            </button>
            <button
              onClick={onSync}
              className="flex items-center space-x-2 text-xs bg-blue-500 text-white px-3 py-1.5 rounded-xl hover:bg-blue-600 hover:scale-105 transition-all duration-200 shadow-sm hover:shadow-md font-medium"
              title="Refresh session sync"
            >
              <RefreshCw size={14} />
              <span>Sync</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileInfo
