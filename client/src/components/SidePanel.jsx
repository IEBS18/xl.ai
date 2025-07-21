import React from "react"
import {
  Code,
  Database,
  Image,
  FileText,
  Copy,
  Download,
  Maximize2,
} from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
const SidePanel = ({ items, activeItem, onItemChange, selectedMessage, onClearSelection }) => {
  const { themeClasses } = useTheme()

  const getTabIcon = (type) => {
    switch (type) {
      case "code": return <Code className="w-4 h-4" />
      case "dataframe": return <Database className="w-4 h-4" />
      case "image": return <Image className="w-4 h-4" />
      case "report": return <FileText className="w-4 h-4" />
      default: return null
    }
  }

  const getTabLabel = (type) => {
    switch (type) {
      case "code": return "Code"
      case "dataframe": return "Data"
      case "image": return "Chart"
      case "report": return "Report"
      default: return "Unknown"
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const renderContent = (item) => {
    console.log(item.type, item.content)
    switch (item.type) {
      case "code":
        return (
          <div className="h-full flex flex-col">
            <div className={`flex items-center justify-between p-4 ${themeClasses.border} border-b`}>
              <h3 className={`font-medium ${themeClasses.text}`}>Generated Code</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => copyToClipboard(item.content)}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}
                  title="Copy code"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}>
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className={`${themeClasses.surface} rounded-lg p-4 overflow-x-auto`}>
                <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                  {item.content}
                </pre>
              </div>
            </div>
          </div>
        )

      case "image":
        return (
          <div className="h-full flex flex-col">
            <div className={`flex items-center justify-between p-4 ${themeClasses.border} border-b`}>
              <h3 className={`font-medium ${themeClasses.text}`}>Visualization</h3>
              <div className="flex items-center gap-2">
                <button className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}>
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}>
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center">
              <img
                src={item.content.data || "/placeholder.svg"}
                alt={item.content.filename}
                className="max-w-full max-h-full object-contain rounded-lg"
              />
            </div>
            {item.content.filename && (
              <div className={`p-4 ${themeClasses.border} border-t`}>
                <p className={`text-sm ${themeClasses.textSecondary}`}>{item.content.filename}</p>
              </div>
            )}
          </div>
        )

      case "dataframe":
        return (
          <div className="h-full flex flex-col">
            <div className={`flex items-center justify-between p-4 ${themeClasses.border} border-b`}>
              <div>
                <h3 className={`font-medium ${themeClasses.text}`}>Data Analysis</h3>
                <p className={`text-sm ${themeClasses.textSecondary}`}>
                  {item.content.shape[0]} rows × {item.content.shape[1]} columns
                </p>
              </div>
              <button className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}>
                <Download className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div
                className={`${themeClasses.surface} rounded-lg ${themeClasses.border} border`}
                dangerouslySetInnerHTML={{ __html: item.content.preview }}
              />
            </div>
          </div>
        )

      case "report":
        return (
          <div className="h-full flex flex-col">
            <div className={`flex items-center justify-between p-4 ${themeClasses.border} border-b`}>
              <h3 className={`font-medium ${themeClasses.text}`}>Analysis Report</h3>
              <div className="flex items-center gap-2">
                <button className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}>
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="prose prose-sm max-w-none">
                <div
                  className={`${themeClasses.text} focus:outline-none`}
                  contentEditable={true}
                  suppressContentEditableWarning={true}
                  dangerouslySetInnerHTML={{ __html: item.content }}
                  onBlur={(e) => {
                    // Update the content when user finishes editing
                    if (onContentChange) {
                      onContentChange(e.target.innerHTML);
                    }
                  }}
                  onInput={(e) => {
                    // Optional: Real-time updates as user types
                    // if (onContentChange) {
                    //   onContentChange(e.target.innerHTML);
                    // }
                  }}
                />
              </div>
            </div>
          </div>
        )

      default:
        return (
          <div className="h-full flex items-center justify-center p-4">
            <p className={themeClasses.textSecondary}>No content available</p>
          </div>
        )
    }
  }

  if (!items || items.length === 0) {
    return (
      <div className={`h-full flex flex-col ${themeClasses.bg} transition-colors`}>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <div className={`w-16 h-16 mx-auto mb-4 ${themeClasses.surface} rounded-full flex items-center justify-center`}>
              <Code className={`w-8 h-8 ${themeClasses.textSecondary}`} />
            </div>
            <p className={`text-sm font-medium ${themeClasses.text} mb-2`}>
              No outputs yet
            </p>
            <p className={`text-xs ${themeClasses.textSecondary}`}>
              {selectedMessage ? 'This query hasn\'t generated any outputs yet' : 'Run a query to see code, charts, and data here'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`h-full flex flex-col ${themeClasses.bg} transition-colors`}>
      {/* Header with context info */}
      {selectedMessage && (
        <div className={`p-4 ${themeClasses.border} border-b ${themeClasses.surface}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className={`text-sm font-medium ${themeClasses.text}`}>
                Query Results
              </span>
            </div>
            <button
              onClick={onClearSelection}
              className={`text-xs px-2 py-1 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surface} rounded-md transition-colors`}
            >
              Show All
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className={`${themeClasses.border} border-b ${themeClasses.surface}`}>
        <div className="flex overflow-x-auto">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => onItemChange(item.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${activeItem === item.id
                ? `border-black ${themeClasses.text} ${themeClasses.bg}`
                : `border-transparent ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary}`
                }`}
            >
              {getTabIcon(item.type)}
              {getTabLabel(item.type)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {items.map((item) => (
          <div
            key={item.id}
            className={`h-full ${activeItem === item.id ? 'block' : 'hidden'}`}
          >
            {renderContent(item)}
          </div>
        ))}
      </div>
    </div>
  )
}

export default SidePanel