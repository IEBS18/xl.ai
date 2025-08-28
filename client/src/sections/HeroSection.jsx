import React, { useState, useRef, useEffect } from "react"
import { Send, Plus, Upload, Database } from "lucide-react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import { getTimeBasedGreeting } from "../utils/helpers"
import AnimatedInterface from "../components/AnimatedInterface"
import AuthModal from "../components/AuthModal"

const HeroSection = ({ isConnected, onSendMessage, onFileUpload, onDatabaseConnect, uploadProgress = 0 }) => {
  const { isDark, themeClasses } = useTheme()
  const { isAuthenticated, user, isLoading, login, register } = useAuth()
  const [inputMessage, setInputMessage] = useState("")
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
  const [showDataSourceDropdown, setShowDataSourceDropdown] = useState(false)
  const heroRef = useRef(null)

  useEffect(() => {
    if (isAuthenticated && authModal.isOpen) {
      closeAuthModal()
    }
  }, [isAuthenticated, authModal.isOpen])

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDataSourceDropdown && !event.target.closest('.relative')) {
        setShowDataSourceDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDataSourceDropdown])

  const openAuthModal = (mode = "login") => {
    setAuthModal({ isOpen: true, mode })
  }

  const closeAuthModal = () => {
    setAuthModal({ isOpen: false, mode: "login" })
  }

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !isConnected) return

    if (!isAuthenticated) {
      openAuthModal('login')
      return
    }

    onSendMessage(inputMessage)
    setInputMessage("")
  }

  const handleFileUpload = () => {
    if (!isAuthenticated) {
      openAuthModal('login')
      return
    }

    setShowDataSourceDropdown(false)
    onFileUpload()
  }

  const handleDatabaseConnect = () => {
    if (!isAuthenticated) {
      openAuthModal('login')
      return
    }

    setShowDataSourceDropdown(false)
    onDatabaseConnect()
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getUserName = () => {
    return isAuthenticated && user?.name ? user.name : "there"
  }

  return (
    <>
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="relative h-full w-full overflow-hidden">
            {/* Background elements */}
            <div className="absolute inset-0 z-0">
              <div className={`absolute inset-0 z-20`}></div>
              <AnimatedInterface />
            </div>

            {/* Main content */}
            <div className="relative z-20 flex flex-col items-center justify-center h-full text-center max-w-4xl mx-auto px-6">
              <div className="mb-8">
                <h1 className={`text-4xl font-black text-transparent bg-clip-text ${isDark ? 'bg-gradient-to-r from-white via-gray-200 to-gray-300' : 'bg-gradient-to-r from-[#04165D] via-[#04165de6] to-[#04134f]'} mb-3`}>
                  {getTimeBasedGreeting()}, {getUserName()}
                </h1>
                <div className={`h-0.5 w-24 ${isDark 
                    ? 'bg-gradient-to-r from-white/60 via-white/80 to-white/60' 
                    : 'bg-gradient-to-r from-black/60 via-black/80 to-black/60'
                  } mx-auto rounded-full shadow-lg`}></div>
                <p
                  className={`text-lg ${themeClasses.textSecondary} mb-2 font-light tracking-wide`}
                  style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                >
                  {isAuthenticated ? "Welcome back to InsiPredict" : "Welcome to InsiPredict"}
                </p>
                <p
                  className={`text-sm ${themeClasses.textMuted} font-light tracking-wide`}
                  style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                >
                  {isAuthenticated 
                    ? "Ready to unlock insights from your data?" 
                    : "Sign in to unlock insights from your data"
                  }
                </p>
              </div>

              <div className="w-full max-w-2xl mb-10 animate-slideIn" style={{ animationDelay: "0.3s" }}>
                <div className="relative group">
                  <div className={`absolute -inset-1 ${isDark 
                    ? 'bg-gradient-to-r from-white/10 via-white/5 to-white/10' 
                    : 'bg-gradient-to-r from-black/10 via-black/5 to-black/10'
                  } rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-300`}></div>
                  <div className="relative">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={
                        !isConnected
                          ? "Connecting to server..."
                          : !isAuthenticated
                          ? "Sign in to upload files and analyze data..."
                          : uploadProgress > 0
                          ? `Uploading... ${uploadProgress}%`
                          : "Upload a file or describe what you'd like to analyze..."
                      }
                      disabled={!isConnected || uploadProgress > 0}
                      className={`w-full px-6 py-4 ${isDark 
                        ? 'bg-black/20 border-white/20 text-white placeholder-gray-400' 
                        : 'bg-white/80 border-black/20 text-black placeholder-gray-600'
                      } backdrop-blur-xl rounded-2xl focus:outline-none focus:ring-2 ${isDark 
                        ? 'focus:ring-white/30 focus:border-white/30' 
                        : 'focus:ring-black/30 focus:border-black/30'
                      } disabled:opacity-50 disabled:cursor-not-allowed text-base shadow-2xl transition-all duration-300 font-light`}
                      style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                    />
                    
                    {/* Upload Progress Bar */}
                    {uploadProgress > 0 && (
                      <div className="absolute bottom-0 left-0 w-full">
                        <div className="w-full bg-transparent rounded-b-2xl overflow-hidden">
                          <div 
                            className="h-1 bg-blue-500 transition-all duration-300 rounded-b-2xl"
                            style={{ width: `${uploadProgress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                    
                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-3">
                      <div className="relative">
                        <button
                          onClick={() => setShowDataSourceDropdown(!showDataSourceDropdown)}
                          disabled={uploadProgress > 0}
                          className={`p-2 ${themeClasses.textMuted} hover:${themeClasses.text} ${isDark 
                            ? 'hover:bg-white/10' 
                            : 'hover:bg-black/10'
                          } transition-all duration-200 rounded-xl backdrop-blur-sm group-hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                            !isAuthenticated ? 'relative' : ''
                          }`}
                          title={
                            uploadProgress > 0 
                              ? "Upload in progress..." 
                              : isAuthenticated 
                              ? "Add data source" 
                              : "Sign in to add data sources"
                          }
                        >
                          <Plus size={18} />
                          {!isAuthenticated && (
                            <div className={`absolute -top-1 -right-1 w-3 h-3 ${isDark ? 'bg-white' : 'bg-black'} rounded-full flex items-center justify-center`}>
                              <span className={`text-xs font-bold ${isDark ? 'text-black' : 'text-white'}`}>!</span>
                            </div>
                          )}
                        </button>
                        
                        {/* Data Source Dropdown */}
                        {showDataSourceDropdown && isAuthenticated && (
                          <div className={`absolute bottom-full mb-2 right-0 ${isDark 
                            ? 'bg-black/80 border-white/20' 
                            : 'bg-white/90 border-black/20'
                          } backdrop-blur-xl rounded-xl shadow-2xl border min-w-48 z-60`}>
                            <div className="p-2">
                              <button
                                onClick={handleFileUpload}
                                className={`w-full flex items-center space-x-3 p-3 ${isDark 
                                  ? 'hover:bg-white/10 text-white' 
                                  : 'hover:bg-black/10 text-black'
                                } rounded-lg transition-all duration-200 text-left`}
                              >
                                <Upload size={16} />
                                <div>
                                  <div className="font-medium">Upload Files</div>
                                  {/* <div className={`text-xs ${themeClasses.textMuted}`}>CSV, Excel files</div> */}
                                </div>
                              </button>
                              <button
                                onClick={handleDatabaseConnect}
                                className={`w-full flex items-center space-x-3 p-3 ${isDark 
                                  ? 'hover:bg-white/10 text-white' 
                                  : 'hover:bg-black/10 text-black'
                                } rounded-lg transition-all duration-200 text-left`}
                              >
                                <Database size={16} />
                                <div>
                                  <div className="font-medium">Connect Database</div>
                                  {/* <div className={`text-xs ${themeClasses.textMuted}`}>PostgreSQL, MySQL, SQLite</div> */}
                                </div>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || !isConnected || uploadProgress > 0}
                        className={`${themeClasses.button} p-2 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl transform hover:scale-105 disabled:transform-none backdrop-blur-sm ${
                          !isAuthenticated && inputMessage.trim() ? 'relative' : ''
                        }`}
                        title={
                          !isConnected 
                            ? "Connecting..." 
                            : uploadProgress > 0
                            ? "Upload in progress..."
                            : !isAuthenticated && inputMessage.trim()
                            ? "Sign in to send messages"
                            : "Send message"
                        }
                      >
                        <Send size={18} />
                        {!isAuthenticated && inputMessage.trim() && (
                          <div className={`absolute -top-1 -right-1 w-3 h-3 ${isDark ? 'bg-white' : 'bg-black'} rounded-full flex items-center justify-center`}>
                            <span className={`text-xs font-bold ${isDark ? 'text-black' : 'text-white'}`}>!</span>
                          </div>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  {/* Authentication prompt for non-logged-in users */}
                  {!isAuthenticated && uploadProgress === 0 && (
                    <div className="mt-4 text-center">
                      <p className={`text-sm ${themeClasses.textMuted} mb-3`}>
                        Sign in to access all features
                      </p>
                    </div>
                  )}

                  {/* Upload status for authenticated users */}
                  {isAuthenticated && uploadProgress > 0 && (
                    <div className="mt-4 text-center">
                      <p className={`text-sm ${themeClasses.textSecondary} mb-2`}>
                        Processing your file...
                      </p>
                      <p className={`text-xs ${themeClasses.textMuted}`}>
                        You'll be redirected to the analysis interface once upload is complete
                      </p>
                    </div>
                  )}
                </div>

                {/* Refined Feature Info */}
                <div className="text-center animate-slideIn" style={{ animationDelay: "0.6s" }}>
                  <div className={`${themeClasses.textMuted} space-y-4`}>
                    <p
                      className={`font-medium text-base ${themeClasses.textSecondary}`}
                      style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                    >
                      Supports seamless CSV and Excel data analysis
                    </p>
                    <div className="flex items-center justify-center space-x-8 text-sm">
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className={`w-2 h-2 ${isDark ? 'bg-white' : 'bg-black'} rounded-full shadow-lg group-hover:shadow-lg transition-all duration-300`}></div>
                        <span
                          className={`font-medium ${themeClasses.textSecondary}`}
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Real-time Analysis
                        </span>
                      </span>
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className={`w-2 h-2 ${isDark ? 'bg-white' : 'bg-black'} rounded-full shadow-lg group-hover:shadow-lg transition-all duration-300`}></div>
                        <span
                          className={`font-medium ${themeClasses.textSecondary}`}
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Interactive Charts
                        </span>
                      </span>
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className={`w-2 h-2 ${isDark ? 'bg-white' : 'bg-black'} rounded-full shadow-lg group-hover:shadow-lg transition-all duration-300`}></div>
                        <span
                          className={`font-medium ${themeClasses.textSecondary}`}
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Strategic Reports
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <AuthModal
        isOpen={authModal.isOpen}
        mode={authModal.mode}
        onClose={closeAuthModal}
        onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
      />
    </>
  )
}

export default HeroSection