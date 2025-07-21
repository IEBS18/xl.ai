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

const MessageItem = ({ message, isExpanded, onToggleExpansion, onChatMessageClick, isSelected }) => {
  const { type, content, isUser, isCompleted = true, id } = message
  const isCollapsible = shouldCollapseByDefault(type)
  const shouldShowContent = !isCollapsible || isExpanded
  const { themeClasses } = useTheme()

  const handleClick = () => {
    if (isUser && onChatMessageClick) {
      onChatMessageClick(id)
    }
  }

  const getStepIcon = (type, isCompleted) => {
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
      case "report":
        return <FileText size={14} />
      case "output":
        return <FileOutput size={14} />
      case "success":
        return <CheckCircle size={14} />
      case "error":
        return <AlertCircle size={14} />
      default:
        return <BarChart3 size={14} />
    }
  }

  const getStepLabel = (type, isCompleted) => {
    return type === "dataframe"
      ? "Data Analysis"
      : type === "image"
        ? "Visualization"
        : type === "report"
          ? "Strategic Report"
          : type === "code"
            ? "Generated Code"
            : type === "output"
              ? "Execution Output"
              : type === "status"
                ? isCompleted
                  ? "Completed"
                  : "Processing"
                : type
  }

  const getStepColorClass = (type, isCompleted) => {
    if (type === "success") return "bg-green-500"
    if (type === "error") return "bg-red-500"
    if (type === "status") return isCompleted ? "bg-green-500" : "bg-blue-500"
    return "bg-gray-500"
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 animate-in slide-in-from-right duration-300">
        <div className="flex items-start gap-3 max-w-2xl">
          <div 
            className={`${themeClasses.button} px-4 py-3 rounded-2xl shadow-sm cursor-pointer transition-all duration-200 hover:shadow-md ${
              isSelected ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-white dark:ring-offset-black' : ''
            }`}
            onClick={handleClick}
          >
            <div className="whitespace-pre-wrap">{content}</div>
          </div>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.button} flex items-center justify-center`}>
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative pl-6 pb-6 animate-in slide-in-from-left duration-300">
      {/* Timeline line */}
      <div className={`absolute left-3 top-6 bottom-0 w-px ${themeClasses.border.replace('border-', 'bg-')}`}></div>

      {/* Step indicator */}
      <div
        className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColorClass(type, isCompleted)} flex items-center justify-center text-white shadow-lg z-10 transition-colors`}
      >
        {getStepIcon(type, isCompleted)}
      </div>

      {/* Content */}
      <div className="ml-6">
        <div className={`${themeClasses.surface} rounded-xl shadow-sm ${themeClasses.border} border overflow-hidden transition-colors`}>
          {/* Header */}
          <div className={`${themeClasses.surfaceSecondary} px-4 py-3 ${themeClasses.border} border-b`}>
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
                    {getStepLabel(type, isCompleted)}
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

          {/* Body - Only show if expanded or not collapsible */}
          {shouldShowContent && (
            <div className="p-4">
              {(type === "system" ||
                type === "status" ||
                type === "success" ||
                type === "error" ||
                type === "output") && (
                  <div
                    className={`${type === "success"
                        ? "text-green-500"
                        : type === "error"
                          ? "text-red-500"
                          : type === "status"
                            ? isCompleted
                              ? "text-green-500"
                              : "text-blue-500"
                            : type === "output"
                              ? themeClasses.text
                              : themeClasses.text
                      } whitespace-pre-wrap text-sm ${type === "output" ? `font-mono ${themeClasses.surface} p-3 rounded-lg` : ""}`}
                  >
                    {content}
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