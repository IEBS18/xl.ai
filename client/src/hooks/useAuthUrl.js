// hooks/useAuthUrl.js
"use client"

import { useEffect } from 'react'

export const useAuthUrl = (onOpenAuthModal) => {
  useEffect(() => {
    const checkUrlForAuthAction = () => {
      const urlParams = new URLSearchParams(window.location.search)
      const resetToken = urlParams.get('reset_token')
      const action = urlParams.get('action')
      
      if (resetToken && action === 'reset_password') {
        // Open auth modal in reset mode with the token
        onOpenAuthModal('reset', resetToken)
        
        // Don't clean up URL parameters immediately - let the modal handle it
        return true // Indicates that we handled a URL action
      }
      
      return false
    }

    // Check URL parameters on mount
    checkUrlForAuthAction()
    
    // Listen for URL changes (browser back/forward navigation)
    const handlePopState = () => {
      checkUrlForAuthAction()
    }
    
    window.addEventListener('popstate', handlePopState)
    
    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [onOpenAuthModal])
}