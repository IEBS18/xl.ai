import React from "react"

const ConnectionStatus = ({ isConnected }) => {
  return (
    <div className="flex items-center space-x-2">
      <div
        className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"} shadow-lg animate-pulse`}
      ></div>
      <span className="text-xs font-medium text-gray-300">
        {isConnected ? "Connected" : "Disconnected"}
      </span>
    </div>
  )
}

export default ConnectionStatus