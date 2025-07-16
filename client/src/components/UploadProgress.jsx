import React from "react"

const UploadProgress = ({ progress }) => {
  return (
    <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-800 rounded-full h-2 shadow-inner">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300 shadow-sm"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-400 mt-1 font-medium">Uploading... {progress}%</p>
      </div>
    </div>
  )
}

export default UploadProgress