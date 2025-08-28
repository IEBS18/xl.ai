"use client"

import { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileSpreadsheet, Loader2, CloudUpload, Files } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"

export function FileUpload({ onFileUpload, loading }) {
  const { themeClasses, isDark } = useTheme()
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileUpload(acceptedFiles)
      }
    },
    [onFileUpload],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    multiple: true,
    disabled: loading,
  })

  return (
    <div className="w-full max-w-2xl">
      <div className="text-center mb-8">
        <Files className="w-16 h-16 text-primary-500 mx-auto mb-4" />
        <h2 className={`text-2xl font-bold ${themeClasses.text} mb-2`}>Import Your Data</h2>
        <p className={themeClasses.textSecondary}>Upload multiple CSV or Excel files to start analyzing your data with AI-powered insights</p>
      </div>

      <div
        {...getRootProps()}
        className={`
          card p-12 text-center cursor-pointer transition-all duration-200 border-2 border-dashed
          ${isDragActive ? "border-primary-400 bg-primary-50 shadow-medium" : "border-gray-300 hover:border-primary-300 hover:shadow-medium"}
          ${loading ? "cursor-not-allowed opacity-50" : ""}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center space-y-4">
          {loading ? (
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
          ) : (
            <FileSpreadsheet className={`w-12 h-12 ${themeClasses.textSecondary}`} />
          )}

          <div>
            <h3 className={`text-lg font-semibold ${themeClasses.text} mb-2`}>
              {loading ? "Processing your files..." : isDragActive ? "Drop your files here" : "Choose files to upload"}
            </h3>
            <p className={`text-sm ${themeClasses.textSecondary} mb-4`}>
              {isDragActive ? "Release to upload your data files" : "Drag and drop your files here, or click to browse"}
            </p>
            <div className={`flex items-center justify-center space-x-4 text-xs ${themeClasses.textMuted}`}>
              <span className={`badge ${themeClasses.surface} ${themeClasses.textSecondary}`}>.CSV</span>
              <span className={`badge ${themeClasses.surface} ${themeClasses.textSecondary}`}>.XLSX</span>
              <span className={`badge ${themeClasses.surface} ${themeClasses.textSecondary}`}>.XLS</span>
            </div>
          </div>

          {!loading && (
            <button className="btn btn-primary px-6 py-2">
              <Upload className="w-4 h-4 mr-2" />
              Select Files
            </button>
          )}
        </div>
      </div>

      <div className={`mt-6 text-center text-xs ${themeClasses.textMuted}`}>
        <p>Your data is processed locally and securely.</p>
      </div>
    </div>
  )
}
