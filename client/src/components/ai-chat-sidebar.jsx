"use client"

import { useState, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Send, Bot, User, Plus, X, Code, Play } from "lucide-react"
import { useSpreadsheet } from "../lib/spreadsheet-context"

export function AIChatSidebar() {
  const { data, activeSheet, updateCell, getCellValue, evaluateFormula, setActiveSheet, addChart } = useSpreadsheet()

  console.log("AiChat: ", data)

  const [messages, setMessages] = useState([
    {
      id: "1",
      type: "ai",
      content:
        "Use the included price data to calculate the correlation between Bitcoin and Ethereum. Include a chart that shows the normalized prices along with the historical correlation. Make sure to clean any non-numeric and null values. Include the correlation analysis and chart in the same code cell. Use plot as last line to display the chart.",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const scrollAreaRef = useRef(null)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleCellUpdate = (command) => {
    const cellUpdateMatch = command.match(/^(?:([^!]+)!)?([A-Z]+\d+)=(.+)$/i)

    if (cellUpdateMatch) {
      const sheetName = cellUpdateMatch[1] || activeSheet
      const cellRef = cellUpdateMatch[2].toUpperCase()
      const value = cellUpdateMatch[3]

      if (!data[sheetName]) {
        return `❌ Sheet "${sheetName}" not found. Available sheets: ${Object.keys(data).join(", ")}`
      }

      try {
        if (sheetName !== activeSheet) {
          setActiveSheet(sheetName)
        }

        if (value.startsWith("=")) {
          const evaluatedValue = evaluateFormula(value, sheetName)
          updateCell(sheetName, cellRef, evaluatedValue, value, "formula")
          return `✅ Formula ${value} applied to ${sheetName}!${cellRef}. Result: ${evaluatedValue}`
        } else if (isImageUrl(value)) {
          updateCell(sheetName, cellRef, value, undefined, "image", value)
          return `✅ Image set in ${sheetName}!${cellRef}. Chart will be displayed in the spreadsheet!`
        } else {
          const numValue = Number.parseFloat(value)
          const finalValue = !isNaN(numValue) && value.trim() !== "" ? numValue : value
          updateCell(sheetName, cellRef, finalValue, undefined, typeof finalValue === "number" ? "number" : "text")
          return `✅ Cell ${sheetName}!${cellRef} updated to: ${finalValue}`
        }
      } catch (error) {
        return `❌ Error updating cell: ${error}`
      }
    }

    return ""
  }

  const queryAIBackend = async (spreadsheet, query, sheetName) => {
    try {
      const res = await fetch("http://localhost:5000/get-cell-value", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spreadsheet, query, sheetName }),
      })

      const data = await res.json()
      return data.result
    } catch (err) {
      console.error("Error calling backend:", err)
      return null
    }
  }


  const parseChartResponse = (response) => {
    const chartMatch = response.match(/([A-Za-z0-9_-]+)!=(.+)/)
    if (chartMatch) {
      return {
        chartId: chartMatch[1],
        imageUrl: chartMatch[2].trim(),
      }
    }
    return null
  }

  const isImageUrl = (url) => {
    return (
      url.startsWith("http") &&
      (url.includes(".jpg") ||
        url.includes(".png") ||
        url.includes(".gif") ||
        url.includes(".svg") ||
        url.includes(".jpeg") ||
        url.includes(".webp") ||
        url.includes("picsum") ||
        url.includes("placeholder"))
    )
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = inputValue
    setInputValue("")
    setIsTyping(true)

    try {
      const spreadsheet = { data: data[activeSheet] || {} }

      const response = await fetch("http://localhost:5000/get-cell-value", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spreadsheet,
          query: currentInput,
          sheetName: activeSheet,
        }),
      })

      const { result } = await response.json()
      let messageText = ""
      let hasChart = false
      let chartId = ""

      // ✅ 1. Handle cell updates
      if (result?.updates?.length > 0) {
        for (const update of result.updates) {
          const { cell, value } = update
          if (cell && value !== undefined) {
            handleCellUpdate(`${cell}=${value}`)
          }
        }
        messageText += `✅ Updated ${result.updates.length} cell(s).\n`
      }

      // ✅ 2. Handle chart insertion
      if (result.chart?.imageUrl) {
        const { id, imageUrl, label } = result.chart
        addChart(activeSheet, id, label, `http://localhost:5000${imageUrl}`)
        messageText += `📊 Chart "${label}" added to sheet "${activeSheet}".`
        hasChart = true
        chartId = id
      }

      // ✅ 3. Show AI confirmation message
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: messageText || "✅ Done.",
        timestamp: new Date(),
        hasChart,
        chartId,
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Error during AI processing:", error)
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: "❌ Error contacting AI backend.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiMessage])
    }

    setIsTyping(false)
  }



  const generateAIResponse = (input) => {
    const lowerInput = input.toLowerCase()

    // Check if user typed "chart"
    if (lowerInput.trim() === "chart") {
      const chartId = `Chart${Date.now()}`
      const imageUrl = `https://picsum.photos/400/300?random=${Date.now()}`

      return {
        response: `${chartId}!=${imageUrl}`,
        hasChart: true,
        chartId,
      }
    }

    if (lowerInput.includes("correlation") || lowerInput.includes("bitcoin")) {
      const chartId = `CorrelationChart${Date.now()}`
      const imageUrl = "https://picsum.photos/500/350?random=correlation"

      return {
        response: `${chartId}!=${imageUrl}`,
        hasChart: true,
        chartId,
      }
    }

    if (lowerInput.includes("line chart") || lowerInput.includes("trend")) {
      const chartId = `LineChart${Date.now()}`
      const imageUrl = "https://picsum.photos/450/300?random=line"

      return {
        response: `${chartId}!=${imageUrl}`,
        hasChart: true,
        chartId,
      }
    }

    if (lowerInput.includes("bar chart") || lowerInput.includes("volume")) {
      const chartId = `BarChart${Date.now()}`
      const imageUrl = "https://picsum.photos/400/280?random=bar"

      return {
        response: `${chartId}!=${imageUrl}`,
        hasChart: true,
        chartId,
      }
    }

    if (lowerInput.includes("formula") || lowerInput.includes("calculate")) {
      return {
        response: `🧮 I can help you with calculations and create charts directly over your spreadsheet!

📊 **Chart Commands:**
• Type "chart" - Creates a random chart
• "correlation chart" - BTC vs ETH correlation
• "line chart" - Price trend analysis
• "bar chart" - Volume or comparison charts

📈 **Financial Formulas:**
• =CORREL(B2:B50,E2:E50) - Calculate correlation
• =AVERAGE(B2:B50) - Average price
• =STDEV(B2:B50) - Standard deviation
• =(B2-B1)/B1 - Price change percentage

💡 **Chart Features:**
• Drag charts around the spreadsheet
• Resize using the corner handle
• Minimize with the - button
• Each chart has a unique ChartID

Charts are mapped to your current sheet: "${activeSheet}"`,
        hasChart: false,
        chartId: "",
      }
    }

    return {
      response: `I can help you analyze your financial data, create charts, and perform calculations. Try:

📈 **Quick Chart Generation:**
• Type "chart" to create a random chart
• "correlation chart" for BTC-ETH analysis
• "line chart" for trend visualization
• "bar chart" for volume analysis

🔧 **Spreadsheet Operations:**
• Update cells with formulas
• Create charts from data ranges
• Clean and process data

All charts are mapped to sheet: "${activeSheet}" and will be included in exports!

What would you like to create?`,
      hasChart: false,
      chartId: "",
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-600" />
          <span className="font-medium">Sheet chat</span>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm">
            <Plus className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Code className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollAreaRef} className="flex-1 p-4 overflow-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-2"
            >
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
                  {message.type === "ai" ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                </div>
                <span className="text-sm font-medium">
                  {message.type === "ai" ? message.chartId || "AI Assistant" : "You"}
                </span>
                {message.type === "ai" && (
                  <div className="flex items-center gap-1 ml-auto">
                    <Button variant="ghost" size="sm">
                      <Code className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Play className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>

              <div className="ml-8 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{message.content}</div>

              {message.hasChart && message.chartId && (
                <div className="ml-8 mt-2">
                  <div className="text-xs text-gray-500 mb-1">Chart {message.chartId} generated</div>
                  <div className="w-full h-20 bg-gradient-to-r from-blue-100 to-purple-100 rounded border flex items-center justify-center">
                    <span className="text-sm text-gray-600">
                      📊 {message.chartId} created on sheet "{activeSheet}"
                    </span>
                  </div>
                </div>
              )}
            </motion.div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex items-center gap-2"
            >
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
                <Bot className="w-3 h-3" />
              </div>
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 bg-gray-400 rounded-full"
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{
                      duration: 1,
                      repeat: Number.POSITIVE_INFINITY,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type 'chart' to create a chart..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            size="icon"
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Current sheet: "{activeSheet}" | Try: "chart", "correlation chart", "line chart"
        </p>
      </div>
    </div>
  )
}
