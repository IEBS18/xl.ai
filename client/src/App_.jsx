"use client"
import { useState, useEffect, useRef, createContext, useContext } from "react"
import { io } from "socket.io-client"
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion"
import * as THREE from "three"
import {
  Send,
  FileText,
  BarChart3,
  Loader2,
  Paperclip,
  Copy,
  CheckCircle,
  AlertCircle,
  Code,
  Database,
  FileOutput,
  Check,
  ChevronDown,
  ChevronRight,
  Users,
  ArrowRight,
  Menu,
  X,
  Search,
  FileSpreadsheet,
  Presentation,
  MessageSquare,
  Moon,
  Sun,
  Eye,
  Network,
  ImageIcon,
} from "lucide-react"

// Theme Context
const ThemeContext = createContext()

const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(true)

  const toggleTheme = () => setIsDark(!isDark)

  return <ThemeContext.Provider value={{ isDark, toggleTheme }}>{children}</ThemeContext.Provider>
}

const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}

const App = () => {
  const { isDark, toggleTheme } = useTheme()
  const [socket, setSocket] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState("")
  const [fileUploaded, setFileUploaded] = useState(false)
  const [fileInfo, setFileInfo] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [connectionRetries, setConnectionRetries] = useState(0)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [backendUrl] = useState("http://localhost:5000")
  const [expandedMessages, setExpandedMessages] = useState(new Set())
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [activeTab, setActiveTab] = useState("spreadsheets")
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  const heroRef = useRef(null)
  const particlesRef = useRef(null)
  const networkRef = useRef(null)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  const { scrollYProgress } = useScroll()
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])

  // Mouse tracking for subtle interactions
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: -(e.clientY / window.innerHeight) * 2 + 1,
      })
    }

    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 60000) // Update every minute

    return () => clearInterval(timer)
  }, [])

  const getTimeBasedGreeting = () => {
    const hour = currentTime.getHours()
    if (hour >= 5 && hour < 12) return "Good Morning"
    if (hour >= 12 && hour < 17) return "Good Afternoon"
    if (hour >= 17 && hour < 22) return "Good Evening"
    return "Hi"
  }

  const shouldCollapseByDefault = (type) => {
    return ["code", "status", "dataframe"].includes(type)
  }

  const toggleMessageExpansion = (messageId) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  useEffect(() => {
    initializeConnection()
    checkSessionInfo()
    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const initializeConnection = () => {
    if (socket) {
      socket.removeAllListeners()
      socket.close()
    }

    const newSocket = io(backendUrl, {
      transports: ["polling", "websocket"],
      withCredentials: true,
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      autoConnect: true,
    })

    newSocket.on("connect", () => {
      setIsConnected(true)
      setConnectionRetries(0)
      console.log("Connected to server")
      if (fileUploaded) {
        setTimeout(() => {
          checkSessionSync()
        }, 500)
      }
    })

    newSocket.on("disconnect", (reason) => {
      setIsConnected(false)
      console.log("Disconnected from server:", reason)
      if (reason !== "io client disconnect") {
        addMessage("error", `Disconnected from server: ${reason}`)
      }
    })

    newSocket.on("connect_error", (error) => {
      console.error("Connection error:", error)
      setConnectionRetries((prev) => prev + 1)
      if (connectionRetries < 3) {
        addMessage("error", `Connection failed, retrying... (${connectionRetries + 1}/3)`)
      } else {
        addMessage("error", "Unable to connect to server. Please check if the backend is running on localhost:5000")
      }
    })

    newSocket.on("stream_data", (data) => {
      handleStreamData(data)
    })

    newSocket.on("status", (data) => {
      console.log("Status:", data.message)
    })

    setSocket(newSocket)
  }

  const checkSessionSync = async () => {
    try {
      const response = await fetch(`${backendUrl}/session-info`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.connected && data.data) {
        if (!fileUploaded) {
          setFileUploaded(true)
          setFileInfo(data.data)
          addMessage("success", "Session synced! File is ready for analysis.")
        } else {
          console.log("Session sync confirmed - file available in backend")
        }
      } else if (fileUploaded) {
        addMessage("error", "Session sync issue detected. Please re-upload your file.")
        setFileUploaded(false)
        setFileInfo(null)
      }
    } catch (error) {
      console.log("Session sync check failed:", error.message)
    }
  }

  const manualSessionSync = async () => {
    addMessage("status", "Checking session sync...")
    await checkSessionSync()
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const checkSessionInfo = async () => {
    try {
      const response = await fetch(`${backendUrl}/session-info`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      if (data.connected && data.data) {
        setFileUploaded(true)
        setFileInfo(data.data)
        addMessage(
          "system",
          `Restored session! Your data file "${data.data.filename}" is loaded with ${data.data.shape[0]} rows and ${data.data.shape[1]} columns.\n\nReady for analysis! What would you like to explore?`,
        )
      }
    } catch (error) {
      console.log("No existing session or connection error:", error.message)
    }
  }

  const handleStreamData = (data) => {
    const { type, data: content, timestamp } = data
    switch (type) {
      case "status":
        addMessage("status", content)
        break
      case "code":
        addMessage("code", content)
        break
      case "dataframe":
        addMessage("dataframe", content)
        break
      case "image":
        addMessage("image", content)
        break
      case "report":
        addMessage("report", content)
        break
      case "success":
        addMessage("success", content)
        setIsAnalyzing(false)
        break
      case "error":
        addMessage("error", content)
        setIsAnalyzing(false)
        break
      case "output":
        addMessage("output", content)
        break
      default:
        addMessage("system", content)
        break
    }
  }

  const addMessage = (type, content, isUser = false) => {
    const message = {
      id: Date.now() + Math.random(),
      type,
      content,
      isUser,
      timestamp: new Date().toISOString(),
      isCompleted: type !== "status", // Status messages start as not completed
    }

    setMessages((prev) => {
      const lastMessage = prev[prev.length - 1]

      // Enhanced duplicate prevention with better object comparison
      if (lastMessage && !isUser && Date.now() - new Date(lastMessage.timestamp).getTime() < 3000) {
        // For simple string content
        if (typeof content === "string" && typeof lastMessage.content === "string") {
          if (lastMessage.type === type && lastMessage.content === content) {
            console.log("Preventing duplicate string message:", content.substring(0, 50))
            return prev
          }
        }

        // For complex objects (dataframe, image)
        if (typeof content === "object" && typeof lastMessage.content === "object" && content && lastMessage.content) {
          if (lastMessage.type === type) {
            // For dataframe objects, compare by name and shape
            if (
              type === "dataframe" &&
              content.name === lastMessage.content.name &&
              JSON.stringify(content.shape) === JSON.stringify(lastMessage.content.shape)
            ) {
              console.log("Preventing duplicate dataframe message:", content.name)
              return prev
            }

            // For image objects, compare by filename
            if (type === "image" && content.filename === lastMessage.content.filename) {
              console.log("Preventing duplicate image message:", content.filename)
              return prev
            }
          }
        }
      }

      // Special handling for output messages - accumulate content with the last output message
      if (type === "output" && !isUser) {
        // Find the last output message in the array
        const lastOutputIndex = prev.findLastIndex((msg) => msg.type === "output")

        if (lastOutputIndex !== -1) {
          // Update the existing output message by accumulating content
          const updatedMessages = [...prev]
          updatedMessages[lastOutputIndex] = {
            ...updatedMessages[lastOutputIndex],
            content: updatedMessages[lastOutputIndex].content + "\n" + content,
            timestamp: new Date().toISOString(),
          }
          return updatedMessages
        }
        // If no previous output message found, add as new message (will fall through to end)
      }

      // Special handling for status messages - mark previous status as completed when new one arrives
      if (type === "status" && !isUser) {
        const updatedMessages = prev.map((msg, index) => {
          // Mark the last status message as completed
          if (index === prev.length - 1 && msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, message]
      }

      // For success, error, or other completion types, mark previous status as completed
      if (
        (type === "success" ||
          type === "error" ||
          type === "code" ||
          type === "dataframe" ||
          type === "image" ||
          type === "report") &&
        !isUser
      ) {
        const updatedMessages = prev.map((msg) => {
          if (msg.type === "status" && !msg.isCompleted) {
            return { ...msg, isCompleted: true }
          }
          return msg
        })
        return [...updatedMessages, message]
      }

      return [...prev, message]
    })
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const validTypes = [".csv", ".xlsx", ".xls"]
    const fileExtension = "." + file.name.split(".").pop().toLowerCase()
    if (!validTypes.includes(fileExtension)) {
      addMessage("error", "Please upload a CSV or Excel file (.csv, .xlsx, .xls)")
      return
    }

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      addMessage("error", "File size too large. Please upload a file smaller than 50MB.")
      return
    }

    const formData = new FormData()
    formData.append("file", file)

    try {
      setUploadProgress(10)
      addMessage("status", `Uploading "${file.name}"...`)
      const response = await fetch(`${backendUrl}/upload`, {
        method: "POST",
        body: formData,
        credentials: "include",
      })
      setUploadProgress(90)

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
      }

      const result = await response.json()
      if (result.success) {
        setFileUploaded(true)
        setFileInfo(result.data)
        setUploadProgress(100)
        addMessage(
          "success",
          `Successfully loaded "${result.data.filename}"!\n\nDataset: ${result.data.shape[0]} rows × ${result.data.shape[1]} columns\nColumns: ${result.data.columns.slice(0, 5).join(", ")}${result.data.columns.length > 5 ? "..." : ""}\n\nWhat would you like to analyze?`,
        )

        if (result.data.preview) {
          addMessage("dataframe", {
            name: "Data Preview",
            shape: result.data.shape,
            columns: result.data.columns,
            preview: result.data.preview,
          })
        }

        setTimeout(() => {
          checkSessionSync()
        }, 1000)
        setTimeout(() => setUploadProgress(0), 1000)
      } else {
        addMessage("error", `${result.error || "Upload failed"}`)
        setUploadProgress(0)
      }
    } catch (error) {
      addMessage("error", `Upload failed: ${error.message}`)
      setUploadProgress(0)
    }
  }

  const handleSendMessage = () => {
    if (!inputMessage.trim() || isAnalyzing) return

    if (!isConnected) {
      addMessage("error", "Not connected to server. Please check your connection.")
      return
    }

    // If no file uploaded and user tries to send message, prompt to upload file
    if (!fileUploaded) {
      addMessage("system", "Please upload a CSV or Excel file first to start analyzing your data.")
      return
    }

    addMessage("user", inputMessage, true)
    setIsAnalyzing(true)
    if (socket) {
      socket.emit("send_message", { message: inputMessage })
    }
    setInputMessage("")
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log("Copied to clipboard")
    })
  }

  const renderMarkdown = (text) => {
    // Simple markdown renderer for basic formatting
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, '<code class="bg-gray-800 text-green-400 px-2 py-1 rounded text-sm">$1</code>')
      .replace(/### (.*?)(\n|$)/g, '<h3 class="text-lg font-semibold mt-4 mb-2 text-white">$1</h3>')
      .replace(/## (.*?)(\n|$)/g, '<h2 class="text-xl font-semibold mt-6 mb-3 text-white">$1</h2>')
      .replace(/# (.*?)(\n|$)/g, '<h1 class="text-2xl font-bold mt-8 mb-4 text-white">$1</h1>')
      .replace(/\n\n/g, '</p><p class="mb-4">')
      .replace(/\n/g, "<br>")
  }

  const getStepIcon = (type, isCompleted) => {
    if (type === "status") {
      return isCompleted ? <Check size={14} /> : <Loader2 size={14} className="animate-spin" />
    }

    switch (type) {
      case "code":
        return <Code size={14} />
      case "dataframe":
        return <Database size={14} />
      case "image":
        return <ImageIcon size={14} />
      case "report":
        return <FileText size={14} />
      case "output":
        return <FileOutput size={14} />
      case "success":
        return <CheckCircle size={14} />
      case "error":
        return <AlertCircle size={14} />
      default:
        return <BarChart3 size={14} />
    }
  }

  const getStepColor = (type, isCompleted) => {
    if (type === "status") {
      return isCompleted ? "border-green-500 bg-green-500" : "border-black-500 bg-black-500"
    }

    switch (type) {
      case "success":
        return "border-green-500 bg-green-500"
      case "error":
        return "border-red-500 bg-red-500"
      case "code":
        return "border-purple-500 bg-purple-500"
      case "dataframe":
        return "border-cyan-500 bg-cyan-500"
      case "image":
        return "border-orange-500 bg-orange-500"
      case "report":
        return "border-indigo-500 bg-indigo-500"
      default:
        return "border-gray-500 bg-gray-500"
    }
  }

  const renderTimelineMessage = (message) => {
    const { type, content, isUser, isCompleted = true, id } = message
    const isCollapsible = shouldCollapseByDefault(type)
    const isExpanded = expandedMessages.has(id)
    const shouldShowContent = !isCollapsible || isExpanded

    if (isUser) {
      return (
        <div className="flex justify-end mb-6 animate-fadeIn">
          <div className="bg-white text-gray-900 px-4 py-3 rounded-xl max-w-xl shadow-lg border border-gray-200">
            {content}
          </div>
        </div>
      )
    }

    return (
      <div className="relative pl-6 pb-6 animate-slideIn">
        {/* Timeline line */}
        <div className="absolute left-3 top-6 bottom-0 w-px bg-gray-700"></div>

        {/* Step indicator */}
        <div
          className={`absolute left-0 top-1 w-6 h-6 rounded-full ${getStepColor(type, isCompleted)} flex items-center justify-center text-white shadow-lg z-10`}
        >
          {getStepIcon(type, isCompleted)}
        </div>

        {/* Content */}
        <div className="ml-6">
          <div className="bg-gray-900 rounded-xl shadow-xl border border-gray-800 overflow-hidden">
            {/* Header */}
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isCollapsible && (
                    <button
                      onClick={() => toggleMessageExpansion(id)}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>
                  )}
                  <span className="text-white font-medium capitalize flex items-center gap-2 text-sm">
                    {getStepIcon(type, isCompleted)}
                    {type === "dataframe"
                      ? "Data Analysis"
                      : type === "image"
                        ? "Visualization"
                        : type === "report"
                          ? "Strategic Report"
                          : type === "code"
                            ? "Generated Code"
                            : type === "output"
                              ? "Execution Output"
                              : type === "status"
                                ? isCompleted
                                  ? "Completed"
                                  : "Processing"
                                : type}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {type === "code" && shouldShowContent && (
                    <button
                      onClick={() => copyToClipboard(content)}
                      className="text-gray-400 hover:text-white p-1 rounded hover:bg-gray-700 transition-colors"
                      title="Copy code"
                    >
                      <Copy size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Body - Only show if expanded or not collapsible */}
            {shouldShowContent && (
              <div className="p-4">
                {type === "code" && (
                  <div className="bg-gray-950 rounded-lg p-3 overflow-x-auto">
                    <pre className="text-green-400 text-sm whitespace-pre-wrap font-mono">{content}</pre>
                  </div>
                )}

                {type === "dataframe" && (
                  <div>
                    <div className="mb-3">
                      <p className="text-gray-300 text-sm">
                        Shape: {content.shape[0]} rows × {content.shape[1]} columns
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-3 overflow-x-auto">
                      <div dangerouslySetInnerHTML={{ __html: content.preview }} />
                    </div>
                  </div>
                )}

                {type === "image" && (
                  <div className="text-center">
                    <img
                      src={content.data || "/placeholder.svg"}
                      alt={content.filename}
                      className="max-w-full h-auto rounded-lg shadow-lg mx-auto"
                    />
                    <p className="text-gray-400 text-sm mt-2">{content.filename}</p>
                  </div>
                )}

                {type === "report" && (
                  <div className="prose prose-invert max-w-none">
                    <div
                      className="text-gray-300 leading-relaxed text-sm"
                      dangerouslySetInnerHTML={{ __html: `<p class="mb-3">${renderMarkdown(content)}</p>` }}
                    />
                  </div>
                )}

                {(type === "system" ||
                  type === "status" ||
                  type === "success" ||
                  type === "error" ||
                  type === "output") && (
                  <div
                    className={`${
                      type === "success"
                        ? "text-green-400"
                        : type === "error"
                          ? "text-red-400"
                          : type === "status"
                            ? isCompleted
                              ? "text-green-400"
                              : "text-black-400"
                            : type === "output"
                              ? "text-cyan-400"
                              : "text-gray-300"
                    } whitespace-pre-wrap text-sm ${type === "output" ? "font-mono" : ""}`}
                  >
                    {content}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  const debugSession = async () => {
    try {
      const response = await fetch(`${backendUrl}/debug-session`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
      if (response.ok) {
        const data = await response.json()
        console.log("Session Debug Info:", data)
        addMessage(
          "system",
          `Debug Info:\nSession ID: ${data.session_id || "None"}\nHas Analyzer: ${data.has_analyzer}\nHas Session Data: ${data.has_session_data}\nAnalyzers: ${data.analyzers_count}\nSessions: ${data.session_data_count}`,
        )
      }
    } catch (error) {
      console.error("Debug failed:", error)
    }
  }

  const getSampleQuestions = () => [
    "Add trend indicators to the data",
    "Calculate performance scores for each category",
    "Forecast next 12 months of sales",
    "Create risk categories based on volatility",
    "Generate comprehensive report on revenue trends",
    "Clean and standardize the data",
    "Analyze seasonal patterns in the data",
    "Identify top performing segments",
  ]

  // Landing page data
  const connectors = [
    { name: "Google Sheets", icon: "📊" },
    { name: "Excel Online", icon: "📈" },
    { name: "Airtable", icon: "🗃️" },
    { name: "Notion", icon: "📝" },
    { name: "MySQL", icon: "🗄️" },
    { name: "PostgreSQL", icon: "🐘" },
    { name: "MongoDB", icon: "🍃" },
    { name: "Salesforce", icon: "☁️" },
    { name: "HubSpot", icon: "🎯" },
    { name: "Zapier", icon: "⚡" },
    { name: "CSV/Excel", icon: "📄" },
    { name: "API", icon: "🔌" },
  ]

  const tabs = [
    { id: "spreadsheets", icon: FileSpreadsheet, label: "Spreadsheets" },
    { id: "presentations", icon: Presentation, label: "Presentations" },
    { id: "documents", icon: FileText, label: "Documents" },
    { id: "analyst", icon: BarChart3, label: "Data Analyst" },
    { id: "search", icon: Search, label: "Deep & Enterprise Search" },
  ]

  const themeClasses = {
    bg: isDark ? "bg-black" : "bg-white",
    text: isDark ? "text-white" : "text-black",
    textSecondary: isDark ? "text-gray-400" : "text-gray-600",
    textMuted: isDark ? "text-gray-500" : "text-gray-400",
    surface: isDark ? "bg-gray-900" : "bg-gray-50",
    surfaceSecondary: isDark ? "bg-gray-800" : "bg-gray-100",
    border: isDark ? "border-gray-800" : "border-gray-200",
    button: isDark ? "bg-white text-black hover:bg-gray-100" : "bg-black text-white hover:bg-gray-900",
    buttonSecondary: isDark
      ? "border-gray-700 text-gray-300 hover:border-gray-600 hover:text-white"
      : "border-gray-300 text-gray-700 hover:border-gray-400 hover:text-black",
    glass: isDark ? "bg-gray-900/50 backdrop-blur-xl border-gray-800" : "bg-white/50 backdrop-blur-xl border-gray-200",
  }

  // Three.js Background Animation
  useEffect(() => {
    if (!heroRef.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    heroRef.current.appendChild(renderer.domElement)

    // Simple nodes - black and white only
    const nodes = []
    const connections = []

    const nodeGeometry = new THREE.SphereGeometry(0.02, 12, 12)
    const nodeMaterial = new THREE.MeshBasicMaterial({
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.6,
    })

    // Create minimal grid pattern
    for (let i = 0; i < 20; i++) {
      const node = new THREE.Mesh(nodeGeometry, nodeMaterial)
      const position = new THREE.Vector3(
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
      )

      node.position.copy(position)
      nodes.push({ core: node, originalPosition: position.clone() })
      scene.add(node)
    }

    // Simple connections
    const lineMaterial = new THREE.LineBasicMaterial({
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.1,
    })

    nodes.forEach((nodeA, i) => {
      nodes.forEach((nodeB, j) => {
        if (i !== j && nodeA.core.position.distanceTo(nodeB.core.position) < 5) {
          const geometry = new THREE.BufferGeometry().setFromPoints([nodeA.core.position, nodeB.core.position])
          const line = new THREE.Line(geometry, lineMaterial)
          connections.push({ line, nodeA: nodeA.core, nodeB: nodeB.core })
          scene.add(line)
        }
      })
    })

    camera.position.z = 8

    const animate = (time) => {
      requestAnimationFrame(animate)

      const t = time * 0.0003

      // Subtle floating motion
      nodes.forEach((node, i) => {
        const { core, originalPosition } = node
        core.position.y = originalPosition.y + Math.sin(t + i) * 0.1
        core.position.x = originalPosition.x + Math.cos(t + i * 0.5) * 0.05

        // Subtle opacity changes
        core.material.opacity = 0.4 + Math.sin(t * 2 + i) * 0.2
      })

      // Update connections
      connections.forEach((connection) => {
        const { line, nodeA, nodeB } = connection
        line.geometry.setFromPoints([nodeA.position, nodeB.position])
      })

      // Very subtle rotation
      scene.rotation.y = t * 0.02

      renderer.render(scene, camera)
    }

    animate(0)

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }

    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      if (heroRef.current && renderer.domElement) {
        heroRef.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [isDark])

  // Minimal particle system
  useEffect(() => {
    if (!particlesRef.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      75,
      particlesRef.current.clientWidth / particlesRef.current.clientHeight,
      0.1,
      1000,
    )
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })

    renderer.setSize(particlesRef.current.clientWidth, particlesRef.current.clientHeight)
    particlesRef.current.appendChild(renderer.domElement)

    const particleGeometry = new THREE.BufferGeometry()
    const particleCount = 50
    const positions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 15
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10
    }

    particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3))

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.02,
      color: isDark ? 0xffffff : 0x000000,
      transparent: true,
      opacity: 0.3,
    })

    const particles = new THREE.Points(particleGeometry, particleMaterial)
    scene.add(particles)

    camera.position.z = 8

    const animate = (time) => {
      requestAnimationFrame(animate)

      const t = time * 0.0005

      const positions = particles.geometry.attributes.position.array
      for (let i = 0; i < particleCount; i++) {
        positions[i * 3 + 1] += Math.sin(t + i * 0.1) * 0.001

        if (positions[i * 3 + 1] > 5) positions[i * 3 + 1] = -5
        if (positions[i * 3 + 1] < -5) positions[i * 3 + 1] = 5
      }
      particles.geometry.attributes.position.needsUpdate = true

      particles.rotation.y = t * 0.05

      renderer.render(scene, camera)
    }

    animate(0)

    return () => {
      if (particlesRef.current && renderer.domElement) {
        particlesRef.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [isDark])

  return (
    <div className={`min-h-screen transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes float-1 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          25% { transform: translateY(-15px) translateX(8px) rotate(1deg); }
          50% { transform: translateY(-8px) translateX(-4px) rotate(-0.5deg); }
          75% { transform: translateY(-12px) translateX(6px) rotate(0.5deg); }
        }
        @keyframes float-2 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          33% { transform: translateY(-12px) translateX(-6px) rotate(-1deg); }
          66% { transform: translateY(-18px) translateX(4px) rotate(0.5deg); }
        }
        @keyframes float-3 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          20% { transform: translateY(-8px) translateX(12px) rotate(0.5deg); }
          40% { transform: translateY(-15px) translateX(-8px) rotate(-0.5deg); }
          60% { transform: translateY(-4px) translateX(6px) rotate(0.3deg); }
          80% { transform: translateY(-12px) translateX(-4px) rotate(-0.3deg); }
        }
        @keyframes float-4 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          25% { transform: translateY(-14px) translateX(-9px) rotate(-0.8deg); }
          50% { transform: translateY(-6px) translateX(8px) rotate(0.4deg); }
          75% { transform: translateY(-16px) translateX(-5px) rotate(0.6deg); }
        }
        @keyframes float-5 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          30% { transform: translateY(-9px) translateX(14px) rotate(0.7deg); }
          60% { transform: translateY(-18px) translateX(-6px) rotate(-0.4deg); }
        }
        @keyframes float-6 {
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          40% { transform: translateY(-12px) translateX(-12px) rotate(-0.6deg); }
          80% { transform: translateY(-6px) translateX(9px) rotate(0.3deg); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out forwards;
          opacity: 0;
        }
        .animate-slideIn {
          animation: slideIn 0.8s ease-out forwards;
          opacity: 0;
        }
        .animate-float-1 {
          animation: float-1 12s ease-in-out infinite;
        }
        .animate-float-2 {
          animation: float-2 15s ease-in-out infinite;
        }
        .animate-float-3 {
          animation: float-3 18s ease-in-out infinite;
        }
        .animate-float-4 {
          animation: float-4 14s ease-in-out infinite;
        }
        .animate-float-5 {
          animation: float-5 16s ease-in-out infinite;
        }
        .animate-float-6 {
          animation: float-6 13s ease-in-out infinite;
        }
      `}</style>

      {/* Header */}
      <header className={`fixed top-0 w-full z-50 ${themeClasses.glass} border-b ${themeClasses.border}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.div
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <div className="flex items-center space-x-1">
                <div className={`w-6 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
                <div className={`w-2 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
              </div>
              <span className={`text-xl font-semibold ${themeClasses.text}`}>DataScope AI</span>
            </motion.div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              <div className="relative group">
                <button
                  className={`flex items-center space-x-1 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                >
                  <span>Use Cases</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>
              <a
                href="#contact"
                className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
              >
                Contact Us
              </a>
              <a
                href="#pricing"
                className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
              >
                Pricing
              </a>
            </nav>

            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-red-400"} shadow-lg animate-pulse`}
                ></div>
                <span className="text-xs font-medium text-gray-300">{isConnected ? "Connected" : "Disconnected"}</span>
              </div>

              {/* Theme Toggle */}
              <motion.button
                onClick={toggleTheme}
                className={`p-2 rounded-lg border ${themeClasses.border} hover:scale-110 transition-all duration-300`}
                whileHover={{ rotate: 180 }}
                whileTap={{ scale: 0.9 }}
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
                      <Sun className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="moon"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Moon className="w-5 h-5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>

              <button
                className={`hidden md:inline-flex ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
              >
                Log in
              </button>

              <motion.button
                className={`${themeClasses.button} px-4 py-2 rounded-lg font-medium transition-all duration-300 flex items-center space-x-2`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span>Sign Up</span>
                <ArrowRight className="w-4 h-4" />
              </motion.button>

              {/* Mobile menu button */}
              <button className={`md:hidden ${themeClasses.textSecondary}`} onClick={() => setIsMenuOpen(!isMenuOpen)}>
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
                className={`md:hidden border-t ${themeClasses.border} py-4`}
              >
                <div className="flex flex-col space-y-4">
                  <a
                    href="#usecases"
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                  >
                    Use Cases
                  </a>
                  <a
                    href="#contact"
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                  >
                    Contact Us
                  </a>
                  <a
                    href="#pricing"
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}
                  >
                    Pricing
                  </a>
                  <button
                    className={`text-left ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
                  >
                    Log in
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Hero Section - Working Chat Interface */}
      <section className="relative pt-32 pb-20 overflow-hidden min-h-screen flex flex-col">
        {/* Three.js Background */}
        <div ref={heroRef} className="absolute inset-0 z-0 opacity-20" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex-1">
          {!fileUploaded && messages.length === 0 ? (
            // Landing page hero content
            <div className="relative h-full w-full overflow-hidden min-h-[80vh]">
              {/* Background with enhanced visibility */}
              <div className="absolute inset-0 z-0">
                <div className="absolute inset-0 bg-gradient-to-br from-gray-900/80 via-gray-950/85 to-black/90 z-20"></div>

                {/* Animated Interface Screenshots with higher visibility */}
                <div className="absolute inset-0 z-10">
                  {/* Keep all the floating animations as they are */}
                  {/* Timeline Animation */}
                  <div className="absolute top-8 left-8 w-64 opacity-50 animate-float-1">
                    <div className="bg-gray-800/90 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2 mb-3">
                        <div className="w-6 h-6 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                          <Check size={12} className="text-white" />
                        </div>
                        <span className="text-green-400 text-sm font-semibold">Completed</span>
                      </div>
                      <p className="text-gray-200 text-xs">Analyzing query: Forecast next 12 months of sales</p>
                    </div>
                  </div>

                  {/* Code Block Animation */}
                  <div className="absolute top-24 right-12 w-60 opacity-45 animate-float-2">
                    <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2 mb-3">
                        <Code size={14} className="text-purple-400" />
                        <span className="text-purple-400 text-sm font-semibold">Generated Code</span>
                      </div>
                      <div className="bg-gray-950/90 rounded-lg p-3 text-xs font-mono border border-gray-700/50">
                        <div className="text-green-400 mb-1">import pandas as pd</div>
                        <div className="text-green-400 mb-1">import numpy as np</div>
                        <div className="text-black-400 mb-1"># Statistical forecasting</div>
                        <div className="text-yellow-400">model = SARIMAX(data)</div>
                      </div>
                    </div>
                  </div>

                  {/* Chart Visualization */}
                  <div className="absolute bottom-24 left-16 w-60 opacity-50 animate-float-3">
                    <div className="bg-gray-800/90 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2 mb-3">
                        <BarChart3 size={14} className="text-orange-400" />
                        <span className="text-orange-400 text-sm font-semibold">Visualization</span>
                      </div>
                      <div className="bg-white rounded-lg p-3 h-20 flex items-center justify-center shadow-inner">
                        <div className="w-full h-full bg-gradient-to-r from-black-100 to-purple-100 rounded flex items-center justify-center">
                          <span className="text-gray-600 text-xs font-medium">Revenue Forecast Chart</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Data Table */}
                  <div className="absolute bottom-12 right-8 w-54 opacity-45 animate-float-4">
                    <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-4 border border-gray-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2 mb-3">
                        <Database size={14} className="text-cyan-400" />
                        <span className="text-cyan-400 text-sm font-semibold">Data Analysis</span>
                      </div>
                      <div className="space-y-1 text-xs font-mono">
                        <div className="text-cyan-300">Shape: 12 rows × 2 columns</div>
                        <div className="text-gray-300">Historical Revenue Analysis</div>
                        <div className="text-gray-400 text-xs">Confidence intervals calculated</div>
                      </div>
                    </div>
                  </div>

                  {/* Success Message */}
                  <div className="absolute top-48 left-24 w-60 opacity-50 animate-float-5">
                    <div className="bg-gradient-to-r from-green-900/70 to-emerald-900/70 backdrop-blur-md rounded-2xl p-4 border border-green-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2">
                        <CheckCircle size={14} className="text-green-300" />
                        <span className="text-green-200 text-sm font-semibold">Analysis completed successfully</span>
                      </div>
                      <p className="text-green-100 text-xs mt-1">Generated 4 result DataFrames</p>
                    </div>
                  </div>

                  {/* Processing Status */}
                  <div className="absolute top-60 right-24 w-54 opacity-45 animate-float-6">
                    <div className="bg-gradient-to-r from-black-900/70 to-indigo-900/70 backdrop-blur-md rounded-2xl p-4 border border-black-600/60 shadow-2xl">
                      <div className="flex items-center space-x-2">
                        <Loader2 size={14} className="text-black-300 animate-spin" />
                        <span className="text-black-200 text-sm font-semibold">Generating insights</span>
                      </div>
                      <p className="text-black-100 text-xs mt-1">Processing advanced analytics</p>
                    </div>
                  </div>
                </div>

                {/* Enhanced ambient background elements */}
                <div
                  className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-r from-black-500/8 to-indigo-500/8 rounded-full blur-3xl animate-bounce"
                  style={{ animationDuration: "8s" }}
                ></div>
                <div
                  className="absolute bottom-1/4 right-1/4 w-56 h-56 bg-gradient-to-r from-purple-500/8 to-pink-500/8 rounded-full blur-3xl animate-pulse"
                  style={{ animationDuration: "10s" }}
                ></div>
                <div
                  className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-gradient-to-r from-indigo-500/6 to-black-500/6 rounded-full blur-3xl animate-ping"
                  style={{ animationDuration: "12s" }}
                ></div>
              </div>

              {/* Content */}
              <div className="relative z-20 flex flex-col items-center justify-center h-full text-center max-w-4xl mx-auto px-6 py-20">
                {/* Stylish Greeting */}
                <div className="mb-8 animate-fadeIn">
                  <div className="mb-4">
                    <h1
                      className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-black-100 to-indigo-200 mb-3 tracking-tight leading-none"
                      style={{ fontFamily: "SF Pro Display, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                    >
                      {getTimeBasedGreeting()}, Ayush
                    </h1>
                    <div className="h-0.5 w-24 bg-gradient-to-r from-black-400 via-purple-500 to-indigo-500 mx-auto rounded-full shadow-lg"></div>
                  </div>
                  <p
                    className="text-lg text-gray-200 mb-2 font-light tracking-wide"
                    style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                  >
                    Welcome back to DataScope AI
                  </p>
                  <p
                    className="text-sm text-gray-400 font-light tracking-wide"
                    style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                  >
                    Ready to unlock insights from your data?
                  </p>
                </div>

                {/* Enhanced Central Input Area */}
                <div className="w-full max-w-2xl mb-10 animate-slideIn" style={{ animationDelay: "0.3s" }}>
                  <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-black-500/20 via-purple-500/20 to-indigo-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-300"></div>
                    <div className="relative">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={
                          !isConnected
                            ? "Connecting to server..."
                            : "Upload a file or describe what you'd like to analyze..."
                        }
                        disabled={!isConnected}
                        className="w-full px-6 py-4 bg-gray-800/90 backdrop-blur-xl border border-gray-600/60 rounded-2xl focus:outline-none focus:ring-2 focus:ring-black-500/60 focus:border-black-500/60 disabled:bg-gray-900/80 disabled:text-gray-500 text-base shadow-2xl text-white placeholder-gray-400 transition-all duration-300 font-light"
                        style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                      />
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-3">
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/60 transition-all duration-200 rounded-xl backdrop-blur-sm group-hover:scale-105"
                          title="Upload file"
                        >
                          <Paperclip size={18} />
                        </button>
                        <button
                          onClick={handleSendMessage}
                          disabled={!inputMessage.trim() || !isConnected}
                          className="bg-gradient-to-r from-black-500 to-purple-500 text-white p-2 rounded-xl hover:from-black-600 hover:to-purple-600 transition-all duration-200 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed shadow-xl transform hover:scale-105 disabled:transform-none backdrop-blur-sm"
                        >
                          <Send size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Refined Feature Info */}
                <div className="text-center animate-slideIn" style={{ animationDelay: "0.6s" }}>
                  <div className="text-gray-400 space-y-4">
                    <p
                      className="font-medium text-base text-gray-300"
                      style={{ fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}
                    >
                      Supports CSV, Excel files up to 50MB
                    </p>
                    <div className="flex items-center justify-center space-x-8 text-sm">
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className="w-2 h-2 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full shadow-lg group-hover:shadow-green-400/50 transition-all duration-300"></div>
                        <span
                          className="font-medium text-gray-300"
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Real-time Analysis
                        </span>
                      </span>
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className="w-2 h-2 bg-gradient-to-r from-black-400 to-cyan-500 rounded-full shadow-lg group-hover:shadow-black-400/50 transition-all duration-300"></div>
                        <span
                          className="font-medium text-gray-300"
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Interactive Charts
                        </span>
                      </span>
                      <span className="flex items-center space-x-2 group cursor-default">
                        <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-indigo-500 rounded-full shadow-lg group-hover:shadow-purple-400/50 transition-all duration-300"></div>
                        <span
                          className="font-medium text-gray-300"
                          style={{
                            fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
                          }}
                        >
                          Strategic Reports
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Connectors Section - Only show when no file uploaded */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.0 }}
                className="text-center mt-20 pb-20"
              >
                <p className={`text-xs ${themeClasses.textMuted} uppercase tracking-widest mb-12 font-medium`}>
                  CONNECTS WITH YOUR FAVORITE TOOLS
                </p>

                <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-12 gap-4 max-w-6xl mx-auto">
                  {connectors.map((connector, index) => (
                    <motion.div
                      key={connector.name}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{
                        duration: 0.4,
                        delay: index * 0.03,
                        type: "spring",
                        stiffness: 200,
                      }}
                      className={`p-4 rounded-xl text-center hover:scale-105 transition-all duration-300 cursor-pointer border ${themeClasses.border} ${themeClasses.glass}`}
                      whileHover={{ y: -2 }}
                    >
                      <div className="text-2xl mb-2">{connector.icon}</div>
                      <div className={`text-xs font-medium ${themeClasses.textMuted}`}>{connector.name}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          ) : (
            // Chat interface - when file is uploaded or messages exist
            <div className="max-w-4xl mx-auto min-h-[80vh] flex flex-col">
              <div className="flex-1">
                {messages.map((message) => (
                  <div key={message.id}>{renderTimelineMessage(message)}</div>
                ))}
                {isAnalyzing && (
                  <div className="relative pl-6 pb-6 animate-slideIn">
                    <div className="absolute left-3 top-6 bottom-0 w-px bg-gray-700"></div>
                    <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-black-500 flex items-center justify-center text-white shadow-lg z-10">
                      <Loader2 size={14} className="animate-spin" />
                    </div>
                    <div className="ml-6">
                      <div className="bg-gray-900 rounded-xl shadow-xl border border-gray-800 p-4">
                        <div className="text-black-400 flex items-center gap-2 text-sm">
                          <Loader2 size={16} className="animate-spin" />
                          Analyzing your request...
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Sample Questions */}
      {fileUploaded && messages.filter((m) => m.isUser).length === 0 && (
        <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
          <div className="max-w-4xl mx-auto">
            <p className="text-xs font-semibold text-gray-300 mb-2">Try these sample questions:</p>
            <div className="flex flex-wrap gap-2">
              {getSampleQuestions()
                .slice(0, 4)
                .map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(question)}
                    className="text-xs bg-gray-800 text-gray-300 px-3 py-2 rounded-full hover:bg-gray-700 transition-colors border border-gray-700 shadow-sm hover:shadow-md"
                  >
                    {question}
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {uploadProgress > 0 && (
        <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-full h-2 shadow-inner">
              <div
                className="bg-gradient-to-r from-black-500 to-purple-500 h-2 rounded-full transition-all duration-300 shadow-sm"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-400 mt-1 font-medium">Uploading... {uploadProgress}%</p>
          </div>
        </div>
      )}

      {/* File Info */}
      {fileUploaded && fileInfo && (
        <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileText size={16} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-300">{fileInfo.filename}</span>
              <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded-full shadow-sm border border-gray-700">
                {fileInfo.shape[0]} rows × {fileInfo.shape[1]} columns
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={debugSession}
                className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded hover:bg-gray-600 transition-colors shadow-sm border border-gray-600"
                title="Debug session info"
              >
                Debug
              </button>
              <button
                onClick={manualSessionSync}
                className="text-xs bg-black-600 text-white px-2 py-1 rounded hover:bg-black-700 transition-colors shadow-sm"
                title="Refresh session sync"
              >
                Sync
              </button>
              <span className="text-xs text-green-400 font-semibold bg-green-900 px-2 py-1 rounded-full border border-green-700">
                Loaded
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Input Area - Only show when file is uploaded */}
      {fileUploaded && (
        <div className="p-4 bg-gray-900 border-t border-gray-800 shadow-xl">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors rounded-lg border border-gray-700"
                title="Upload new file"
              >
                <Paperclip size={18} />
              </button>
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={!isConnected ? "Connecting to server..." : "Ask me anything about your data..."}
                  disabled={isAnalyzing || !isConnected}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-black-500 focus:border-transparent disabled:bg-gray-900 disabled:text-gray-500 text-sm shadow-sm text-white placeholder-gray-500"
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isAnalyzing || !isConnected}
                className="bg-white text-gray-900 p-3 rounded-xl hover:bg-gray-100 transition-all duration-200 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
                title={!isConnected ? "Not connected" : "Send message"}
              >
                {isAnalyzing ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden File Input */}
      <input ref={fileInputRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} className="hidden" />

      {/* Landing Page Sections - Only show when no file uploaded AND no messages */}
      {!fileUploaded && messages.length === 0 && (
        <>
          {/* Collaboration Section */}
          <section className={`py-24 ${themeClasses.surface} relative overflow-hidden`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
                className="text-center mb-20"
              >
                <h2 className={`text-4xl md:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
                  One workspace to
                  <br />
                  move faster, together
                </h2>
              </motion.div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                {/* Performance Report Mockup */}
                <motion.div
                  initial={{ opacity: 0, x: -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
                >
                  <motion.div
                    className={`${themeClasses.surface} p-8 rounded-2xl shadow-2xl border ${themeClasses.border}`}
                    whileHover={{ scale: 1.01 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="flex items-center justify-between mb-6">
                      <h3 className={`text-2xl font-semibold ${themeClasses.text}`}>Performance Report</h3>
                      <span className={`text-sm ${themeClasses.textMuted}`}>Q2 2025</span>
                    </div>

                    <div className="space-y-8">
                      <div>
                        <h4 className={`font-medium mb-3 ${themeClasses.text}`}>Summary</h4>
                        <p className={`text-sm ${themeClasses.textSecondary} leading-relaxed`}>
                          Performance metrics show significant improvement across key indicators with notable
                          enhancement in operational efficiency and customer satisfaction.
                        </p>
                      </div>

                      <div>
                        <h4 className={`font-medium mb-6 ${themeClasses.text}`}>Monthly Active Users</h4>
                        <div className="flex items-end space-x-2 h-32">
                          {[...Array(12)].map((_, i) => (
                            <motion.div
                              key={i}
                              className={`${isDark ? "bg-white" : "bg-black"} rounded-sm flex-1 opacity-80`}
                              style={{ height: `${Math.random() * 80 + 20}%` }}
                              initial={{ height: 0 }}
                              whileInView={{ height: `${Math.random() * 80 + 20}%` }}
                              transition={{ duration: 1, delay: i * 0.1 }}
                              viewport={{ once: true }}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </motion.div>

                {/* Chat Interface Mockup */}
                <motion.div
                  initial={{ opacity: 0, x: 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className={`${isDark ? "bg-gray-900" : "bg-gray-100"} p-8 rounded-3xl border ${themeClasses.border}`}
                >
                  <div className="flex items-center space-x-3 mb-8">
                    <div
                      className={`w-10 h-10 ${isDark ? "bg-gray-800" : "bg-gray-200"} rounded-lg flex items-center justify-center`}
                    >
                      <MessageSquare className="w-5 h-5" />
                    </div>
                    <div>
                      <div className={`font-medium ${themeClasses.text}`}>DataScope AI</div>
                      <div className={`text-sm ${themeClasses.textMuted}`}>Market-team</div>
                    </div>
                  </div>

                  <div className="space-y-6 mb-8">
                    <motion.div
                      className="flex items-start space-x-3"
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: 0.2 }}
                      viewport={{ once: true }}
                    >
                      <div
                        className={`w-8 h-8 ${isDark ? "bg-gray-700" : "bg-gray-300"} rounded-full flex-shrink-0`}
                      ></div>
                      <div>
                        <div className={`font-medium text-sm ${themeClasses.text}`}>Tony</div>
                        <div className={`text-sm ${themeClasses.textSecondary}`}>
                          How's the progress on the report team?
                        </div>
                      </div>
                    </motion.div>

                    <motion.div
                      className="flex items-start space-x-3"
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: 0.4 }}
                      viewport={{ once: true }}
                    >
                      <div
                        className={`w-8 h-8 ${isDark ? "bg-gray-700" : "bg-gray-300"} rounded-full flex-shrink-0`}
                      ></div>
                      <div>
                        <div className={`font-medium text-sm ${themeClasses.text}`}>David</div>
                        <div className={`text-sm ${themeClasses.textSecondary}`}>
                          Just gave the task to DataScope AI, should have it soon
                        </div>
                      </div>
                    </motion.div>
                  </div>

                  <motion.div
                    className={`${isDark ? "bg-gray-800" : "bg-gray-200"} rounded-xl p-6 border ${themeClasses.border}`}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.6 }}
                    viewport={{ once: true }}
                    whileHover={{ scale: 1.01 }}
                  >
                    <div className={`flex items-center space-x-2 text-sm ${themeClasses.textSecondary} mb-2`}>
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Q2_Performance_Report.xlsx</span>
                    </div>
                    <div className={`text-xs ${themeClasses.textMuted}`}>Generated by DataScope AI • 2 min ago</div>
                  </motion.div>
                </motion.div>
              </div>

              {/* Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
                {[
                  {
                    title: "Smart collaboration",
                    description:
                      "Built-in editors for spreadsheets, presentations and documents that run many iterations across multitudes of drafts",
                    icon: Users,
                  },
                  {
                    title: "Uses your tools like you do",
                    description:
                      "DataScope AI integrates with any spreadsheet, database, doc, chat, ticket, and data source that you have. From Slack to Salesforce.",
                    icon: Network,
                  },
                  {
                    title: "Shows its thinking",
                    description:
                      "Deep research capabilities that lead to all deliverables being grounded in data and tailored for your use case",
                    icon: Eye,
                  },
                ].map((feature, index) => (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className={`text-center p-8 rounded-2xl border ${themeClasses.border} hover:scale-105 transition-all duration-300 group cursor-pointer`}
                    whileHover={{ y: -5 }}
                  >
                    <motion.div
                      className={`w-12 h-12 ${themeClasses.surfaceSecondary} rounded-xl flex items-center justify-center mb-6 mx-auto border ${themeClasses.border}`}
                      whileHover={{ scale: 1.1 }}
                    >
                      <feature.icon className={`w-6 h-6 ${themeClasses.text}`} />
                    </motion.div>
                    <h3 className={`text-xl font-semibold mb-4 ${themeClasses.text}`}>{feature.title}</h3>
                    <p className={`${themeClasses.textSecondary} leading-relaxed`}>{feature.description}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </section>

          {/* AI Deliverables Section */}
          <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
            {/* Particles Background */}
            <div ref={particlesRef} className="absolute inset-0 z-0 opacity-30" />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
                className="text-center mb-20"
              >
                <h2 className={`text-4xl md:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
                  Your deliverables,
                  <br />
                  powered by AI
                </h2>
              </motion.div>

              {/* AI Spreadsheets Feature */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-24">
                <motion.div
                  initial={{ opacity: 0, x: -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                >
                  <div className="flex items-center space-x-2 mb-6">
                    <FileSpreadsheet className="w-5 h-5" />
                    <span className="font-medium text-sm uppercase tracking-wider">AI Spreadsheets</span>
                  </div>

                  <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                    Insight-ready spreadsheets
                  </h3>

                  <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                    No broken formulas. No manual cleanup. DataScope AI helps you catch issues and surface insights in
                    real time.
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
                >
                  <motion.div
                    className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl border ${themeClasses.border}`}
                    whileHover={{ scale: 1.01 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="flex items-center space-x-2 mb-6">
                      <div className="flex space-x-1">
                        {["⟲", "↶", "↷", "$", "%", "⚡", "⌘", "✓", "⋮"].map((symbol, i) => (
                          <motion.div
                            key={i}
                            className={`w-8 h-8 ${themeClasses.surfaceSecondary} rounded flex items-center justify-center text-xs border ${themeClasses.border}`}
                            whileHover={{ scale: 1.1 }}
                            transition={{ type: "spring", stiffness: 400 }}
                          >
                            {symbol}
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    <div className={`text-sm ${themeClasses.textMuted} mb-6 font-mono`}>
                      ∑ FORECAST (1, B2:B5, A2:A5)
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className={`border-b ${themeClasses.border}`}>
                            <th className={`text-left p-3 ${themeClasses.surfaceSecondary} rounded-tl`}>A</th>
                            <th className={`text-left p-3 ${themeClasses.text}`}>B</th>
                            <th className={`text-left p-3 ${themeClasses.surfaceSecondary}`}>C</th>
                            <th className={`text-left p-3 ${themeClasses.text}`}>D</th>
                            <th className={`text-left p-3 ${themeClasses.text} rounded-tr`}>E</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            ["1", "Month", "Units Sold", "Revenue ($)", "COGS ($)"],
                            ["2", "Apr 2025", "5,083", "609,960", "355,810"],
                            ["3", "May 2025", "4,925", "591,000", "344,750"],
                            ["4", "Jun 2025", "4,741", "568,920", "331,870"],
                            ["5", "Jul 2025", "4,995", "599,400", "349,650"],
                          ].map((row, i) => (
                            <motion.tr
                              key={i}
                              initial={{ opacity: 0, x: -20 }}
                              whileInView={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.3, delay: i * 0.1 }}
                              viewport={{ once: true }}
                              className={`border-b ${themeClasses.border} hover:${themeClasses.surfaceSecondary} transition-colors`}
                            >
                              {row.map((cell, j) => (
                                <td
                                  key={j}
                                  className={`p-3 ${i === 0 && (j === 0 || j === 2) ? themeClasses.surfaceSecondary : themeClasses.text}`}
                                >
                                  {cell}
                                </td>
                              ))}
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                </motion.div>
              </div>

              {/* AI Presentations Feature */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-24">
                <motion.div
                  initial={{ opacity: 0, x: 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className={`order-2 lg:order-1 ${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
                >
                  <motion.div
                    className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl border ${themeClasses.border}`}
                    whileHover={{ scale: 1.01 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h4 className={`font-semibold text-lg ${themeClasses.text}`}>Sales Report</h4>
                        <span className={`text-sm ${themeClasses.textMuted}`}>2024 Sales Progression</span>
                      </div>

                      <div className={`border-b ${themeClasses.border} pb-4`}>
                        <div className="flex items-center space-x-2">
                          <span className={`text-sm ${themeClasses.textSecondary}`}>FINANCIALS</span>
                          <div className={`${themeClasses.button} px-2 py-1 rounded text-xs`}>DataScope AI</div>
                        </div>
                      </div>

                      <div className={`${themeClasses.surfaceSecondary} p-4 rounded-xl border ${themeClasses.border}`}>
                        <p className={`text-sm ${themeClasses.textSecondary}`}>
                          Every insight, a step toward exponential growth.
                          <span className={`${themeClasses.button} px-1 rounded text-xs ml-1`}>DataScope AI</span> turns
                          intelligence into ROI.
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className="order-1 lg:order-2"
                >
                  <div className="flex items-center space-x-2 mb-6">
                    <Presentation className="w-5 h-5" />
                    <span className="font-medium text-sm uppercase tracking-wider">AI Presentations</span>
                  </div>

                  <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                    Polished, client-ready presentations
                  </h3>

                  <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                    Slides made easy. Any data, any topic, any input. DataScope AI turns it into a polished story fast.
                  </p>
                </motion.div>
              </div>

              {/* AI Documents Feature */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                <motion.div
                  initial={{ opacity: 0, x: -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                >
                  <div className="flex items-center space-x-2 mb-6">
                    <FileText className="w-5 h-5" />
                    <span className="font-medium text-sm uppercase tracking-wider">AI Documents</span>
                  </div>

                  <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                    Documents, ready for hand off
                  </h3>

                  <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                    DataScope AI formats, edits, and checks your docs so that you don't have to.
                  </p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
                >
                  <motion.div
                    className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl transform rotate-2 hover:rotate-0 transition-all duration-500 border ${themeClasses.border}`}
                    whileHover={{ scale: 1.02, rotate: 0 }}
                  >
                    <h4 className={`font-bold text-lg mb-6 ${themeClasses.text}`}>
                      Top 5 Enterprise AI Startups to Watch in 2025
                    </h4>

                    <div className="space-y-4 text-sm">
                      {[
                        { label: "Comprehensive Analysis" },
                        { label: "Market Trends" },
                        { label: "Investment Insights" },
                      ].map((item, i) => (
                        <motion.div
                          key={item.label}
                          className="flex items-center space-x-3"
                          initial={{ opacity: 0, x: -20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: i * 0.1 }}
                          viewport={{ once: true }}
                        >
                          <div className={`w-2 h-2 ${isDark ? "bg-white" : "bg-black"} rounded`}></div>
                          <span className={themeClasses.textSecondary}>{item.label}</span>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>

                  <motion.div
                    className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl transform -rotate-1 hover:rotate-0 transition-all duration-500 mt-4 border ${themeClasses.border}`}
                    whileHover={{ scale: 1.02, rotate: 0 }}
                  >
                    <h4 className={`font-bold text-lg mb-3 ${themeClasses.text}`}>
                      Marketing Budget Proposal — Q2 2025
                    </h4>
                    <p className={`text-sm ${themeClasses.textSecondary}`}>
                      Strategic rationale for budget allocation across digital channels...
                    </p>
                  </motion.div>
                </motion.div>
              </div>
            </div>
          </section>

          {/* Integrations Section */}
          <section className={`py-24 ${themeClasses.surface} relative overflow-hidden`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                <motion.div
                  initial={{ opacity: 0, x: -40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                >
                  <h2 className={`text-4xl md:text-5xl font-bold ${themeClasses.text} mb-8 tracking-tight`}>
                    Integrations
                  </h2>

                  <p className={`text-lg ${themeClasses.textSecondary} mb-10 leading-relaxed`}>
                    300+ integrations so you can research, analyze, and create without switching between platforms.
                  </p>

                  <p className={`${themeClasses.text} mb-8 font-medium`}>DataScope AI integrates with:</p>

                  <div className="flex flex-wrap gap-3 mb-10">
                    {[
                      { name: "Gmail" },
                      { name: "Salesforce" },
                      { name: "Docs" },
                      { name: "Slack" },
                      { name: "Excel" },
                      { name: "PowerPoint" },
                    ].map((integration, index) => (
                      <motion.span
                        key={integration.name}
                        className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.border} ${themeClasses.textSecondary} hover:${themeClasses.text} cursor-pointer hover:scale-105 transition-all duration-300`}
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                        transition={{
                          duration: 0.6,
                          delay: index * 0.1,
                          type: "spring",
                          stiffness: 200,
                        }}
                        viewport={{ once: true }}
                        whileHover={{ y: -2 }}
                      >
                        {integration.name}
                      </motion.span>
                    ))}
                  </div>

                  <p className={`${themeClasses.textMuted} text-sm`}>+ many more</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 40 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8 }}
                  viewport={{ once: true }}
                  className="relative"
                >
                  <div className="grid grid-cols-3 gap-8 items-center">
                    {[
                      [{ delay: 0 }, { delay: 0.1 }],
                      [{ delay: 0.2 }, { delay: 0.3 }, { delay: 0.4 }],
                      [{ delay: 0.5 }, { delay: 0.6 }],
                    ].map((column, colIndex) => (
                      <div key={colIndex} className="space-y-8">
                        {column.map((item, itemIndex) => (
                          <motion.div
                            key={itemIndex}
                            className={`w-16 h-16 ${themeClasses.surfaceSecondary} rounded-2xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group border ${themeClasses.border}`}
                            initial={{ opacity: 0, scale: 0, rotate: -90 }}
                            whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                            transition={{
                              duration: 0.6,
                              delay: item.delay,
                              type: "spring",
                              stiffness: 200,
                            }}
                            viewport={{ once: true }}
                            whileHover={{ scale: 1.1, rotate: 3 }}
                          >
                            <div
                              className={`w-8 h-8 ${isDark ? "bg-white" : "bg-black"} rounded group-hover:rotate-12 transition-transform duration-300`}
                            />
                          </motion.div>
                        ))}
                      </div>
                    ))}
                  </div>
                </motion.div>
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
              >
                <h2 className={`text-4xl md:text-5xl font-bold ${themeClasses.text} mb-6 tracking-tight`}>
                  Endless use cases
                </h2>
                <p className={`text-lg ${themeClasses.textSecondary} mb-12 max-w-2xl mx-auto leading-relaxed`}>
                  DataScope AI has 1000+ use cases for any corporate role, helping you and your team take care of
                  serious work
                </p>

                <motion.button
                  className={`${themeClasses.button} px-12 py-4 rounded-xl font-semibold transition-all duration-300 text-lg`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Sign up
                </motion.button>
              </motion.div>
            </div>
          </section>

          {/* Footer */}
          <footer className={`${themeClasses.surface} py-20 border-t ${themeClasses.border} relative overflow-hidden`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
                <div className="col-span-1 md:col-span-2">
                  <motion.div
                    className="flex items-center space-x-3 mb-8"
                    whileHover={{ scale: 1.02 }}
                    transition={{ type: "spring", stiffness: 400 }}
                  >
                    <div className="flex items-center space-x-1">
                      <div className={`w-6 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
                      <div className={`w-2 h-6 ${isDark ? "bg-white" : "bg-black"} rounded`} />
                    </div>
                  </motion.div>
                  <p className={`${themeClasses.textSecondary} mb-8 max-w-md leading-relaxed text-lg`}>
                    Work smarter, faster, and more efficiently with DataScope AI.
                  </p>
                  <div className="flex items-center space-x-6">
                    <span className={`${themeClasses.textMuted} text-sm uppercase tracking-wider`}>Socials</span>
                    <div className="flex space-x-4">
                      {[0, 1].map((i) => (
                        <motion.div
                          key={i}
                          className={`w-10 h-10 ${themeClasses.surfaceSecondary} rounded-lg flex items-center justify-center cursor-pointer border ${themeClasses.border} hover:scale-110 transition-all duration-300`}
                          whileHover={{ y: -2 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <div className={`w-4 h-4 ${themeClasses.textMuted}`}></div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className={`text-lg font-semibold mb-6 ${themeClasses.text}`}>Company</h3>
                  <ul className="space-y-4">
                    {["Home", "Blog", "Careers", "Brand Kit", "Affiliate"].map((item, index) => (
                      <motion.li
                        key={item}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        viewport={{ once: true }}
                      >
                        <a
                          href="#"
                          className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                        >
                          {item}
                        </a>
                      </motion.li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className={`text-lg font-semibold mb-6 ${themeClasses.text}`}>Legal</h3>
                  <ul className="space-y-4">
                    {["Security", "Privacy", "Terms of use"].map((item, index) => (
                      <motion.li
                        key={item}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        viewport={{ once: true }}
                      >
                        <a
                          href="#"
                          className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                        >
                          {item}
                        </a>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </div>

              <motion.div
                className={`border-t ${themeClasses.border} mt-16 pt-8`}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
              >
                <p className={`${themeClasses.textMuted} text-sm`}>© 2025 DataScope AI. All rights reserved.</p>
              </motion.div>
            </div>
          </footer>
        </>
      )}
    </div>
  )
}

// Main App Component with Theme Provider
const MainApp = () => {
  return (
    <ThemeProvider>
      <App />
    </ThemeProvider>
  )
}

export default MainApp
