import React from "react"
import { Check, Code, BarChart3, Database, CheckCircle, Loader2 } from "lucide-react"

const AnimatedInterface = () => {
  return (
    <div className="absolute inset-0 z-10">
      {/* Timeline Animation */}
      <div className="absolute top-8 left-8 w-64 opacity-50 animate-float-1">
        <div className="bg-gray-800/90 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-6 h-6 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-lg">
              <Check size={12} className="text-white" />
            </div>
            <span className="text-green-400 text-sm font-semibold">Completed</span>
          </div>
          <p className="text-gray-200 text-xs">Analyzing query: Forecast next 12 months of sales</p>
        </div>
      </div>

      {/* Code Block Animation */}
      <div className="absolute top-24 right-12 w-60 opacity-45 animate-float-2">
        <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
          <div className="flex items-center space-x-2 mb-3">
            <Code size={14} className="text-purple-400" />
            <span className="text-purple-400 text-sm font-semibold">Generated Code</span>
          </div>
          <div className="bg-gray-950/90 rounded-lg p-3 text-xs font-mono border border-gray-700/50">
            <div className="text-green-400 mb-1">import pandas as pd</div>
            <div className="text-green-400 mb-1">import numpy as np</div>
            <div className="text-blue-400 mb-1"># Statistical forecasting</div>
            <div className="text-yellow-400">model = SARIMAX(data)</div>
          </div>
        </div>
      </div>

      {/* Chart Visualization */}
      <div className="absolute bottom-24 left-16 w-60 opacity-50 animate-float-3">
        <div className="bg-gray-800/90 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
          <div className="flex items-center space-x-2 mb-3">
            <BarChart3 size={14} className="text-orange-400" />
            <span className="text-orange-400 text-sm font-semibold">Visualization</span>
          </div>
          <div className="bg-white rounded-lg p-3 h-20 flex items-center justify-center shadow-inner">
            <div className="w-full h-full bg-gradient-to-r from-blue-100 to-purple-100 rounded flex items-center justify-center">
              <span className="text-gray-600 text-xs font-medium">Revenue Forecast Chart</span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="absolute bottom-12 right-8 w-54 opacity-45 animate-float-4">
        <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
          <div className="flex items-center space-x-2 mb-3">
            <Database size={14} className="text-cyan-400" />
            <span className="text-cyan-400 text-sm font-semibold">Data Analysis</span>
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="text-cyan-300">Shape: 12 rows × 2 columns</div>
            <div className="text-gray-300">Historical Revenue Analysis</div>
            <div className="text-gray-400 text-xs">Confidence intervals calculated</div>
          </div>
        </div>
      </div>

      {/* Success Message */}
      <div className="absolute top-48 left-24 w-60 opacity-50 animate-float-5">
        <div className="bg-gradient-to-r from-green-900/70 to-emerald-900/70 backdrop-blur-md rounded-2xl p-4 border border-green-600/60 shadow-2xl">
          <div className="flex items-center space-x-2">
            <CheckCircle size={14} className="text-green-300" />
            <span className="text-green-200 text-sm font-semibold">Analysis completed successfully</span>
          </div>
          <p className="text-green-100 text-xs mt-1">Generated 4 result DataFrames</p>
        </div>
      </div>

      {/* Processing Status */}
      <div className="absolute top-60 right-24 w-54 opacity-45 animate-float-6">
        <div className="bg-gradient-to-r from-blue-900/70 to-indigo-900/70 backdrop-blur-md rounded-2xl p-4 border border-blue-600/60 shadow-2xl">
          <div className="flex items-center space-x-2">
            <Loader2 size={14} className="text-blue-300 animate-spin" />
            <span className="text-blue-200 text-sm font-semibold">Generating insights</span>
          </div>
          <p className="text-blue-100 text-xs mt-1">Processing advanced analytics</p>
        </div>
      </div>
    </div>
  )
}

export default AnimatedInterface