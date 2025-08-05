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
} from "lucide-react"
import { shouldCollapseByDefault, getStepColor, copyToClipboard, renderMarkdown } from "../utils/helpers"
import RichTextReport from "./RichTextReport"
import { useTheme } from "@/context/ThemeProvider"

const renderSafeContent = (value) => {
  if (typeof value === "string") return value
  if (typeof value === "object") return JSON.stringify(value, null, 2)
  return String(value)
}

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

  const getStepIcon = (type, isCompleted, queryCategory) => {
    if (type === "status") {
      return isCompleted ? <Check size={14} /> : <Loader2 size={14} className="animate-spin" />
    }
    switch (type) {
      case "code": return <Code size={14} />
      case "dataframe": return <Database size={14} />
      case "image": return <Image size={14} />
      case "report": return <FileText size={14} />
      case "output": return <FileOutput size={14} />
      case "success": return <CheckCircle size={14} />
      case "error": return <AlertCircle size={14} />
      default: return <BarChart3 size={14} />
    }
  }

  const getStepLabel = (type, isCompleted, queryCategory) => {
    return type === "dataframe"
      ? "Data Analysis"
      : type === "image"
        ? "Visualization"
        : type === "report"
          ? "Strategic Report"
          : type === "code"
            ? "Generated Code"
            : type === "output"
              ? "Analysis Result"
              : type === "status"
                ? isCompleted
                  ? "Completed"
                  : "Processing"
                : type
  }

  const getStepColorClass = (type, isCompleted, queryCategory) => {
    return isDark ? "bg-gray-600" : "bg-gray-700"
  }

  const getTextColorClass = (type) => {
    return themeClasses.text
  }

  const shouldUseClaudeStyle = (type, queryCategory) => {
    if (queryCategory === "conversational" || queryCategory === "textual_analytical") return true
    if (type === "output" && !queryCategory) return true
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

  if (isClaudeStyle) {
    return (
      <div className="flex justify-start mb-4 animate-in slide-in-from-left duration-300">
        <div className="flex items-start gap-3 max-w-2xl lg:max-w-4xl">
          <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center mt-1`}>
            <Bot className={`w-4 h-4 ${themeClasses.textSecondary}`} />
          </div>
          <div className={`px-0 py-0 rounded-2xl ${themeClasses.text} max-w-none`}>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {renderSafeContent(content)}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative pl-6 pb-6 animate-in slide-in-from-left duration-300">
      <div className={`absolute left-3 top-6 bottom-0 w-px ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}></div>
      <div className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColorClass(type, isCompleted, queryCategory)} flex items-center justify-center text-white shadow-lg z-10 transition-colors`}>
        {getStepIcon(type, isCompleted, queryCategory)}
      </div>
      <div className="ml-6">
        <div className={`${themeClasses.surface} rounded-xl shadow-sm border ${themeClasses.border} overflow-hidden transition-colors`}>
          <div className={`${themeClasses.surfaceSecondary} px-4 py-3 border-b ${themeClasses.border}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isCollapsible && (
                  <button onClick={() => onToggleExpansion(id)} className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}>
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
                {type === "code" && shouldShowContent && (
                  <button
                    onClick={() => copyToClipboard(content)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} p-1 rounded hover:${themeClasses.surfaceSecondary} transition-colors`}
                    title="Copy code"
                  >
                    <Copy size={14} />
                  </button>
                )}
              </div>
            </div>
          </div>
          {shouldShowContent && (
            <div className="p-4">
              {(type === "system" || type === "status" || type === "success" || type === "error" || type === "output") && (
                <div className={`${getTextColorClass(type)} whitespace-pre-wrap text-sm ${type === "output" ? `font-mono ${themeClasses.surface} p-3 rounded-lg border ${themeClasses.border}` : ""}`}>
                  {content}
                </div>
              )}
              {type === "code" && (
                <div className={`${themeClasses.surface} rounded-lg p-4 overflow-x-auto border ${themeClasses.border}`}>
                  <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                    {typeof content === "object" && content.code ? content.code : renderSafeContent(content)}
                  </pre>
                </div>
              )}
              {type === "dataframe" && content && (
                <div className="space-y-3">
                  {content.shape && (
                    <div className={`text-sm ${themeClasses.textSecondary}`}>
                      Shape: {content.shape[0]} rows × {content.shape[1]} columns
                    </div>
                  )}
                  {content.preview && (
                    <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto`} dangerouslySetInnerHTML={{ __html: content.preview }} />
                  )}
                </div>
              )}
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
              {type === "report" && content && (
                <div className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''}`}>
                  {typeof content === 'string' && content.includes('<!DOCTYPE html>') ? (
                    <div dangerouslySetInnerHTML={{ __html: content }} className={`report-content ${themeClasses.text}`} />
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
