// context/AuthProvider.jsx
"use client"

import { createContext, useContext, useEffect } from 'react'
import { useUserStore } from '@/hooks/useUserStore'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    authChecked,
    checkAuthStatus, 
    login, 
    register, 
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
    clearUser 
  } = useUserStore()

  // Check authentication status on app load
  useEffect(() => {
    if (!authChecked) {
      checkAuthStatus()
    }
  }, [authChecked, checkAuthStatus])

  const value = {
    user,
    isAuthenticated,
    isLoading,
    authChecked,
    login,
    register,
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
    logout: clearUser,
    checkAuthStatus
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}