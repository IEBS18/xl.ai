"use client"

import { useState, useCallback, useMemo, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  X,
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  TrendingUp,
  BarChart3,
  Zap,
  Shield,
  CheckCircle,
  AlertCircle,
} from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import logo from '../../public/logo.svg'


const AuthModal = ({ isOpen, mode, resetToken, onClose, onSwitchMode }) => {
  const { login, register, verifyEmail, resendVerification, forgotPassword, resetPassword, isAuthenticated } = useAuth()
  const { isDark, themeClasses } = useTheme()
  const [currentView, setCurrentView] = useState(mode)
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
    verificationCode: "",
    resetToken: resetToken || "",
    rememberMe: false,
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [successMessage, setSuccessMessage] = useState("")
  const [countdown, setCountdown] = useState(0)
  const [shouldAutoClose, setShouldAutoClose] = useState(false)
  const [autoCloseCountdown, setAutoCloseCountdown] = useState(0)

  console.log(
    "🎭 AuthModal render - isOpen:",
    isOpen,
    "isAuthenticated:",
    isAuthenticated,
    "shouldAutoClose:",
    shouldAutoClose,
  )

  // Update current view when mode prop changes
  useEffect(() => {
    setCurrentView(mode)
  }, [mode])

  // Handle resetToken prop
  useEffect(() => {
    if (resetToken) {
      setFormData((prev) => ({ ...prev, resetToken }))
    }
  }, [resetToken])

  // Countdown for resend verification
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  // Get reset token from URL if needed
  useEffect(() => {
    if (!resetToken && isOpen) {
      const urlParams = new URLSearchParams(window.location.search)
      const token = urlParams.get("reset_token")
      const action = urlParams.get("action")

      if (token && action === "reset_password") {
        setCurrentView("reset")
        setFormData((prev) => ({ ...prev, resetToken: token }))
      }
    }
  }, [isOpen, resetToken])

  // Auto-close when user becomes authenticated
  useEffect(() => {
    console.log(
      "🔐 Auth useEffect - isAuthenticated:",
      isAuthenticated,
      "currentView:",
      currentView,
      "shouldAutoClose:",
      shouldAutoClose,
    )
    if (isAuthenticated && isOpen && currentView === "reset" && !shouldAutoClose) {
      console.log("🚀 User authenticated, triggering auto-close")
      setShouldAutoClose(true)
    }
  }, [isAuthenticated, isOpen, currentView, shouldAutoClose])

  // Handle auto-close countdown
  useEffect(() => {
    console.log("⏰ Auto-close useEffect - shouldAutoClose:", shouldAutoClose, "isOpen:", isOpen)
    if (shouldAutoClose && isOpen) {
      console.log("🎯 Starting 3-second countdown to close modal")
      setAutoCloseCountdown(3)

      const interval = setInterval(() => {
        setAutoCloseCountdown((prev) => {
          console.log("⏳ Countdown tick:", prev)
          if (prev <= 1) {
            console.log("🚪 CLOSING MODAL NOW!")
            clearInterval(interval)
            resetForm()
            onClose()
            setShouldAutoClose(false)
            return 0
          }
          return prev - 1
        })
      }, 1000)

      return () => {
        console.log("🧹 Cleaning up countdown interval")
        clearInterval(interval)
      }
    }
  }, [shouldAutoClose, isOpen, onClose])

  // Memoized theme styles
  const themeStyles = useMemo(
    () => ({
      modal: `${themeClasses.surfaceCard} ${themeClasses.border}`,
      leftPanel: isDark
        ? "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900"
        : "bg-gradient-to-br from-gray-50 via-white to-gray-100",
      text: themeClasses.text,
      textSecondary: themeClasses.textSecondary,
      textMuted: themeClasses.textMuted,
      input: isDark
        ? "bg-gray-800/50 border-gray-700 text-white placeholder-gray-500"
        : "bg-gray-50/50 border-gray-300 text-gray-900 placeholder-gray-400",
      inputFocus: isDark
        ? "focus:ring-2 focus:ring-gray-500/30 focus:border-gray-400"
        : "focus:ring-2 focus:ring-gray-400/30 focus:border-gray-600",
      inputError: "border-red-500 focus:ring-red-500/30 focus:border-red-500",
      button: themeClasses.button,
      link: isDark ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-gray-900",
      accent: themeClasses.text,
      success: themeClasses.success,
      warning: themeClasses.warning,
    }),
    [isDark],
  )

  // Animation features data
  const features = [
    { icon: TrendingUp, text: "Real-time Analytics", delay: 0 },
    { icon: BarChart3, text: "Advanced Insights", delay: 0.2 },
    { icon: Zap, text: "Lightning Fast", delay: 0.4 },
    { icon: Shield, text: "Enterprise Security", delay: 0.6 },
  ]

  const handleInputChange = useCallback(
    (e) => {
      const { name, value, type, checked } = e.target
      setFormData((prev) => ({
        ...prev,
        [name]: type === "checkbox" ? checked : value,
      }))
      if (errors[name]) {
        setErrors((prev) => ({ ...prev, [name]: "" }))
      }
      if (errors.general) {
        setErrors((prev) => ({ ...prev, general: "" }))
      }
      if (successMessage) {
        setSuccessMessage("")
      }
    },
    [errors, successMessage],
  )

  const validateForm = useCallback(() => {
    const newErrors = {}

    if (currentView === "signup" && !formData.firstName.trim()) {
      newErrors.firstName = "First name is required"
    }

    if (currentView === "signup" && !formData.lastName.trim()) {
      newErrors.lastName = "Last name is required"
    }

    if ((currentView === "login" || currentView === "signup" || currentView === "forgot") && !formData.email.trim()) {
      newErrors.email = "Email is required"
    } else if (
      (currentView === "login" || currentView === "signup" || currentView === "forgot") &&
      !/\S+@\S+\.\S+/.test(formData.email)
    ) {
      newErrors.email = "Email is invalid"
    }

    if ((currentView === "login" || currentView === "signup" || currentView === "reset") && !formData.password) {
      newErrors.password = "Password is required"
    } else if ((currentView === "signup" || currentView === "reset") && formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters"
    }

    if (currentView === "signup" && formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match"
    }

    if (currentView === "reset" && formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match"
    }

    if (currentView === "verify" && !formData.verificationCode.trim()) {
      newErrors.verificationCode = "Verification code is required"
    }

    if (currentView === "reset" && !formData.resetToken.trim()) {
      newErrors.resetToken = "Reset token is required"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [currentView, formData])

  const resetForm = useCallback(() => {
    setFormData({
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
      verificationCode: "",
      resetToken: resetToken || "",
      rememberMe: false,
    })
    setErrors({})
    setSuccessMessage("")
    setShowPassword(false)
    setShowConfirmPassword(false)
    setCountdown(0)
    setShouldAutoClose(false)
    setAutoCloseCountdown(0)
  }, [resetToken])

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault()
      if (!validateForm()) return

      setIsLoading(true)
      setErrors({})
      setSuccessMessage("")

      try {
        switch (currentView) {
          case "login":
            console.log("🔑 Login attempt")
            const loginResult = await login(formData.email, formData.password, formData.rememberMe)
            console.log("🔑 Login result:", loginResult)
            if (loginResult.requires_verification) {
              setCurrentView("verify")
              setSuccessMessage("Please verify your email to continue.")
            } else {
              resetForm()
              onClose()
            }
            break

          case "signup":
            console.log("📝 Signup attempt")
            await register(formData.firstName, formData.lastName, formData.email, formData.password)
            setCurrentView("verify")
            setSuccessMessage("Account created! Please check your email for verification code.")
            break

          case "verify":
            console.log("✉️ Email verification attempt")
            await verifyEmail(formData.email, formData.verificationCode)
            resetForm()
            onClose()
            break

          case "forgot":
            console.log("🔒 Forgot password attempt")
            await forgotPassword(formData.email)
            setSuccessMessage(
              "Password reset email sent! Please check your inbox and click the link to reset your password.",
            )
            break

          case "reset":
            console.log("🔥 PASSWORD RESET STARTED")
            console.log("📤 Calling resetPassword with token:", formData.resetToken)
            const resetResult = await resetPassword(formData.resetToken, formData.password)
            console.log("✅ Reset password result:", resetResult)

            const emailForLogin = resetResult?.email || formData.email
            console.log("📧 Email for auto-login:", emailForLogin)

            if (emailForLogin) {
              try {
                console.log("🔑 Attempting auto-login")
                const autoLoginResult = await login(emailForLogin, formData.password, false)
                console.log("🎯 Auto-login result:", autoLoginResult)

                if (autoLoginResult.requires_verification) {
                  console.log("📧 Verification required")
                  setCurrentView("verify")
                  setSuccessMessage("Please verify your email to continue.")
                } else if (autoLoginResult.success) {
                  console.log("🎉 AUTO-LOGIN SUCCESS! Should trigger modal close")
                  setSuccessMessage("Password reset successful! Welcome back!")
                  // The useEffect will handle closing when isAuthenticated becomes true
                } else {
                  console.log("❌ Auto-login failed - no success flag")
                  setSuccessMessage("Password reset successfully! Please login with your new password.")
                  setCurrentView("login")
                  setFormData((prev) => ({
                    ...prev,
                    email: emailForLogin,
                    password: "",
                    confirmPassword: "",
                    resetToken: "",
                  }))
                }
              } catch (loginError) {
                console.error("💥 Auto-login failed:", loginError)
                setSuccessMessage("Password reset successfully! Please login with your new password.")
                setCurrentView("login")
                setFormData((prev) => ({
                  ...prev,
                  email: emailForLogin,
                  password: "",
                  confirmPassword: "",
                  resetToken: "",
                }))
              }
            } else {
              console.log("❌ No email for auto-login")
              setSuccessMessage("Password reset successfully! Please login with your new password.")
              setCurrentView("login")
              setFormData((prev) => ({ ...prev, password: "", confirmPassword: "", resetToken: "" }))
            }
            break

          default:
            break
        }
      } catch (error) {
        console.error("💥 Auth error:", error)
        if (error.message.includes("verify your email")) {
          setCurrentView("verify")
          setSuccessMessage("Please verify your email to continue.")
        } else {
          setErrors({
            general: error.message || "Network error. Please try again.",
          })
        }
      } finally {
        setIsLoading(false)
      }
    },
    [
      validateForm,
      formData,
      currentView,
      login,
      register,
      verifyEmail,
      forgotPassword,
      resetPassword,
      resetForm,
      onClose,
    ],
  )

  const handleResendVerification = useCallback(async () => {
    if (countdown > 0) return

    setIsLoading(true)
    try {
      await resendVerification(formData.email)
      setSuccessMessage("Verification code sent!")
      setCountdown(60)
    } catch (error) {
      setErrors({ general: error.message || "Failed to resend verification code." })
    } finally {
      setIsLoading(false)
    }
  }, [formData.email, resendVerification, countdown])

  const handleViewSwitch = useCallback(
    (newView) => {
      setCurrentView(newView)
      setErrors({})
      setSuccessMessage("")
      if (newView !== currentView) {
        if (
          !(
            (currentView === "signup" && newView === "verify") ||
            (currentView === "login" && newView === "verify") ||
            (currentView === "forgot" && newView === "reset")
          )
        ) {
          resetForm()
        }
      }
      if (onSwitchMode) {
        onSwitchMode(newView)
      }
    },
    [currentView, resetForm, onSwitchMode],
  )

  const handleClose = useCallback(() => {
    console.log("🚪 handleClose called")
    resetForm()
    setCurrentView(mode)
    onClose()
  }, [resetForm, mode, onClose])

  const getViewContent = useCallback(() => {
    switch (currentView) {
      case "signup":
        return {
          title: "Create Account",
          description: "Fill in your details to get started",
          submitText: "Create Account",
        }
      case "verify":
        return {
          title: "Verify Email",
          description: "Enter the verification code sent to your email",
          submitText: "Verify Email",
        }
      case "forgot":
        return {
          title: "Forgot Password",
          description: "Enter your email to receive a reset link",
          submitText: "Send Reset Link",
        }
      case "reset":
        return {
          title: "Reset Password",
          description: "Enter your new password",
          submitText: "Reset Password",
        }
      default:
        return {
          title: "Sign In",
          description: "Enter your credentials to continue",
          submitText: "Sign In",
        }
    }
  }, [currentView])

  // Animation variants
  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
  }

  const modalVariants = {
    hidden: {
      opacity: 0,
      x: "100%",
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: "spring",
        duration: 0.5,
        bounce: 0.1,
        staggerChildren: 0.1,
      },
    },
    exit: {
      opacity: 0,
      x: "100%",
      scale: 0.95,
      transition: { duration: 0.3 },
    },
  }

  const leftPanelVariants = {
    hidden: { opacity: 0, x: -50 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.6, ease: "easeOut" },
    },
  }

  const rightPanelVariants = {
    hidden: { opacity: 0, x: 50 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.6, ease: "easeOut", delay: 0.2 },
    },
  }

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      transition: {
        duration: 4,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut",
      },
    },
  }

  const viewContent = getViewContent()

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
              <div className={`absolute inset-0 opacity-10 ${isDark ? "bg-white" : "bg-gray-900"}`}>
                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" />
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
                  <div className="flex items-center space-x-2">
                    <div className="flex flex-row gap-[3px]">
                      <span className={`text-2xl font-bold ${isDark ? "text-white" : "text-[#04165D]"}`}>
                        Insi
                      </span>
                      <img src={logo} className="w-8 h-8" alt="Logo" />
                      <span className={`text-2xl font-bold ${isDark ? "text-white" : "text-[#04165D]"}`}>
                        redict
                      </span>
                    </div>
                  </div>
                </motion.div>

                {/* Main Content */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="mb-8"
                >
                  <h2 className={`text-4xl font-bold ${themeStyles.text} mb-4 leading-tight`}>
                    {currentView === "login"
                      ? "Welcome Back!"
                      : currentView === "signup"
                        ? "Join InsiPredict"
                        : currentView === "verify"
                          ? "Almost There!"
                          : currentView === "forgot"
                            ? "Reset Password"
                            : currentView === "reset"
                              ? "New Password"
                              : "Welcome!"}
                  </h2>
                  <p className={`text-lg ${themeStyles.textSecondary} leading-relaxed`}>
                    {currentView === "login"
                      ? "Continue your journey with powerful data insights and predictive analytics."
                      : currentView === "signup"
                        ? "Transform your data into actionable insights with our advanced analytics platform."
                        : currentView === "verify"
                          ? "We've sent a verification code to your email. Please enter it below to activate your account."
                          : currentView === "forgot"
                            ? "Enter your email address and we'll send you a link to reset your password."
                            : currentView === "reset"
                              ? "Create a new password for your account."
                              : "Get started with InsiPredict today."}
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
                        className={`p-2 rounded-lg ${isDark ? "bg-gray-800/50" : "bg-white/50"} backdrop-blur-sm`}
                      >
                        <feature.icon className={`w-5 h-5 ${themeStyles.accent}`} />
                      </motion.div>
                      <span className={`${themeStyles.textSecondary} font-medium`}>{feature.text}</span>
                    </motion.div>
                  ))}
                </div>

                {/* Floating Elements */}
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  className={`absolute top-20 right-20 w-20 h-20 rounded-full ${isDark ? "bg-gray-700/30" : "bg-gray-300/30"} backdrop-blur-sm`}
                />
                <motion.div
                  variants={floatingVariants}
                  animate="animate"
                  transition={{ delay: 2 }}
                  className={`absolute bottom-32 right-16 w-12 h-12 rounded-full ${isDark ? "bg-gray-600/20" : "bg-gray-400/20"} backdrop-blur-sm`}
                />
              </div>
            </motion.div>

            {/* Right Form Panel */}
            <motion.div variants={rightPanelVariants} className="w-full lg:w-1/2 flex flex-col relative">
              {/* Close Button */}
              <button
                onClick={handleClose}
                className={`absolute top-6 right-6 z-20 p-2 rounded-lg transition-all duration-200 ${themeStyles.link}`}
              >
                <X className="w-5 h-5" />
              </button>

              {/* Scrollable Content */}
              <div
                className={`custom-scrollbar flex-1 overflow-y-auto p-8 ${isDark
                  ? "[&::-webkit-scrollbar-track]:bg-gray-800 [&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500"
                  : "[&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-400 [&::-webkit-scrollbar-thumb:hover]:bg-gray-500"
                  } [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:rounded-sm`}
                style={{
                  scrollbarWidth: "thin",
                  scrollbarColor: isDark ? "#4B5563 #1F2937" : "#9CA3AF #F3F4F6",
                }}
              >
                <div className="max-w-md mx-auto">
                  {/* Form Header */}
                  <div className="mb-8 pt-8">
                    <h2 className={`text-3xl font-bold ${themeStyles.text} mb-2`}>{viewContent.title}</h2>
                    <p className={`${themeStyles.textSecondary}`}>{viewContent.description}</p>
                  </div>

                  {/* Success Message */}
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-lg border mb-5 ${themeStyles.success}`}
                    >
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            {successMessage}
                            {shouldAutoClose && autoCloseCountdown > 0 && (
                              <span className="block mt-1 text-xs opacity-90">
                                Closing in {autoCloseCountdown} second{autoCloseCountdown !== 1 ? "s" : ""}...
                              </span>
                            )}
                          </p>
                          {currentView === "forgot" && successMessage.includes("email sent") && (
                            <div className="mt-2 text-xs opacity-90">
                              <p>• Check your spam folder if you don't see the email</p>
                              <p>• The reset link will expire in 1 hour</p>
                              <p>• Click the link in the email to reset your password</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Form */}
                  <form onSubmit={handleSubmit} className="space-y-5">
                    {errors.general && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center space-x-2"
                      >
                        <AlertCircle className="w-5 h-5" />
                        <span>{errors.general}</span>
                      </motion.div>
                    )}

                    {/* First Name - Signup */}
                    {currentView === "signup" && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>First Name</label>
                        <div className="relative">
                          <User
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`}
                          />
                          <input
                            type="text"
                            name="firstName"
                            value={formData.firstName}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${errors.firstName
                              ? themeStyles.inputError
                              : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder="Enter your first name"
                            disabled={isLoading}
                          />
                        </div>
                        {errors.firstName && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-red-500 text-sm mt-1"
                          >
                            {errors.firstName}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {/* Last Name - Signup */}
                    {currentView === "signup" && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>Last Name</label>
                        <div className="relative">
                          <User
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`}
                          />
                          <input
                            type="text"
                            name="lastName"
                            value={formData.lastName}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${errors.lastName
                              ? themeStyles.inputError
                              : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder="Enter your last name"
                            disabled={isLoading}
                          />
                        </div>
                        {errors.lastName && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-red-500 text-sm mt-1"
                          >
                            {errors.lastName}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {/* Verification Code - Verify */}
                    {currentView === "verify" && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                          Verification Code
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            name="verificationCode"
                            value={formData.verificationCode}
                            onChange={handleInputChange}
                            className={`w-full px-4 py-3 border rounded-lg transition-all duration-200 text-center text-2xl font-mono tracking-widest ${errors.verificationCode ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder="000000"
                            maxLength="6"
                            disabled={isLoading}
                          />
                        </div>
                        {errors.verificationCode && (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                            {errors.verificationCode}
                          </motion.p>
                        )}

                        {/* Resend Verification */}
                        <div className="mt-3 text-center">
                          <button
                            type="button"
                            onClick={handleResendVerification}
                            disabled={countdown > 0 || isLoading}
                            className={`text-sm font-medium transition-colors ${countdown > 0 ? themeStyles.textMuted : themeStyles.link} disabled:cursor-not-allowed`}
                          >
                            {countdown > 0 ? `Resend in ${countdown}s` : "Resend verification code"}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Email - Login, Signup, Forgot */}
                    {(currentView === "login" || currentView === "signup" || currentView === "forgot") && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>Email Address</label>
                        <div className="relative">
                          <Mail
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`}
                          />
                          <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-4 py-3 border rounded-lg transition-all duration-200 ${errors.email ? themeStyles.inputError : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder="Enter your email"
                            disabled={isLoading}
                          />
                        </div>
                        {errors.email && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-red-500 text-sm mt-1"
                          >
                            {errors.email}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {/* Password - Login, Signup, Reset */}
                    {(currentView === "login" || currentView === "signup" || currentView === "reset") && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>
                          {currentView === "reset" ? "New Password" : "Password"}
                        </label>
                        <div className="relative">
                          <Lock
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`}
                          />
                          <input
                            type={showPassword ? "text" : "password"}
                            name="password"
                            value={formData.password}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${errors.password
                              ? themeStyles.inputError
                              : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder={currentView === "reset" ? "Enter new password" : "Enter your password"}
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.link}`}
                          >
                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                        {errors.password && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-red-500 text-sm mt-1"
                          >
                            {errors.password}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {/* Confirm Password - Signup, Reset */}
                    {(currentView === "signup" || currentView === "reset") && (
                      <div>
                        <label className={`block text-sm font-medium ${themeStyles.text} mb-2`}>Confirm Password</label>
                        <div className="relative">
                          <Lock
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${themeStyles.textSecondary}`}
                          />
                          <input
                            type={showConfirmPassword ? "text" : "password"}
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            className={`w-full pl-10 pr-12 py-3 border rounded-lg transition-all duration-200 ${errors.confirmPassword
                              ? themeStyles.inputError
                              : `${themeStyles.input} ${themeStyles.inputFocus}`
                              }`}
                            placeholder="Confirm your password"
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className={`absolute right-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${themeStyles.link}`}
                          >
                            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                          </button>
                        </div>
                        {errors.confirmPassword && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-red-500 text-sm mt-1"
                          >
                            {errors.confirmPassword}
                          </motion.p>
                        )}
                      </div>
                    )}

                    {/* Remember Me & Forgot Password - Login */}
                    {currentView === "login" && (
                      <div className="flex items-center justify-between">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            name="rememberMe"
                            checked={formData.rememberMe}
                            onChange={handleInputChange}
                            className={`rounded border ${isDark ? "border-gray-600 bg-gray-700 text-gray-600" : "border-gray-300 bg-white text-gray-600"} focus:ring-gray-500 focus:ring-2`}
                            disabled={isLoading}
                          />
                          <span className={`ml-2 text-sm ${themeStyles.textSecondary}`}>Remember me</span>
                        </label>
                        <button
                          type="button"
                          onClick={() => handleViewSwitch("forgot")}
                          className={`text-sm font-medium transition-colors ${themeStyles.link}`}
                          disabled={isLoading}
                        >
                          Forgot password?
                        </button>
                      </div>
                    )}

                    {/* Submit Button */}
                    <motion.button
                      type="submit"
                      disabled={isLoading}
                      className={`w-full py-3 rounded-lg font-medium transition-all duration-200 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${themeClasses.button}"
                        }`}
                      whileHover={!isLoading ? { scale: 1.02 } : {}}
                      whileTap={!isLoading ? { scale: 0.98 } : {}}
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div
                            className={`w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin`}
                          />
                          <span>
                            {currentView === "login"
                              ? "Signing in..."
                              : currentView === "signup"
                                ? "Creating account..."
                                : currentView === "verify"
                                  ? "Verifying..."
                                  : currentView === "forgot"
                                    ? "Sending..."
                                    : currentView === "reset"
                                      ? "Resetting..."
                                      : "Processing..."}
                          </span>
                        </div>
                      ) : (
                        viewContent.submitText
                      )}
                    </motion.button>
                  </form>

                  {/* Footer Navigation */}
                  <div className="mt-6 text-center space-y-3">
                    {currentView === "login" && (
                      <p className={`text-sm ${themeStyles.textSecondary}`}>
                        Don't have an account?{" "}
                        <button
                          onClick={() => handleViewSwitch("signup")}
                          className={`font-medium transition-colors ${themeStyles.link}`}
                          disabled={isLoading}
                        >
                          Sign up
                        </button>
                      </p>
                    )}

                    {currentView === "signup" && (
                      <p className={`text-sm ${themeStyles.textSecondary}`}>
                        Already have an account?{" "}
                        <button
                          onClick={() => handleViewSwitch("login")}
                          className={`font-medium transition-colors ${themeStyles.link}`}
                          disabled={isLoading}
                        >
                          Sign in
                        </button>
                      </p>
                    )}

                    {currentView === "verify" && (
                      <p className={`text-sm ${themeStyles.textSecondary}`}>
                        Wrong email?{" "}
                        <button
                          onClick={() => handleViewSwitch("signup")}
                          className={`font-medium transition-colors ${themeStyles.link}`}
                          disabled={isLoading}
                        >
                          Change email
                        </button>
                      </p>
                    )}

                    {(currentView === "forgot" || currentView === "reset") && (
                      <p className={`text-sm ${themeStyles.textSecondary}`}>
                        Remember your password?{" "}
                        <button
                          onClick={() => handleViewSwitch("login")}
                          className={`font-medium transition-colors ${themeStyles.link}`}
                          disabled={isLoading}
                        >
                          Sign in
                        </button>
                      </p>
                    )}
                  </div>

                  {/* Terms and Privacy - Signup */}
                  {currentView === "signup" && (
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
