// "use client"

// import { useState, useEffect } from "react"
// import { motion, AnimatePresence } from "framer-motion"
// import { ChevronDown, Menu, X, Moon, Sun, User, Settings, LogOut } from "lucide-react"
// import { useTheme } from "../context/ThemeProvider"
// import ConnectionStatus from "./ConnectionStatus"
// import AuthModal from "./AuthModal.jsx"

// const Header = ({ isConnected }) => {
//   const { isDark, toggleTheme, themeClasses } = useTheme()
//   const [isMenuOpen, setIsMenuOpen] = useState(false)
//   const [activeDropdown, setActiveDropdown] = useState(null)
//   const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
//   const [isAuthenticated, setIsAuthenticated] = useState(false)
//   const [user, setUser] = useState(null)

//   const navigationItems = [
//     {
//       label: "Products",
//       hasDropdown: true,
//       items: [
//         { label: "Data Analysis", href: "#analysis" },
//         { label: "Predictions", href: "#predictions" },
//         { label: "Insights", href: "#insights" },
//         { label: "API Access", href: "#api" },
//       ],
//     },
//     {
//       label: "Resources",
//       hasDropdown: true,
//       items: [
//         { label: "Documentation", href: "#docs" },
//         { label: "Tutorials", href: "#tutorials" },
//         { label: "Blog", href: "#blog" },
//         { label: "Community", href: "#community" },
//       ],
//     },
//     {
//       label: "Use Cases",
//       hasDropdown: true,
//       items: [
//         { label: "Business Intelligence", href: "#bi" },
//         { label: "Market Research", href: "#research" },
//         { label: "Financial Analysis", href: "#finance" },
//         { label: "Customer Analytics", href: "#customer" },
//       ],
//     },
//     {
//       label: "Company",
//       hasDropdown: true,
//       items: [
//         { label: "About", href: "#about" },
//         { label: "Careers", href: "#careers" },
//         { label: "Contact", href: "#contact" },
//         { label: "Press", href: "#press" },
//       ],
//     },
//     {
//       label: "Pricing",
//       hasDropdown: false,
//       href: "#pricing",
//     },
//   ]

//   // Close dropdowns when clicking outside
//   useEffect(() => {
//     const handleClickOutside = () => {
//       setActiveDropdown(null)
//     }

//     if (activeDropdown) {
//       document.addEventListener("click", handleClickOutside)
//       return () => document.removeEventListener("click", handleClickOutside)
//     }
//   }, [activeDropdown])

//   const openAuthModal = (mode) => {
//     setAuthModal({ isOpen: true, mode })
//     setIsMenuOpen(false)
//   }

//   const closeAuthModal = () => {
//     setAuthModal({ isOpen: false, mode: "login" })
//   }

//   const handleAuthSuccess = (userData) => {
//     setIsAuthenticated(true)
//     setUser(userData)
//     closeAuthModal()
//   }

//   const handleLogout = () => {
//     setIsAuthenticated(false)
//     setUser(null)
//     setActiveDropdown(null)
//   }

//   return (
//     <>
//       {/* Header */}
//       <header className={`fixed top-0 left-0 right-0 z-[9999] backdrop-blur-md ${
//         isDark ? "bg-black/80" : "bg-white/80"
//       }`}>
//         <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
//           <div className="flex h-16 items-center justify-between">
//             {/* Logo */}
//             <motion.div
//               className="flex items-center space-x-3 z-10"
//               whileHover={{ scale: 1.02 }}
//               transition={{ type: "spring", stiffness: 400, damping: 25 }}
//             >
//               <div className="flex items-center space-x-1">
//                 <div className={`h-6 w-6 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
//                 <div className={`h-6 w-2 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
//               </div>
//               <span className={`text-xl font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>InsiPredict</span>
//             </motion.div>

