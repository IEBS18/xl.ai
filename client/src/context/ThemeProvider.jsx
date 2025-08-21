import React, { createContext, useContext, useState, useEffect } from "react"

const ThemeContext = createContext()

export const ThemeProvider = ({ children }) => {
  // Detect system theme preference
  const getSystemTheme = () => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return true // Dark mode
    }
    return false // Light mode
  }

  const [isDark, setIsDark] = useState(getSystemTheme)

  const toggleTheme = () => setIsDark(!isDark)

  const themeClasses = {
    // Main backgrounds
    bg: isDark ? "bg-black" : "bg-white",
    
    // Text colors
    text: isDark ? "text-white" : "text-[#04165D]",
    textSecondary: isDark ? "text-gray-300" : "text-gray-700",
    textMuted: isDark ? "text-gray-400" : "text-gray-500",
    textOnGradient: "text-white", // Always white on gradients
    
    // Surface colors
    surface: isDark ? "bg-[#101828]" : "bg-[#F9FAFB]",
    surfaceSecondary: isDark ? "bg-[#1E2939]" : "bg-gray-50",
    surfaceCard: isDark ? "bg-black" : "bg-white",
    
    // Border colors
    border: isDark ? "border-gray-700" : "border-gray-200",
    borderSecondary: isDark ? "border-[#1E2939]" : "border-gray-100",
    
    // Button styles
    button: isDark 
      ? "bg-gradient-to-r from-[#29CFF8] to-[#187A92] text-white hover:from-[#32C9F0] hover:to-[#1D748A]"
      : "bg-gradient-to-r from-[#04165D] to-[#082EC3] text-white hover:from-[#011D89] hover:to-[#000723]",
    
    buttonSecondary: isDark
      ? "border-[#1E2939] text-gray-300 hover:border-[#32C9F0] hover:text-[#32C9F0]"
      : "border-gray-300 text-gray-700 hover:border-[#04165D] hover:text-[#04165D]",
    
    // Special elements
    glass: isDark 
      ? "bg-black/50 backdrop-blur-xl border-[#1E2939]" 
      : "bg-white/50 backdrop-blur-xl border-gray-200",
    
    // Chart/data visualization
    chartBar: isDark
      ? "bg-gradient-to-t from-[#1D748A] to-[#32C9F0]"
      : "bg-gradient-to-r from-[#04165D] to-[#000723]",
    
    // Feature cards
    featureCard: isDark
      ? "bg-gradient-to-b from-[#082EC3]/50 to-[#000B35]/50"
      : "bg-gradient-to-br from-[#011D89] to-[#00092B]",
    
    // Icon containers
    iconContainer: isDark
      ? "bg-[#1E2939]"
      : "bg-gradient-to-b from-[#0525A3] to-[#010C38]",
    
    // Accent colors
    accent: isDark ? "#32C9F0" : "#04165D",
    accentSecondary: isDark ? "#1D748A" : "#082EC3",
    
    // Shadow styles
    shadow: isDark 
      ? "shadow-2xl shadow-black/50" 
      : "shadow-lg shadow-black/25",
    
    // Navigation
    navItem: isDark
      ? "text-white hover:text-[#32C9F0]"
      : "text-white hover:text-gray-200",
    
    // Spreadsheet/table elements
    tableHeader: isDark ? "bg-[#1E2939]" : "bg-[#F9FAFB]",
    tableRow: isDark ? "bg-black hover:bg-[#101828]" : "bg-white hover:bg-gray-50",
    tableBorder: isDark ? "border-[#1E2939]" : "border-gray-200",
    
    // Status indicators
    success: isDark ? "#32C9F0" : "#04165D",
    warning: isDark ? "#F59E0B" : "#D97706",
    error: isDark ? "#EF4444" : "#DC2626",
    
    // Logo area
    logoContainer: isDark ? "bg-black" : "bg-white",
    
    // Side panels/overlays
    overlay: isDark ? "bg-black/80" : "bg-white/80",
    sidePanel: isDark ? "bg-black border-[#1E2939]" : "bg-white border-gray-200",
  }

  // CSS custom properties for complex gradients
  const themeStyles = {
    '--gradient-primary': isDark 
      ? 'linear-gradient(98.08deg, #29CFF8 8.83%, #187A92 88.66%)'
      : 'linear-gradient(98.43deg, #04165D 7.77%, #082EC3 92.46%)',
    
    '--gradient-card': isDark
      ? 'linear-gradient(180deg, rgba(8, 118, 144, 0.5) 0%, rgba(41, 207, 248, 0.5) 100%)'
      : 'linear-gradient(232.59deg, #011D89 22.28%, #00092B 92.41%)',
    
    '--gradient-feature': isDark
      ? 'linear-gradient(50.68deg, #000B35 6.44%, #082EC3 92.06%)'
      : 'linear-gradient(50.68deg, #000B35 6.44%, #082EC3 92.06%)',
    
    '--shadow-card': isDark
      ? '0px 4px 6.9px rgba(0, 0, 0, 0.47)'
      : '0px 4px 4px rgba(0, 0, 0, 0.25)',
  }

  return (
    <ThemeContext.Provider value={{ 
      isDark, 
      toggleTheme, 
      themeClasses,
      themeStyles,
    }}>
      <div style={themeStyles}>
        {children}
      </div>
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