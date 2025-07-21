import React from "react"
import { Loader2 } from "lucide-react"
import MessageItem from "./MessageItem"

const MessageTimeline = ({ 
  messages, 
  isAnalyzing, 
  expandedMessages, 
  toggleMessageExpansion, 
  messagesEndRef,
  onChatMessageClick,
  selectedChatMessage
}) => {
  return (
    <div className="space-y-6 pb-6">
      {/* Add some top padding for better visual spacing */}
      <div className="h-4"></div>
      
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          isExpanded={expandedMessages.has(message.id)}
          onToggleExpansion={toggleMessageExpansion}
          onChatMessageClick={onChatMessageClick}
          isSelected={selectedChatMessage === message.id}
        />
      ))}
      
      {isAnalyzing && (
        <div className="relative pl-6 pb-6 animate-in slide-in-from-left duration-300">
          <div className="absolute left-3 top-6 bottom-0 w-px bg-gray-300 dark:bg-gray-700"></div>
          <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-blue-500 dark:bg-blue-600 flex items-center justify-center text-white shadow-lg z-10">
            <Loader2 size={14} className="animate-spin" />
          </div>
          <div className="ml-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 transition-colors">
              <div className="text-blue-600 dark:text-blue-400 flex items-center gap-2 text-sm">
                <Loader2 size={16} className="animate-spin" />
                Analyzing your request...
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Bottom spacer to ensure last message is visible above input */}
      <div className="h-8"></div>
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageTimeline