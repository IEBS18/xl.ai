import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  ChevronDown, 
  ArrowRight, 
  Menu, 
  X, 
  Moon, 
  Sun 
} from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import ConnectionStatus from "./ConnectionStatus"

const Header = ({ isConnected }) => {
  const { isDark, toggleTheme, themeClasses } = useTheme()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className={`fixed top-0 w-full z-50 ${themeClasses.glass} border-b ${themeClasses.border}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <motion.div
            className="flex items-center space-x-3"
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 400 }}
          >
            <div className="flex items-center space-x-1">
              <div className={`w-6 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
              <div className={`w-2 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
            </div>
            <span className={`text-xl font-semibold ${themeClasses.text}`}>DataScope AI</span>
          </motion.div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            <div className="relative group">
              <button
                className={`flex items-center space-x-1 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
              >
                <span>Use Cases</span>
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
            <a
              href="#contact"
              className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
            >
              Contact Us
            </a>
            <a
              href="#pricing"
              className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
            >
              Pricing
            </a>
          </nav>

          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <ConnectionStatus isConnected={isConnected} />

            {/* Theme Toggle */}
            <motion.button
              onClick={toggleTheme}
              className={`p-2 rounded-lg border ${themeClasses.border} hover:scale-110 transition-all duration-300`}
              whileHover={{ rotate: 180 }}
              whileTap={{ scale: 0.9 }}
            >
              <AnimatePresence mode="wait">
                {isDark ? (
                  <motion.div
                    key="sun"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Sun className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="moon"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Moon className="w-5 h-5" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>

            <button
              className={`hidden md:inline-flex ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
            >
              Log in
            </button>

            <motion.button
              className={`${themeClasses.button} px-4 py-2 rounded-lg font-medium transition-all duration-300 flex items-center space-x-2`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span>Sign Up</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>

            {/* Mobile menu button */}
            <button 
              className={`md:hidden ${themeClasses.textSecondary}`} 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className={`md:hidden border-t ${themeClasses.border} py-4`}
            >
              <div className="flex flex-col space-y-4">
                <a
                  href="#usecases"
                  className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                >
                  Use Cases
                </a>
                <a
                  href="#contact"
                  className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                >
                  Contact Us
                </a>
                <a
                  href="#pricing"
                  className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                >
                  Pricing
                </a>
                <button
                  className={`text-left ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
                >
                  Log in
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  )
}

export default Header