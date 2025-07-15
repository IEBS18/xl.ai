"use client"

import { useState } from "react"
import { Edit3, Hash, Type, Calendar, MoreHorizontal } from "lucide-react"

export function DataGrid({ data, onCellUpdate }) {
  console.log(data)
  const [editingCell, setEditingCell] = useState(null)
  const [editValue, setEditValue] = useState("")

  // Add safety check for data
  if (!data || !data.records || !data.columns) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">No data available</p>
        </div>
      </div>
    )
  }

  const handleCellClick = (row, column, currentValue) => {
    setEditingCell({ row, column })
    setEditValue(String(currentValue || ""))
  }

  const handleCellSave = () => {
    if (editingCell) {
      onCellUpdate(editingCell.row, editingCell.column, editValue)
      setEditingCell(null)
      setEditValue("")
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleCellSave()
    } else if (e.key === "Escape") {
      setEditingCell(null)
      setEditValue("")
    }
  }

  const getColumnType = (column) => {
    // Add safety checks for data and records
    if (!data || !data.records || data.records.length === 0) {
      return "text"
    }

    const sample = data.records.find((record) => record[column] != null)?.[column]
    if (typeof sample === "number") return "number"
    if (typeof sample === "boolean") return "boolean"
    if (sample instanceof Date || /^\d{4}-\d{2}-\d{2}/.test(sample)) return "date"
    return "text"
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case "number":
        return <Hash className="w-3 h-3" />
      case "date":
        return <Calendar className="w-3 h-3" />
      case "boolean":
        return <MoreHorizontal className="w-3 h-3" />
      default:
        return <Type className="w-3 h-3" />
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case "number":
        return "text-blue-600 bg-blue-50"
      case "date":
        return "text-purple-600 bg-purple-50"
      case "boolean":
        return "text-green-600 bg-green-50"
      default:
        return "text-gray-600 bg-gray-50"
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Data View</h2>
          <p className="text-sm text-gray-600">
            Click any cell to edit • {data.shape[0].toLocaleString()} rows × {data.shape[1]} columns
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="badge badge-primary">{(data.shape[0] * data.shape[1]).toLocaleString()} cells</span>
        </div>
      </div>

      {/* Data Grid */}
      <div className="flex-1 card overflow-hidden">
        <div className="h-full overflow-auto custom-scrollbar">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="w-16 px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                  #
                </th>
                {data.columns.map((column) => {
                  const type = getColumnType(column)
                  return (
                    <th
                      key={column}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200 min-w-32"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="truncate font-semibold text-gray-900">{column}</span>
                        <div
                          className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getTypeColor(type)}`}
                        >
                          {getTypeIcon(type)}
                          <span>{type}</span>
                        </div>
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.records.map((record, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm text-gray-500 font-mono border-r border-gray-100">{rowIndex + 1}</td>
                  {data.columns.map((column) => (
                    <td
                      key={`${rowIndex}-${column}`}
                      className="px-4 py-3 text-sm text-gray-900 cursor-pointer hover:bg-blue-50 transition-colors relative group"
                      onClick={() => handleCellClick(rowIndex, column, record[column])}
                    >
                      {editingCell?.row === rowIndex && editingCell?.column === column ? (
                        <input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onBlur={handleCellSave}
                          onKeyDown={handleKeyDown}
                          className="w-full px-2 py-1 text-sm border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                          autoFocus
                        />
                      ) : (
                        <div className="flex items-center justify-between">
                          <span className="truncate">{record[column] != null ? String(record[column]) : ""}</span>
                          <Edit3 className="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
