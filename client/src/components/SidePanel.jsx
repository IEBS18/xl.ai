import React, { useState, useRef, useEffect } from "react"
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
import html2pdf from "html2pdf.js"
import { BACKEND_URL } from "../utils/constants"


const SidePanel = ({ items, activeItem, onItemChange, selectedMessage, onClearSelection, onUpdateItem }) => {
  const { themeClasses } = useTheme()
  const [isMaximized, setIsMaximized] = useState(false)
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false)
  const panelRef = useRef(null)

  // Maximizing content to full screen
  const toggleFullscreen = () => {
    if (panelRef.current) {
      if (isMaximized) {
        // Exit fullscreen mode
        document.exitFullscreen()
      } else {
        // Request fullscreen mode
        panelRef.current.requestFullscreen()
      }
      setIsMaximized(!isMaximized)
    }
  }

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

  // Optimized PDF generation specifically for comprehensive HTML reports
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
      alert("Failed to download PDF. Please try again.")
    } finally {
      setIsGeneratingPDF(false)
    }
  }

  // Fallback PDF generation for simpler content
  const generateBasicPDF = async (content, item) => {
    setIsGeneratingPDF(true)

    try {
      // Extract HTML content (remove ```html wrapper if present)
      let htmlContent = content
      if (content.includes('```html')) {
        htmlContent = content.replace(/```html\s*/, '').replace(/```\s*$/, '')
      }

      // Create a temporary container for the PDF content
      const tempContainer = document.createElement('div')
      tempContainer.style.position = 'absolute'
      tempContainer.style.left = '-9999px'
      tempContainer.style.top = '-9999px'
      tempContainer.style.width = '210mm' // A4 width

      // If it's a complete HTML document, use the entire document
      if (htmlContent.includes('<!DOCTYPE html>')) {
        // Create an iframe to properly render the complete HTML document
        const iframe = document.createElement('iframe')
        iframe.style.position = 'absolute'
        iframe.style.left = '-9999px'
        iframe.style.top = '-9999px'
        iframe.style.width = '210mm'
        iframe.style.height = '297mm' // A4 height
        iframe.style.border = 'none'

        document.body.appendChild(iframe)
        iframe.contentDocument.open()
        iframe.contentDocument.write(htmlContent)
        iframe.contentDocument.close()

        // Wait for the iframe to load completely
        await new Promise((resolve) => {
          iframe.onload = resolve
          // Fallback timeout
          setTimeout(resolve, 1000)
        })

        // Use the iframe's document body for PDF generation
        tempContainer.innerHTML = iframe.contentDocument.body.innerHTML

        // Copy all stylesheets from the iframe to the temp container
        const iframeStyles = iframe.contentDocument.querySelectorAll('style, link[rel="stylesheet"]')
        iframeStyles.forEach(styleEl => {
          const clonedStyle = styleEl.cloneNode(true)
          tempContainer.appendChild(clonedStyle)
        })

        // Clean up iframe
        document.body.removeChild(iframe)
      } else {
        // For HTML fragments, use as-is with minimal additions
        tempContainer.innerHTML = htmlContent
      }

      // Add only essential PDF-specific styles (without overriding existing styles)
      const pdfStyle = document.createElement('style')
      pdfStyle.textContent = `
        @media print {
          * { print-color-adjust: exact !important; }
          .no-print { display: none !important; }
        }
        .page-break {
          page-break-before: always;
        }
        /* Ensure content fits properly on PDF pages */
        img {
          max-width: 100% !important;
          height: auto !important;
        }
        table {
          page-break-inside: avoid;
        }
        tr {
          page-break-inside: avoid;
        }
      `
      tempContainer.appendChild(pdfStyle)
      document.body.appendChild(tempContainer)

      // PDF generation options
      const options = {
        margin: [15, 15, 15, 15], // top, right, bottom, left in mm
        filename: `analysis-report-${new Date().toISOString().split('T')[0]}.pdf`,
        image: {
          type: 'jpeg',
          quality: 0.98
        },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true,
          allowTaint: false,
          backgroundColor: '#ffffff',
          scrollX: 0,
          scrollY: 0,
          width: tempContainer.offsetWidth,
          height: tempContainer.offsetHeight
        },
        jsPDF: {
          unit: 'mm',
          format: 'a4',
          orientation: 'portrait',
          compress: true
        },
        pagebreak: {
          mode: ['avoid-all', 'css', 'legacy'],
          before: '.page-break',
          after: '.page-break',
          avoid: ['tr', 'img']
        }
      }

      // Generate and download PDF
      await html2pdf()
        .set(options)
        .from(tempContainer)
        .save()

      // Clean up
      document.body.removeChild(tempContainer)

      console.log('Basic PDF generated successfully')

    } catch (error) {
      console.error('Error generating basic PDF:', error)
      alert('Error generating PDF. Please try again.')
    } finally {
      setIsGeneratingPDF(false)
    }
  }

  const downloadFile = (content, type, item) => {
    let blob, fileName

    if (type === "code") {
      // Code download as Python file
      blob = new Blob([content], { type: "text/x-python" })
      fileName = "generated_code.py"
    } else if (type === "image") {
      // Image download
      const link = document.createElement('a')
      link.href = content.data || "/placeholder.svg"
      link.download = content.filename || "image.png"
      link.click()
      return
    } else if (type === "dataframe") {
      console.log("csv content: ", content)
      // Data download as CSV - convert array of objects to CSV format
      let csvContent

      if (content.data && Array.isArray(content.data) && content.data.length > 0) {
        // content.data is an array of objects, convert to CSV
        const headers = content.columns || Object.keys(content.data[0])

        // Create CSV header row
        csvContent = headers.join(",") + "\n"

        // Add data rows
        csvContent += content.data.map(row => {
          return headers.map(header => {
            const value = row[header]
            // Handle values that might contain commas or quotes
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
              return `"${value.replace(/"/g, '""')}"`
            }
            return value
          }).join(",")
        }).join("\n")

      } else if (content.data && typeof content.data === 'string') {
        // If content.data is already a CSV string
        csvContent = content.data
      } else if (content.rows && content.columns) {
        // Fallback to the old structure if data property doesn't exist
        csvContent = content.columns.join(",") + "\n" + content.rows.map(row => row.join(",")).join("\n")
      } else {
        console.error("No valid data found for CSV download")
        return
      }

      blob = new Blob([csvContent], { type: "text/csv" })
      fileName = "data.csv"
    } else if (type === "report") {
      console.log(content);

      // Get updated HTML from DOM
      const editableDiv = document.querySelector(`[data-report-id="${item.id}"]`)
      const updatedHTML = editableDiv ? editableDiv.innerHTML : content

      // Update the item's content in the parent component to persist changes
      if (editableDiv && onUpdateItem) {
        onUpdateItem(item.id, updatedHTML)
      }

      // Always use the updated HTML content
      generateReportPDF(updatedHTML, item)
      return
    }

    // Trigger download for non-report types
    if (blob) {
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      link.click()

      // Clean up the object URL to free memory
      setTimeout(() => URL.revokeObjectURL(link.href), 100)
    }
  }

  const renderContent = (item) => {
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
                <button
                  onClick={() => downloadFile(item.content, "code", item)}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}
                  title="Download code"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className={`${themeClasses.surface} rounded-lg p-4 overflow-x-auto`}>
                <pre className={`text-sm ${themeClasses.text} font-mono whitespace-pre-wrap`}>{item.content}</pre>
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
                <button
                  onClick={toggleFullscreen}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}
                  title="Maximize image"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => downloadFile(item.content, "image", item)}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}
                  title="Download image"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className={`flex-1 overflow-auto p-4 flex items-center justify-center ${isMaximized ? "w-full h-full" : "max-w-full max-h-full"}`}>
              <img
                src={item.content.data || "/placeholder.svg"}
                alt={item.content.filename}
                className={`object-contain rounded-lg ${isMaximized ? "w-full h-full" : ""}`}
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
              <button
                onClick={() => downloadFile(item.content, "dataframe", item)}
                className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors`}
                title="Download data"
              >
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
                <button
                  onClick={() => downloadFile(item.content, "report", item)}
                  disabled={isGeneratingPDF}
                  className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={isGeneratingPDF ? "Generating PDF..." : "Download as PDF"}
                >
                  {isGeneratingPDF ? (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div id={`report-content-${item.id}`} className="prose prose-sm max-w-none">
                <EditableReportContent
                  itemId={item.id}
                  content={item.content}
                  themeClasses={themeClasses}
                  onUpdateItem={onUpdateItem}
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

  return (
    <div className={`h-full flex flex-col ${themeClasses.bg} transition-colors`} ref={panelRef}>
      {/* Header with context info */}
      {selectedMessage && (
        <div className={`p-4 ${themeClasses.border} border-b ${themeClasses.surface}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className={`text-sm font-medium ${themeClasses.text}`}>Query Results</span>
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

