import React from "react"
import {
  Code,
  Database,
  Image,
  FileText,
  FileOutput,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Check,
  Loader2,
  ChevronDown,
  ChevronRight,
  Copy,
  User,
  Bot,
  File,
  Download,
  Play,
  Zap,
  HelpCircle,
  ExternalLink
} from "lucide-react"
import { shouldCollapseByDefault, getStepColor, copyToClipboard, renderMarkdown } from "../utils/helpers"
import RichTextReport from "./RichTextReport"
import { useTheme } from "@/context/ThemeProvider"

const MessageItem = ({ message, isExpanded, onToggleExpansion, onChatMessageClick, isSelected }) => {
  const { type, content, isUser, isCompleted = true, id, queryCategory } = message
  const isCollapsible = shouldCollapseByDefault(type)
  const shouldShowContent = !isCollapsible || isExpanded
  const { themeClasses, isDark } = useTheme()

  const handleClick = () => {
    if (isUser && onChatMessageClick) {
      onChatMessageClick(id)
    }
  }

  // Helper functions
  const getStepIcon = (type, isCompleted, queryCategory) => {
    if (type === "status") {
      return isCompleted ? <Check size={14} /> : <Loader2 size={14} className="animate-spin" />
    }

    switch (type) {
      case "code":
        return <Code size={14} />
      case "dataframe":
        return <Database size={14} />
      case "image":
        return <Image size={14} />
      case "file":
        return <File size={14} />
      case "report":
        return <FileText size={14} />
      case "output":
      case "response":
        return <FileOutput size={14} />
      case "success":
        return <CheckCircle size={14} />
      case "error":
        return <AlertCircle size={14} />
      case "function_call":
        return <Play size={14} />
      case "step_start":
        return <Zap size={14} />
      case "warning":
        return <AlertCircle size={14} />
      case "system":
        return <BarChart3 size={14} />
      case "unknown":
        return <HelpCircle size={14} />
      default:
        return <BarChart3 size={14} />
    }
  }

  const getStepLabel = (type, isCompleted, queryCategory) => {
    switch (type) {
      case "dataframe":
        return "Data Analysis"
      case "image":
        return "Visualization"
      case "file":
        return "Generated File"
      case "report":
        return "Strategic Report"
      case "code":
        return "Generated Code"
      case "output":
        return "Analysis Result"
      case "response":
        return "Assistant Response"
      case "function_call":
        return "Function Call"
      case "step_start":
        return "Step Started"
      case "status":
        return isCompleted ? "Completed" : "Processing"
      case "warning":
        return "Warning"
      case "system":
        return "System Message"
      case "unknown":
        return "Unknown Message"
      default:
        return type.charAt(0).toUpperCase() + type.slice(1)
    }
  }

  const getStepColorClass = (type, isCompleted, queryCategory) => {
    // Color coding based on message type
    switch (type) {
      case "error":
        return "bg-red-600"
      case "success":
        return "bg-green-600"
      case "warning":
        return "bg-yellow-600"
      case "code":
        return "bg-blue-600"
      case "image":
        return "bg-purple-600"
      case "file":
        return "bg-orange-600"
      case "dataframe":
        return "bg-indigo-600"
      case "report":
        return "bg-emerald-600"
      case "function_call":
        return "bg-pink-600"
      case "step_start":
        return "bg-cyan-600"
      default:
        return isDark ? "bg-gray-600" : "bg-gray-700"
    }
  }

  const getTextColorClass = (type) => {
    return themeClasses.text
  }

  // Helper function to determine file type from filename or mime type
  const getFileType = (filename, mimeType) => {
    if (mimeType) {
      if (mimeType.startsWith('image/')) return 'image'
      if (mimeType.includes('pdf')) return 'pdf'
      if (mimeType.includes('text')) return 'text'
      if (mimeType.includes('csv')) return 'csv'
      if (mimeType.includes('json')) return 'json'
    }
    
    if (filename) {
      const ext = filename.toLowerCase().split('.').pop()
      switch (ext) {
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
        case 'svg':
          return 'image'
        case 'pdf':
          return 'pdf'
        case 'txt':
        case 'md':
          return 'text'
        case 'csv':
          return 'csv'
        case 'json':
          return 'json'
        case 'html':
          return 'html'
        default:
          return 'unknown'
      }
    }
    
    return 'unknown'
  }

  // Helper function to format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Claude-like styling determination
  const shouldUseClaudeStyle = (type, queryCategory) => {
    if (queryCategory === "conversational" || queryCategory === "textual_analytical") {
      return true
    }
    
    if ((type === "output" || type === "response") && !queryCategory) {
      return true
    }
    
    return false
  }

  const isClaudeStyle = shouldUseClaudeStyle(type, queryCategory)

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 animate-in slide-in-from-right duration-300">
        <div className="flex items-end gap-2 max-w-2xl">
          <div 
            className={`px-4 py-3 rounded-2xl max-w-xs lg:max-w-md xl:max-w-2xl ${themeClasses.button} shadow-sm cursor-pointer transition-all duration-200 hover:shadow-md ${
              isSelected ? `ring-2 ring-gray-400 ring-offset-2 ${isDark ? 'ring-offset-black' : 'ring-offset-white'}` : ''
            }`}
            onClick={handleClick}
          >
            <div className="whitespace-pre-wrap text-sm">{content}</div>
          </div>
        </div>
      </div>
    )
  }

  // Claude-style response for conversational and simple analytical queries
  if (isClaudeStyle) {
    return (
      <div className="flex justify-start mb-4 animate-in slide-in-from-left duration-300">
        <div className="flex items-start gap-3 max-w-2xl lg:max-w-4xl">
          <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center mt-1`}>
            <Bot className={`w-4 h-4 ${themeClasses.textSecondary}`} />
          </div>
          <div className={`px-0 py-0 rounded-2xl ${themeClasses.text} max-w-none`}>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {content}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Timeline style for complex analytical queries (enhanced)
  return (
    <div className="relative pl-6 pb-6 animate-in slide-in-from-left duration-300">
      {/* Timeline line */}
      <div className={`absolute left-3 top-6 bottom-0 w-px ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}></div>

      {/* Step indicator */}
      <div
        className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColorClass(type, isCompleted, queryCategory)} flex items-center justify-center text-white shadow-lg z-10 transition-colors`}
      >
        {getStepIcon(type, isCompleted, queryCategory)}
      </div>

      {/* Content */}
      <div className="ml-6">
        <div className={`${themeClasses.surface} rounded-xl shadow-sm border ${themeClasses.border} overflow-hidden transition-colors`}>
          {/* Header */}
          <div className={`${themeClasses.surfaceSecondary} px-4 py-3 border-b ${themeClasses.border}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isCollapsible && (
                  <button
                    onClick={() => onToggleExpansion(id)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                  >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                )}
                <div className="flex items-center gap-2">
                  <Bot className={`w-4 h-4 ${themeClasses.textSecondary}`} />
                  <span className={`${themeClasses.text} font-medium text-sm`}>
                    {getStepLabel(type, isCompleted, queryCategory)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {(type === "code" || type === "output") && shouldShowContent && (
                  <button
                    onClick={() => copyToClipboard(content)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} p-1 rounded hover:${themeClasses.surfaceSecondary} transition-colors`}
                    title="Copy content"
                  >
                    <Copy size={14} />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Body - Only show if expanded or not collapsible */}
          {shouldShowContent && (
            <div className="p-4">
              {/* Handle text-based content */}
              {(type === "system" ||
                type === "status" ||
                type === "success" ||
                type === "error" ||
                type === "warning" ||
                type === "output" ||
                type === "response" ||
                type === "step_start" ||
                type === "unknown") && (
                  <div
                    className={`${getTextColorClass(type)} whitespace-pre-wrap text-sm ${
                      (type === "output" || type === "response") 
                        ? `font-mono ${themeClasses.surface} p-3 rounded-lg border ${themeClasses.border}` 
                        : ""
                    } ${
                      type === "error" || type === "warning"
                        ? "text-red-600 dark:text-red-400"
                        : ""
                    } ${
                      type === "unknown"
                        ? "text-orange-600 dark:text-orange-400 italic"
                        : ""
                    }`}
                  >
                    {content}
                  </div>
                )}

              {/* Handle code content */}
              {type === "code" && (
                <div className={`${themeClasses.surface} rounded-lg p-4 overflow-x-auto border ${themeClasses.border}`}>
                  <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                    {content}
                  </pre>
                </div>
              )}

              {/* Handle function call content */}
              {type === "function_call" && content && (
                <div className="space-y-3">
                  <div className={`${themeClasses.surface} rounded-lg p-4 border ${themeClasses.border}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Play className="w-4 h-4 text-pink-600" />
                      <span className="font-medium">Function Call</span>
                    </div>
                    {message.functionInfo && (
                      <div className="space-y-2">
                        <div><strong>Name:</strong> {message.functionInfo.name}</div>
                        {message.functionInfo.arguments && (
                          <div>
                            <strong>Arguments:</strong>
                            <pre className="mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                              {JSON.stringify(message.functionInfo.arguments, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Handle dataframe content */}
              {type === "dataframe" && content && (
                <div className="space-y-3">
                  {content.shape && (
                    <div className={`text-sm ${themeClasses.textSecondary}`}>
                      Shape: {content.shape[0]} rows × {content.shape[1]} columns
                    </div>
                  )}
                  {content.preview && (
                    <div
                      className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto`}
                      dangerouslySetInnerHTML={{ __html: content.preview }}
                    />
                  )}
                </div>
              )}

              {/* Handle image content */}
              {type === "image" && content && (
                <div className="space-y-3">
                  <div className={`flex items-center justify-center p-4 ${themeClasses.surface} rounded-lg`}>
                    <img
                      src={content.data || content.path || "/placeholder.svg"}
                      alt={content.filename || "Generated visualization"}
                      className="max-w-full h-auto rounded-lg shadow-sm"
                      onError={(e) => {
                        e.target.src = "/placeholder.svg"
                        e.target.alt = "Image failed to load"
                      }}
                    />
                  </div>
                  {content.filename && (
                    <div className={`text-sm ${themeClasses.textSecondary} text-center`}>
                      {content.filename}
                    </div>
                  )}
                </div>
              )}

              {/* Handle report content */}
              {type === "report" && content && (
                <div className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''}`}>
                  {typeof content === 'string' && content.includes('<!DOCTYPE html>') ? (
                    <div
                      dangerouslySetInnerHTML={{ __html: content }}
                      className={`report-content ${themeClasses.text}`}
                    />
                  ) : (
                    <div className={`whitespace-pre-wrap ${themeClasses.text}`}>
                      {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MessageItem