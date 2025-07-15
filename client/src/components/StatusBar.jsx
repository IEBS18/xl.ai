import { Activity, Database, Zap } from "lucide-react"

export function StatusBar({ data, analysisStatus, connected }) {
  return (
    <footer className="bg-white border-t border-gray-200 px-6 py-2">
      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center space-x-4">
          {data && (
            <>
              <div className="flex items-center space-x-1">
                <Database className="w-3 h-3" />
                <span>Dataset loaded</span>
              </div>
              <span className="text-gray-400">•</span>
              <span>{data.shape[0] * data.shape[1]} total cells</span>
            </>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {analysisStatus && (
            <div className="flex items-center space-x-1 text-primary-600">
              <Activity className="w-3 h-3 animate-pulse" />
              <span>{analysisStatus.data?.message || "Processing..."}</span>
            </div>
          )}

          <div className="flex items-center space-x-1">
            <Zap className={`w-3 h-3 ${connected ? "text-green-500" : "text-gray-400"}`} />
            <span>AI {connected ? "Ready" : "Offline"}</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