// Separate component to handle editable report content
const EditableReportContent = ({ itemId, content, themeClasses, onUpdateItem }) => {
  const contentRef = useRef(null)
  const [currentContent, setCurrentContent] = useState(content)

  // Update local content when prop changes (but preserve user edits)
  useEffect(() => {
    if (contentRef.current && contentRef.current.innerHTML !== content) {
      // Only update if the content is different and the element isn't focused
      if (document.activeElement !== contentRef.current) {
        setCurrentContent(content)
        contentRef.current.innerHTML = content
      }
    }
  }, [content])

  // Handle content changes and sync with parent
  const handleInput = (e) => {
    const newContent = e.target.innerHTML
    setCurrentContent(newContent)
    
    // Debounced update to parent (optional)
    if (onUpdateItem) {
      clearTimeout(handleInput.timeoutId)
      handleInput.timeoutId = setTimeout(() => {
        onUpdateItem(itemId, newContent)
      }, 1000) // Update parent after 1 second of no changes
    }
  }

  // Ensure content is set on initial render
  useEffect(() => {
    if (contentRef.current && !contentRef.current.innerHTML) {
      contentRef.current.innerHTML = currentContent
    }
  }, [currentContent])

  return (
    <div
      ref={contentRef}
      className={`${themeClasses.text} focus:outline-none`}
      contentEditable={true}
      suppressContentEditableWarning={true}
      data-report-id={itemId}
      onInput={handleInput}
      dangerouslySetInnerHTML={{ __html: currentContent }}
    />
  )
}

export default SidePanel