import React, { useState, useCallback, useRef, useEffect } from "react"
import ReactMarkdown from 'react-markdown';
import {
  Code,
  Image,
  Database,
  FileText,
  File,
  Loader2,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Bot,
  User,
  Copy,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  X,
  LayoutDashboard,
  Plus
} from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"
import { copyToClipboard } from "../utils/helpers"
import { BACKEND_URL } from "../utils/constants"
import InputArea from "./InputArea"
import FileInfo from "./FileInfo"
import UploadProgress from "./UploadProgress"
import FilePreviewModal from "./FilePreviewModal"

const ChatInterface = ({
  messages,
  isAnalyzing,
  isConnected,
  fileUploaded,
  fileInfo,
  onSendMessage,
  messagesEndRef,
  expandedMessages,
  toggleMessageExpansion,
  uploadProgress,
  fileInputRef,
  handleFileUpload,
  triggerFileUpload,
  debugSession,
  manualSessionSync,
  onUpdateMessage,
  sessionId,
  currentQueryCategory,
  isFileProcessing, // New prop for file processing state
  setFileProcessingState // New prop to control file processing state
}) => {
  const [activeSidePanel, setActiveSidePanel] = useState(null)
  const [selectedQueryId, setSelectedQueryId] = useState(null)
  const [selectedComponentId, setSelectedComponentId] = useState(null)
  const [sidePanelOpen, setSidePanelOpen] = useState(false)
  const [chatPanelWidth, setChatPanelWidth] = useState(65)
  const [isDragging, setIsDragging] = useState(false)
  const [isFilePreviewModalOpen, setIsFilePreviewModalOpen] = useState(false)
  const containerRef = useRef(null)
  const { themeClasses, isDark } = useTheme()

  // Process messages into query groups (user message + all related responses)
  const processMessagesIntoQueries = (messages) => {
    const queries = []
    let currentQuery = null

    messages.forEach(message => {
      if (message.isUser) {
        // Start new query
        if (currentQuery) {
          queries.push(currentQuery)
        }
        currentQuery = {
          id: message.id,
          userMessage: message,
          responses: [],
          steps: [],
          finalAnswer: null,
          queryCategory: message.queryCategory
        }
      } else if (currentQuery) {
        // Add to current query
        if (message.type === 'output' || message.type === 'response') {
          currentQuery.finalAnswer = message
        } else if (['code', 'image', 'dataframe', 'report', 'file'].includes(message.type)) {
          currentQuery.responses.push(message)
        } else {
          currentQuery.steps.push(message)
        }
      }
    })

    if (currentQuery) {
      queries.push(currentQuery)
    }

    return queries
  }

  const queries = processMessagesIntoQueries(messages)

  // Get side panel items for a specific component
  const getSidePanelItemsForComponent = (componentId) => {
    if (!componentId) return []

    // Find the specific component across all queries
    for (const query of queries) {
      const allComponents = [...query.responses, ...query.steps]
      const component = allComponents.find(item => item.id === componentId)
      if (component) {
        return [component] // Return only the specific component
      }
    }

    return []
  }

  // Handle component click from answer
  const handleComponentClick = (queryId, componentType, componentId) => {
    setSelectedQueryId(queryId)
    setSelectedComponentId(componentId)
    setSidePanelOpen(true)
    setActiveSidePanel(componentId)
  }

  // Enhanced file upload handler with processing state
  const handleEnhancedFileUpload = useCallback(async (event) => {
    try {
      // Set processing state to true when upload starts
      if (setFileProcessingState) {
        setFileProcessingState(true)
      }

      // Call the original file upload handler
      await handleFileUpload(event)
      
      // Note: Don't set processing to false here - 
      // it will be automatically set to false when 
      // assistant_upload_complete event is received in useMessages
    } catch (error) {
      console.error('File upload failed:', error)
      // Reset processing state on error
      if (setFileProcessingState) {
        setFileProcessingState(false)
      }
    }
  }, [handleFileUpload, setFileProcessingState])

  // Enhanced trigger file upload
  const handleEnhancedTriggerFileUpload = useCallback(() => {
    // Only trigger if not currently processing
    if (!isFileProcessing) {
      triggerFileUpload()
    }
  }, [triggerFileUpload, isFileProcessing])

  // Handle file preview
  const handleShowFilePreview = useCallback(() => {
    if (!fileInfo || isFileProcessing) return

    // Open the file preview modal
    setIsFilePreviewModalOpen(true)
  }, [fileInfo, isFileProcessing])

  // Handle file removal
  const handleRemoveFile = useCallback(() => {
    if (isFileProcessing) {
      // If currently processing, ask for confirmation
      if (window.confirm('File is currently being processed. Are you sure you want to remove it?')) {
        // Reset processing state
        if (setFileProcessingState) {
          setFileProcessingState(false)
        }
        // Close any related previews
        if (sidePanelOpen && selectedComponentId && selectedComponentId.startsWith('file-preview-')) {
          handleCloseSidePanel()
        }
        console.log('File removed during processing')
      }
    } else {
      // Normal removal
      if (window.confirm('Remove the uploaded file?')) {
        // Close any related previews
        if (sidePanelOpen && selectedComponentId && selectedComponentId.startsWith('file-preview-')) {
          handleCloseSidePanel()
        }
        console.log('File removed')
      }
    }
  }, [isFileProcessing, setFileProcessingState, sidePanelOpen, selectedComponentId])

  // Handle closing side panel
  const handleCloseSidePanel = () => {
    setSidePanelOpen(false)
    setSelectedQueryId(null)
    setSelectedComponentId(null)
    setActiveSidePanel(null)
  }

  // Handle updating a specific message/item content
  const handleUpdateItem = useCallback((itemId, newContent) => {
    if (onUpdateMessage) {
      onUpdateMessage(itemId, { content: newContent })
    }
  }, [onUpdateMessage])

  // Enhanced sample questions based on query categories
  const enhancedSampleQuestions = [
    {
      question: "Hi, what can you help me with?",
      category: "conversational",
      description: "Start a conversation"
    },
    {
      question: "What capabilities do you have?",
      category: "conversational",
      description: "Learn about features"
    },
    {
      question: "What is the average sales value?",
      category: "textual_analytical",
      description: "Quick data answer"
    },
    {
      question: "How many rows are in my dataset?",
      category: "textual_analytical",
      description: "Simple data query"
    },
    {
      question: "What's the maximum revenue?",
      category: "textual_analytical",
      description: "Find maximum value"
    },
    {
      question: "Generate a comprehensive sales analysis",
      category: "fully_analytical",
      description: "Detailed analysis with charts"
    },
    {
      question: "Create a 12-month forecast model",
      category: "fully_analytical",
      description: "Predictive modeling"
    },
    {
      question: "Show me trends and correlations in the data",
      category: "fully_analytical",
      description: "Pattern analysis"
    }
  ]

  // Handle mouse down on resize handle
  const handleMouseDown = useCallback((e) => {
    setIsDragging(true)
    e.preventDefault()
  }, [])

  // Handle mouse move during drag
  const handleMouseMove = useCallback((e) => {
    if (!isDragging || !containerRef.current) return

    const containerRect = containerRef.current.getBoundingClientRect()
    const newChatWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100

    const constrainedWidth = Math.min(Math.max(newChatWidth, 45), 75)
    setChatPanelWidth(constrainedWidth)
  }, [isDragging])

  // Handle mouse up to stop dragging
  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Add event listeners for mouse move and up
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className={`flex h-full ${themeClasses.bg} transition-colors`}>
      {/* Main Chat Area */}
      <div
        className="flex flex-col transition-all duration-300"
        style={{
          width: sidePanelOpen ? `${chatPanelWidth}%` : '100%'
        }}
      >
        {/* Messages Area - Scrollable with explicit height */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {/* Header padding to prevent content being covered */}
          <div className="h-16"></div>
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <PerplexityMessageTimeline
              queries={queries}
              isAnalyzing={isAnalyzing}
              expandedMessages={expandedMessages}
              toggleMessageExpansion={toggleMessageExpansion}
              messagesEndRef={messagesEndRef}
              onComponentClick={handleComponentClick}
              currentQueryCategory={currentQueryCategory}
            />
          </div>
        </div>

        {/* Bottom UI Elements - Fixed at bottom */}
        <div className={`flex-shrink-0 ${themeClasses.border} border-t transition-colors`}>
          {/* Enhanced Sample Questions */}
          {fileUploaded && messages.filter((m) => m.isUser).length === 0 && (
            <EnhancedSampleQuestions
              questions={enhancedSampleQuestions}
              onSelectQuestion={(question) => onSendMessage(question)}
            />
          )}

          {/* Upload Progress */}
          {uploadProgress > 0 && <UploadProgress progress={uploadProgress} />}

          {/* Input Area - Always visible at bottom with enhanced file processing */}
          {fileUploaded && (
            <InputArea
              isConnected={isConnected}
              isAnalyzing={isAnalyzing}
              onSendMessage={onSendMessage}
              onFileUpload={handleEnhancedTriggerFileUpload}
              fileInfo={fileInfo}
              onShowFilePreview={handleShowFilePreview}
              onRemoveFile={handleRemoveFile}
              isFileProcessing={isFileProcessing} // Pass the processing state
            />
          )}
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleEnhancedFileUpload}
          className="hidden"
        />
      </div>
      {/* Resize Handle */}
      {sidePanelOpen && (
        <div
          className={`w-1 ${themeClasses.border} border-l hover:bg-blue-500/20 cursor-col-resize flex-shrink-0 relative group transition-colors duration-200`}
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-y-0 left-1/2 w-0.5 bg-transparent group-hover:bg-blue-500/40 transition-colors duration-200 transform -translate-x-1/2"></div>
          <div className="absolute inset-y-0 -left-2 -right-2 cursor-col-resize"></div>
        </div>
      )}

      {/* Side Panel - Only when open */}
      {sidePanelOpen && (
        <div
          className={`${themeClasses.border} transition-all duration-300 ${themeClasses.bg} flex-shrink-0`}
          style={{
            width: `${100 - chatPanelWidth}%`
          }}
        >
          <EnhancedSidePanel
            items={getSidePanelItemsForComponent(selectedComponentId)}
            activeItem={activeSidePanel}
            onItemChange={setActiveSidePanel}
            selectedMessage={selectedQueryId}
            onClose={handleCloseSidePanel}
            onUpdateItem={handleUpdateItem}
          />
        </div>
      )}

      {/* File Preview Modal */}
      <FilePreviewModal
        isOpen={isFilePreviewModalOpen}
        onClose={() => setIsFilePreviewModalOpen(false)}
        fileInfo={fileInfo}
      />
    </div>
  )
}

