// "use client"

// import { useState, useCallback, useMemo } from "react"
// import { motion, AnimatePresence } from "framer-motion"
// import { X, Eye, EyeOff, Mail, Lock, User, TrendingUp, BarChart3, Zap, Shield } from "lucide-react"
// import { useTheme } from "../context/ThemeProvider"

// const AuthModal = ({ isOpen, mode, onClose, onSuccess, onSwitchMode }) => {
//   const { isDark } = useTheme()
//   const [formData, setFormData] = useState({
//     name: "",
//     email: "",
//     password: "",
//     confirmPassword: "",
//   })
//   const [showPassword, setShowPassword] = useState(false)
//   const [showConfirmPassword, setShowConfirmPassword] = useState(false)
//   const [isLoading, setIsLoading] = useState(false)
//   const [errors, setErrors] = useState({})

//   // Memoized theme styles for optimal performance
//   const themeStyles = useMemo(() => ({
//     modal: isDark 
//       ? "bg-gray-900/95 border-gray-800/50" 
//       : "bg-white/95 border-gray-200/50",
//     leftPanel: isDark
//       ? "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900"
//       : "bg-gradient-to-br from-gray-50 via-white to-gray-100",
//     text: isDark ? "text-white" : "text-gray-900",
//     textSecondary: isDark ? "text-gray-400" : "text-gray-600",
//     textMuted: isDark ? "text-gray-500" : "text-gray-500",
//     input: isDark 
//       ? "bg-gray-800/50 border-gray-700 text-white placeholder-gray-500" 
//       : "bg-gray-50/50 border-gray-300 text-gray-900 placeholder-gray-400",
//     inputFocus: isDark
//       ? "focus:ring-2 focus:ring-gray-500/30 focus:border-gray-400"
//       : "focus:ring-2 focus:ring-gray-400/30 focus:border-gray-600",
//     inputError: "border-red-500 focus:ring-red-500/30 focus:border-red-500",
//     button: isDark 
//       ? "hover:bg-gray-800/50 text-gray-300 hover:text-white" 
//       : "hover:bg-gray-100/50 text-gray-600 hover:text-gray-900",
//     link: isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900",
//     accent: isDark ? "text-gray-200" : "text-gray-700",
//   }), [isDark])

//   // Animation features data
//   const features = [
//     { icon: TrendingUp, text: "Real-time Analytics", delay: 0 },
//     { icon: BarChart3, text: "Advanced Insights", delay: 0.2 },
//     { icon: Zap, text: "Lightning Fast", delay: 0.4 },
//     { icon: Shield, text: "Enterprise Security", delay: 0.6 },
//   ]

//   const handleInputChange = useCallback((e) => {
//     const { name, value } = e.target
//     setFormData((prev) => ({ ...prev, [name]: value }))
//     if (errors[name]) {
//       setErrors((prev) => ({ ...prev, [name]: "" }))
//     }
//   }, [errors])

//   const validateForm = useCallback(() => {
//     const newErrors = {}

//     if (mode === "signup" && !formData.name.trim()) {
//       newErrors.name = "Name is required"
//     }

//     if (!formData.email.trim()) {
//       newErrors.email = "Email is required"
//     } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
//       newErrors.email = "Email is invalid"
//     }

//     if (!formData.password) {
//       newErrors.password = "Password is required"
//     } else if (formData.password.length < 6) {
//       newErrors.password = "Password must be at least 6 characters"
//     }

//     if (mode === "signup" && formData.password !== formData.confirmPassword) {
//       newErrors.confirmPassword = "Passwords do not match"
//     }

//     setErrors(newErrors)
//     return Object.keys(newErrors).length === 0
//   }, [mode, formData])

//   const handleSubmit = useCallback(async (e) => {
//     e.preventDefault()
//     if (!validateForm()) return

//     setIsLoading(true)

//     try {
//       await new Promise((resolve) => setTimeout(resolve, 1500))
      
//       const userData = {
//         name: formData.name || formData.email.split("@")[0],
//         email: formData.email,
//         id: Date.now(),
//       }

//       onSuccess(userData)
//       setFormData({ name: "", email: "", password: "", confirmPassword: "" })
//     } catch (error) {
//       setErrors({ general: "Authentication failed. Please try again." })
//     } finally {
//       setIsLoading(false)
//     }
//   }, [validateForm, formData, onSuccess])

//   const resetForm = useCallback(() => {
//     setFormData({ name: "", email: "", password: "", confirmPassword: "" })
//     setErrors({})
//     setShowPassword(false)
//     setShowConfirmPassword(false)
//   }, [])

//   const handleModeSwitch = useCallback((newMode) => {
//     resetForm()
//     onSwitchMode(newMode)
//   }, [resetForm, onSwitchMode])

//   const handleClose = useCallback(() => {
//     resetForm()
//     onClose()
//   }, [resetForm, onClose])

//   // Optimized animation variants
//   const backdropVariants = {
//     hidden: { opacity: 0 },
//     visible: { opacity: 1 },
//     exit: { opacity: 0 }
//   }

//   const modalVariants = {
//     hidden: { 
//       opacity: 0, 
//       x: "100%",
//       scale: 0.95
//     },
//     visible: { 
//       opacity: 1, 
//       x: 0,
//       scale: 1,
//       transition: { 
//         type: "spring", 
//         duration: 0.5, 
//         bounce: 0.1,
//         staggerChildren: 0.1
//       }
//     },
//     exit: { 
//       opacity: 0, 
//       x: "100%",
//       scale: 0.95,
//       transition: { duration: 0.3 }
//     }
//   }

//   const leftPanelVariants = {
//     hidden: { opacity: 0, x: -50 },
//     visible: { 
//       opacity: 1, 
//       x: 0,
//       transition: { duration: 0.6, ease: "easeOut" }
//     }
//   }

//   const rightPanelVariants = {
//     hidden: { opacity: 0, x: 50 },
//     visible: { 
//       opacity: 1, 
//       x: 0,
//       transition: { duration: 0.6, ease: "easeOut", delay: 0.2 }
//     }
//   }

//   const floatingVariants = {
//     animate: {
//       y: [-10, 10, -10],
//       transition: {
//         duration: 4,
//         repeat: Infinity,
//         ease: "easeInOut"
//       }
//     }
//   }

//   return (
//     <AnimatePresence mode="wait">
//       {isOpen && (
//         <motion.div
//           variants={backdropVariants}
//           initial="hidden"
//           animate="visible"
//           exit="exit"
//           className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
//           onClick={handleClose}
//         >
//           <motion.div
//             variants={modalVariants}
//             initial="hidden"
//             animate="visible"
//             exit="exit"
//             className={`w-full max-w-5xl h-[90vh] ${themeStyles.modal} border rounded-2xl shadow-2xl backdrop-blur-xl overflow-hidden flex`}
//             onClick={(e) => e.stopPropagation()}
//           >
//             {/* Left Animated Panel */}
//             <motion.div
//               variants={leftPanelVariants}
//               className={`hidden lg:flex lg:w-1/2 ${themeStyles.leftPanel} relative overflow-hidden`}
//             >
//               {/* Background Pattern */}
//               <div className={`absolute inset-0 opacity-10 ${isDark ? 'bg-white' : 'bg-gray-900'}`}>
//                 <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
//                   <defs>
//                     <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
//                       <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5"/>
//                     </pattern>
//                   </defs>
//                   <rect width="100%" height="100%" fill="url(#grid)" />
//                 </svg>
//               </div>

//               {/* Content */}
//               <div className="relative z-10 p-12 flex flex-col justify-center">
//                 {/* Logo */}
//                 <motion.div
//                   initial={{ opacity: 0, y: 20 }}
//                   animate={{ opacity: 1, y: 0 }}
//                   transition={{ delay: 0.3 }}
//                   className="flex items-center space-x-3 mb-8"
//                 >
//                   <div className="flex items-center space-x-1">
//                     <div className={`h-8 w-8 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
//                     <div className={`h-8 w-3 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
//                   </div>
//                   <span className={`text-2xl font-semibold ${themeStyles.text}`}>InsiPredict</span>
//                 </motion.div>

//                 {/* Main Content */}
//                 <motion.div
//                   initial={{ opacity: 0, y: 30 }}
//                   animate={{ opacity: 1, y: 0 }}
//                   transition={{ delay: 0.5 }}
//                   className="mb-8"
//                 >
//                   <h2 className={`text-4xl font-bold ${themeStyles.text} mb-4 leading-tight`}>
//                     {mode === "login" ? "Welcome Back!" : "Join InsiPredict"}
//                   </h2>
//                   <p className={`text-lg ${themeStyles.textSecondary} leading-relaxed`}>
//                     {mode === "login" 
//                       ? "Continue your journey with powerful data insights and predictive analytics."
//                       : "Transform your data into actionable insights with our advanced analytics platform."
//                     }
//                   </p>
//                 </motion.div>

//                 {/* Animated Features */}
//                 <div className="space-y-4">
//                   {features.map((feature, index) => (
//                     <motion.div
//                       key={feature.text}
//                       initial={{ opacity: 0, x: -20 }}
//                       animate={{ opacity: 1, x: 0 }}
//                       transition={{ delay: 0.7 + feature.delay }}
//                       className="flex items-center space-x-3"
//                     >
//                       <motion.div
//                         variants={floatingVariants}
//                         animate="animate"
//                         transition={{ delay: index * 0.5 }}
//                         className={`p-2 rounded-lg ${isDark ? 'bg-gray-800/50' : 'bg-white/50'} backdrop-blur-sm`}
//                       >
//                         <feature.icon className={`w-5 h-5 ${themeStyles.accent}`} />
//                       </motion.div>
//                       <span className={`${themeStyles.textSecondary} font-medium`}>
//                         {feature.text}
//                       </span>
//                     </motion.div>
//                   ))}
//                 </div>

//                 {/* Floating Elements */}
//                 <motion.div
//                   variants={floatingVariants}
//                   animate="animate"
//                   className={`absolute top-20 right-20 w-20 h-20 rounded-full ${isDark ? 'bg-gray-700/30' : 'bg-gray-300/30'} backdrop-blur-sm`}
//                 />
//                 <motion.div
//                   variants={floatingVariants}
//                   animate="animate"
//                   transition={{ delay: 2 }}
//                   className={`absolute bottom-32 right-16 w-12 h-12 rounded-full ${isDark ? 'bg-gray-600/20' : 'bg-gray-400/20'} backdrop-blur-sm`}
//                 />
//               </div>
//             </motion.div>

//             {/* Right Form Panel */}
//             <motion.div
//               variants={rightPanelVariants}
//               className="w-full lg:w-1/2 flex flex-col relative"
//             >
//               {/* Close Button */}
//               <button
//                 onClick={handleClose}
//                 className={`absolute top-6 right-6 z-20 p-2 rounded-lg transition-all duration-200 ${themeStyles.button}`}
//               >
//                 <X className="w-5 h-5" />
//               </button>

//               {/* Scrollable Content */}
//               <div className={`flex-1 overflow-y-auto p-8 ${
//                 isDark 
//                   ? 'scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800' 
//                   : 'scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100'
//               }`}
//               style={{
//                 scrollbarWidth: 'thin',
//                 scrollbarColor: isDark ? '#4B5563 #1F2937' : '#9CA3AF #F3F4F6'
//               }}
//               >
//                 <div className="max-w-md mx-auto">
//                   {/* Form Header */}
//                   <div className="mb-8 pt-8">
//                     <h2 className={`text-3xl font-bold ${themeStyles.text} mb-2`}>
//                       {mode === "login" ? "Sign In" : "Create Account"}
//                     </h2>
//                     <p className={`${themeStyles.textSecondary}`}>
//                       {mode === "login" ? "Enter your credentials to continue" : "Fill in your details to get started"}
//                     </p>
//                   </div>

//               {/* Form */}
//               <form onSubmit={handleSubmit} className="space-y-5">
//                 {errors.general && (
//                   <motion.div 
//                     initial={{ opacity: 0, y: -10 }}
//                     animate={{ opacity: 1, y: 0 }}
//                     className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm"
//                   >
//                     {errors.general}
//                   </motion.div>
//                 )}

//                 {mode === "signup" && (
//                   <div>
//                     <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
//                       Full Name
//                     </label>
//                     <div className="relative">
//                       <User className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
//                       <input
//                         type="text"
//                         name="name"
//                         value={formData.name}
//                         onChange={handleInputChange}
//                         className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${
//                           errors.name ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
//                         }`}
//                         placeholder="Enter your full name"
//                         disabled={isLoading}
//                       />
//                     </div>
//                     {errors.name && (
//                       <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
//                         {errors.name}
//                       </motion.p>
//                     )}
//                   </div>
//                 )}

//                 <div>
//                   <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
//                     Email Address
//                   </label>
//                   <div className="relative">
//                     <Mail className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
//                     <input
//                       type="email"
//                       name="email"
//                       value={formData.email}
//                       onChange={handleInputChange}
//                       className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${
//                         errors.email ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
//                       }`}
//                       placeholder="Enter your email"
//                       disabled={isLoading}
//                     />
//                   </div>
//                   {errors.email && (
//                     <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
//                       {errors.email}
//                     </motion.p>
//                   )}
//                 </div>

//                 <div>
//                   <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
//                     Password
//                   </label>
//                   <div className="relative">
//                     <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
//                     <input
//                       type={showPassword ? "text" : "password"}
//                       name="password"
//                       value={formData.password}
//                       onChange={handleInputChange}
//                       className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${
//                         errors.password ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
//                       }`}
//                       placeholder="Enter your password"
//                       disabled={isLoading}
//                     />
//                     <button
//                       type="button"
//                       onClick={() => setShowPassword(!showPassword)}
//                       className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.button}`}
//                     >
//                       {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
//                     </button>
//                   </div>
//                   {errors.password && (
//                     <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
//                       {errors.password}
//                     </motion.p>
//                   )}
//                 </div>

//                 {mode === "signup" && (
//                   <div>
//                     <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
//                       Confirm Password
//                     </label>
//                     <div className="relative">
//                       <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
//                       <input
//                         type={showConfirmPassword ? "text" : "password"}
//                         name="confirmPassword"
//                         value={formData.confirmPassword}
//                         onChange={handleInputChange}
//                         className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${
//                           errors.confirmPassword ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
//                         }`}
//                         placeholder="Confirm your password"
//                         disabled={isLoading}
//                       />
//                       <button
//                         type="button"
//                         onClick={() => setShowConfirmPassword(!showConfirmPassword)}
//                         className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.button}`}
//                       >
//                         {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
//                       </button>
//                     </div>
//                     {errors.confirmPassword && (
//                       <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
//                         {errors.confirmPassword}
//                       </motion.p>
//                     )}
//                   </div>
//                 )}

//                 {mode === "login" && (
//                   <div className="flex items-center justify-between">
//                     <label className="flex items-center">
//                       <input
//                         type="checkbox"
//                         className={`rounded border ${isDark ? 'border-gray-600 bg-gray-700 text-gray-600' : 'border-gray-300 bg-white text-gray-600'} focus:ring-gray-500 focus:ring-2`}
//                       />
//                       <span className={`ml-2 text-sm ${themeStyles.textSecondary}`}>Remember me</span>
//                     </label>
//                     <button 
//                       type="button" 
//                       className={`text-sm font-medium transition-colors ${themeStyles.link}`}
//                     >
//                       Forgot password?
//                     </button>
//                   </div>
//                 )}

//                 <motion.button
//                   type="submit"
//                   disabled={isLoading}
//                   className={`w-full py-3 rounded-lg font-medium transition-all duration-200 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${
//                     isDark
//                       ? "bg-white text-gray-900 hover:bg-gray-100"
//                       : "bg-gray-900 text-white hover:bg-gray-800"
//                   }`}
//                   whileHover={!isLoading ? { scale: 1.02 } : {}}
//                   whileTap={!isLoading ? { scale: 0.98 } : {}}
//                 >
//                   {isLoading ? (
//                     <div className="flex items-center justify-center space-x-2">
//                       <div className={`w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin`} />
//                       <span>{mode === "login" ? "Signing in..." : "Creating account..."}</span>
//                     </div>
//                   ) : mode === "login" ? (
//                     "Sign In"
//                   ) : (
//                     "Create Account"
//                   )}
//                 </motion.button>
//               </form>

//               {/* Footer */}
//               <div className="mt-6 text-center">
//                 <p className={`text-sm ${themeStyles.textSecondary}`}>
//                   {mode === "login" ? "Don't have an account? " : "Already have an account? "}
//                   <button
//                     onClick={() => handleModeSwitch(mode === "login" ? "signup" : "login")}
//                     className={`font-medium transition-colors ${themeStyles.link}`}
//                     disabled={isLoading}
//                   >
//                     {mode === "login" ? "Sign up" : "Sign in"}
//                   </button>
//                 </p>
//               </div>

//               {mode === "signup" && (
//                 <p className={`text-xs ${themeStyles.textMuted} text-center mt-4 leading-relaxed mb-8`}>
//                   By creating an account, you agree to our{" "}
//                   <a href="#terms" className={`font-medium transition-colors ${themeStyles.link}`}>
//                     Terms of Service
//                   </a>{" "}
//                   and{" "}
//                   <a href="#privacy" className={`font-medium transition-colors ${themeStyles.link}`}>
//                     Privacy Policy
//                   </a>
//                 </p>
//               )}
//               </div>
//             </div>
//             </motion.div>
//           </motion.div>
//         </motion.div>
//       )}
//     </AnimatePresence>
//   )
// }

// export default AuthModal


"use client"

import { useState, useCallback, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Eye, EyeOff, Mail, Lock, User, TrendingUp, BarChart3, Zap, Shield } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"

const AuthModal = ({ isOpen, mode, onClose, onSuccess, onSwitchMode }) => {
  const { isDark } = useTheme()
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState({})

  const API_BASE_URL =  'http://localhost:5000'

  // Memoized theme styles for optimal performance
  const themeStyles = useMemo(() => ({
    modal: isDark 
      ? "bg-gray-900/95 border-gray-800/50" 
      : "bg-white/95 border-gray-200/50",
    leftPanel: isDark
      ? "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900"
      : "bg-gradient-to-br from-gray-50 via-white to-gray-100",
    text: isDark ? "text-white" : "text-gray-900",
    textSecondary: isDark ? "text-gray-400" : "text-gray-600",
    textMuted: isDark ? "text-gray-500" : "text-gray-500",
    input: isDark 
      ? "bg-gray-800/50 border-gray-700 text-white placeholder-gray-500" 
      : "bg-gray-50/50 border-gray-300 text-gray-900 placeholder-gray-400",
    inputFocus: isDark
      ? "focus:ring-2 focus:ring-gray-500/30 focus:border-gray-400"
      : "focus:ring-2 focus:ring-gray-400/30 focus:border-gray-600",
    inputError: "border-red-500 focus:ring-red-500/30 focus:border-red-500",
    button: isDark 
      ? "hover:bg-gray-800/50 text-gray-300 hover:text-white" 
      : "hover:bg-gray-100/50 text-gray-600 hover:text-gray-900",
    link: isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900",
    accent: isDark ? "text-gray-200" : "text-gray-700",
  }), [isDark])

  // Animation features data
  const features = [
    { icon: TrendingUp, text: "Real-time Analytics", delay: 0 },
    { icon: BarChart3, text: "Advanced Insights", delay: 0.2 },
    { icon: Zap, text: "Lightning Fast", delay: 0.4 },
    { icon: Shield, text: "Enterprise Security", delay: 0.6 },
  ]

  const handleInputChange = useCallback((e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }))
    }
  }, [errors])

  const validateForm = useCallback(() => {
    const newErrors = {}

    if (mode === "signup" && !formData.firstName.trim()) {
      newErrors.firstName = "First name is required"
    }

    if (mode === "signup" && !formData.lastName.trim()) {
      newErrors.lastName = "Last name is required"
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required"
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid"
    }

    if (!formData.password) {
      newErrors.password = "Password is required"
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters"
    }

    if (mode === "signup" && formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [mode, formData])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setIsLoading(true)
    setErrors({})

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup"
      const payload = mode === "login" 
        ? { email: formData.email, password: formData.password }
        : {
            firstName: formData.firstName,
            lastName: formData.lastName,
            email: formData.email,
            password: formData.password
          }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (response.ok) {
        // Success - call the success handler with user data
        onSuccess({
          user_insipredict_id: data.user_insipredict_id,
          first_name: data.first_name,
          last_name: data.last_name,
          email: formData.email
        })
        
        // Reset form
        setFormData({ firstName: "", lastName: "", email: "", password: "", confirmPassword: "" })
      } else {
        // Handle server errors
        setErrors({ general: data.error || "Authentication failed. Please try again." })
      }
    } catch (error) {
      console.error('Auth error:', error)
      setErrors({ general: "Network error. Please check your connection and try again." })
    } finally {
      setIsLoading(false)
    }
  }, [validateForm, formData, mode, onSuccess, API_BASE_URL])

  const resetForm = useCallback(() => {
    setFormData({ firstName: "", lastName: "", email: "", password: "", confirmPassword: "" })
    setErrors({})
    setShowPassword(false)
    setShowConfirmPassword(false)
  }, [])

  const handleModeSwitch = useCallback((newMode) => {
    resetForm()
    onSwitchMode(newMode)
  }, [resetForm, onSwitchMode])

  const handleClose = useCallback(() => {
    resetForm()
    onClose()
  }, [resetForm, onClose])

  // Optimized animation variants
  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 }
  }

  const modalVariants = {
    hidden: { 
      opacity: 0, 
      x: "100%",
      scale: 0.95
    },
    visible: { 
      opacity: 1, 
      x: 0,
      scale: 1,
      transition: { 
        type: "spring", 
        duration: 0.5, 
        bounce: 0.1,
        staggerChildren: 0.1
      }
    },
    exit: { 
      opacity: 0, 
      x: "100%",
      scale: 0.95,
      transition: { duration: 0.3 }
    }
  }

  const leftPanelVariants = {
    hidden: { opacity: 0, x: -50 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.6, ease: "easeOut" }
    }
  }

  const rightPanelVariants = {
    hidden: { opacity: 0, x: 50 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.6, ease: "easeOut", delay: 0.2 }
    }
  }

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={handleClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={`w-full max-w-5xl h-[90vh] ${themeStyles.modal} border rounded-2xl shadow-2xl backdrop-blur-xl overflow-hidden flex`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Left Animated Panel */}
            <motion.div
              variants={leftPanelVariants}
              className={`hidden lg:flex lg:w-1/2 ${themeStyles.leftPanel} relative overflow-hidden`}
            >
              {/* Background Pattern */}
              <div className={`absolute inset-0 opacity-10 ${isDark ? 'bg-white' : 'bg-gray-900'}`}>
                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5"/>
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>
              </div>

              {/* Content */}
              <div className="relative z-10 p-12 flex flex-col justify-center">
                {/* Logo */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center space-x-3 mb-8"
                >
                  <div className="flex items-center space-x-1">
                    <div className={`h-8 w-8 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
                    <div className={`h-8 w-3 rounded ${isDark ? "bg-white" : "bg-gray-900"}`} />
                  </div>
                  <span className={`text-2xl font-semibold ${themeStyles.text}`}>InsiPredict</span>
                </motion.div>

                {/* Main Content */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="mb-8"
                >
                  <h2 className={`text-4xl font-bold ${themeStyles.text} mb-4 leading-tight`}>
                    {mode === "login" ? "Welcome Back!" : "Join InsiPredict"}
                  </h2>
                  <p className={`text-lg ${themeStyles.textSecondary} leading-relaxed`}>
                    {mode === "login" 
                      ? "Continue your journey with powerful data insights and predictive analytics."
                      : "Transform your data into actionable insights with our advanced analytics platform."
                    }
                  </p>
                </motion.div>

                {/* Animated Features */}
                <div className="space-y-4">
                  {features.map((feature, index) => (
                    <motion.div
                      key={feature.text}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + feature.delay }}
                      className="flex items-center space-x-3"
                    >
                      <motion.div
                        variants={floatingVariants}
                        animate="animate"
                        transition={{ delay: index * 0.5 }}
                        className={`p-2 rounded-lg ${isDark ? 'bg-gray-800/50' : 'bg-white/50'} backdrop-blur-sm`}
                      >
                        <feature.icon className={`w-5 h-5 ${themeStyles.accent}`} />
                      </motion.div>
                      <span className={`${themeStyles.textSecondary} font-medium`}>
                        {feature.text}
                      </span>
                    </motion.div>
                  ))}
                </div>

                {/* Floating Elements */}
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  className={`absolute top-20 right-20 w-20 h-20 rounded-full ${isDark ? 'bg-gray-700/30' : 'bg-gray-300/30'} backdrop-blur-sm`}
                />
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  transition={{ delay: 2 }}
                  className={`absolute bottom-32 right-16 w-12 h-12 rounded-full ${isDark ? 'bg-gray-600/20' : 'bg-gray-400/20'} backdrop-blur-sm`}
                />
              </div>
            </motion.div>

            {/* Right Form Panel */}
            <motion.div
              variants={rightPanelVariants}
              className="w-full lg:w-1/2 flex flex-col relative"
            >
              {/* Close Button */}
              <button
                onClick={handleClose}
                className={`absolute top-6 right-6 z-20 p-2 rounded-lg transition-all duration-200 ${themeStyles.button}`}
              >
                <X className="w-5 h-5" />
              </button>

              {/* Scrollable Content */}
              <div 
                className={`custom-scrollbar flex-1 overflow-y-auto p-8 ${
                  isDark 
                    ? '[&::-webkit-scrollbar-track]:bg-gray-800 [&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500' 
                    : '[&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-400 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500'
                } [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:rounded-sm`}
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: isDark ? '#4B5563 #1F2937' : '#9CA3AF #F3F4F6'
                }}
              >
                <div className="max-w-md mx-auto">
                  {/* Form Header */}
                  <div className="mb-8 pt-8">
                    <h2 className={`text-3xl font-bold ${themeStyles.text} mb-2`}>
                      {mode === "login" ? "Sign In" : "Create Account"}
                    </h2>
                    <p className={`${themeStyles.textSecondary}`}>
                      {mode === "login" ? "Enter your credentials to continue" : "Fill in your details to get started"}
                    </p>
                  </div>

                  {/* Form */}
                  <form onSubmit={handleSubmit} className="space-y-5">
                    {errors.general && (
                      <motion.div 
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm"
                      >
                        {errors.general}
                      </motion.div>
                    )}

                    {mode === "signup" && (
                      <>
                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            First Name
                          </label>
                          <div className="relative">
                            <User className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                            <input
                              type="text"
                              name="firstName"
                              value={formData.firstName}
                              onChange={handleInputChange}
                              className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${
                                errors.firstName ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                              placeholder="Enter your first name"
                              disabled={isLoading}
                            />
                          </div>
                          {errors.firstName && (
                            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                              {errors.firstName}
                            </motion.p>
                          )}
                        </div>

                        <div>
                          <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                            Last Name
                          </label>
                          <div className="relative">
                            <User className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                            <input
                              type="text"
                              name="lastName"
                              value={formData.lastName}
                              onChange={handleInputChange}
                              className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${
                                errors.lastName ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                              placeholder="Enter your last name"
                              disabled={isLoading}
                            />
                          </div>
                          {errors.lastName && (
                            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                              {errors.lastName}
                            </motion.p>
                          )}
                        </div>
                      </>
                    )}

                    <div>
                      <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                        Email Address
                      </label>
                      <div className="relative">
                        <Mail className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                        <input
                          type="email"
                          name="email"
                          value={formData.email}
                          onChange={handleInputChange}
                          className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${
                            errors.email ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                          }`}
                          placeholder="Enter your email"
                          disabled={isLoading}
                        />
                      </div>
                      {errors.email && (
                        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                          {errors.email}
                        </motion.p>
                      )}
                    </div>

                    <div>
                      <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                        Password
                      </label>
                      <div className="relative">
                        <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                        <input
                          type={showPassword ? "text" : "password"}
                          name="password"
                          value={formData.password}
                          onChange={handleInputChange}
                          className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${
                            errors.password ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                          }`}
                          placeholder="Enter your password"
                          disabled={isLoading}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.button}`}
                        >
                          {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                      </div>
                      {errors.password && (
                        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                          {errors.password}
                        </motion.p>
                      )}
                    </div>

                    {mode === "signup" && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                          Confirm Password
                        </label>
                        <div className="relative">
                          <Lock className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`} />
                          <input
                            type={showConfirmPassword ? "text" : "password"}
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${
                              errors.confirmPassword ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                            }`}
                            placeholder="Confirm your password"
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.button}`}
                          >
                            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                        {errors.confirmPassword && (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                            {errors.confirmPassword}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {mode === "login" && (
                      <div className="flex items-center justify-between">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            className={`rounded border ${isDark ? 'border-gray-600 bg-gray-700 text-gray-600' : 'border-gray-300 bg-white text-gray-600'} focus:ring-gray-500 focus:ring-2`}
                          />
                          <span className={`ml-2 text-sm ${themeStyles.textSecondary}`}>Remember me</span>
                        </label>
                        <button 
                          type="button" 
                          className={`text-sm font-medium transition-colors ${themeStyles.link}`}
                        >
                          Forgot password?
                        </button>
                      </div>
                    )}

                    <motion.button
                      type="submit"
                      disabled={isLoading}
                      className={`w-full py-3 rounded-lg font-medium transition-all duration-200 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${
                        isDark
                          ? "bg-white text-gray-900 hover:bg-gray-100"
                          : "bg-gray-900 text-white hover:bg-gray-800"
                      }`}
                      whileHover={!isLoading ? { scale: 1.02 } : {}}
                      whileTap={!isLoading ? { scale: 0.98 } : {}}
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className={`w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin`} />
                          <span>{mode === "login" ? "Signing in..." : "Creating account..."}</span>
                        </div>
                      ) : mode === "login" ? (
                        "Sign In"
                      ) : (
                        "Create Account"
                      )}
                    </motion.button>
                  </form>

                  {/* Footer */}
                  <div className="mt-6 text-center">
                    <p className={`text-sm ${themeStyles.textSecondary}`}>
                      {mode === "login" ? "Don't have an account? " : "Already have an account? "}
                      <button
                        onClick={() => handleModeSwitch(mode === "login" ? "signup" : "login")}
                        className={`font-medium transition-colors ${themeStyles.link}`}
                        disabled={isLoading}
                      >
                        {mode === "login" ? "Sign up" : "Sign in"}
                      </button>
                    </p>
                  </div>

                  {mode === "signup" && (
                    <p className={`text-xs ${themeStyles.textMuted} text-center mt-4 leading-relaxed mb-8`}>
                      By creating an account, you agree to our{" "}
                      <a href="#terms" className={`font-medium transition-colors ${themeStyles.link}`}>
                        Terms of Service
                      </a>{" "}
                      and{" "}
                      <a href="#privacy" className={`font-medium transition-colors ${themeStyles.link}`}>
                        Privacy Policy
                      </a>
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default AuthModal