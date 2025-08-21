import React, { useState, useEffect } from 'react'
import { LayoutDashboard, Plus, Calendar, BarChart3, Eye, Trash2 } from 'lucide-react'
import { useTheme } from '@/context/ThemeProvider'
import { BACKEND_URL } from '../utils/constants'
import DashboardView from './DashboardView'

const DashboardList = ({ onClose }) => {
  const { themeClasses } = useTheme()
  const [dashboards, setDashboards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedDashboard, setSelectedDashboard] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newDashboardName, setNewDashboardName] = useState('')
  const [newDashboardDescription, setNewDashboardDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    loadDashboards()
  }, [])

  const loadDashboards = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${BACKEND_URL}/api/dashboards`, {
        credentials: 'include'
      })
      const data = await response.json()
      if (data.success) {
        setDashboards(data.dashboards)
      } else {
        setError(data.error || 'Failed to load dashboards')
      }
    } catch (err) {
      setError('Failed to load dashboards')
      console.error('Error loading dashboards:', err)
    } finally {
      setLoading(false)
    }
  }

  const createDashboard = async () => {
    if (!newDashboardName.trim()) return

    try {
      setIsCreating(true)
      const response = await fetch(`${BACKEND_URL}/api/dashboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name: newDashboardName.trim(),
          description: newDashboardDescription.trim()
        })
      })
      
      const data = await response.json()
      if (data.success) {
        setDashboards(prev => [data.dashboard, ...prev])
        setNewDashboardName('')
        setNewDashboardDescription('')
        setShowCreateForm(false)
      } else {
        setError(data.error || 'Failed to create dashboard')
      }
    } catch (err) {
      setError('Failed to create dashboard')
      console.error('Error creating dashboard:', err)
    } finally {
      setIsCreating(false)
    }
  }

  const deleteDashboard = async (dashboardId) => {
    if (!window.confirm('Are you sure you want to delete this dashboard? This action cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/dashboards/${dashboardId}`, {
        method: 'DELETE',
        credentials: 'include'
      })
      
      const data = await response.json()
      if (data.success) {
        setDashboards(prev => prev.filter(d => d.id !== dashboardId))
      } else {
        setError(data.error || 'Failed to delete dashboard')
      }
    } catch (error) {
      setError('Failed to delete dashboard')
      console.error('Error deleting dashboard:', error)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (selectedDashboard) {
    return (
      <DashboardView 
        dashboardId={selectedDashboard} 
        onClose={() => setSelectedDashboard(null)}
      />
    )
  }

  return (
    <div className={`fixed inset-0 ${themeClasses.bg} z-50 flex flex-col pt-12`}>
      {/* Header */}
      <div className={`${themeClasses.surface} ${themeClasses.border} border-b p-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LayoutDashboard className={`w-8 h-8 ${themeClasses.text}`} />
            <div>
              <h1 className={`text-2xl font-bold ${themeClasses.text}`}>My Dashboards</h1>
              <p className={`${themeClasses.textSecondary}`}>
                Manage and view your visualization dashboards
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowCreateForm(true)}
              className={`flex items-center gap-2 px-4 py-2 ${themeClasses.button} rounded-lg hover:opacity-90 transition-opacity`}
            >
              <Plus className="w-4 h-4" />
              New Dashboard
            </button>
            <button
              onClick={onClose}
              className={`px-4 py-2 ${themeClasses.textSecondary} hover:${themeClasses.text} rounded-lg transition-colors`}
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
              <span className={themeClasses.text}>Loading dashboards...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-red-500 mb-4">Error: {error}</div>
              <button
                onClick={loadDashboards}
                className={`px-4 py-2 ${themeClasses.button} rounded-lg`}
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto">
            {/* Create New Dashboard Form */}
            {showCreateForm && (
              <div className={`${themeClasses.surface} ${themeClasses.border} border rounded-lg p-6 mb-6`}>
                <h3 className={`text-lg font-medium ${themeClasses.text} mb-4`}>Create New Dashboard</h3>
                <div className="space-y-4">
                  <div>
                    <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
                      Dashboard Name *
                    </label>
                    <input
                      type="text"
                      value={newDashboardName}
                      onChange={(e) => setNewDashboardName(e.target.value)}
                      placeholder="Enter dashboard name"
                      className={`w-full p-3 ${themeClasses.surface} ${themeClasses.border} border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${themeClasses.text} mb-2`}>
                      Description (optional)
                    </label>
                    <textarea
                      value={newDashboardDescription}
                      onChange={(e) => setNewDashboardDescription(e.target.value)}
                      placeholder="Describe what this dashboard will contain"
                      rows={3}
                      className={`w-full p-3 ${themeClasses.surface} ${themeClasses.border} border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none`}
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={createDashboard}
                      disabled={!newDashboardName.trim() || isCreating}
                      className={`px-4 py-2 ${themeClasses.button} rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {isCreating ? 'Creating...' : 'Create Dashboard'}
                    </button>
                    <button
                      onClick={() => {
                        setShowCreateForm(false)
                        setNewDashboardName('')
                        setNewDashboardDescription('')
                      }}
                      className={`px-4 py-2 ${themeClasses.textSecondary} hover:${themeClasses.text} rounded-lg transition-colors`}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Dashboard Grid */}
            {dashboards.length === 0 ? (
              <div className="text-center py-16">
                <LayoutDashboard className={`w-16 h-16 ${themeClasses.textSecondary} mx-auto mb-4`} />
                <h3 className={`text-lg font-medium ${themeClasses.text} mb-2`}>No dashboards yet</h3>
                <p className={`${themeClasses.textSecondary} mb-6`}>
                  Create your first dashboard to start organizing your visualizations
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className={`flex items-center gap-2 px-4 py-2 ${themeClasses.button} rounded-lg hover:opacity-90 transition-opacity mx-auto`}
                >
                  <Plus className="w-4 h-4" />
                  Create Your First Dashboard
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashboards.map((dashboard) => (
                  <DashboardCard
                    key={dashboard.id}
                    dashboard={dashboard}
                    onView={() => setSelectedDashboard(dashboard.id)}
                    onDelete={() => deleteDashboard(dashboard.id)}
                    themeClasses={themeClasses}
                    formatDate={formatDate}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Individual Dashboard Card Component
const DashboardCard = ({ dashboard, onView, onDelete, themeClasses, formatDate }) => {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className={`${themeClasses.surface} ${themeClasses.border} border rounded-lg p-6 transition-all hover:shadow-lg cursor-pointer`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onView}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 ${themeClasses.surfaceSecondary} rounded-lg`}>
            <LayoutDashboard className={`w-5 h-5 ${themeClasses.text}`} />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className={`font-medium ${themeClasses.text} truncate`}>
              {dashboard.name}
            </h3>
            {dashboard.description && (
              <p className={`text-sm ${themeClasses.textSecondary} line-clamp-2 mt-1`}>
                {dashboard.description}
              </p>
            )}
          </div>
        </div>
        {isHovered && (
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={onView}
              className={`p-1 ${themeClasses.textSecondary} hover:${themeClasses.text} rounded transition-colors`}
              title="View dashboard"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={onDelete}
              className={`p-1 ${themeClasses.textSecondary} hover:text-red-500 rounded transition-colors`}
              title="Delete dashboard"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {/* Stats */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <BarChart3 className={`w-4 h-4 ${themeClasses.textSecondary}`} />
            <span className={`text-sm ${themeClasses.textSecondary}`}>
              {dashboard.visualization_count} chart{dashboard.visualization_count !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Date */}
        <div className="flex items-center gap-1">
          <Calendar className={`w-4 h-4 ${themeClasses.textSecondary}`} />
          <span className={`text-sm ${themeClasses.textSecondary}`}>
            Created {formatDate(dashboard.created_at)}
          </span>
        </div>

        {/* Action Button */}
        <button
          onClick={onView}
          className={`w-full mt-4 py-2 px-4 ${themeClasses.button} rounded-lg hover:opacity-90 transition-opacity text-sm font-medium`}
        >
          Open Dashboard
        </button>
      </div>
    </div>
  )
}

export default DashboardList