// New Perplexity-style Message Timeline Component
const PerplexityMessageTimeline = ({
  queries,
  isAnalyzing,
  expandedMessages,
  toggleMessageExpansion,
  messagesEndRef,
  onComponentClick,
  currentQueryCategory
}) => {
  const { themeClasses } = useTheme()

  const getAnalyzingMessage = (category) => {
    switch (category) {
      case "conversational":
        return "Thinking about your message..."
      case "textual_analytical":
        return "Analyzing your data quickly..."
      case "fully_analytical":
        return "Performing comprehensive analysis..."
      default:
        return "Processing your request..."
    }
  }

  return (
    <div className="space-y-8 pb-6">
      {/* Top padding */}
      <div className="h-4"></div>

      {/* Render all query groups */}
      {queries.map((query, index) => (
        <PerplexityQueryGroup
          key={query.id}
          query={query}
          onComponentClick={onComponentClick}
          expandedMessages={expandedMessages}
          toggleMessageExpansion={toggleMessageExpansion}
        />
      ))}

      {/* Analyzing indicator */}
      {isAnalyzing && (
        <div className="animate-in slide-in-from-left duration-300">
          <div className="flex justify-start mb-6">
            <div className="flex items-start gap-3 max-w-2xl">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center`}>
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
              <div className={`px-4 py-3 rounded-2xl shadow-sm border ${themeClasses.surface} ${themeClasses.border} ${themeClasses.text}`}>
                <span className="text-sm">{getAnalyzingMessage(currentQueryCategory)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom spacer */}
      <div className="h-8"></div>

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}

// Individual Query Group Component (User message + Answer/Steps)
const PerplexityQueryGroup = ({ query, onComponentClick, expandedMessages, toggleMessageExpansion }) => {
  const [activeTab, setActiveTab] = useState('answer')
  const { themeClasses, isDark } = useTheme()

  const hasSteps = query.steps.length > 0
  const hasComponents = query.responses.length > 0

  return (
    <div className="space-y-4">
      {/* User Message */}
      <div className="flex justify-end mb-4 animate-in slide-in-from-right duration-300">
        <div className="flex items-end gap-2 max-w-2xl">
          <div className={`px-4 py-3 rounded-2xl max-w-xs lg:max-w-md xl:max-w-2xl ${themeClasses.button} shadow-sm`}>
            <div className="whitespace-pre-wrap text-sm">{query.userMessage.content}</div>
          </div>
        </div>
      </div>

      {/* Response Section */}
      <div className="animate-in slide-in-from-left duration-300">
        <div className="flex items-start gap-3 max-w-4xl">
          {/* Bot Avatar */}
          <div className={`flex-shrink-0 w-8 h-8 rounded-full ${themeClasses.surfaceSecondary} flex items-center justify-center mt-1`}>
            <Bot className={`w-4 h-4 ${themeClasses.textSecondary}`} />
          </div>

          {/* Response Content */}
          <div className="flex-1 min-w-0">
            {/* Tabs - Only show if there are steps */}
            {hasSteps && (
              <div className="flex mb-4">
                <button
                  onClick={() => setActiveTab('answer')}
                  className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${activeTab === 'answer'
                    ? `border-blue-500 ${themeClasses.text}`
                    : `border-transparent ${themeClasses.textSecondary} hover:${themeClasses.text}`
                    }`}
                >
                  Answer
                </button>
                <button
                  onClick={() => setActiveTab('steps')}
                  className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${activeTab === 'steps'
                    ? `border-blue-500 ${themeClasses.text}`
                    : `border-transparent ${themeClasses.textSecondary} hover:${themeClasses.text}`
                    }`}
                >
                  Steps ({query.steps.length})
                </button>
              </div>
            )}

            {/* Content based on active tab */}
            {activeTab === 'answer' ? (
              <div className="space-y-4">
                {/* Final Answer */}
                {query.finalAnswer && (
                  <div className={`${themeClasses.text} leading-relaxed text-sm`}>
                    <ReactMarkdown>
                      {query.finalAnswer.content}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Component Pills */}
                {hasComponents && (
                  <div className="flex flex-wrap gap-2 mt-4">
                    {query.responses.map((component, index) => (
                      <ComponentPill
                        key={component.id}
                        component={component}
                        onClick={() => onComponentClick(query.id, component.type, component.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <ConnectedTimelineSteps
                steps={query.steps}
                expandedMessages={expandedMessages}
                toggleMessageExpansion={toggleMessageExpansion}
                onComponentClick={onComponentClick}
                queryId={query.id}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Connected Timeline Steps Component
const ConnectedTimelineSteps = ({ steps, expandedMessages, toggleMessageExpansion, onComponentClick, queryId }) => {
  const { themeClasses, isDark } = useTheme()

  if (steps.length === 0) {
    return (
      <div className={`text-sm ${themeClasses.textSecondary} text-center py-4`}>
        No processing steps to display
      </div>
    )
  }

  return (
    <div className="space-y-0">
      {steps.map((step, index) => (
        <ConnectedTimelineStep
          key={step.id}
          step={step}
          index={index}
          isLast={index === steps.length - 1}
          isExpanded={expandedMessages.has(step.id)}
          onToggleExpansion={toggleMessageExpansion}
          onComponentClick={onComponentClick}
          queryId={queryId}
        />
      ))}
    </div>
  )
}

// Individual Connected Timeline Step
const ConnectedTimelineStep = ({
  step,
  index,
  isLast,
  isExpanded,
  onToggleExpansion,
  onComponentClick,
  queryId
}) => {
  const { themeClasses, isDark } = useTheme()

  const getStepIcon = (type, isCompleted) => {
    switch (type) {
      case 'status':
        return isCompleted ? <CheckCircle className="w-4 h-4" /> : <Loader2 className="w-4 h-4 animate-spin" />
      case 'code':
        return <Code className="w-4 h-4" />
      case 'dataframe':
        return <Database className="w-4 h-4" />
      case 'image':
        return <Image className="w-4 h-4" />
      case 'report':
        return <FileText className="w-4 h-4" />
      case 'file':
        return <File className="w-4 h-4" />
      case 'success':
        return <CheckCircle className="w-4 h-4" />
      case 'error':
        return <AlertCircle className="w-4 h-4" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Loader2 className="w-4 h-4" />
    }
  }

  const getStepLabel = (type) => {
    switch (type) {
      case 'code':
        return 'Generated Code'
      case 'dataframe':
        return 'Data Analysis'
      case 'image':
        return 'Visualization'
      case 'report':
        return 'Report'
      case 'file':
        return 'Generated File'
      case 'status':
        return 'Processing'
      case 'success':
        return 'Success'
      case 'error':
        return 'Error'
      case 'warning':
        return 'Warning'
      default:
        return 'Step'
    }
  }

  const getStepColorClass = (type) => {
    return themeClasses.surfaceSecondary
  }

  const isClickableComponent = ['code', 'image', 'dataframe', 'report', 'file'].includes(step.type)
  const shouldCollapse = step.content && typeof step.content === 'string' && step.content.length > 200

  return (
    <div className="relative pl-6 pb-6">
      {/* Timeline line */}
      {!isLast && (
        <div className={`absolute left-3 top-6 bottom-0 w-px ${themeClasses.border}`}></div>
      )}

      {/* Step indicator */}
      <div className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColorClass(step.type)} flex items-center justify-center ${themeClasses.textOnGradient} shadow-lg z-10 transition-colors`}>
        {getStepIcon(step.type, step.isCompleted)}
      </div>

      {/* Content */}
      <div className="ml-6">
        <div className={`${themeClasses.surface} rounded-xl shadow-sm border ${themeClasses.border} overflow-hidden transition-colors`}>
          {/* Header */}
          <div className={`${themeClasses.surfaceSecondary} px-4 py-3 border-b ${themeClasses.border}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {shouldCollapse && (
                  <button
                    onClick={() => onToggleExpansion(step.id)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                  >
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                )}
                <div className="flex items-center gap-2">
                  <Bot className={`w-4 h-4 ${themeClasses.textSecondary}`} />
                  <span className={`${themeClasses.text} font-medium text-sm`}>
                    {getStepLabel(step.type)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isClickableComponent && (
                  <button
                    onClick={() => onComponentClick(queryId, step.type, step.id)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} p-1 rounded hover:${themeClasses.surfaceSecondary} transition-colors`}
                    title="View in detail panel"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                )}
                {step.type === "code" && (!shouldCollapse || isExpanded) && (
                  <button
                    onClick={() => copyToClipboard(step.content)}
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} p-1 rounded hover:${themeClasses.surfaceSecondary} transition-colors`}
                    title="Copy code"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Body - Only show if expanded or not collapsible */}
          {(!shouldCollapse || isExpanded) && (
            <div className="p-4">
              {(step.type === "system" ||
                step.type === "status" ||
                step.type === "success" ||
                step.type === "error" ||
                step.type === "warning") && (
                  <div className={`${themeClasses.text} whitespace-pre-wrap text-sm`}>
                    {step.content}
                  </div>
                )}

              {/* Handle code content */}
              {step.type === "code" && (
                <div className={`${themeClasses.surface} rounded-lg p-4 overflow-x-auto border ${themeClasses.border}`}>
                  <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>
                    {step.content}
                  </pre>
                </div>
              )}

              {/* Handle dataframe content */}
              {step.type === "dataframe" && step.content && (
                <div className="space-y-3">
                  {step.content.shape && (
                    <div className={`text-sm ${themeClasses.textSecondary}`}>
                      Shape: {step.content.shape[0]} rows × {step.content.shape[1]} columns
                    </div>
                  )}
                  {step.content.preview && (
                    <div
                      className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto`}
                      dangerouslySetInnerHTML={{ __html: step.content.preview }}
                    />
                  )}
                </div>
              )}

              {/* Handle image content */}
              {step.type === "image" && step.content && (
                <div className="space-y-3">
                  <div className={`flex items-center justify-center p-4 ${themeClasses.surface} rounded-lg`}>
                    <img
                      src={step.content.data || step.content.path || "/placeholder.svg"}
                      alt={step.content.filename || "Generated visualization"}
                      className="max-w-full h-auto rounded-lg shadow-sm"
                      onError={(e) => {
                        e.target.src = "/placeholder.svg"
                        e.target.alt = "Image failed to load"
                      }}
                    />
                  </div>
                  {step.content.filename && (
                    <div className={`text-sm ${themeClasses.textSecondary} text-center`}>
                      {step.content.filename}
                    </div>
                  )}
                </div>
              )}

              {/* Handle report content */}
              {step.type === "report" && step.content && (
                <div className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''}`}>
                  {typeof step.content === 'string' && step.content.includes('<!DOCTYPE html>') ? (
                    <div
                      dangerouslySetInnerHTML={{ __html: step.content }}
                      className={`report-content ${themeClasses.text}`}
                    />
                  ) : (
                    <div className={`whitespace-pre-wrap ${themeClasses.text}`}>
                      {typeof step.content === 'string' ? step.content : JSON.stringify(step.content, null, 2)}
                    </div>
                  )}
                </div>
              )}

              {/* Handle file content */}
              {step.type === "file" && step.content && (
                <div className={`text-sm ${themeClasses.text}`}>
                  {step.content.filename && (
                    <div className="mb-2">
                      <strong>Filename:</strong> {step.content.filename}
                    </div>
                  )}
                  {step.content.size && (
                    <div className="mb-2">
                      <strong>Size:</strong> {step.content.size}
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

// Component Pill for clickable components
const ComponentPill = ({ component, onClick }) => {
  const { themeClasses, isDark } = useTheme()

  const getComponentInfo = (type) => {
    switch (type) {
      case 'code':
        return {
          label: 'Generated Code',
          icon: <Code className="w-4 h-4" />,
          color: isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-800'
        }
      case 'image':
        return {
          label: 'Visualization',
          icon: <Image className="w-4 h-4" />,
          color: isDark ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-100 text-purple-800'
        }
      case 'dataframe':
        return {
          label: 'Data Table',
          icon: <Database className="w-4 h-4" />,
          color: isDark ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800'
        }
      case 'report':
        return {
          label: 'Report',
          icon: <FileText className="w-4 h-4" />,
          color: isDark ? 'bg-orange-900/30 text-orange-300' : 'bg-orange-100 text-orange-800'
        }
      case 'file':
        return {
          label: 'File',
          icon: <File className="w-4 h-4" />,
          color: isDark ? 'bg-gray-900/30 text-gray-300' : 'bg-gray-100 text-gray-800'
        }
      default:
        return {
          label: type,
          icon: <File className="w-4 h-4" />,
          color: isDark ? 'bg-gray-900/30 text-gray-300' : 'bg-gray-100 text-gray-800'
        }
    }
  }

  const info = getComponentInfo(component.type)

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3 py-2 rounded-full text-xs font-medium transition-colors hover:opacity-80 ${info.color}`}
    >
      {info.icon}
      {info.label}
    </button>
  )
}

