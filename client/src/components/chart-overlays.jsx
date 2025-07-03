"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "./ui/button"
import { X, Minimize2 } from "lucide-react"
import { useSpreadsheet } from "../lib/spreadsheet-context"

export function ChartOverlays() {
  const { activeSheet, getCharts, updateChart, removeChart } = useSpreadsheet()
  const charts = getCharts(activeSheet)

  const [draggedChart, setDraggedChart] = useState(null)

  const handleChartDrag = (chartId, x, y) => {
    updateChart(activeSheet, chartId, { position: { x, y } })
  }

  const handleChartResize = (chartId, width, height) => {
    updateChart(activeSheet, chartId, { size: { width, height } })
  }

  const toggleMinimize = (chartId) => {
    const chart = charts.find((c) => c.id === chartId)
    if (chart) {
      updateChart(activeSheet, chartId, {
        isMinimized: !chart.isMinimized,
        size: chart.isMinimized ? { width: 400, height: 300 } : { width: 200, height: 40 },
      })
    }
  }

  const handleRemoveChart = (chartId) => {
    removeChart(activeSheet, chartId)
  }

  if (charts.length === 0) return null

  return (
    <div className="absolute inset-0 pointer-events-none z-30">
      {charts.map((chart) => (
        <motion.div
          key={chart.id}
          drag={!chart.isMinimized}
          dragMomentum={false}
          onDrag={(_, info) => {
            if (!chart.isMinimized) {
              handleChartDrag(chart.id, chart.position.x + info.delta.x, chart.position.y + info.delta.y)
            }
          }}
          className="absolute pointer-events-auto"
          style={{
            left: chart.position.x,
            top: chart.position.y,
            width: chart.size.width,
            height: chart.size.height,
            zIndex: draggedChart === chart.id ? 50 : 40,
          }}
          onDragStart={() => setDraggedChart(chart.id)}
          onDragEnd={() => setDraggedChart(null)}
        >
          <div className="w-full h-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg overflow-hidden">
            {/* Chart Header */}
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 cursor-move">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium truncate">{chart.id}</span>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" onClick={() => toggleMinimize(chart.id)} className="h-6 w-6 p-0">
                  <Minimize2 className="w-3 h-3" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleRemoveChart(chart.id)} className="h-6 w-6 p-0">
                  <X className="w-3 h-3" />
                </Button>
              </div>
            </div>

            {/* Chart Content */}
            {!chart.isMinimized && (
              <div className="flex-1 p-4 h-full relative">
                <img
                  src={chart.imageUrl || "/placeholder.svg"}
                  alt={chart.title}
                  className="w-full h-full object-contain rounded"
                  onError={(e) => {
                    const target = e.target
                    target.src = "/placeholder.svg?height=300&width=400&text=Chart+Error"
                  }}
                />

                {/* Resize Handle */}
                <div
                  className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize bg-gray-300 dark:bg-gray-600 opacity-50 hover:opacity-100"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    const startX = e.clientX
                    const startY = e.clientY
                    const startWidth = chart.size.width
                    const startHeight = chart.size.height

                    const handleMouseMove = (e) => {
                      const newWidth = Math.max(200, startWidth + (e.clientX - startX))
                      const newHeight = Math.max(150, startHeight + (e.clientY - startY))
                      handleChartResize(chart.id, newWidth, newHeight)
                    }

                    const handleMouseUp = () => {
                      document.removeEventListener("mousemove", handleMouseMove)
                      document.removeEventListener("mouseup", handleMouseUp)
                    }

                    document.addEventListener("mousemove", handleMouseMove)
                    document.addEventListener("mouseup", handleMouseUp)
                  }}
                />
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}
