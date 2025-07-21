import React from "react"
import { ThemeProvider } from "./context/ThemeProvider"
import Header from "./components/Header"
import MainContent from "./components/MainContent"

const App = () => {
  return (
    <ThemeProvider>
      <div className="min-h-screen transition-all duration-500 flex flex-col">
        <Header />
        <main className="flex-1">
          <MainContent />
        </main>
      </div>
    </ThemeProvider>
  )
}

export default App
