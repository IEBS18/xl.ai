import React, { createContext, useContext, useState } from "react"

const ThemeContext = createContext()

export const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => setIsDark(!isDark)

  const themeClasses = {
    bg: isDark ? "bg-black" : "bg-white",
    text: isDark ? "text-white" : "text-black",
    textSecondary: isDark ? "text-gray-400" : "text-gray-600",
    textMuted: isDark ? "text-gray-500" : "text-gray-400",
    surface: isDark ? "bg-gray-900" : "bg-gray-50",
    surfaceSecondary: isDark ? "bg-gray-800" : "bg-gray-100",
    border: isDark ? "border-gray-800" : "border-gray-200",
    button: isDark ? "bg-white text-black hover:bg-gray-100" : "bg-black text-white hover:bg-gray-900",
    buttonSecondary: isDark
      ? "border-gray-700 text-gray-300 hover:border-gray-600 hover:text-white"
      : "border-gray-300 text-gray-700 hover:border-gray-400 hover:text-black",
    glass: isDark ? "bg-gray-900/50 backdrop-blur-xl border-gray-800" : "bg-white/50 backdrop-blur-xl border-gray-200",
  }

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme, themeClasses }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}