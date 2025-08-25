import React from "react"
import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "./context/ThemeProvider"
import { AuthProvider } from "./context/AuthProvider"
import { useAuthUrl } from "./hooks/useAuthUrl"
import Header from "./components/Header"
import MainContent from "./components/MainContent"
import ChatSession from "./components/ChatSession"
import DashboardList from "./components/DashboardList"

// Create a wrapper component to use hooks inside Router
const AppContent = () => {
  // This function will be called by useAuthUrl when a reset password link is clicked
  const handleOpenAuthModal = (mode = 'login', resetToken = null) => {
    // Dispatch a custom event that the Header can listen to
    window.dispatchEvent(new CustomEvent('openAuthModal', { 
      detail: { mode, resetToken } 
    }))
  }

  // Use the auth URL hook to handle password reset links
  useAuthUrl(handleOpenAuthModal)

  return (
    <div className="min-h-screen transition-all duration-500 flex flex-col">
      <Routes>
        {/* Landing page route */}
        <Route 
          path="/" 
          element={
            <>
              <Header />
              <main className="flex-1">
                <MainContent />
              </main>
            </>
          } 
        />
        
        {/* Chat session route */}
        <Route 
          path="/chat/:sessionId" 
          element={<ChatSession />} 
        />
        
        {/* Dashboard routes */}
        <Route 
          path="/dashboards" 
          element={<DashboardList onClose={() => window.history.back()} />} 
        />
        
        {/* Fallback to landing page */}
        <Route 
          path="*" 
          element={
            <>
              <Header />
              <main className="flex-1">
                <MainContent />
              </main>
            </>
          } 
        />
      </Routes>
    </div>
  )
}

// Create a wrapper component to use hooks inside Router
const AppContent = () => {
  // This function will be called by useAuthUrl when a reset password link is clicked
  const handleOpenAuthModal = (mode = 'login', resetToken = null) => {
    // Dispatch a custom event that the Header can listen to
    window.dispatchEvent(new CustomEvent('openAuthModal', { 
      detail: { mode, resetToken } 
    }))
  }

  // Use the auth URL hook to handle password reset links
  useAuthUrl(handleOpenAuthModal)

  return (
    <div className="min-h-screen transition-all duration-500 flex flex-col">
      <Routes>
        {/* Landing page route */}
        <Route 
          path="/" 
          element={
            <>
              <Header />
              <main className="flex-1">
                <MainContent />
              </main>
            </>
          } 
        />
        
        {/* Chat session route */}
        <Route 
          path="/chat/:sessionId" 
          element={<ChatSession />} 
        />
        
        {/* Fallback to landing page */}
        <Route 
          path="*" 
          element={
            <>
              <Header />
              <main className="flex-1">
                <MainContent />
              </main>
            </>
          } 
        />
      </Routes>
    </div>
  )
}

const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App