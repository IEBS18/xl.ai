import React from "react"
import { FileText } from "lucide-react"

const FileInfo = ({ fileInfo, onDebug, onSync }) => {
  return (
    <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText size={16} className="text-gray-400" />
          <span className="text-sm font-medium text-gray-300">{fileInfo.filename}</span>
          <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded-full shadow-sm border border-gray-700">
            {fileInfo.shape[0]} rows × {fileInfo.shape[1]} columns
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onDebug}
            className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded hover:bg-gray-600 transition-colors shadow-sm border border-gray-600"
            title="Debug session info"
          >
            Debug
          </button>
          <button
            onClick={onSync}
            className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 transition-colors shadow-sm"
            title="Refresh session sync"
          >
            Sync
          </button>
          <span className="text-xs text-green-400 font-semibold bg-green-900 px-2 py-1 rounded-full border border-green-700">
            Loaded
          </span>
        </div>
      </div>
    </div>
  )
}

export default FileInfo