//             {/* Desktop Navigation */}
//             <nav className="hidden lg:block">
//               <div
//                 className={`flex items-center rounded-full px-1 py-1 ${
//                   isDark
//                     ? "bg-gray-900/80 border border-gray-800/50 shadow-xl"
//                     : "bg-white/80 border border-gray-200/50 shadow-lg"
//                 } backdrop-blur-md`}
//               >
//                 {navigationItems.map((item, index) => (
//                   <div
//                     key={item.label}
//                     className="relative"
//                     onMouseEnter={() => item.hasDropdown && setActiveDropdown(index)}
//                     onMouseLeave={() => item.hasDropdown && setActiveDropdown(null)}
//                   >
//                     {item.hasDropdown ? (
//                       <button
//                         className={`flex items-center space-x-1 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
//                           isDark
//                             ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
//                             : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                         } ${activeDropdown === index ? (isDark ? "text-white bg-gray-800/50" : "text-gray-900 bg-gray-100/50") : ""}`}
//                       >
//                         <span>{item.label}</span>
//                         <motion.div
//                           animate={{ rotate: activeDropdown === index ? 180 : 0 }}
//                           transition={{ duration: 0.2, ease: "easeInOut" }}
//                         >
//                           <ChevronDown className="h-4 w-4" />
//                         </motion.div>
//                       </button>
//                     ) : (
//                       <a
//                         href={item.href}
//                         className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
//                           isDark
//                             ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
//                             : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                         }`}
//                       >
//                         {item.label}
//                       </a>
//                     )}

//                     {/* Dropdown Menu */}
//                     <AnimatePresence>
//                       {item.hasDropdown && activeDropdown === index && (
//                         <motion.div
//                           initial={{ opacity: 0, y: 8, scale: 0.96 }}
//                           animate={{ opacity: 1, y: 0, scale: 1 }}
//                           exit={{ opacity: 0, y: 8, scale: 0.96 }}
//                           transition={{ duration: 0.15, ease: "easeOut" }}
//                           className={`absolute left-0 top-full z-50 mt-2 w-56 rounded-xl border shadow-xl ${
//                             isDark ? "bg-gray-900/95 border-gray-800/50" : "bg-white/95 border-gray-200/50"
//                           } backdrop-blur-md`}
//                         >
//                           <div className="p-1">
//                             {item.items.map((subItem, subIndex) => (
//                               <a
//                                 key={subItem.label}
//                                 href={subItem.href}
//                                 className={`block rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
//                                   isDark
//                                     ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
//                                     : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                                 }`}
//                                 onClick={() => setActiveDropdown(null)}
//                               >
//                                 {subItem.label}
//                               </a>
//                             ))}
//                           </div>
//                         </motion.div>
//                       )}
//                     </AnimatePresence>
//                   </div>
//                 ))}
//               </div>
//             </nav>

//             {/* Right Side Actions */}
//             <div className="flex items-center space-x-3 z-10">
//               {/* Connection Status */}
//               <div className="hidden sm:block">
//                 <ConnectionStatus isConnected={isConnected} />
//               </div>

//               {/* Theme Toggle */}
//               <motion.button
//                 onClick={toggleTheme}
//                 className={`rounded-lg border p-2 transition-all duration-200 hover:scale-105 ${
//                   isDark
//                     ? "border-gray-700 text-gray-300 hover:text-white hover:bg-gray-800/50"
//                     : "border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                 }`}
//                 whileHover={{ rotate: 180 }}
//                 whileTap={{ scale: 0.95 }}
//               >
//                 <AnimatePresence mode="wait">
//                   {isDark ? (
//                     <motion.div
//                       key="sun"
//                       initial={{ rotate: -90, opacity: 0 }}
//                       animate={{ rotate: 0, opacity: 1 }}
//                       exit={{ rotate: 90, opacity: 0 }}
//                       transition={{ duration: 0.2 }}
//                     >
//                       <Sun className="h-4 w-4" />
//                     </motion.div>
//                   ) : (
//                     <motion.div
//                       key="moon"
//                       initial={{ rotate: -90, opacity: 0 }}
//                       animate={{ rotate: 0, opacity: 1 }}
//                       exit={{ rotate: 90, opacity: 0 }}
//                       transition={{ duration: 0.2 }}
//                     >
//                       <Moon className="h-4 w-4" />
//                     </motion.div>
//                   )}
//                 </AnimatePresence>
//               </motion.button>

//               {/* Authentication Section */}
//               {isAuthenticated ? (
//                 <div
//                   className="relative"
//                   onMouseEnter={() => setActiveDropdown("user")}
//                   onMouseLeave={() => setActiveDropdown(null)}
//                 >
//                   <button
//                     className={`flex items-center space-x-2 rounded-lg border px-3 py-2 transition-all duration-200 ${
//                       isDark ? "border-gray-700 hover:bg-gray-800/50" : "border-gray-300 hover:bg-gray-100/50"
//                     }`}
//                   >
//                     <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-blue-500">
//                       <User className="h-3 w-3 text-white" />
//                     </div>
//                     <span className={`hidden text-sm font-medium sm:block ${isDark ? "text-white" : "text-gray-900"}`}>
//                       {user?.name || "User"}
//                     </span>
//                     <ChevronDown className={`h-4 w-4 ${isDark ? "text-white" : "text-gray-900"}`} />
//                   </button>

//                   <AnimatePresence>
//                     {activeDropdown === "user" && (
//                       <motion.div
//                         initial={{ opacity: 0, y: 8, scale: 0.96 }}
//                         animate={{ opacity: 1, y: 0, scale: 1 }}
//                         exit={{ opacity: 0, y: 8, scale: 0.96 }}
//                         transition={{ duration: 0.15, ease: "easeOut" }}
//                         className={`absolute right-0 top-full z-50 mt-2 w-48 rounded-xl border shadow-xl ${
//                           isDark ? "bg-gray-900/95 border-gray-800/50" : "bg-white/95 border-gray-200/50"
//                         } backdrop-blur-md`}
//                       >
//                         <div className="p-1">
//                           <div className={`border-b px-3 py-2 ${isDark ? "border-gray-800" : "border-gray-200"}`}>
//                             <p className={`text-sm font-medium ${isDark ? "text-white" : "text-gray-900"}`}>
//                               {user?.name}
//                             </p>
//                             <p className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>{user?.email}</p>
//                           </div>
//                           <a
//                             href="#profile"
//                             className={`flex items-center space-x-2 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
//                               isDark
//                                 ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
//                                 : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                             }`}
//                           >
//                             <User className="h-4 w-4" />
//                             <span>Profile</span>
//                           </a>
//                           <a
//                             href="#settings"
//                             className={`flex items-center space-x-2 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
//                               isDark
//                                 ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
//                                 : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
//                             }`}
//                           >
//                             <Settings className="h-4 w-4" />
//                             <span>Settings</span>
//                           </a>
//                           <button
//                             onClick={handleLogout}
//                             className="flex w-full items-center space-x-2 rounded-lg px-3 py-2 text-sm text-red-500 transition-colors duration-150 hover:bg-red-50 dark:hover:bg-red-900/20"
//                           >
//                             <LogOut className="h-4 w-4" />
//                             <span>Sign out</span>
//                           </button>
//                         </div>
//                       </motion.div>
//                     )}
//                   </AnimatePresence>
//                 </div>
//               ) : (
//                 <div className="hidden items-center space-x-3 md:flex">
                  
//                   <motion.button
//                     onClick={() => openAuthModal("login")}
//                     className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-105 ${
//                       isDark
//                         ? "bg-white text-gray-900 hover:bg-gray-100 shadow-lg"
//                         : "bg-gray-900 text-white hover:bg-gray-800 shadow-lg"
//                     }`}
//                     whileHover={{ scale: 1.02 }}
//                     whileTap={{ scale: 0.98 }}
//                   >
//                     Log In
//                   </motion.button>
//                 </div>
//               )}

//               {/* Mobile menu button */}
//               <button
//                 className={`lg:hidden ${isDark ? "text-gray-300" : "text-gray-600"}`}
//                 onClick={() => setIsMenuOpen(!isMenuOpen)}
//               >
//                 {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
//               </button>
//             </div>
//           </div>

//           {/* Mobile Navigation */}
//           <AnimatePresence>
//             {isMenuOpen && (
//               <motion.div
//                 initial={{ opacity: 0, height: 0 }}
//                 animate={{ opacity: 1, height: "auto" }}
//                 exit={{ opacity: 0, height: 0 }}
//                 transition={{ duration: 0.2, ease: "easeInOut" }}
//                 className={`lg:hidden border-t py-4 ${isDark ? "border-gray-800" : "border-gray-200"}`}
//               >
//                 <div className="space-y-3">
//                   {navigationItems.map((item) => (
//                     <div key={item.label}>
//                       {item.hasDropdown ? (
//                         <div>
//                           <button
//                             onClick={() =>
//                               setActiveDropdown(
//                                 activeDropdown === `mobile-${item.label}` ? null : `mobile-${item.label}`,
//                               )
//                             }
//                             className={`flex w-full items-center justify-between font-medium transition-colors ${
//                               isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
//                             }`}
//                           >
//                             <span>{item.label}</span>
//                             <motion.div
//                               animate={{
//                                 rotate: activeDropdown === `mobile-${item.label}` ? 180 : 0,
//                               }}
//                               transition={{ duration: 0.2 }}
//                             >
//                               <ChevronDown className="h-4 w-4" />
//                             </motion.div>
//                           </button>
//                           <AnimatePresence>
//                             {activeDropdown === `mobile-${item.label}` && (
//                               <motion.div
//                                 initial={{ opacity: 0, height: 0 }}
//                                 animate={{ opacity: 1, height: "auto" }}
//                                 exit={{ opacity: 0, height: 0 }}
//                                 transition={{ duration: 0.2 }}
//                                 className="ml-4 mt-2 space-y-2"
//                               >
//                                 {item.items.map((subItem) => (
//                                   <a
//                                     key={subItem.label}
//                                     href={subItem.href}
//                                     className={`block text-sm transition-colors ${
//                                       isDark ? "text-gray-400 hover:text-gray-300" : "text-gray-500 hover:text-gray-600"
//                                     }`}
//                                   >
//                                     {subItem.label}
//                                   </a>
//                                 ))}
//                               </motion.div>
//                             )}
//                           </AnimatePresence>
//                         </div>
//                       ) : (
//                         <a
//                           href={item.href}
//                           className={`font-medium transition-colors ${
//                             isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
//                           }`}
//                         >
//                           {item.label}
//                         </a>
//                       )}
//                     </div>
//                   ))}

//                   {!isAuthenticated && (
//                     <div className={`space-y-3 border-t pt-4 ${isDark ? "border-gray-800" : "border-gray-200"}`}>
                      
//                       <button
//                         onClick={() => openAuthModal("login")}
//                         className={`w-full rounded-lg px-4 py-2 text-left font-medium transition-all duration-200 ${
//                           isDark
//                             ? "bg-white text-gray-900 hover:bg-gray-100"
//                             : "bg-gray-900 text-white hover:bg-gray-800"
//                         }`}
//                       >
//                         Log In
//                       </button>
//                     </div>
//                   )}
//                 </div>
//               </motion.div>
//             )}
//           </AnimatePresence>
//         </div>
//       </header>

//       {/* Auth Modal */}
//       <AuthModal
//         isOpen={authModal.isOpen}
//         mode={authModal.mode}
//         onClose={closeAuthModal}
//         onSuccess={handleAuthSuccess}
//         onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
//       />
//     </>
//   )
// }

// export default Header



"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, Menu, X, Moon, Sun, User, Settings, LogOut } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import ConnectionStatus from "./ConnectionStatus"
import AuthModal from "./AuthModal.jsx"

const Header = ({ isConnected }) => {
  const { isDark, toggleTheme } = useTheme()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState(null)
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE_URL = 'http://localhost:5000'

  const navigationItems = [
    {
      label: "Products",
      hasDropdown: true,
      items: [
        { label: "Data Analysis", href: "#analysis" },
        { label: "Predictions", href: "#predictions" },
        { label: "Insights", href: "#insights" },
        { label: "API Access", href: "#api" },
      ],
    },
    {
      label: "Resources",
      hasDropdown: true,
      items: [
        { label: "Documentation", href: "#docs" },
        { label: "Tutorials", href: "#tutorials" },
        { label: "Blog", href: "#blog" },
        { label: "Community", href: "#community" },
      ],
    },
    {
      label: "Use Cases",
      hasDropdown: true,
      items: [
        { label: "Business Intelligence", href: "#bi" },
        { label: "Market Research", href: "#research" },
        { label: "Financial Analysis", href: "#finance" },
        { label: "Customer Analytics", href: "#customer" },
      ],
    },
    {
      label: "Company",
      hasDropdown: true,
      items: [
        { label: "About", href: "#about" },
        { label: "Careers", href: "#careers" },
        { label: "Contact", href: "#contact" },
        { label: "Press", href: "#press" },
      ],
    },
    {
      label: "Pricing",
      hasDropdown: false,
      href: "#pricing",
    },
  ]

  // Check authentication status on component mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = useCallback(async () => {
    try {
      const userId = localStorage.getItem('user_insipredict_id')
      const firstName = localStorage.getItem('first_name_insipredict_user')
      const email = localStorage.getItem('email_insipredict_user')

      if (userId && firstName) {
        // Verify with backend
        const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'user_insipredict_id': userId,
            'first_name_insipredict_user': firstName
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.logged_in) {
            setIsAuthenticated(true)
            setUser({
              id: userId,
              name: firstName,
              email: email || ''
            })
          } else {
            // Clear invalid session data
            localStorage.removeItem('user_insipredict_id')
            localStorage.removeItem('first_name_insipredict_user')
            localStorage.removeItem('email_insipredict_user')
          }
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      // Clear potentially corrupted session data
      localStorage.removeItem('user_insipredict_id')
      localStorage.removeItem('first_name_insipredict_user')
      localStorage.removeItem('email_insipredict_user')
    } finally {
      setIsLoading(false)
    }
  }, [API_BASE_URL])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setActiveDropdown(null)
    }

    if (activeDropdown) {
      document.addEventListener("click", handleClickOutside)
      return () => document.removeEventListener("click", handleClickOutside)
    }
  }, [activeDropdown])

  const openAuthModal = useCallback((mode) => {
    setAuthModal({ isOpen: true, mode })
    setIsMenuOpen(false)
  }, [])

  const closeAuthModal = useCallback(() => {
    setAuthModal({ isOpen: false, mode: "login" })
  }, [])

  const handleAuthSuccess = useCallback((userData) => {
    setIsAuthenticated(true)
    setUser({
      id: userData.user_insipredict_id,
      name: userData.first_name,
      email: userData.email || ''
    })
    
    // Store in localStorage for persistence
    localStorage.setItem('user_insipredict_id', userData.user_insipredict_id.toString())
    localStorage.setItem('first_name_insipredict_user', userData.first_name)
    if (userData.email) {
      localStorage.setItem('email_insipredict_user', userData.email)
    }
    
    closeAuthModal()
  }, [closeAuthModal])

  const handleLogout = useCallback(async () => {
    try {
      // Call backend logout endpoint
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      // Clear local state and storage regardless of backend response
      setIsAuthenticated(false)
      setUser(null)
      setActiveDropdown(null)
      
      // Clear localStorage
      localStorage.removeItem('user_insipredict_id')
      localStorage.removeItem('first_name_insipredict_user')
      localStorage.removeItem('email_insipredict_user')
    }
  }, [API_BASE_URL])

  if (isLoading) {
    return (
      <header className={`fixed top-0 left-0 right-0 z-[9999] backdrop-blur-md ${
        isDark ? "bg-black/80" : "bg-white/80"
      }`}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-center">
            <div className={`animate-spin rounded-full h-6 w-6 border-b-2 ${
              isDark ? "border-white" : "border-gray-900"
            }`}></div>
          </div>
        </div>
      </header>
    )
  }

  return (
    <>
      {/* Header */}
      <header className={`fixed top-0 left-0 right-0 z-[9999] backdrop-blur-md ${
        isDark ? "bg-black/80" : "bg-white/80"
      }`}>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <motion.div
              className="flex items-center space-x-3 z-10"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <div className="flex items-center space-x-1">
                <div className={`h-6 w-6 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
                <div className={`h-6 w-2 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
              </div>
              <span className={`text-xl font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>InsiPredict</span>
            </motion.div>

            {/* Desktop Navigation */}
            <nav className="hidden lg:block">
              <div
                className={`flex items-center rounded-full px-1 py-1 ${
                  isDark
                    ? "bg-gray-900/80 border border-gray-800/50 shadow-xl"
                    : "bg-white/80 border border-gray-200/50 shadow-lg"
                } backdrop-blur-md`}
              >
                {navigationItems.map((item, index) => (
                  <div
                    key={item.label}
                    className="relative"
                    onMouseEnter={() => item.hasDropdown && setActiveDropdown(index)}
                    onMouseLeave={() => item.hasDropdown && setActiveDropdown(null)}
                  >
                    {item.hasDropdown ? (
                      <button
                        className={`flex items-center space-x-1 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
                          isDark
                            ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                        } ${activeDropdown === index ? (isDark ? "text-white bg-gray-800/50" : "text-gray-900 bg-gray-100/50") : ""}`}
                      >
                        <span>{item.label}</span>
                        <motion.div
                          animate={{ rotate: activeDropdown === index ? 180 : 0 }}
                          transition={{ duration: 0.2, ease: "easeInOut" }}
                        >
                          <ChevronDown className="h-4 w-4" />
                        </motion.div>
                      </button>
                    ) : (
                      <a
                        href={item.href}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
                          isDark
                            ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                        }`}
                      >
                        {item.label}
                      </a>
                    )}

                    {/* Dropdown Menu */}
                    <AnimatePresence>
                      {item.hasDropdown && activeDropdown === index && (
                        <motion.div
                          initial={{ opacity: 0, y: 8, scale: 0.96 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 8, scale: 0.96 }}
                          transition={{ duration: 0.15, ease: "easeOut" }}
                          className={`absolute left-0 top-full z-50 mt-2 w-56 rounded-xl border shadow-xl ${
                            isDark ? "bg-gray-900/95 border-gray-800/50" : "bg-white/95 border-gray-200/50"
                          } backdrop-blur-md`}
                        >
                          <div className="p-1">
                            {item.items.map((subItem, subIndex) => (
                              <a
                                key={subItem.label}
                                href={subItem.href}
                                className={`block rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
                                  isDark
                                    ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
                                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                                }`}
                                onClick={() => setActiveDropdown(null)}
                              >
                                {subItem.label}
                              </a>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>
            </nav>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-3 z-10">
              {/* Connection Status */}
              <div className="hidden sm:block">
                <ConnectionStatus isConnected={isConnected} />
              </div>

              {/* Theme Toggle */}
              <motion.button
                onClick={toggleTheme}
                className={`rounded-lg border p-2 transition-all duration-200 hover:scale-105 ${
                  isDark
                    ? "border-gray-700 text-gray-300 hover:text-white hover:bg-gray-800/50"
                    : "border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                }`}
                whileHover={{ rotate: 180 }}
                whileTap={{ scale: 0.95 }}
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
                      <Sun className="h-4 w-4" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="moon"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Moon className="h-4 w-4" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>

              {/* Authentication Section */}
              {isAuthenticated ? (
                <div
                  className="relative"
                  onMouseEnter={() => setActiveDropdown("user")}
                  onMouseLeave={() => setActiveDropdown(null)}
                >
                  <button
                    className={`flex items-center space-x-2 rounded-lg border px-3 py-2 transition-all duration-200 ${
                      isDark ? "border-gray-700 hover:bg-gray-800/50" : "border-gray-300 hover:bg-gray-100/50"
                    }`}
                  >
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-blue-500">
                      <User className="h-3 w-3 text-white" />
                    </div>
                    <span className={`hidden text-sm font-medium sm:block ${isDark ? "text-white" : "text-gray-900"}`}>
                      {user?.name || "User"}
                    </span>
                    <ChevronDown className={`h-4 w-4 ${isDark ? "text-white" : "text-gray-900"}`} />
                  </button>

                  <AnimatePresence>
                    {activeDropdown === "user" && (
                      <motion.div
                        initial={{ opacity: 0, y: 8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.96 }}
                        transition={{ duration: 0.15, ease: "easeOut" }}
                        className={`absolute right-0 top-full z-50 mt-2 w-48 rounded-xl border shadow-xl ${
                          isDark ? "bg-gray-900/95 border-gray-800/50" : "bg-white/95 border-gray-200/50"
                        } backdrop-blur-md`}
                      >
                        <div className="p-1">
                          <div className={`border-b px-3 py-2 ${isDark ? "border-gray-800" : "border-gray-200"}`}>
                            <p className={`text-sm font-medium ${isDark ? "text-white" : "text-gray-900"}`}>
                              {user?.name}
                            </p>
                            {user?.email && (
                              <p className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>{user.email}</p>
                            )}
                          </div>
                          <a
                            href="#profile"
                            className={`flex items-center space-x-2 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
                              isDark
                                ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
                                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                            }`}
                          >
                            <User className="h-4 w-4" />
                            <span>Profile</span>
                          </a>
                          <a
                            href="#settings"
                            className={`flex items-center space-x-2 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
                              isDark
                                ? "text-gray-300 hover:text-white hover:bg-gray-800/50"
                                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                            }`}
                          >
                            <Settings className="h-4 w-4" />
                            <span>Settings</span>
                          </a>
                          <button
                            onClick={handleLogout}
                            className="flex w-full items-center space-x-2 rounded-lg px-3 py-2 text-sm text-red-500 transition-colors duration-150 hover:bg-red-50 dark:hover:bg-red-900/20"
                          >
                            <LogOut className="h-4 w-4" />
                            <span>Sign out</span>
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <div className="hidden items-center space-x-3 md:flex">
                  <button
                    onClick={() => openAuthModal("login")}
                    className={`rounded-lg border px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-105 ${
                      isDark
                        ? "border-gray-700 text-gray-300 hover:text-white hover:bg-gray-800/50"
                        : "border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
                    }`}
                  >
                    Get a demo
                  </button>
                  <motion.button
                    onClick={() => openAuthModal("login")}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 hover:scale-105 ${
                      isDark
                        ? "bg-white text-gray-900 hover:bg-gray-100 shadow-lg"
                        : "bg-gray-900 text-white hover:bg-gray-800 shadow-lg"
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Log In
                  </motion.button>
                </div>
              )}

              {/* Mobile menu button */}
              <button
                className={`lg:hidden ${isDark ? "text-gray-300" : "text-gray-600"}`}
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
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className={`lg:hidden border-t py-4 ${isDark ? "border-gray-800" : "border-gray-200"}`}
              >
                <div className="space-y-3">
                  {navigationItems.map((item) => (
                    <div key={item.label}>
                      {item.hasDropdown ? (
                        <div>
                          <button
                            onClick={() =>
                              setActiveDropdown(
                                activeDropdown === `mobile-${item.label}` ? null : `mobile-${item.label}`,
                              )
                            }
                            className={`flex w-full items-center justify-between font-medium transition-colors ${
                              isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
                            }`}
                          >
                            <span>{item.label}</span>
                            <motion.div
                              animate={{
                                rotate: activeDropdown === `mobile-${item.label}` ? 180 : 0,
                              }}
                              transition={{ duration: 0.2 }}
                            >
                              <ChevronDown className="h-4 w-4" />
                            </motion.div>
                          </button>
                          <AnimatePresence>
                            {activeDropdown === `mobile-${item.label}` && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="ml-4 mt-2 space-y-2"
                              >
                                {item.items.map((subItem) => (
                                  <a
                                    key={subItem.label}
                                    href={subItem.href}
                                    className={`block text-sm transition-colors ${
                                      isDark ? "text-gray-400 hover:text-gray-300" : "text-gray-500 hover:text-gray-600"
                                    }`}
                                  >
                                    {subItem.label}
                                  </a>
                                ))}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ) : (
                        <a
                          href={item.href}
                          className={`font-medium transition-colors ${
                            isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
                          }`}
                        >
                          {item.label}
                        </a>
                      )}
                    </div>
                  ))}

                  {!isAuthenticated && (
                    <div className={`space-y-3 border-t pt-4 ${isDark ? "border-gray-800" : "border-gray-200"}`}>
                      <button
                        onClick={() => openAuthModal("login")}
                        className={`w-full text-left font-medium transition-colors ${
                          isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900"
                        }`}
                      >
                        Get a demo
                      </button>
                      <button
                        onClick={() => openAuthModal("login")}
                        className={`w-full rounded-lg px-4 py-2 text-left font-medium transition-all duration-200 ${
                          isDark
                            ? "bg-white text-gray-900 hover:bg-gray-100"
                            : "bg-gray-900 text-white hover:bg-gray-800"
                        }`}
                      >
                        Log In
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModal.isOpen}
        mode={authModal.mode}
        onClose={closeAuthModal}
        onSuccess={handleAuthSuccess}
        onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
      />
    </>
  )
}

export default Header