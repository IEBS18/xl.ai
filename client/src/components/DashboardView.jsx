import React, { useState, useEffect, useRef } from 'react'
import { X, LayoutDashboard, Trash2, Move, Settings } from 'lucide-react'
import { useTheme } from '@/context/ThemeProvider'
import { BACKEND_URL } from '../utils/constants'

const DashboardView = ({ dashboardId, onClose }) => {
  const { themeClasses } = useTheme()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedViz, setSelectedViz] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isResizing, setIsResizing] = useState(false)
  const dragRef = useRef(null)

  useEffect(() => {
    loadDashboard()
  }, [dashboardId])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${BACKEND_URL}/api/dashboards/${dashboardId}`, {
        credentials: 'include'
      })
      const data = await response.json()
      if (data.success) {
        setDashboard(data.dashboard)
      } else {
        setError(data.error || 'Failed to load dashboard')
      }
    } catch (err) {
      setError('Failed to load dashboard')
      console.error('Error loading dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const updateVisualizationPosition = async (vizId, position) => {
    try {
      // Update local state immediately for smooth UX
      setDashboard(prev => ({
        ...prev,
        visualizations: prev.visualizations.map(viz => 
          viz.id === vizId ? { ...viz, position } : viz
        )
      }))

      // Update position in backend
      await fetch(`${BACKEND_URL}/api/dashboards/${dashboardId}/visualizations/${vizId}/position`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(position)
      })
    } catch (error) {
      console.error('Error updating position:', error)
      // Reload dashboard on error to revert changes
      loadDashboard()
    }
  }

  const removeVisualization = async (vizId) => {
    if (!window.confirm('Are you sure you want to remove this visualization from the dashboard?')) {
      return
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/dashboards/${dashboardId}/visualizations/${vizId}`, {
        method: 'DELETE',
        credentials: 'include'
      })
      
      const data = await response.json()
      if (data.success) {
        setDashboard(prev => ({
          ...prev,
          visualizations: prev.visualizations.filter(viz => viz.id !== vizId)
        }))
      } else {
        console.error('Failed to remove visualization:', data.error)
      }
    } catch (error) {
      console.error('Error removing visualization:', error)
    }
  }

  const handleMouseDown = (e, vizId) => {
    if (e.target.closest('.resize-handle') || e.target.closest('.viz-controls')) {
      return
    }

    setSelectedViz(vizId)
    setIsDragging(true)
    
    const rect = e.currentTarget.getBoundingClientRect()
    setDragStart({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    })
    
    e.preventDefault()
  }

  const handleMouseMove = (e) => {
    if (!isDragging || !selectedViz) return

    const container = e.currentTarget.getBoundingClientRect()
    const newX = Math.max(0, Math.min(e.clientX - container.left - dragStart.x, container.width - 400))
    const newY = Math.max(0, Math.min(e.clientY - container.top - dragStart.y, container.height - 300))

    const viz = dashboard?.visualizations.find(v => v.id === selectedViz)
    if (viz) {
      updateVisualizationPosition(selectedViz, {
        ...viz.position,
        x: newX,
        y: newY
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setSelectedViz(null)
  }

  const handleResize = (vizId, newSize) => {
    const viz = dashboard?.visualizations.find(v => v.id === vizId)
    if (viz) {
      updateVisualizationPosition(vizId, {
        ...viz.position,
        width: Math.max(200, newSize.width),
        height: Math.max(150, newSize.height)
      })
    }
  }

  if (loading) {
    return (
      <div className={`fixed inset-0 ${themeClasses.bg} z-50 flex items-center justify-center`}>
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span className={themeClasses.text}>Loading dashboard...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`fixed inset-0 ${themeClasses.bg} z-50 flex items-center justify-center`}>
        <div className="text-center">
          <div className={`text-red-500 mb-4`}>Error: {error}</div>
          <button
            onClick={onClose}
            className={`px-4 py-2 ${themeClasses.button} rounded-lg`}
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  if (!dashboard) {
    return null
  }

  return (
    <div className={`fixed inset-0 ${themeClasses.bg} z-50 flex flex-col`}>
      {/* Header */}
      <div className={`${themeClasses.surface} ${themeClasses.border} border-b p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LayoutDashboard className={`w-6 h-6 ${themeClasses.text}`} />
            <div>
              <h1 className={`text-xl font-bold ${themeClasses.text}`}>{dashboard.name}</h1>
              {dashboard.description && (
                <p className={`text-sm ${themeClasses.textSecondary}`}>{dashboard.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-sm ${themeClasses.textSecondary}`}>
              {dashboard.visualizations.length} visualization{dashboard.visualizations.length !== 1 ? 's' : ''}
            </span>
            <button
              onClick={onClose}
              className={`p-2 ${themeClasses.textSecondary} hover:${themeClasses.text} hover:${themeClasses.surfaceSecondary} rounded-lg transition-colors`}
              title="Close dashboard"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard Canvas */}
      <div 
        className="flex-1 relative overflow-hidden select-none"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {dashboard.visualizations.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <LayoutDashboard className={`w-16 h-16 ${themeClasses.textSecondary} mx-auto mb-4`} />
              <h3 className={`text-lg font-medium ${themeClasses.text} mb-2`}>No visualizations yet</h3>
              <p className={`${themeClasses.textSecondary}`}>
                Add charts to this dashboard from the chat interface
              </p>
            </div>
          </div>
        ) : (
          dashboard.visualizations.map((viz) => (
            <VisualizationWidget
              key={viz.id}
              visualization={viz}
              isSelected={selectedViz === viz.id}
              onMouseDown={(e) => handleMouseDown(e, viz.id)}
              onResize={(newSize) => handleResize(viz.id, newSize)}
              onRemove={() => removeVisualization(viz.id)}
              themeClasses={themeClasses}
            />
          ))
        )}
      </div>
    </div>
  )
}

// Individual visualization widget component
const VisualizationWidget = ({ 
  visualization, 
  isSelected, 
  onMouseDown, 
  onResize, 
  onRemove,
  themeClasses 
}) => {
  const [isHovered, setIsHovered] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 })

  const handleResizeStart = (e) => {
    e.stopPropagation()
    setIsResizing(true)
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: visualization.position.width,
      height: visualization.position.height
    })
  }

  const handleResizeMove = (e) => {
    if (!isResizing) return
    
    const deltaX = e.clientX - resizeStart.x
    const deltaY = e.clientY - resizeStart.y
    
    onResize({
      width: resizeStart.width + deltaX,
      height: resizeStart.height + deltaY
    })
  }

  const handleResizeEnd = () => {
    setIsResizing(false)
  }

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove)
      document.addEventListener('mouseup', handleResizeEnd)
      
      return () => {
        document.removeEventListener('mousemove', handleResizeMove)
        document.removeEventListener('mouseup', handleResizeEnd)
      }
    }
  }, [isResizing, resizeStart])

  return (
    <div
      className={`absolute ${themeClasses.surface} ${themeClasses.border} border rounded-lg shadow-lg overflow-hidden cursor-move transition-all ${
        isSelected ? 'ring-2 ring-blue-500 shadow-xl' : ''
      }`}
      style={{
        left: visualization.position.x,
        top: visualization.position.y,
        width: visualization.position.width,
        height: visualization.position.height,
      }}
      onMouseDown={onMouseDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className={`${themeClasses.surfaceSecondary} ${themeClasses.border} border-b p-2 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Move className={`w-4 h-4 ${themeClasses.textSecondary}`} />
          <span className={`text-sm font-medium ${themeClasses.text} truncate`}>
            {visualization.title}
          </span>
        </div>
        {(isHovered || isSelected) && (
          <div className="viz-controls flex items-center gap-1">
            <button
              onClick={onRemove}
              className={`p-1 ${themeClasses.textSecondary} hover:text-red-500 rounded transition-colors`}
              title="Remove from dashboard"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-2 h-full">
        {visualization.chart_type === 'image' && visualization.chart_data ? (
          <img
            src={visualization.chart_data}
            alt={visualization.title}
            className="w-full h-full object-contain rounded"
            draggable={false}
          />
        ) : (
          <div className={`w-full h-full flex items-center justify-center ${themeClasses.surfaceSecondary} rounded`}>
            <span className={`text-sm ${themeClasses.textSecondary}`}>
              No preview available
            </span>
          </div>
        )}
      </div>

      {/* Resize Handle */}
      {(isHovered || isSelected) && (
        <div
          className="resize-handle absolute bottom-0 right-0 w-4 h-4 bg-gray-400 cursor-se-resize"
          onMouseDown={handleResizeStart}
          style={{
            clipPath: 'polygon(100% 0%, 0% 100%, 100% 100%)'
          }}
        />
      )}
    </div>
  )
}

export default DashboardView