import React from "react"
import { FileText, Database, CheckCircle, Bug, RefreshCw } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
const FileInfo = ({ fileInfo, onDebug, onSync }) => {
  const { themeClasses } = useTheme()

  return (
    <div className={`px-4 py-4 ${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className="max-w-4xl mx-auto">
        <div className={`${themeClasses.glass} rounded-2xl p-2 shadow-sm`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2 ${themeClasses.surface} rounded-lg`}>
                <FileText size={16} className={themeClasses.textSecondary} />
              </div>
              <div className="flex flex-col">
                <span className={`text-sm font-medium ${themeClasses.text}`}>
                  {fileInfo.filename}
                </span>
                <div className="flex items-center space-x-2 mt-1">
                  <div className={`flex items-center space-x-1 text-xs ${themeClasses.textSecondary} ${themeClasses.surface} px-2 py-1 rounded-full`}>
                    <Database size={12} />
                    <span>{fileInfo.shape[0]} rows × {fileInfo.shape[1]} columns</span>
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full border border-green-200">
                    <CheckCircle size={12} />
                    <span className="font-medium">Loaded</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={onDebug}
                className={`flex items-center space-x-1 text-xs ${themeClasses.buttonSecondary} border px-3 py-2 rounded-xl hover:scale-105 transition-all duration-200 shadow-sm hover:shadow-md`}
                title="Debug session info"
              >
                <Bug size={12} />
                <span>Debug</span>
              </button>
              <button
                onClick={onSync}
                className="flex items-center space-x-1 text-xs bg-blue-500 text-white px-3 py-2 rounded-xl hover:bg-blue-600 hover:scale-105 transition-all duration-200 shadow-sm hover:shadow-md"
                title="Refresh session sync"
              >
                <RefreshCw size={12} />
                <span>Sync</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileInfo