"use client"

import { Download, BarChart3, Maximize2 } from "lucide-react"

export function ChartDisplay({ charts }) {
  const downloadChart = (chart) => {
    const link = document.createElement("a")
    link.href = chart.image_data
    link.download = chart.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (charts.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <BarChart3 className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Charts Generated</h3>
          <p className="text-gray-600 mb-4">Ask the AI assistant to create visualizations from your data.</p>
          <div className="text-sm text-gray-500">
            <p>Try asking: "Create a bar chart of sales by region" or "Show me a trend analysis"</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Generated Charts</h2>
        <p className="text-sm text-gray-600">
          {charts.length} visualization{charts.length !== 1 ? "s" : ""} generated from your data
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full overflow-auto custom-scrollbar">
        {charts.map((chart, index) => (
          <div key={index} className="card overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">Chart {index + 1}</h3>
                  <p className="text-xs text-gray-500">{chart.filename}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="btn btn-ghost p-2" title="Expand">
                    <Maximize2 className="w-4 h-4" />
                  </button>
                  <button onClick={() => downloadChart(chart)} className="btn btn-secondary px-3 py-2" title="Download">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            <div className="p-4">
              <div className="relative bg-white rounded-lg border border-gray-200 overflow-hidden">
                <img
                  src={chart.image_data || "/placeholder.svg?height=300&width=400"}
                  alt={chart.filename}
                  className="w-full h-auto"
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
