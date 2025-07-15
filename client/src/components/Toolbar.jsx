"use client"

import { Download, MessageSquare, Database, Wifi, WifiOff } from "lucide-react"

export function Toolbar({ data, onExport, onToggleChat, chatOpen, connected }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Database className="w-6 h-6 text-primary-600" />
            <h1 className="text-xl font-bold text-gray-900">DataFlow Pro</h1>
          </div>

          {data && (
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="font-medium">{data.filename}</span>
              <span className="text-gray-400">•</span>
              <span>{data.shape[0].toLocaleString()} rows</span>
              <span className="text-gray-400">•</span>
              <span>{data.shape[1]} columns</span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {connected ? <Wifi className="w-4 h-4 text-green-500" /> : <WifiOff className="w-4 h-4 text-red-500" />}
            <span className={`text-xs font-medium ${connected ? "text-green-600" : "text-red-600"}`}>
              {connected ? "Connected" : "Disconnected"}
            </span>
          </div>

          {/* Export Button */}
          {data && (
            <button onClick={onExport} className="btn btn-secondary px-3 py-2">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          )}

          {/* Chat Toggle */}
          <button onClick={onToggleChat} className={`btn px-3 py-2 ${chatOpen ? "btn-primary" : "btn-secondary"}`}>
            <MessageSquare className="w-4 h-4 mr-2" />
            {chatOpen ? "Close AI" : "Open AI"}
          </button>
        </div>
      </div>
    </header>
  )
}
