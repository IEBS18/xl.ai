import React, { useState, useEffect } from "react"
import { 
  X, 
  Code, 
  Image, 
  Database, 
  FileText, 
  File,
  Copy,
  Download,
  ExternalLink,
  Maximize2,
  ChevronDown,
  ChevronRight
} from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
import { copyToClipboard } from "../utils/helpers"

const SidePanel = ({ 
  items = [], 
  activeItem, 
  onItemChange, 
  selectedMessage, 
  onClose,
  onUpdateItem 
}) => {
  const { themeClasses, isDark } = useTheme()
  const [expandedSections, setExpandedSections] = useState(new Set())

  // Auto-expand first item if none expanded
  useEffect(() => {
    if (items.length > 0 && expandedSections.size === 0) {
      setExpandedSections(new Set([items[0].id]))
    }
  }, [items])

  // Auto-select first item if none selected
  useEffect(() => {
    if (items.length > 0 && !activeItem) {
      onItemChange?.(items[0].id)
    }
  }, [items, activeItem, onItemChange])

  const toggleSection = (itemId) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId)
    } else {
      newExpanded.add(itemId)
    }
    setExpandedSections(newExpanded)
  }

  const getItemIcon = (type) => {
    switch (type) {
      case 'code':
        return <Code className="w-4 h-4" />
      case 'image':
        return <Image className="w-4 h-4" />
      case 'dataframe':
        return <Database className="w-4 h-4" />
      case 'report':
        return <FileText className="w-4 h-4" />
      case 'file':
        return <File className="w-4 h-4" />
      default:
        return <File className="w-4 h-4" />
    }
  }

  const getItemLabel = (type) => {
    switch (type) {
      case 'code':
        return 'Generated Code'
      case 'image':
        return 'Visualization'
      case 'dataframe':
        return 'Data Table'
      case 'report':
        return 'Report'
      case 'file':
        return 'Generated File'
      default:
        return 'Item'
    }
  }

  const getItemColor = (type) => {
    switch (type) {
      case 'code':
        return 'text-blue-600 dark:text-blue-400'
      case 'image':
        return 'text-purple-600 dark:text-purple-400'
      case 'dataframe':
        return 'text-green-600 dark:text-green-400'
      case 'report':
        return 'text-orange-600 dark:text-orange-400'
      case 'file':
        return 'text-gray-600 dark:text-gray-400'
      default:
        return themeClasses.textSecondary
    }
  }

  const renderCodeContent = (item, isExpanded) => {
    const getCodeContent = (content) => {
      if (typeof content === "string") return content
      if (typeof content === "object" && content !== null) {
        if (content.code) return content.code
        return JSON.stringify(content, null, 2)
      }
      return String(content)
    }

    const codeContent = getCodeContent(item.content)

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Code Preview</span>
          </button>
          <button
            onClick={() => copyToClipboard(codeContent)}
            className={`p-1 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded transition-colors`}
            title="Copy code"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-hidden`}>
            <div className="max-h-96 overflow-y-auto">
              <pre className={`p-4 text-xs ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                {codeContent}
              </pre>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderImageContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Visualization</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4`}>
            <div className="flex justify-center">
              <img
                src={item.content?.data || item.content?.path || "/placeholder.svg"}
                alt={item.content?.filename || "Generated visualization"}
                className="max-w-full h-auto rounded-lg shadow-sm"
                onError={(e) => {
                  e.target.src = "/placeholder.svg"
                  e.target.alt = "Image failed to load"
                }}
              />
            </div>
            {item.content?.filename && (
              <div className={`text-xs ${themeClasses.textSecondary} text-center mt-2`}>
                {item.content.filename}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderDataframeContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Data Table</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className="space-y-2">
            {item.content?.shape && (
              <div className={`text-xs ${themeClasses.textSecondary}`}>
                Shape: {item.content.shape[0]} rows × {item.content.shape[1]} columns
              </div>
            )}
            {item.content?.preview && (
              <div
                className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto max-h-96 overflow-y-auto`}
                dangerouslySetInnerHTML={{ __html: item.content.preview }}
              />
            )}
          </div>
        )}
      </div>
    )
  }

  const renderReportContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Report</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4 max-h-96 overflow-y-auto`}>
            {typeof item.content === 'string' && item.content.includes('<!DOCTYPE html>') ? (
              <div
                dangerouslySetInnerHTML={{ __html: item.content }}
                className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''} ${themeClasses.text}`}
              />
            ) : (
              <div className={`text-sm ${themeClasses.text} whitespace-pre-wrap`}>
                {typeof item.content === 'string' ? item.content : JSON.stringify(item.content, null, 2)}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderFileContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Generated File</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4`}>
            <div className={`text-sm ${themeClasses.text}`}>
              {item.content?.filename && (
                <div className="mb-2">
                  <strong>Filename:</strong> {item.content.filename}
                </div>
              )}
              {item.content?.size && (
                <div className="mb-2">
                  <strong>Size:</strong> {item.content.size}
                </div>
              )}
              {item.content?.path && (
                <button
                  onClick={() => window.open(item.content.path, '_blank')}
                  className={`flex items-center gap-2 mt-2 px-3 py-1 ${themeClasses.button} rounded-lg text-sm transition-colors`}
                >
                  <ExternalLink className="w-4 h-4" />
                  Open File
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderContent = (item) => {
    const isExpanded = expandedSections.has(item.id)
    
    switch (item.type) {
      case 'code':
        return renderCodeContent(item, isExpanded)
      case 'image':
        return renderImageContent(item, isExpanded)
      case 'dataframe':
        return renderDataframeContent(item, isExpanded)
      case 'report':
        return renderReportContent(item, isExpanded)
      case 'file':
        return renderFileContent(item, isExpanded)
      default:
        return (
          <div className={`text-sm ${themeClasses.textSecondary}`}>
            Content type not supported: {item.type}
          </div>
        )
    }
  }

  if (items.length === 0) {
    return null
  }

  return (
    <div className={`h-full flex flex-col ${themeClasses.bg} ${themeClasses.border} border-l transition-colors`}>
      {/* Header with close button */}
      <div className={`p-4 ${themeClasses.border} border-b ${themeClasses.surface}`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className={`font-semibold ${themeClasses.text} text-sm`}>Analysis Details</h3>
            <p className={`text-xs ${themeClasses.textSecondary} mt-1`}>
              {items.length} component{items.length !== 1 ? 's' : ''} generated
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors`}
            title="Close panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-6">
          {items.map((item, index) => (
            <div
              key={item.id}
              className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-hidden transition-colors`}
            >
              {/* Item Header */}
              <div className={`p-3 ${themeClasses.surfaceSecondary} border-b ${themeClasses.border}`}>
                <div className="flex items-center gap-2">
                  <div className={getItemColor(item.type)}>
                    {getItemIcon(item.type)}
                  </div>
                  <span className={`font-medium text-sm ${themeClasses.text}`}>
                    {getItemLabel(item.type)}
                  </span>
                  <span className={`text-xs ${themeClasses.textSecondary} ml-auto`}>
                    #{index + 1}
                  </span>
                </div>
              </div>

              {/* Item Content */}
              <div className="p-3">
                {renderContent(item)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className={`p-3 ${themeClasses.border} border-t ${themeClasses.surface}`}>
        <div className={`text-xs ${themeClasses.textSecondary} text-center`}>
          Click components in the answer to view details
        </div>
      </div>
    </div>
  )
}

export default SidePanel

  const renderCodeContent = (item, isExpanded) => {
    const getCodeContent = (content) => {
      if (typeof content === "string") return content
      if (typeof content === "object" && content !== null) {
        if (content.code) return content.code
        return JSON.stringify(content, null, 2)
      }
      return String(content)
    }

    const codeContent = getCodeContent(item.content)

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Code Preview</span>
          </button>
          <button
            onClick={() => copyToClipboard(codeContent)}
            className={`p-1 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded transition-colors`}
            title="Copy code"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-hidden`}>
            <div className="max-h-96 overflow-y-auto">
              <pre className={`p-4 text-xs ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                {codeContent}
              </pre>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderImageContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Visualization</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4`}>
            <div className="flex justify-center">
              <img
                src={item.content?.data || item.content?.path || "/placeholder.svg"}
                alt={item.content?.filename || "Generated visualization"}
                className="max-w-full h-auto rounded-lg shadow-sm"
                onError={(e) => {
                  e.target.src = "/placeholder.svg"
                  e.target.alt = "Image failed to load"
                }}
              />
            </div>
            {item.content?.filename && (
              <div className={`text-xs ${themeClasses.textSecondary} text-center mt-2`}>
                {item.content.filename}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderDataframeContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Data Table</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className="space-y-2">
            {item.content?.shape && (
              <div className={`text-xs ${themeClasses.textSecondary}`}>
                Shape: {item.content.shape[0]} rows × {item.content.shape[1]} columns
              </div>
            )}
            {item.content?.preview && (
              <div
                className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto max-h-96 overflow-y-auto`}
                dangerouslySetInnerHTML={{ __html: item.content.preview }}
              />
            )}
          </div>
        )}
      </div>
    )
  }

  const renderReportContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Report</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4 max-h-96 overflow-y-auto`}>
            {typeof item.content === 'string' && item.content.includes('<!DOCTYPE html>') ? (
              <div
                dangerouslySetInnerHTML={{ __html: item.content }}
                className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''} ${themeClasses.text}`}
              />
            ) : (
              <div className={`text-sm ${themeClasses.text} whitespace-pre-wrap`}>
                {typeof item.content === 'string' ? item.content : JSON.stringify(item.content, null, 2)}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderFileContent = (item, isExpanded) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => toggleSection(item.id)}
            className={`flex items-center gap-2 ${themeClasses.text} hover:${themeClasses.textSecondary} transition-colors`}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <span className="text-sm font-medium">Generated File</span>
          </button>
        </div>
        
        {isExpanded && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4`}>
            <div className={`text-sm ${themeClasses.text}`}>
              {item.content?.filename && (
                <div className="mb-2">
                  <strong>Filename:</strong> {item.content.filename}
                </div>
              )}
              {item.content?.size && (
                <div className="mb-2">
                  <strong>Size:</strong> {item.content.size}
                </div>
              )}
              {item.content?.path && (
                <button
                  onClick={() => window.open(item.content.path, '_blank')}
                  className={`flex items-center gap-2 mt-2 px-3 py-1 ${themeClasses.button} rounded-lg text-sm transition-colors`}
                >
                  <ExternalLink className="w-4 h-4" />
                  Open File
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderContent = (item) => {
    const isExpanded = expandedSections.has(item.id)
    
    switch (item.type) {
      case 'code':
        return renderCodeContent(item, isExpanded)
      case 'image':
        return renderImageContent(item, isExpanded)
      case 'dataframe':
        return renderDataframeContent(item, isExpanded)
      case 'report':
        return renderReportContent(item, isExpanded)
      case 'file':
        return renderFileContent(item, isExpanded)
      default:
        return (
          <div className={`text-sm ${themeClasses.textSecondary}`}>
            Content type not supported: {item.type}
          </div>
        )
    }
  }