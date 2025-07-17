import React, { useState, useRef } from "react"
import { Send, Paperclip } from "lucide-react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"
import { getTimeBasedGreeting } from "../utils/helpers"
import AnimatedInterface from "../components/AnimatedInterface"

const HeroSection = ({ isConnected, onSendMessage, onFileUpload }) => {
  const { isDark, themeClasses } = useTheme()
  const [inputMessage, setInputMessage] = useState("")
  const heroRef = useRef(null)

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !isConnected) return
    onSendMessage(inputMessage)
    setInputMessage("")
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      {/* Three.js Background */}
      {/* <ThreeBackground ref={heroRef} /> */}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="relative h-full w-full overflow-hidden">
          {/* Background with enhanced visibility - Pure black/white theme */}
          <div className="absolute inset-0 z-0">
            <div className={`absolute inset-0 ${isDark 
              ? 'bg-gradient-to-br from-black/60 via-gray-900/70 to-black/80' 
              : 'bg-gradient-to-br from-white/60 via-gray-100/70 to-white/80'
            } z-20`}></div>

            {/* Animated Interface Screenshots */}
            <AnimatedInterface />

            {/* Enhanced ambient background elements - Pure black/white */}
            <div
              className={`absolute top-1/4 left-1/4 w-64 h-64 ${isDark 
                ? 'bg-white/3' 
                : 'bg-black/3'
              } rounded-full blur-3xl animate-bounce`}
              style={{ animationDuration: "8s" }}
            ></div>
            <div
              className={`absolute bottom-1/4 right-1/4 w-56 h-56 ${isDark 
                ? 'bg-white/2' 
                : 'bg-black/2'
              } rounded-full blur-3xl animate-pulse`}
              style={{ animationDuration: "10s" }}
            ></div>
            <div
              className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 ${isDark 
                ? 'bg-white/2' 
                : 'bg-black/2'
              } rounded-full blur-3xl animate-ping`}
              style={{ animationDuration: "12s" }}
            ></div>
          </div>

          {/* Content */}
          <div className="relative z-20 flex flex-col items-center justify-center h-full text-center max-w-4xl mx-auto px-6">
            {/* Stylish Greeting */}
            <div className="mb-8 animate-fadeIn">
              <div className="mb-4">
                <h1
                  className={`text-4xl font-black text-transparent bg-clip-text ${isDark 
                    ? 'bg-gradient-to-r from-white via-gray-200 to-gray-300' 
                    : 'bg-gradient-to-r from-black via-gray-800 to-gray-900'
                  } mb-3 tracking-tight leading-none`}
                  style={{ fontFamily: "SF Pro Display, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                >
                  {getTimeBasedGreeting()}, Ayush
                </h1>
                <div className={`h-0.5 w-24 ${isDark 
                  ? 'bg-gradient-to-r from-white/60 via-white/80 to-white/60' 
                  : 'bg-gradient-to-r from-black/60 via-black/80 to-black/60'
                } mx-auto rounded-full shadow-lg`}></div>
              </div>
              <p
                className={`text-lg ${themeClasses.textSecondary} mb-2 font-light tracking-wide`}
                style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
              >
                Welcome back to InsiPredict
              </p>
              <p
                className={`text-sm ${themeClasses.textMuted} font-light tracking-wide`}
                style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
              >
                Ready to unlock insights from your data?
              </p>
            </div>

            {/* Enhanced Central Input Area */}
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
                        : "Upload a file or describe what you'd like to analyze..."
                    }
                    disabled={!isConnected}
                    className={`w-full px-6 py-4 ${isDark 
                      ? 'bg-black/20 border-white/20 text-white placeholder-gray-400' 
                      : 'bg-white/80 border-black/20 text-black placeholder-gray-600'
                    } backdrop-blur-xl rounded-2xl focus:outline-none focus:ring-2 ${isDark 
                      ? 'focus:ring-white/30 focus:border-white/30' 
                      : 'focus:ring-black/30 focus:border-black/30'
                    } disabled:opacity-50 disabled:cursor-not-allowed text-base shadow-2xl transition-all duration-300 font-light`}
                    style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                  />
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-3">
                    <button
                      onClick={onFileUpload}
                      className={`p-2 ${themeClasses.textMuted} hover:${themeClasses.text} ${isDark 
                        ? 'hover:bg-white/10' 
                        : 'hover:bg-black/10'
                      } transition-all duration-200 rounded-xl backdrop-blur-sm group-hover:scale-105`}
                      title="Upload file"
                    >
                      <Paperclip size={18} />
                    </button>
                    <button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || !isConnected}
                      className={`${themeClasses.button} p-2 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl transform hover:scale-105 disabled:transform-none backdrop-blur-sm`}
                    >
                      <Send size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Refined Feature Info */}
            <div className="text-center animate-slideIn" style={{ animationDelay: "0.6s" }}>
              <div className={`${themeClasses.textMuted} space-y-4`}>
                <p
                  className={`font-medium text-base ${themeClasses.textSecondary}`}
                  style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                >
                  Supports CSV, Excel files up to 50MB
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
    </section>
  )
}

export default HeroSection