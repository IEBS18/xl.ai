import React from "react"
import { ThemeProvider } from "./context/ThemeProvider"
import Header from "./components/Header"
import MainContent from "./components/MainContent"
const App = () => {
  return (
    <ThemeProvider>
      <div className="min-h-screen transition-all duration-500">
        <Header />
        <MainContent />
      </div>
    </ThemeProvider>
  )
}

export default App