import React from "react"
import {
  Code,
  Database,
  ImageIcon,
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
} from "lucide-react"
import { shouldCollapseByDefault, getStepColor, copyToClipboard, renderMarkdown } from "../utils/helpers"

const MessageItem = ({ message, isExpanded, onToggleExpansion }) => {
  const { type, content, isUser, isCompleted = true, id } = message
  const isCollapsible = shouldCollapseByDefault(type)
  const shouldShowContent = !isCollapsible || isExpanded

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
        return <ImageIcon size={14} />
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

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 animate-fadeIn">
        <div className="bg-white text-gray-900 px-4 py-3 rounded-xl max-w-xl shadow-lg border border-gray-200">
          {content}
        </div>
      </div>
    )
  }

  return (
    <div className="relative pl-6 pb-6 animate-slideIn">
      {/* Timeline line */}
      <div className="absolute left-3 top-6 bottom-0 w-px bg-gray-700"></div>

      {/* Step indicator */}
      <div
        className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColor(type, isCompleted)} flex items-center justify-center text-white shadow-lg z-10`}
      >
        {getStepIcon(type, isCompleted)}
      </div>

      {/* Content */}
      <div className="ml-6">
        <div className="bg-gray-900 rounded-xl shadow-xl border border-gray-800 overflow-hidden">
          {/* Header */}
          <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isCollapsible && (
                  <button
                    onClick={() => onToggleExpansion(id)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                )}
                <span className="text-white font-medium capitalize flex items-center gap-2 text-sm">
                  {getStepIcon(type, isCompleted)}
                  {getStepLabel(type, isCompleted)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {type === "code" && shouldShowContent && (
                  <button
                    onClick={() => copyToClipboard(content)}
                    className="text-gray-400 hover:text-white p-1 rounded hover:bg-gray-700 transition-colors"
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
              {type === "code" && (
                <div className="bg-gray-950 rounded-lg p-3 overflow-x-auto">
                  <pre className="text-green-400 text-sm whitespace-pre-wrap font-mono">{content}</pre>
                </div>
              )}

              {type === "dataframe" && (
                <div>
                  <div className="mb-3">
                    <p className="text-gray-300 text-sm">
                      Shape: {content.shape[0]} rows × {content.shape[1]} columns
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3 overflow-x-auto">
                    <div dangerouslySetInnerHTML={{ __html: content.preview }} />
                  </div>
                </div>
              )}

              {type === "image" && (
                <div className="text-center">
                  <img
                    src={content.data || "/placeholder.svg"}
                    alt={content.filename}
                    className="max-w-full h-auto rounded-lg shadow-lg mx-auto"
                  />
                  <p className="text-gray-400 text-sm mt-2">{content.filename}</p>
                </div>
              )}

              {type === "report" && (
                <div className="prose prose-invert max-w-none">
                  <div
                    className="text-gray-300 leading-relaxed text-sm"
                    dangerouslySetInnerHTML={{ __html: `<p class="mb-3">${renderMarkdown(content)}</p>` }}
                  />
                </div>
              )}

              {(type === "system" ||
                type === "status" ||
                type === "success" ||
                type === "error" ||
                type === "output") && (
                <div
                  className={`${
                    type === "success"
                      ? "text-green-400"
                      : type === "error"
                      ? "text-red-400"
                      : type === "status"
                      ? isCompleted
                        ? "text-green-400"
                        : "text-blue-400"
                      : type === "output"
                      ? "text-cyan-400"
                      : "text-gray-300"
                  } whitespace-pre-wrap text-sm ${type === "output" ? "font-mono" : ""}`}
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