// Enhanced Side Panel with Download Functionality
const EnhancedSidePanel = ({
  items = [],
  activeItem,
  onItemChange,
  selectedMessage,
  onClose,
  onUpdateItem
}) => {
  const { themeClasses, isDark } = useTheme()
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false)
  const [dashboards, setDashboards] = useState([])
  const [showDashboardDropdown, setShowDashboardDropdown] = useState(false)
  const [isLoadingDashboards, setIsLoadingDashboards] = useState(false)
  const [showNewDashboardForm, setShowNewDashboardForm] = useState(false)
  const [newDashboardName, setNewDashboardName] = useState('')
  const [addingToDashboard, setAddingToDashboard] = useState(null) // Track which dashboard is being added to
  const [isCreatingDashboard, setIsCreatingDashboard] = useState(false) // Track creating new dashboard
  const dashboardDropdownRef = useRef(null)

  // Load dashboards when dropdown is opened
  const loadDashboards = async () => {
    if (isLoadingDashboards) return
    
    setIsLoadingDashboards(true)
    try {
      const response = await fetch(`${BACKEND_URL}/api/dashboards`, {
        credentials: 'include'
      })
      const data = await response.json()
      if (data.success) {
        setDashboards(data.dashboards)
      }
    } catch (error) {
      console.error('Error loading dashboards:', error)
    } finally {
      setIsLoadingDashboards(false)
    }
  }

  // Create new dashboard
  const createNewDashboard = async () => {
    if (!newDashboardName.trim() || isCreatingDashboard) return
    
    try {
      setIsCreatingDashboard(true)
      
      const response = await fetch(`${BACKEND_URL}/api/dashboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name: newDashboardName.trim()
        })
      })
      const data = await response.json()
      if (data.success) {
        await loadDashboards() // Refresh the list
        setNewDashboardName('')
        setShowNewDashboardForm(false)
        // Automatically add to the newly created dashboard
        await addToDashboard(data.dashboard.id)
      } else {
        throw new Error(data.error || 'Failed to create dashboard')
      }
    } catch (error) {
      console.error('Error creating dashboard:', error)
    } finally {
      setIsCreatingDashboard(false)
    }
  }

  // Add visualization to dashboard
  const addToDashboard = async (dashboardId) => {
    if (!items.length) return
    
    const item = items[0]
    let chartData = ''
    let title = 'Visualization'
    let chartType = 'unknown'
    
    if (item.type === 'image' && item.content) {
      chartData = item.content.data || item.content.path || ''
      title = item.content.filename || 'Chart'
      chartType = 'image'
    }
    
    try {
      setAddingToDashboard(dashboardId) // Set loading state
      
      const response = await fetch(`${BACKEND_URL}/api/dashboards/${dashboardId}/visualizations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title,
          chart_data: chartData,
          filename: item.content?.filename || '',
          chart_type: chartType
        })
      })
      const data = await response.json()
      if (data.success) {
        setShowDashboardDropdown(false)
        setAddingToDashboard(null)
        console.log('Added to dashboard successfully')
        // Optional: Show success notification
      } else {
        throw new Error(data.error || 'Failed to add to dashboard')
      }
    } catch (error) {
      console.error('Error adding to dashboard:', error)
      setAddingToDashboard(null)
      // Optional: Show error notification
    }
  }

  // Handle dashboard button click
  const handleDashboardClick = () => {
    if (!showDashboardDropdown) {
      loadDashboards()
    }
    setShowDashboardDropdown(!showDashboardDropdown)
  }

  // Handle outside click for dashboard dropdown
  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (dashboardDropdownRef.current && !dashboardDropdownRef.current.contains(event.target)) {
        setShowDashboardDropdown(false)
      }
    }

    if (showDashboardDropdown) {
      document.addEventListener('mousedown', handleOutsideClick)
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick)
    }
  }, [showDashboardDropdown])

  const downloadFile = (content, type, item) => {
    let blob, fileName

    if (type === "code") {
      // Code download as Python file
      const codeContent = typeof content === "string" ? content :
        (content && content.code) ? content.code :
          JSON.stringify(content, null, 2)
      blob = new Blob([codeContent], { type: "text/x-python" })
      fileName = "generated_code.py"
    } else if (type === "image") {
      // Image download
      const link = document.createElement('a')
      link.href = content.data || content.path || "/placeholder.svg"
      link.download = content.filename || "image.png"
      link.click()
      return
    } else if (type === "dataframe") {
      // Data download as CSV
      let csvContent
      if (content.data && Array.isArray(content.data) && content.data.length > 0) {
        const headers = content.columns || Object.keys(content.data[0])
        csvContent = headers.join(",") + "\n"
        csvContent += content.data.map(row => {
          return headers.map(header => {
            const value = row[header]
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
              return `"${value.replace(/"/g, '""')}"`
            }
            return value
          }).join(",")
        }).join("\n")
      } else if (content.data && typeof content.data === 'string') {
        csvContent = content.data
      } else if (content.rows && content.columns) {
        csvContent = content.columns.join(",") + "\n" + content.rows.map(row => row.join(",")).join("\n")
      } else {
        console.error("No valid data found for CSV download")
        return
      }
      blob = new Blob([csvContent], { type: "text/csv" })
      fileName = "data.csv"
    } else if (type === "report") {
      // Generate PDF for report - get current edited content
      const editableDiv = document.querySelector(`[data-report-id="${item.id}"]`)
      const updatedHTML = editableDiv ? editableDiv.innerHTML : content

      // Update the item's content to persist changes
      if (editableDiv && onUpdateItem) {
        onUpdateItem(item.id, updatedHTML)
      }

      generateReportPDF(updatedHTML, item)
      return
    }

    if (blob) {
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      link.click()
      setTimeout(() => URL.revokeObjectURL(link.href), 100)
    }
  }

  // Backend PDF generation for reports
  const generateReportPDF = async (htmlContent, item) => {
    setIsGeneratingPDF(true)

    try {
      // Clean HTML if wrapped in code block
      let cleanedContent = htmlContent
      if (cleanedContent.includes('```html')) {
        cleanedContent = cleanedContent.replace(/```html\s*/, '').replace(/```\s*$/, '')
      }

      const response = await fetch(`${BACKEND_URL}/api/generate-pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "text/plain",
        },
        body: cleanedContent,
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `report-${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      console.log("PDF downloaded from backend successfully")
    } catch (error) {
      console.error("Failed to download PDF:", error)

      // Fallback to client-side PDF generation
      try {
        await generateBasicPDF(htmlContent, item)
      } catch (fallbackError) {
        console.error("Fallback PDF generation failed:", fallbackError)
        alert("Failed to download PDF. Please try again.")
      }
    } finally {
      setIsGeneratingPDF(false)
    }
  }

  // Fallback client-side PDF generation
  const generateBasicPDF = async (content, item) => {
    // Import html2pdf dynamically if available
    if (typeof window !== 'undefined' && window.html2pdf) {
      const tempContainer = document.createElement('div')
      tempContainer.style.position = 'absolute'
      tempContainer.style.left = '-9999px'
      tempContainer.style.top = '-9999px'
      tempContainer.style.width = '210mm'

      tempContainer.innerHTML = content
      document.body.appendChild(tempContainer)

      const options = {
        margin: [15, 15, 15, 15],
        filename: `analysis-report-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true,
          backgroundColor: '#ffffff'
        },
        jsPDF: {
          unit: 'mm',
          format: 'a4',
          orientation: 'portrait'
        }
      }

      await window.html2pdf().set(options).from(tempContainer).save()
      document.body.removeChild(tempContainer)
    } else {
      // Final fallback - browser print dialog
      const printWindow = window.open('', '_blank')
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Analysis Report</title>
            <style>
              body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                line-height: 1.6;
                color: #333;
              }
              @media print { 
                body { margin: 0; }
                .no-print { display: none !important; }
              }
              h1, h2, h3, h4, h5, h6 { color: #2c3e50; margin-top: 1.5em; }
              table { border-collapse: collapse; width: 100%; margin: 1em 0; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #f8f9fa; font-weight: bold; }
              img { max-width: 100%; height: auto; }
            </style>
          </head>
          <body>
            ${typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
          </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.focus()
      printWindow.print()
      printWindow.close()
    }
  }

  if (items.length === 0) {
    return null
  }

  const item = items[0] // Show only the selected component

  return (
    <div className={`h-full flex flex-col ${themeClasses.bg} ${themeClasses.border} border-l transition-colors`}>
      {/* Header */}
      <div className={`p-4 ${themeClasses.border} border-b ${themeClasses.surface}`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className={`font-semibold ${themeClasses.text} text-sm`}>
              {item.type === 'code' ? 'Generated Code' :
                item.type === 'image' ? 'Visualization' :
                  item.type === 'dataframe' ? 'Data Table' :
                    item.type === 'report' ? 'Analysis Report' :
                      'Component'}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {/* Dashboard Button - only show for image/chart visualizations */}
            {item.type === 'image' && (
              <div className="relative" ref={dashboardDropdownRef}>
                <button
                  onClick={handleDashboardClick}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors`}
                  title="Add to Dashboard"
                >
                  <LayoutDashboard className="w-4 h-4" />
                </button>
                
                {/* Dashboard Dropdown */}
                {showDashboardDropdown && (
                  <div 
                    className={`absolute top-full right-0 mt-2 w-64 ${themeClasses.surface} ${themeClasses.border} border rounded-lg shadow-lg z-50`}
                    onClick={(e) => e.stopPropagation()} // Prevent dropdown from closing when clicking inside
                  >
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className={`text-sm font-medium ${themeClasses.text}`}>Add to Dashboard</h4>
                        <button
                          onClick={() => setShowDashboardDropdown(false)}
                          className={`p-1 ${themeClasses.textSecondary} hover:${themeClasses.text} rounded`}
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                      
                      {isLoadingDashboards ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {dashboards.length > 0 && (
                            <div className="space-y-1">
                              {dashboards.map((dashboard) => (
                                <button
                                  key={dashboard.id}
                                  onClick={() => addToDashboard(dashboard.id)}
                                  disabled={addingToDashboard === dashboard.id}
                                  className={`w-full text-left p-2 text-sm ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} rounded border ${themeClasses.border} transition-colors flex items-center justify-between disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                  <div className="flex-1">
                                    <div className={`font-medium ${themeClasses.text}`}>{dashboard.name}</div>
                                    {dashboard.visualization_count > 0 && (
                                      <div className={`text-xs ${themeClasses.textSecondary}`}>
                                        {dashboard.visualization_count} visualizations
                                      </div>
                                    )}
                                  </div>
                                  {addingToDashboard === dashboard.id && (
                                    <div className="flex items-center ml-2">
                                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                    </div>
                                  )}
                                </button>
                              ))}
                            </div>
                          )}
                          
                          {!showNewDashboardForm ? (
                            <button
                              onClick={() => setShowNewDashboardForm(true)}
                              className={`w-full p-2 text-sm ${themeClasses.button} hover:opacity-80 rounded transition-colors flex items-center gap-2`}
                            >
                              <Plus className="w-4 h-4" />
                              Create New Dashboard
                            </button>
                          ) : (
                            <div className="space-y-2">
                              <input
                                type="text"
                                value={newDashboardName}
                                onChange={(e) => setNewDashboardName(e.target.value)}
                                placeholder="Dashboard name"
                                className={`w-full p-2 text-sm ${themeClasses.surface} ${themeClasses.border} border rounded focus:outline-none focus:ring-2 focus:ring-blue-500`}
                                autoFocus
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') {
                                    createNewDashboard()
                                  } else if (e.key === 'Escape') {
                                    setShowNewDashboardForm(false)
                                    setNewDashboardName('')
                                  }
                                }}
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={createNewDashboard}
                                  disabled={!newDashboardName.trim() || isCreatingDashboard}
                                  className={`flex-1 p-2 text-xs ${themeClasses.button} hover:opacity-80 rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-2`}
                                >
                                  {isCreatingDashboard ? (
                                    <>
                                      <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                      Creating...
                                    </>
                                  ) : (
                                    'Create'
                                  )}
                                </button>
                                <button
                                  onClick={() => {
                                    setShowNewDashboardForm(false)
                                    setNewDashboardName('')
                                  }}
                                  className={`flex-1 p-2 text-xs ${themeClasses.textSecondary} hover:${themeClasses.text} rounded transition-colors`}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <button
              onClick={() => downloadFile(item.content, item.type, item)}
              disabled={isGeneratingPDF}
              className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isGeneratingPDF ? "Generating PDF..." : "Download"}
            >
              {isGeneratingPDF ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={onClose}
              className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors`}
              title="Close panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {item.type === 'code' && (
          <div className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} p-4 overflow-x-auto`}>
            <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>
              {typeof item.content === "string" ? item.content :
                (item.content && item.content.code) ? item.content.code :
                  JSON.stringify(item.content, null, 2)}
            </pre>
          </div>
        )}

        {item.type === 'image' && (
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
            {/* {item.content?.filename && (
              // <div className={`text-sm ${themeClasses.textSecondary} text-center mt-2`}>
              //   {item.content.filename}
              // </div>
            )} */}
          </div>
        )}

        {item.type === 'dataframe' && (
          <div className="space-y-3">
            {item.content?.shape && (
              <div className={`text-sm ${themeClasses.textSecondary}`}>
                Shape: {item.content.shape[0]} rows × {item.content.shape[1]} columns
              </div>
            )}
            {item.content?.preview && (
              <div
                className={`${themeClasses.surface} rounded-lg border ${themeClasses.border} overflow-x-auto`}
                dangerouslySetInnerHTML={{ __html: item.content.preview }}
              />
            )}
          </div>
        )}

        {item.type === 'report' && (
          <div
            className={`prose prose-sm max-w-none ${isDark ? 'prose-invert' : ''} ${themeClasses.text} focus:outline-none`}
            contentEditable={true}
            suppressContentEditableWarning={true}
            data-report-id={item.id}
            onInput={(e) => onUpdateItem && onUpdateItem(item.id, e.target.innerHTML)}
            dangerouslySetInnerHTML={{
              __html: typeof item.content === 'string' ? item.content : JSON.stringify(item.content, null, 2)
            }}
          />
        )}
      </div>
    </div>
  )
}

// Enhanced Sample Questions Component
const EnhancedSampleQuestions = ({ questions, onSelectQuestion }) => {
  const { themeClasses, isDark } = useTheme()
  const [selectedCategory, setSelectedCategory] = useState("all")

  const categories = [
    { id: "all", label: "All", icon: <Code className="w-4 h-4" /> },
    { id: "conversational", label: "Chat", icon: <User className="w-4 h-4" /> },
    { id: "textual_analytical", label: "Quick Q&A", icon: <Database className="w-4 h-4" /> },
    { id: "fully_analytical", label: "Deep Analysis", icon: <FileText className="w-4 h-4" /> }
  ]

  const filteredQuestions = selectedCategory === "all"
    ? questions
    : questions.filter(q => q.category === selectedCategory)

  return (
    <div className={`p-4 ${themeClasses.surface} ${themeClasses.border} border-b`}>
      <div className="max-w-4xl mx-auto">
        <div className="mb-4">
          <h3 className={`text-sm font-medium ${themeClasses.text} mb-2`}>
            Try these example queries:
          </h3>

          <div className="flex gap-2 mb-3">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedCategory === category.id
                  ? `${themeClasses.button} ${themeClasses.text}`
                  : `${themeClasses.surface} ${themeClasses.textSecondary} hover:${themeClasses.text}`
                  }`}
              >
                {category.icon}
                {category.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {filteredQuestions.map((item, index) => (
            <button
              key={index}
              onClick={() => onSelectQuestion(item.question)}
              className={`text-left p-3 rounded-lg border ${themeClasses.border} ${themeClasses.surface} hover:${themeClasses.surfaceSecondary} transition-colors group`}
            >
              <div className="flex items-start gap-2">
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs ${item.category === "conversational"
                  ? (isDark ? "bg-green-900/30 text-green-400" : "bg-green-100 text-green-600")
                  : item.category === "textual_analytical"
                    ? (isDark ? "bg-blue-900/30 text-blue-400" : "bg-blue-100 text-blue-600")
                    : (isDark ? "bg-purple-900/30 text-purple-400" : "bg-purple-100 text-purple-600")
                  }`}>
                  {item.category === "conversational" ? <User className="w-3 h-3" /> :
                    item.category === "textual_analytical" ? <Database className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm ${themeClasses.text} font-medium mb-1 ${isDark ? 'group-hover:text-blue-400' : 'group-hover:text-blue-600'} transition-colors`}>
                    {item.question}
                  </div>
                  <div className={`text-xs ${themeClasses.textSecondary}`}>
                    {item.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ChatInterface