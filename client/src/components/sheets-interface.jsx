"use client"

import { useState, useRef, useMemo } from "react"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { useSpreadsheet, getCellRef, getColumnLabel } from "../lib/spreadsheet-context"
import {
  Save,
  Undo,
  Redo,
  Bold,
  Italic,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Palette,
  FlagIcon as BorderAll,
  Merge,
  Plus,
  Share,
  ChevronDown,
  Percent,
  DollarSign,
  Hash,
  ImageIcon,
  BarChart3,
  Filter,
  Upload,
} from "lucide-react"
import { AIChatSidebar } from "./ai-chat-sidebar"
import { ChartOverlays } from "./chart-overlays"
import { DataUploadModal } from "./data-upload-modal"

// Virtual scrolling configuration
const CELL_HEIGHT = 60
const CELL_WIDTH = 112
const HEADER_HEIGHT = 32
const VISIBLE_ROWS = 25
const VISIBLE_COLS = 15

export function SheetsInterface() {
  const {
    data,
    activeSheet,
    setActiveSheet,
    addSheet,
    renameSheet,
    updateCell,
    getCellValue,
    addRow,
    addColumn,
    deleteRow,
    deleteColumn,
    evaluateFormula,
    recalculateSheet,
  } = useSpreadsheet()

  console.log(data)

  const [selectedCell, setSelectedCell] = useState(null)
  const [editingCell, setEditingCell] = useState(null)
  const [editValue, setEditValue] = useState("")
  const [formulaBarValue, setFormulaBarValue] = useState("")
  const [showAIChat, setShowAIChat] = useState(true)
  const [editingSheetName, setEditingSheetName] = useState(null)
  const [newSheetName, setNewSheetName] = useState("")
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [scrollTop, setScrollTop] = useState(0)
  const [scrollLeft, setScrollLeft] = useState(0)

  const currentSheetData = data[activeSheet]
  const sheets = Object.keys(data)
  const inputRef = useRef(null)
  const scrollContainerRef = useRef(null)

  // Calculate visible range for virtual scrolling
  const visibleRange = useMemo(() => {
    const startRow = Math.floor(scrollTop / CELL_HEIGHT)
    const endRow = Math.min(startRow + VISIBLE_ROWS + 5, currentSheetData?.rows || 50)
    const startCol = Math.max(0, Math.floor(scrollLeft / CELL_WIDTH))
    const endCol = Math.min(startCol + VISIBLE_COLS + 5, currentSheetData?.cols || 20)

    return { startRow, endRow, startCol, endCol }
  }, [scrollTop, scrollLeft, currentSheetData])

  const handleScroll = (e) => {
    const target = e.target
    setScrollTop(target.scrollTop)
    setScrollLeft(target.scrollLeft)
  }

  const handleCellClick = (row, col) => {
    setSelectedCell({ row, col })
    setEditingCell(null)

    const cellRef = getCellRef(row, col)
    const cellValue = getCellValue(activeSheet, cellRef)
    setFormulaBarValue(cellValue?.formula || cellValue?.value?.toString() || "")
  }

  const handleCellDoubleClick = (row, col) => {
    setEditingCell({ row, col })
    const cellRef = getCellRef(row, col)
    const cellValue = getCellValue(activeSheet, cellRef)
    setEditValue(cellValue?.formula || cellValue?.value?.toString() || "")
  }

  const handleCellEdit = (value) => {
    if (editingCell) {
      const cellRef = getCellRef(editingCell.row, editingCell.col)

      if (value.startsWith("=")) {
        updateCell(activeSheet, cellRef, value, value, "formula")
      } else {
        updateCell(activeSheet, cellRef, value)
      }

      setEditingCell(null)
      setFormulaBarValue(value)
      setTimeout(() => recalculateSheet(activeSheet), 10)
    }
  }

  const handleFormulaBarChange = (value) => {
    if (selectedCell) {
      const cellRef = getCellRef(selectedCell.row, selectedCell.col)

      if (value.startsWith("=")) {
        updateCell(activeSheet, cellRef, value, value, "formula")
      } else {
        updateCell(activeSheet, cellRef, value)
      }

      setFormulaBarValue(value)
      setTimeout(() => recalculateSheet(activeSheet), 10)
    }
  }

  const renderCellContent = (row, col) => {
    const cellRef = getCellRef(row, col)
    const cellValue = getCellValue(activeSheet, cellRef)

    if (!cellValue) return ""

    if (cellValue.type === "image" && cellValue.imageUrl) {
      return (
        <div className="w-full h-full flex items-center justify-center p-1">
          <img
            src={cellValue.imageUrl || "/placeholder.svg"}
            alt="Cell image"
            className="max-w-full max-h-full object-contain rounded"
            onError={(e) => {
              const target = e.target
              target.src = "/placeholder.svg?height=60&width=80&text=Image+Error"
            }}
          />
        </div>
      )
    }

    if (cellValue.type === "formula") {
      return (
        <div className="flex items-center justify-between w-full">
          <span className="text-blue-600 font-medium">{cellValue.value}</span>
        </div>
      )
    }

    if (cellValue.type === "number") {
      return (
        <span className={`${row === 0 ? "font-semibold" : ""} text-right block w-full`}>
          {typeof cellValue.value === "number" ? cellValue.value.toLocaleString() : cellValue.value}
        </span>
      )
    }

    return <span className={row === 0 ? "font-semibold" : ""}>{cellValue.value}</span>
  }

  const handleSheetNameEdit = (sheetName) => {
    if (newSheetName.trim() && newSheetName !== sheetName) {
      renameSheet(sheetName, newSheetName.trim())
    }
    setEditingSheetName(null)
    setNewSheetName("")
  }

  // Generate visible cells only
  const visibleCells = useMemo(() => {
    const cells = []
    for (let row = visibleRange.startRow; row < visibleRange.endRow; row++) {
      for (let col = visibleRange.startCol; col < visibleRange.endCol; col++) {
        cells.push({ row, col })
      }
    }
    return cells
  }, [visibleRange])

  // Generate visible row headers
  const visibleRowHeaders = useMemo(() => {
    const headers = []
    for (let row = visibleRange.startRow; row < visibleRange.endRow; row++) {
      headers.push(row)
    }
    return headers
  }, [visibleRange])

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900">
      {/* Top Menu Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-green-500 rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">📊</span>
            </div>
            <span className="font-medium text-gray-700 dark:text-gray-300">SpreadSheet AI</span>
          </div>

          <nav className="flex items-center gap-4 text-sm">
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              File
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              Edit
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              View
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              Insert
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              Format
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              Help
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-600 dark:text-gray-400">
              Feedback
            </Button>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">My files</span>
          <span className="text-sm text-gray-500">BTC vs ETH</span>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <Button variant="ghost" size="sm">
          <Undo className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Redo className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Save className="w-4 h-4" />
        </Button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />

        <Button variant="ghost" size="sm">
          <Percent className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <DollarSign className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Hash className="w-4 h-4" />
        </Button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />

        <Button variant="ghost" size="sm">
          <Bold className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Italic className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Underline className="w-4 h-4" />
        </Button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />

        <Button variant="ghost" size="sm">
          <AlignLeft className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <AlignCenter className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <AlignRight className="w-4 h-4" />
        </Button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />

        <Button variant="ghost" size="sm">
          <BorderAll className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Merge className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Palette className="w-4 h-4" />
        </Button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />

        <Button variant="ghost" size="sm">
          <ImageIcon className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <BarChart3 className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Filter className="w-4 h-4" />
        </Button>

        <Button variant="ghost" size="sm" onClick={() => setShowUploadModal(true)}>
          <Upload className="w-4 h-4 mr-2" />
          Upload Data
        </Button>

        <div className="flex-1" />

        <span className="text-sm text-gray-500">94%</span>
      </div>

      {/* Name Box and Formula Bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex items-center gap-2">
          <div className="w-16 h-8 border border-gray-300 dark:border-gray-600 rounded px-2 flex items-center text-sm font-medium">
            {selectedCell ? `${getColumnLabel(selectedCell.col)}${selectedCell.row + 1}` : "A1"}
          </div>
          <Button variant="ghost" size="sm">
            <ChevronDown className="w-4 h-4" />
          </Button>
        </div>

        <div className="text-sm font-medium text-gray-600 dark:text-gray-400 px-2">fx</div>

        <Input
          className="flex-1 font-mono border-0 focus:ring-0 bg-transparent"
          placeholder="Enter formula or value..."
          value={formulaBarValue}
          onChange={(e) => setFormulaBarValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleFormulaBarChange(formulaBarValue)
            }
          }}
          onBlur={() => handleFormulaBarChange(formulaBarValue)}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* AI Chat Sidebar */}
        {showAIChat && (
          <div className="w-80 border-r border-gray-200 dark:border-gray-700">
            <AIChatSidebar />
          </div>
        )}

        {/* Spreadsheet Grid with Chart Overlays */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <div
            ref={scrollContainerRef}
            className="flex-1 overflow-auto bg-white dark:bg-gray-900 relative"
            onScroll={handleScroll}
          >
            {/* Chart Overlays */}
            <ChartOverlays />

            {/* Virtual Spreadsheet Grid */}
            <div
              className="relative"
              style={{
                height: (currentSheetData?.rows || 50) * CELL_HEIGHT + HEADER_HEIGHT,
                width: (currentSheetData?.cols || 20) * CELL_WIDTH + 48, // 48px for row header
              }}
            >
              {/* Column Headers */}
              <div className="sticky top-0 bg-gray-50 dark:bg-gray-800 z-10 flex" style={{ height: HEADER_HEIGHT }}>
                <div
                  className="w-12 border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 sticky left-0 z-20"
                  style={{ height: HEADER_HEIGHT }}
                />
                {Array.from({ length: visibleRange.endCol - visibleRange.startCol }).map((_, index) => {
                  const colIndex = visibleRange.startCol + index
                  return (
                    <div
                      key={colIndex}
                      className="border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 text-xs font-medium text-gray-600 dark:text-gray-400 px-2 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center justify-center"
                      style={{
                        width: CELL_WIDTH,
                        height: HEADER_HEIGHT,
                        left: 48 + colIndex * CELL_WIDTH,
                        position: "absolute",
                      }}
                    >
                      {getColumnLabel(colIndex)}
                    </div>
                  )
                })}
              </div>

              {/* Row Headers - Render separately */}
              {visibleRowHeaders.map((row) => (
                <div
                  key={`row-header-${row}`}
                  className="w-12 border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-xs font-medium text-gray-600 dark:text-gray-400 text-center cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 sticky left-0 z-10 flex items-center justify-center"
                  style={{
                    height: CELL_HEIGHT,
                    top: HEADER_HEIGHT + row * CELL_HEIGHT,
                    position: "absolute",
                  }}
                >
                  {row + 1}
                </div>
              ))}

              {/* Virtualized Cells - All cells including first column */}
              {visibleCells.map(({ row, col }) => {
                const cellRef = getCellRef(row, col)
                const cellValue = getCellValue(activeSheet, cellRef)
                const isImage = cellValue?.type === "image"
                const isSelected = selectedCell?.row === row && selectedCell?.col === col

                return (
                  <div
                    key={`${row}-${col}`}
                    className={`border border-gray-300 dark:border-gray-600 text-sm cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 bg-white dark:bg-gray-900 ${
                      isSelected ? "bg-blue-100 dark:bg-blue-900/30 ring-2 ring-blue-500 ring-inset" : ""
                    } ${isImage ? "p-1" : "px-2"} flex items-center`}
                    style={{
                      width: CELL_WIDTH,
                      height: isImage ? CELL_HEIGHT * 2.5 : CELL_HEIGHT,
                      left: 48 + col * CELL_WIDTH,
                      top: HEADER_HEIGHT + row * CELL_HEIGHT,
                      position: "absolute",
                    }}
                    onClick={() => handleCellClick(row, col)}
                    onDoubleClick={() => handleCellDoubleClick(row, col)}
                  >
                    {editingCell?.row === row && editingCell?.col === col ? (
                      <Input
                        ref={inputRef}
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={() => handleCellEdit(editValue)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            handleCellEdit(editValue)
                          } else if (e.key === "Escape") {
                            setEditingCell(null)
                          }
                        }}
                        className="w-full h-full text-sm border-none p-1 focus:ring-0 bg-transparent"
                        autoFocus
                      />
                    ) : (
                      renderCellContent(row, col)
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Sheet Tabs */}
          <div className="flex items-center gap-1 p-2 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <Button variant="ghost" size="sm" onClick={() => addSheet(`Sheet ${sheets.length + 1}`)}>
              <Plus className="w-4 h-4" />
            </Button>

            {sheets.map((sheet) => (
              <div key={sheet} className="flex items-center">
                {editingSheetName === sheet ? (
                  <Input
                    value={newSheetName}
                    onChange={(e) => setNewSheetName(e.target.value)}
                    onBlur={() => handleSheetNameEdit(sheet)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleSheetNameEdit(sheet)
                      } else if (e.key === "Escape") {
                        setEditingSheetName(null)
                        setNewSheetName("")
                      }
                    }}
                    className="w-24 h-8 text-xs"
                    autoFocus
                  />
                ) : (
                  <Button
                    variant={activeSheet === sheet ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setActiveSheet(sheet)}
                    onDoubleClick={() => {
                      setEditingSheetName(sheet)
                      setNewSheetName(sheet)
                    }}
                    className="text-xs"
                  >
                    {sheet}
                  </Button>
                )}
              </div>
            ))}

            <div className="flex-1" />

            <Button variant="ghost" size="sm" onClick={() => setShowAIChat(!showAIChat)}>
              💬 Sheet chat
            </Button>
          </div>
        </div>
      </div>
      {/* Upload Modal */}
      <DataUploadModal
        open={showUploadModal}
        onOpenChange={setShowUploadModal}
        onDataUploaded={(sheetNames) => {
          setShowUploadModal(false)
        }}
      />
    </div>
  )
}
