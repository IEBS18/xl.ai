"use client"

import { Download, FileText, Copy } from "lucide-react"

export function ReportDisplay({ reports }) {
  const copyReport = (report) => {
    navigator.clipboard.writeText(report)
    // You could add a toast notification here
  }

  const downloadReport = (report, index) => {
    const blob = new Blob([report], { type: "text/plain" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `report_${index + 1}_${new Date().toISOString().split("T")[0]}.txt`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  if (reports.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <FileText className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Reports Generated</h3>
          <p className="text-gray-600 mb-4">Ask the AI assistant to generate comprehensive reports from your data.</p>
          <div className="text-sm text-gray-500">
            <p>Try asking: "Generate a summary report" or "Create a detailed analysis"</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Generated Reports</h2>
        <p className="text-sm text-gray-600">
          {reports.length} report{reports.length !== 1 ? "s" : ""} generated from your data analysis
        </p>
      </div>

      <div className="space-y-6 h-full overflow-auto custom-scrollbar">
        {reports.map((report, index) => (
          <div key={index} className="card overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">Analysis Report {index + 1}</h3>
                  <p className="text-xs text-gray-500">Generated on {new Date().toLocaleDateString()}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => copyReport(report)}
                    className="btn btn-ghost px-3 py-2"
                    title="Copy to clipboard"
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    Copy
                  </button>
                  <button
                    onClick={() => downloadReport(report, index)}
                    className="btn btn-secondary px-3 py-2"
                    title="Download report"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </button>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto custom-scrollbar">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">{report}</pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
