import React from "react"
import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "./context/ThemeProvider"
import Header from "./components/Header"
import MainContent from "./components/MainContent"
import ChatSession from "./components/ChatSession"

const App = () => {
  return (
    <ThemeProvider>
      <Router>
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
      </Router>
    </ThemeProvider>
  )
}

export default App