// "use client"

// import { useState, useEffect, useCallback } from "react"
// import { motion, AnimatePresence } from "framer-motion"
// import {
//   Moon,
//   Sun,
//   User,
//   Settings,
//   LogOut,
//   MessageSquare,
//   History,
//   FileText,
//   Plus,
//   Search,
//   Filter,
//   Clock,
//   ChevronRight,
//   MoreHorizontal,
//   Wifi,
//   WifiOff,
// } from "lucide-react"
// import { useTheme } from "../context/ThemeProvider"
// import { useAuth } from "../context/AuthProvider"
// import AuthModal from "./AuthModal.jsx"

// const Sidebar = ({
//   isConnected,
//   currentChatId,
//   onNewChat,
//   onChatSelect,
//   onDeleteChat,
//   chatHistory = [],
//   isCollapsed: initialCollapsed = true, // Changed to true (collapsed by default)
//   onToggleCollapse,
// }) => {
//   const { isDark, toggleTheme } = useTheme()
//   const { user, isAuthenticated, logout, isLoading } = useAuth()
//   const [isCollapsed, setIsCollapsed] = useState(initialCollapsed)
//   const [activeView, setActiveView] = useState("chat")
//   const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
//   const [searchQuery, setSearchQuery] = useState("")
//   const [filterBy, setFilterBy] = useState("all")
//   const [selectedChats, setSelectedChats] = useState(new Set())
//   const [hoveredChat, setHoveredChat] = useState(null)
//   const [isSearchFocused, setIsSearchFocused] = useState(false)

//   // Sync with parent component
//   useEffect(() => {
//     setIsCollapsed(initialCollapsed)
//   }, [initialCollapsed])

//   const handleToggleCollapse = () => {
//     const newCollapsed = !isCollapsed
//     setIsCollapsed(newCollapsed)
//     onToggleCollapse?.(newCollapsed)
//   }

//   // Animation variants with smooth easing
//   const sidebarVariants = {
//     expanded: {
//       width: 320,
//       transition: {
//         duration: 0.4,
//         ease: [0.4, 0, 0.2, 1],
//         staggerChildren: 0.05,
//       },
//     },
//     collapsed: {
//       width: 64,
//       transition: {
//         duration: 0.4,
//         ease: [0.4, 0, 0.2, 1],
//         staggerChildren: 0.02,
//         staggerDirection: -1,
//       },
//     },
//   }

//   const contentVariants = {
//     expanded: {
//       opacity: 1,
//       x: 0,
//       transition: { duration: 0.3, delay: 0.1 },
//     },
//     collapsed: {
//       opacity: 0,
//       x: -20,
//       transition: { duration: 0.2 },
//     },
//   }

//   // Filter chat history
//   const filteredChatHistory = chatHistory.filter((chat) => {
//     const matchesSearch =
//       !searchQuery ||
//       chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
//       (chat.lastMessage && chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()))

//     const now = new Date()
//     const chatDate = new Date(chat.createdAt)
//     let matchesFilter = true

//     switch (filterBy) {
//       case "today":
//         matchesFilter = chatDate.toDateString() === now.toDateString()
//         break
//       case "week":
//         const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
//         matchesFilter = chatDate >= weekAgo
//         break
//       case "month":
//         const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
//         matchesFilter = chatDate >= monthAgo
//         break
//       default:
//         matchesFilter = true
//     }

//     return matchesSearch && matchesFilter
//   })

//   const openAuthModal = useCallback((mode) => {
//     setAuthModal({ isOpen: true, mode })
//   }, [])

//   const closeAuthModal = useCallback(() => {
//     setAuthModal({ isOpen: false, mode: "login" })
//   }, [])

//   const handleLogout = useCallback(async () => {
//     await logout()
//   }, [logout])

//   const handleChatSelect = (chatId) => {
//     onChatSelect?.(chatId)
//     if (window.innerWidth < 1024) {
//       setIsCollapsed(true)
//     }
//   }

//   const handleDeleteSelected = () => {
//     selectedChats.forEach((chatId) => {
//       onDeleteChat?.(chatId)
//     })
//     setSelectedChats(new Set())
//   }

//   const toggleChatSelection = (chatId) => {
//     const newSelection = new Set(selectedChats)
//     if (newSelection.has(chatId)) {
//       newSelection.delete(chatId)
//     } else {
//       newSelection.add(chatId)
//     }
//     setSelectedChats(newSelection)
//   }

//   const formatDate = (dateString) => {
//     const date = new Date(dateString)
//     const now = new Date()
//     const diffTime = Math.abs(now - date)
//     const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

//     if (diffDays === 1) return "Today"
//     if (diffDays === 2) return "Yesterday"
//     if (diffDays <= 7) return `${diffDays - 1}d ago`
//     return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
//   }

//   // Show loading state
//   if (isLoading) {
//     return (
//       <motion.div
//         className={`fixed left-0 top-0 h-full z-[9999] backdrop-blur-xl border-r flex items-center justify-center ${
//           isDark ? "bg-black/95 border-white/10" : "bg-white/95 border-black/10"
//         }`}
//         animate={{ width: isCollapsed ? 64 : 320 }}
//         transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
//       >
//         <motion.div
//           animate={{ rotate: 360 }}
//           transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
//           className={`w-6 h-6 border-2 border-t-transparent rounded-full ${
//             isDark ? "border-white/30" : "border-black/30"
//           }`}
//         />
//       </motion.div>
//     )
//   }

//   return (
//     <>
//       {/* Sidebar */}
//       <motion.div
//         variants={sidebarVariants}
//         animate={isCollapsed ? "collapsed" : "expanded"}
//         className={`fixed left-0 top-0 h-full z-[9999] backdrop-blur-xl border-r flex flex-col ${
//           isDark ? "bg-black/95 border-white/10" : "bg-white/95 border-black/10"
//         }`}
//         style={{
//           boxShadow: isDark ? "4px 0 24px rgba(255, 255, 255, 0.05)" : "4px 0 24px rgba(0, 0, 0, 0.05)",
//         }}
//       >
//         {/* Header */}
//         <div
//           className={`flex items-center justify-between p-4 border-b ${isDark ? "border-white/10" : "border-black/10"}`}
//         >
//           <AnimatePresence mode="wait">
//             {!isCollapsed && (
//               <motion.div
//                 variants={contentVariants}
//                 initial="collapsed"
//                 animate="expanded"
//                 exit="collapsed"
//                 className="flex items-center space-x-3"
//               >
//                 <div className="relative">
//                   <div
//                     className={`h-8 w-8 rounded-xl ${
//                       isDark ? "bg-white text-black" : "bg-black text-white"
//                     } flex items-center justify-center font-bold text-sm shadow-lg`}
//                   >
//                     IP
//                   </div>
//                   <div
//                     className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 ${
//                       isConnected ? "bg-green-400 border-green-300" : "bg-red-400 border-red-300"
//                     } ${isDark ? "border-black" : "border-white"}`}
//                   ></div>
//                 </div>
//                 <div>
//                   <h1 className={`text-lg font-bold ${isDark ? "text-white" : "text-black"}`}>InsiPredict</h1>
//                   <p className={`text-xs ${isDark ? "text-white/60" : "text-black/60"}`}>AI Analytics</p>
//                 </div>
//               </motion.div>
//             )}
//           </AnimatePresence>

//           <motion.button
//             onClick={handleToggleCollapse}
//             className={`relative p-2.5 rounded-xl transition-all duration-200 group ${
//               isDark
//                 ? "hover:bg-white/10 text-white/70 hover:text-white"
//                 : "hover:bg-black/10 text-black/70 hover:text-black"
//             }`}
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.95 }}
//           >
//             <motion.div
//               animate={{ rotate: isCollapsed ? 0 : 180 }}
//               transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
//             >
//               <ChevronRight className="h-5 w-5" />
//             </motion.div>
//           </motion.button>
//         </div>

//         {/* Navigation Tabs */}
//         <AnimatePresence>
//           {!isCollapsed && (
//             <motion.div
//               variants={contentVariants}
//               initial="collapsed"
//               animate="expanded"
//               exit="collapsed"
//               className={`flex border-b ${isDark ? "border-white/10" : "border-black/10"}`}
//             >
//               {[
//                 { key: "chat", icon: MessageSquare, label: "Chat" },
//                 { key: "history", icon: History, label: "History" },
//               ].map((tab) => (
//                 <button
//                   key={tab.key}
//                   onClick={() => setActiveView(tab.key)}
//                   className={`relative flex-1 flex items-center justify-center space-x-2 p-4 text-sm font-medium transition-all duration-300 ${
//                     activeView === tab.key
//                       ? isDark
//                         ? "text-white"
//                         : "text-black"
//                       : isDark
//                         ? "text-white/60 hover:text-white/80"
//                         : "text-black/60 hover:text-black/80"
//                   }`}
//                 >
//                   <tab.icon className="h-4 w-4" />
//                   <span>{tab.label}</span>
//                   {activeView === tab.key && (
//                     <motion.div
//                       layoutId="activeTab"
//                       className={`absolute bottom-0 left-0 right-0 h-0.5 ${isDark ? "bg-white" : "bg-black"}`}
//                       transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
//                     />
//                   )}
//                 </button>
//               ))}
//             </motion.div>
//           )}
//         </AnimatePresence>

//         {/* Content Area */}
//         <div className="flex-1 overflow-hidden">
//           {isCollapsed ? (
//             // Collapsed view
//             <motion.div className="p-3 space-y-2" variants={contentVariants} animate="expanded">
//               {[
//                 {
//                   icon: Plus,
//                   onClick: onNewChat,
//                   tooltip: "New Chat",
//                   primary: true,
//                 },
//                 {
//                   icon: MessageSquare,
//                   onClick: () => setActiveView("chat"),
//                   tooltip: "Chat",
//                   active: activeView === "chat",
//                 },
//                 {
//                   icon: History,
//                   onClick: () => setActiveView("history"),
//                   tooltip: "History",
//                   active: activeView === "history",
//                 },
//               ].map((item, index) => (
//                 <motion.button
//                   key={index}
//                   onClick={item.onClick}
//                   className={`relative w-full group p-3 rounded-2xl transition-all duration-300 ${
//                     item.primary
//                       ? isDark
//                         ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
//                         : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
//                       : item.active
//                         ? isDark
//                           ? "bg-white/10 text-white"
//                           : "bg-black/10 text-black"
//                         : isDark
//                           ? "hover:bg-white/5 text-white/70 hover:text-white"
//                           : "hover:bg-black/5 text-black/70 hover:text-black"
//                   }`}
//                   whileHover={{ scale: item.primary ? 1.05 : 1.02 }}
//                   whileTap={{ scale: 0.95 }}
//                   title={item.tooltip}
//                 >
//                   <item.icon className="h-5 w-5 mx-auto" />

//                   {/* Tooltip */}
//                   <div
//                     className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
//                       isDark
//                         ? "bg-white text-black border border-white/20"
//                         : "bg-black text-white border border-black/20"
//                     }`}
//                   >
//                     {item.tooltip}
//                     <div
//                       className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
//                         isDark ? "border-r-white" : "border-r-black"
//                       }`}
//                     ></div>
//                   </div>
//                 </motion.button>
//               ))}
//             </motion.div>
//           ) : (
//             // Expanded view
//             <AnimatePresence mode="wait">
//               {activeView === "chat" ? (
//                 <motion.div
//                   key="chat"
//                   variants={contentVariants}
//                   initial="collapsed"
//                   animate="expanded"
//                   exit="collapsed"
//                   className="h-full flex flex-col"
//                 >
//                   {/* New Chat Button */}
//                   <div className="p-4">
//                     <motion.button
//                       onClick={onNewChat}
//                       className={`w-full group relative p-4 rounded-2xl font-semibold transition-all duration-300 overflow-hidden ${
//                         isDark
//                           ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
//                           : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
//                       }`}
//                       whileHover={{ scale: 1.02, y: -1 }}
//                       whileTap={{ scale: 0.98 }}
//                     >
//                       <div className="relative flex items-center justify-center space-x-2">
//                         <Plus className="h-5 w-5" />
//                         <span>New Chat</span>
//                       </div>
//                     </motion.button>
//                   </div>
//                 </motion.div>
//               ) : (
//                 <motion.div
//                   key="history"
//                   variants={contentVariants}
//                   initial="collapsed"
//                   animate="expanded"
//                   exit="collapsed"
//                   className="h-full flex flex-col"
//                 >
//                   {/* Search and Filter */}
//                   <div className="p-4 space-y-4">
//                     {/* Search */}
//                     <motion.div
//                       className="relative"
//                       initial={{ opacity: 0, y: -10 }}
//                       animate={{ opacity: 1, y: 0 }}
//                       transition={{ delay: 0.1 }}
//                     >
//                       <div
//                         className={`absolute left-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${
//                           isSearchFocused
//                             ? isDark
//                               ? "text-white"
//                               : "text-black"
//                             : isDark
//                               ? "text-white/50"
//                               : "text-black/50"
//                         }`}
//                       >
//                         <Search className="h-4 w-4" />
//                       </div>
//                       <input
//                         type="text"
//                         placeholder="Search conversations..."
//                         value={searchQuery}
//                         onChange={(e) => setSearchQuery(e.target.value)}
//                         onFocus={() => setIsSearchFocused(true)}
//                         onBlur={() => setIsSearchFocused(false)}
//                         className={`w-full pl-10 pr-4 py-3 rounded-xl text-sm border-2 transition-all duration-200 ${
//                           isSearchFocused
//                             ? isDark
//                               ? "bg-white/5 border-white/30 text-white placeholder-white/50"
//                               : "bg-black/5 border-black/30 text-black placeholder-black/50"
//                             : isDark
//                               ? "bg-white/5 border-transparent text-white placeholder-white/40 hover:bg-white/10"
//                               : "bg-black/5 border-transparent text-black placeholder-black/40 hover:bg-black/10"
//                         }`}
//                       />
//                     </motion.div>

//                     {/* Filter */}
//                     <motion.div
//                       className="flex items-center space-x-2"
//                       initial={{ opacity: 0, y: -10 }}
//                       animate={{ opacity: 1, y: 0 }}
//                       transition={{ delay: 0.2 }}
//                     >
//                       <Filter className={`h-4 w-4 ${isDark ? "text-white/50" : "text-black/50"}`} />
//                       <select
//                         value={filterBy}
//                         onChange={(e) => setFilterBy(e.target.value)}
//                         className={`flex-1 text-sm rounded-lg px-3 py-2 border transition-all duration-200 appearance-none cursor-pointer ${
//                           isDark
//                             ? "bg-white/5 border-white/20 text-white hover:bg-white/10"
//                             : "bg-black/5 border-black/20 text-black hover:bg-black/10"
//                         }`}
//                       >
//                         <option value="all">All conversations</option>
//                         <option value="today">Today</option>
//                         <option value="week">This week</option>
//                         <option value="month">This month</option>
//                       </select>
//                     </motion.div>

//                     {/* Bulk Actions */}
//                     <AnimatePresence>
//                       {selectedChats.size > 0 && (
//                         <motion.div
//                           initial={{ opacity: 0, scale: 0.9, y: -10 }}
//                           animate={{ opacity: 1, scale: 1, y: 0 }}
//                           exit={{ opacity: 0, scale: 0.9, y: -10 }}
//                           className={`flex items-center justify-between p-3 rounded-xl border ${
//                             isDark ? "bg-white/5 border-white/20" : "bg-black/5 border-black/20"
//                           }`}
//                         >
//                           <span className={`text-sm font-medium ${isDark ? "text-white" : "text-black"}`}>
//                             {selectedChats.size} selected
//                           </span>
//                           <button
//                             onClick={handleDeleteSelected}
//                             className="text-red-500 hover:text-red-600 text-sm font-medium transition-colors duration-200"
//                           >
//                             Delete
//                           </button>
//                         </motion.div>
//                       )}
//                     </AnimatePresence>
//                   </div>

//                   {/* Chat History List - Now scrollable */}
//                   <div className="flex-1 overflow-y-auto px-4 pb-4">
//                     <motion.div className="space-y-2">
//                       <AnimatePresence>
//                         {filteredChatHistory.map((chat, index) => (
//                           <motion.div
//                             key={chat.id}
//                             initial={{ opacity: 0, y: 20 }}
//                             animate={{ opacity: 1, y: 0 }}
//                             exit={{ opacity: 0, y: -20 }}
//                             transition={{ delay: index * 0.05 }}
//                             onMouseEnter={() => setHoveredChat(chat.id)}
//                             onMouseLeave={() => setHoveredChat(null)}
//                             className={`group relative p-4 rounded-2xl border cursor-pointer transition-all duration-300 ${
//                               currentChatId === chat.id
//                                 ? isDark
//                                   ? "bg-white/10 border-white/30 shadow-lg"
//                                   : "bg-black/10 border-black/30 shadow-lg"
//                                 : isDark
//                                   ? "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
//                                   : "bg-black/5 border-black/10 hover:bg-black/10 hover:border-black/20"
//                             }`}
//                           >
//                             <div className="flex items-start justify-between">
//                               <div className="flex-1 min-w-0" onClick={() => handleChatSelect(chat.id)}>
//                                 <div className="flex items-start space-x-3">
//                                   <div
//                                     className={`flex-shrink-0 w-3 h-3 rounded-full mt-2 ${
//                                       currentChatId === chat.id
//                                         ? isDark
//                                           ? "bg-white"
//                                           : "bg-black"
//                                         : isDark
//                                           ? "bg-white/30"
//                                           : "bg-black/30"
//                                     }`}
//                                   ></div>

//                                   <div className="flex-1 min-w-0">
//                                     <h4
//                                       className={`text-sm font-semibold truncate mb-1 ${
//                                         isDark ? "text-white" : "text-black"
//                                       }`}
//                                     >
//                                       {chat.title}
//                                     </h4>

//                                     {chat.lastMessage && (
//                                       <p
//                                         className={`text-xs truncate mb-2 ${
//                                           isDark ? "text-white/60" : "text-black/60"
//                                         }`}
//                                       >
//                                         {chat.lastMessage}
//                                       </p>
//                                     )}

//                                     <div className="flex items-center space-x-3">
//                                       <div className="flex items-center space-x-1">
//                                         <Clock className={`h-3 w-3 ${isDark ? "text-white/40" : "text-black/40"}`} />
//                                         <span className={`text-xs ${isDark ? "text-white/40" : "text-black/40"}`}>
//                                           {formatDate(chat.createdAt)}
//                                         </span>
//                                       </div>

//                                       {chat.attachedFiles && chat.attachedFiles.length > 0 && (
//                                         <div className="flex items-center space-x-1">
//                                           <FileText
//                                             className={`h-3 w-3 ${isDark ? "text-white/40" : "text-black/40"}`}
//                                           />
//                                           <span className={`text-xs ${isDark ? "text-white/40" : "text-black/40"}`}>
//                                             {chat.attachedFiles.length}
//                                           </span>
//                                         </div>
//                                       )}
//                                     </div>
//                                   </div>
//                                 </div>
//                               </div>

//                               {/* Actions */}
//                               <div className="flex items-center space-x-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
//                                 <motion.button
//                                   onClick={(e) => {
//                                     e.stopPropagation()
//                                     toggleChatSelection(chat.id)
//                                   }}
//                                   className={`p-1.5 rounded-lg transition-all duration-200 ${
//                                     selectedChats.has(chat.id)
//                                       ? isDark
//                                         ? "bg-white text-black"
//                                         : "bg-black text-white"
//                                       : isDark
//                                         ? "hover:bg-white/10 text-white/60 hover:text-white"
//                                         : "hover:bg-black/10 text-black/60 hover:text-black"
//                                   }`}
//                                   whileHover={{ scale: 1.1 }}
//                                   whileTap={{ scale: 0.9 }}
//                                 >
//                                   <div className="w-3 h-3 border border-current rounded-sm flex items-center justify-center">
//                                     {selectedChats.has(chat.id) && (
//                                       <motion.div
//                                         initial={{ scale: 0 }}
//                                         animate={{ scale: 1 }}
//                                         className="w-1.5 h-1.5 bg-current rounded-sm"
//                                       />
//                                     )}
//                                   </div>
//                                 </motion.button>

//                                 <motion.button
//                                   className={`p-1.5 rounded-lg transition-colors duration-200 ${
//                                     isDark
//                                       ? "hover:bg-white/10 text-white/60 hover:text-white"
//                                       : "hover:bg-black/10 text-black/60 hover:text-black"
//                                   }`}
//                                   whileHover={{ scale: 1.1 }}
//                                   whileTap={{ scale: 0.9 }}
//                                 >
//                                   <MoreHorizontal className="h-3 w-3" />
//                                 </motion.button>
//                               </div>
//                             </div>
//                           </motion.div>
//                         ))}
//                       </AnimatePresence>

//                       {filteredChatHistory.length === 0 && (
//                         <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
//                           <div
//                             className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
//                               isDark ? "bg-white/5" : "bg-black/5"
//                             }`}
//                           >
//                             <History className={`h-8 w-8 ${isDark ? "text-white/40" : "text-black/40"}`} />
//                           </div>
//                           <h3 className={`text-lg font-semibold mb-2 ${isDark ? "text-white/80" : "text-black/80"}`}>
//                             {searchQuery || filterBy !== "all" ? "No matches found" : "No conversations yet"}
//                           </h3>
//                           <p className={`text-sm ${isDark ? "text-white/50" : "text-black/50"}`}>
//                             {searchQuery || filterBy !== "all"
//                               ? "Try adjusting your search or filters"
//                               : "Start a new chat to begin your analysis"}
//                           </p>
//                         </motion.div>
//                       )}
//                     </motion.div>
//                   </div>
//                 </motion.div>
//               )}
//             </AnimatePresence>
//           )}
//         </div>

//         {/* Bottom Section - User Auth & Theme Controls */}
//         <div className={`border-t backdrop-blur-sm ${isDark ? "border-white/10" : "border-black/10"}`}>
//           <AnimatePresence>
//             {!isCollapsed && (
//               <motion.div
//                 variants={contentVariants}
//                 initial="collapsed"
//                 animate="expanded"
//                 exit="collapsed"
//                 className="p-4 space-y-4"
//               >
//                 {isAuthenticated ? (
//                   <motion.div
//                     className="space-y-3"
//                     initial={{ opacity: 0, y: 10 }}
//                     animate={{ opacity: 1, y: 0 }}
//                     transition={{ delay: 0.2 }}
//                   >
//                     {/* User Profile */}
//                     <div
//                       className={`relative p-4 rounded-2xl border overflow-hidden ${
//                         isDark ? "bg-white/5 border-white/10" : "bg-black/5 border-black/10"
//                       }`}
//                     >
//                       <div className="relative z-10 flex items-center space-x-3">
//                         <div className="relative">
//                           <div
//                             className={`flex h-10 w-10 items-center justify-center rounded-xl ${
//                               isDark ? "bg-white text-black" : "bg-black text-white"
//                             } shadow-lg`}
//                           >
//                             <User className="h-5 w-5" />
//                           </div>
//                           <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white dark:border-black flex items-center justify-center">
//                             <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
//                           </div>
//                         </div>
//                         <div className="flex-1 min-w-0">
//                           <h4 className={`text-sm font-semibold truncate ${isDark ? "text-white" : "text-black"}`}>
//                             {user?.name || "User"}
//                           </h4>
//                           {user?.email && (
//                             <p className={`text-xs truncate ${isDark ? "text-white/60" : "text-black/60"}`}>
//                               {user.email}
//                             </p>
//                           )}
//                           <div className="flex items-center space-x-2 mt-1">
//                             <div
//                               className={`text-xs px-2 py-0.5 rounded-full ${
//                                 isDark
//                                   ? "bg-green-500/20 text-green-300 border border-green-500/30"
//                                   : "bg-green-500/20 text-green-700 border border-green-500/30"
//                               }`}
//                             >
//                               Pro
//                             </div>
//                           </div>
//                         </div>
//                       </div>
//                     </div>

//                     {/* Control Buttons */}
//                     <div className="grid grid-cols-3 gap-2">
//                       <motion.button
//                         onClick={toggleTheme}
//                         className={`flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 ${
//                           isDark
//                             ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
//                             : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
//                         }`}
//                         whileHover={{ scale: 1.02, y: -1 }}
//                         whileTap={{ scale: 0.98 }}
//                       >
//                         <motion.div
//                           animate={{ rotate: isDark ? 0 : 180 }}
//                           transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
//                           className="mb-1"
//                         >
//                           {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
//                         </motion.div>
//                         <span>Theme</span>
//                       </motion.button>

//                       <motion.button
//                         className={`flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 ${
//                           isDark
//                             ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
//                             : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
//                         }`}
//                         whileHover={{ scale: 1.02, y: -1 }}
//                         whileTap={{ scale: 0.98 }}
//                       >
//                         <Settings className="h-4 w-4 mb-1" />
//                         <span>Settings</span>
//                       </motion.button>

//                       <motion.button
//                         onClick={handleLogout}
//                         className="flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 text-red-500 hover:text-red-600 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/30"
//                         whileHover={{ scale: 1.02, y: -1 }}
//                         whileTap={{ scale: 0.98 }}
//                       >
//                         <LogOut className="h-4 w-4 mb-1" />
//                         <span>Logout</span>
//                       </motion.button>
//                     </div>
//                   </motion.div>
//                 ) : (
//                   <motion.div
//                     className="space-y-3"
//                     initial={{ opacity: 0, y: 10 }}
//                     animate={{ opacity: 1, y: 0 }}
//                     transition={{ delay: 0.2 }}
//                   >
//                     {/* Sign In Button */}
//                     <motion.button
//                       onClick={() => openAuthModal("login")}
//                       className={`w-full relative p-4 rounded-2xl font-semibold transition-all duration-300 overflow-hidden group ${
//                         isDark
//                           ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
//                           : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
//                       }`}
//                       whileHover={{ scale: 1.02, y: -1 }}
//                       whileTap={{ scale: 0.98 }}
//                     >
//                       <div className="relative flex items-center justify-center space-x-2">
//                         <User className="h-5 w-5" />
//                         <span>Sign In</span>
//                       </div>
//                     </motion.button>

//                     {/* Theme Toggle */}
//                     <motion.button
//                       onClick={toggleTheme}
//                       className={`w-full flex items-center justify-center space-x-2 p-3 rounded-xl text-sm font-medium transition-all duration-300 ${
//                         isDark
//                           ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
//                           : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
//                       }`}
//                       whileHover={{ scale: 1.02, y: -1 }}
//                       whileTap={{ scale: 0.98 }}
//                     >
//                       <motion.div
//                         animate={{ rotate: isDark ? 0 : 180 }}
//                         transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
//                       >
//                         {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
//                       </motion.div>
//                       <span>Toggle Theme</span>
//                     </motion.button>
//                   </motion.div>
//                 )}
//               </motion.div>
//             )}
//           </AnimatePresence>

//           {/* Collapsed view controls */}
//           {isCollapsed && (
//             <motion.div className="p-3 space-y-3" variants={contentVariants} animate="expanded">
//               {/* Theme Toggle */}
//               <motion.button
//                 onClick={toggleTheme}
//                 className={`w-full p-3 rounded-2xl transition-all duration-300 group relative ${
//                   isDark
//                     ? "hover:bg-white/10 text-white/70 hover:text-white"
//                     : "hover:bg-black/10 text-black/70 hover:text-black"
//                 }`}
//                 whileHover={{ scale: 1.05 }}
//                 whileTap={{ scale: 0.95 }}
//                 title="Toggle Theme"
//               >
//                 <motion.div
//                   animate={{ rotate: isDark ? 0 : 180 }}
//                   transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
//                 >
//                   {isDark ? <Sun className="h-5 w-5 mx-auto" /> : <Moon className="h-5 w-5 mx-auto" />}
//                 </motion.div>

//                 {/* Tooltip */}
//                 <div
//                   className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
//                     isDark ? "bg-white text-black border border-white/20" : "bg-black text-white border border-black/20"
//                   }`}
//                 >
//                   Toggle Theme
//                   <div
//                     className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
//                       isDark ? "border-r-white" : "border-r-black"
//                     }`}
//                   ></div>
//                 </div>
//               </motion.button>

//               {/* User Avatar/Sign In */}
//               {isAuthenticated ? (
//                 <motion.div className="relative group" whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
//                   <div
//                     className={`flex h-10 w-10 items-center justify-center rounded-2xl shadow-lg mx-auto ${
//                       isDark ? "bg-white text-black" : "bg-black text-white"
//                     }`}
//                   >
//                     <User className="h-5 w-5" />
//                   </div>
//                   <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white dark:border-black"></div>

//                   {/* Tooltip */}
//                   <div
//                     className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
//                       isDark
//                         ? "bg-white text-black border border-white/20"
//                         : "bg-black text-white border border-black/20"
//                     }`}
//                   >
//                     {user?.name || "User"}
//                     <div
//                       className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
//                         isDark ? "border-r-white" : "border-r-black"
//                       }`}
//                     ></div>
//                   </div>
//                 </motion.div>
//               ) : (
//                 <motion.button
//                   onClick={() => openAuthModal("login")}
//                   className={`w-full p-3 rounded-2xl transition-all duration-300 group shadow-lg hover:shadow-xl ${
//                     isDark ? "bg-white text-black hover:bg-white/90" : "bg-black text-white hover:bg-black/90"
//                   }`}
//                   whileHover={{ scale: 1.05 }}
//                   whileTap={{ scale: 0.95 }}
//                   title="Sign In"
//                 >
//                   <User className="h-5 w-5 mx-auto" />

//                   {/* Tooltip */}
//                   <div
//                     className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
//                       isDark
//                         ? "bg-white text-black border border-white/20"
//                         : "bg-black text-white border border-black/20"
//                     }`}
//                   >
//                     Sign In
//                     <div
//                       className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
//                         isDark ? "border-r-white" : "border-r-black"
//                       }`}
//                     ></div>
//                   </div>
//                 </motion.button>
//               )}
//             </motion.div>
//           )}
//         </div>
//       </motion.div>

//       {/* Mobile Overlay */}
//       <AnimatePresence>
//         {!isCollapsed && typeof window !== "undefined" && window.innerWidth < 1024 && (
//           <motion.div
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             exit={{ opacity: 0 }}
//             className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[9998] lg:hidden"
//             onClick={() => setIsCollapsed(true)}
//           />
//         )}
//       </AnimatePresence>

//       {/* Auth Modal */}
//       <AuthModal
//         isOpen={authModal.isOpen}
//         mode={authModal.mode}
//         onClose={closeAuthModal}
//         onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
//       />
//     </>
//   )
// }

// export default Sidebar


"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Moon,
  Sun,
  User,
  Settings,
  LogOut,
  MessageSquare,
  History,
  FileText,
  Plus,
  Search,
  Filter,
  Clock,
  ChevronRight,
  MoreHorizontal,
  Wifi,
  WifiOff,
} from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import { useAuth } from "../context/AuthProvider"
import AuthModal from "./AuthModal.jsx"
import logo from '../../public/logo.svg'

const Sidebar = ({
  isConnected,
  currentChatId,
  onNewChat,
  onChatSelect,
  onDeleteChat,
  chatHistory = [],
  isCollapsed: initialCollapsed = true, // Changed to true (collapsed by default)
  onToggleCollapse,
}) => {
  const { isDark, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout, isLoading } = useAuth()
  const [isCollapsed, setIsCollapsed] = useState(initialCollapsed)
  const [activeView, setActiveView] = useState("chat")
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: "login" })
  const [searchQuery, setSearchQuery] = useState("")
  const [filterBy, setFilterBy] = useState("all")
  const [selectedChats, setSelectedChats] = useState(new Set())
  const [hoveredChat, setHoveredChat] = useState(null)
  const [isSearchFocused, setIsSearchFocused] = useState(false)

  // Sync with parent component
  useEffect(() => {
    setIsCollapsed(initialCollapsed)
  }, [initialCollapsed])

  const handleToggleCollapse = () => {
    const newCollapsed = !isCollapsed
    setIsCollapsed(newCollapsed)
    onToggleCollapse?.(newCollapsed)
  }

  // Animation variants with smooth easing
  const sidebarVariants = {
    expanded: {
      width: 320,
      transition: {
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1],
        staggerChildren: 0.05,
      },
    },
    collapsed: {
      width: 64,
      transition: {
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1],
        staggerChildren: 0.02,
        staggerDirection: -1,
      },
    },
  }

  const contentVariants = {
    expanded: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.3, delay: 0.1 },
    },
    collapsed: {
      opacity: 0,
      x: -20,
      transition: { duration: 0.2 },
    },
  }

  // Filter chat history
  const filteredChatHistory = chatHistory.filter((chat) => {
    const matchesSearch =
      !searchQuery ||
      chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (chat.lastMessage && chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()))

    const now = new Date()
    const chatDate = new Date(chat.createdAt)
    let matchesFilter = true

    switch (filterBy) {
      case "today":
        matchesFilter = chatDate.toDateString() === now.toDateString()
        break
      case "week":
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        matchesFilter = chatDate >= weekAgo
        break
      case "month":
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        matchesFilter = chatDate >= monthAgo
        break
      default:
        matchesFilter = true
    }

    return matchesSearch && matchesFilter
  })

  const openAuthModal = useCallback((mode) => {
    setAuthModal({ isOpen: true, mode })
  }, [])

  const closeAuthModal = useCallback(() => {
    setAuthModal({ isOpen: false, mode: "login" })
  }, [])

  const handleLogout = useCallback(async () => {
    await logout()
  }, [logout])

  const handleChatSelect = (chatId) => {
    onChatSelect?.(chatId)
    if (window.innerWidth < 1024) {
      setIsCollapsed(true)
    }
  }

  const handleDeleteSelected = () => {
    selectedChats.forEach((chatId) => {
      onDeleteChat?.(chatId)
    })
    setSelectedChats(new Set())
  }

  const toggleChatSelection = (chatId) => {
    const newSelection = new Set(selectedChats)
    if (newSelection.has(chatId)) {
      newSelection.delete(chatId)
    } else {
      newSelection.add(chatId)
    }
    setSelectedChats(newSelection)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 1) return "Today"
    if (diffDays === 2) return "Yesterday"
    if (diffDays <= 7) return `${diffDays - 1}d ago`
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  }

  // Show loading state
  if (isLoading) {
    return (
      <motion.div
        className={`fixed left-0 top-0 h-full z-[9999] backdrop-blur-xl border-r flex items-center justify-center ${
          isDark ? "bg-black/95 border-white/10" : "bg-white/95 border-black/10"
        }`}
        animate={{ width: isCollapsed ? 64 : 320 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
          className={`w-6 h-6 border-2 border-t-transparent rounded-full ${
            isDark ? "border-white/30" : "border-black/30"
          }`}
        />
      </motion.div>
    )
  }

  return (
    <>
      {/* Sidebar */}
      <motion.div
        variants={sidebarVariants}
        animate={isCollapsed ? "collapsed" : "expanded"}
        className={`fixed left-0 top-0 h-full z-[9999] backdrop-blur-xl border-r flex flex-col ${
          isDark ? "bg-black/95 border-white/10" : "bg-white/95 border-black/10"
        }`}
        style={{
          boxShadow: isDark ? "4px 0 24px rgba(255, 255, 255, 0.05)" : "4px 0 24px rgba(0, 0, 0, 0.05)",
        }}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between p-4 border-b ${isDark ? "border-white/10" : "border-black/10"}`}
        >
          <AnimatePresence mode="wait">
            {!isCollapsed && (
              <motion.div
                variants={contentVariants}
                initial="collapsed"
                animate="expanded"
                exit="collapsed"
                className="flex items-center space-x-3"
              >
                <div className="relative">
                  <div className="w-8 h-8 rounded-xl overflow-hidden shadow-lg">
                    <img 
                      src={logo} 
                      alt="InsiPredict Logo" 
                      className="w-full h-full object-contain"
                    />
                  </div>
                  <div
                    className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 ${
                      isConnected ? "bg-green-400 border-green-300" : "bg-red-400 border-red-300"
                    } ${isDark ? "border-black" : "border-white"}`}
                  ></div>
                </div>
                <div>
                  <h1 className={`text-lg font-bold ${isDark ? "text-white" : "text-black"}`}>InsiPredict</h1>
                  <p className={`text-xs ${isDark ? "text-white/60" : "text-black/60"}`}>AI Analytics</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Toggle Button - Show logo when collapsed, arrow when expanded */}
          <AnimatePresence mode="wait">
            {isCollapsed ? (
              <motion.button
                key="logo-button"
                onClick={handleToggleCollapse}
                className={`relative p-2.5 rounded-xl transition-all duration-200 group ${
                  isDark
                    ? "hover:bg-white/10 text-white/70 hover:text-white"
                    : "hover:bg-black/10 text-black/70 hover:text-black"
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.2 }}
              >
                {/* Logo that disappears completely on hover */}
                <div className="relative w-5 h-5">
                  <motion.div
                    className="absolute inset-0 flex items-center justify-center"
                    initial={{ opacity: 1, scale: 1 }}
                    whileHover={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.2 }}
                  >
                    <img 
                      src={logo} 
                      alt="InsiPredict Logo" 
                      className="w-5 h-5 object-contain"
                    />
                  </motion.div>
                  {/* Arrow that appears clearly on hover */}
                  <motion.div
                    className="absolute inset-0 flex items-center justify-center"
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileHover={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronRight className="h-5 w-5" />
                  </motion.div>
                </div>
              </motion.button>
            ) : (
              <motion.button
                key="arrow-button"
                onClick={handleToggleCollapse}
                className={`relative p-2.5 rounded-xl transition-all duration-200 group ${
                  isDark
                    ? "hover:bg-white/10 text-white/70 hover:text-white"
                    : "hover:bg-black/10 text-black/70 hover:text-black"
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.2 }}
              >
                <motion.div
                  animate={{ rotate: 180 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                >
                  <ChevronRight className="h-5 w-5" />
                </motion.div>
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation Tabs */}
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div
              variants={contentVariants}
              initial="collapsed"
              animate="expanded"
              exit="collapsed"
              className={`flex border-b ${isDark ? "border-white/10" : "border-black/10"}`}
            >
              {[
                { key: "chat", icon: MessageSquare, label: "Chat" },
                { key: "history", icon: History, label: "History" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveView(tab.key)}
                  className={`relative flex-1 flex items-center justify-center space-x-2 p-4 text-sm font-medium transition-all duration-300 ${
                    activeView === tab.key
                      ? isDark
                        ? "text-white"
                        : "text-black"
                      : isDark
                        ? "text-white/60 hover:text-white/80"
                        : "text-black/60 hover:text-black/80"
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                  {activeView === tab.key && (
                    <motion.div
                      layoutId="activeTab"
                      className={`absolute bottom-0 left-0 right-0 h-0.5 ${isDark ? "bg-white" : "bg-black"}`}
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {isCollapsed ? (
            // Collapsed view
            <motion.div className="p-3 space-y-2" variants={contentVariants} animate="expanded">
              {[
                {
                  icon: Plus,
                  onClick: () => {
                    onNewChat()
                    // Don't expand sidebar for primary action
                  },
                  tooltip: "New Chat",
                  primary: true,
                },
                {
                  icon: MessageSquare,
                  onClick: () => {
                    setActiveView("chat")
                    handleToggleCollapse() // Expand sidebar when switching views
                  },
                  tooltip: "Chat",
                  active: activeView === "chat",
                },
                {
                  icon: History,
                  onClick: () => {
                    setActiveView("history")
                    handleToggleCollapse() // Expand sidebar when switching views
                  },
                  tooltip: "History",
                  active: activeView === "history",
                },
              ].map((item, index) => (
                <motion.button
                  key={index}
                  onClick={item.onClick}
                  className={`relative w-full group p-3 rounded-2xl transition-all duration-300 ${
                    item.primary
                      ? isDark
                        ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
                        : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
                      : item.active
                        ? isDark
                          ? "bg-white/10 text-white"
                          : "bg-black/10 text-black"
                        : isDark
                          ? "hover:bg-white/5 text-white/70 hover:text-white"
                          : "hover:bg-black/5 text-black/70 hover:text-black"
                  }`}
                  whileHover={{ scale: item.primary ? 1.05 : 1.02 }}
                  whileTap={{ scale: 0.95 }}
                  title={item.tooltip}
                >
                  <item.icon className="h-5 w-5 mx-auto" />

                  {/* Enhanced Tooltip */}
                  <div
                    className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
                      isDark
                        ? "bg-white text-black border border-white/20 shadow-lg"
                        : "bg-black text-white border border-black/20 shadow-lg"
                    }`}
                  >
                    {item.tooltip}
                    {!item.primary && (
                      <span className="block text-xs opacity-70 mt-1">Click to expand</span>
                    )}
                    <div
                      className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
                        isDark ? "border-r-white" : "border-r-black"
                      }`}
                    ></div>
                  </div>
                </motion.button>
              ))}
            </motion.div>
          ) : (
            // Expanded view
            <AnimatePresence mode="wait">
              {activeView === "chat" ? (
                <motion.div
                  key="chat"
                  variants={contentVariants}
                  initial="collapsed"
                  animate="expanded"
                  exit="collapsed"
                  className="h-full flex flex-col"
                >
                  {/* New Chat Button */}
                  <div className="p-4">
                    <motion.button
                      onClick={onNewChat}
                      className={`w-full group relative p-4 rounded-2xl font-semibold transition-all duration-300 overflow-hidden ${
                        isDark
                          ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
                          : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
                      }`}
                      whileHover={{ scale: 1.02, y: -1 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="relative flex items-center justify-center space-x-2">
                        <Plus className="h-5 w-5" />
                        <span>New Chat</span>
                      </div>
                    </motion.button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="history"
                  variants={contentVariants}
                  initial="collapsed"
                  animate="expanded"
                  exit="collapsed"
                  className="h-full flex flex-col"
                >
                  {/* Search and Filter */}
                  <div className="p-4 space-y-4">
                    {/* Search */}
                    <motion.div
                      className="relative"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      <div
                        className={`absolute left-3 top-1/2 transform -translate-y-1/2 transition-colors duration-200 ${
                          isSearchFocused
                            ? isDark
                              ? "text-white"
                              : "text-black"
                            : isDark
                              ? "text-white/50"
                              : "text-black/50"
                        }`}
                      >
                        <Search className="h-4 w-4" />
                      </div>
                      <input
                        type="text"
                        placeholder="Search conversations..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => setIsSearchFocused(true)}
                        onBlur={() => setIsSearchFocused(false)}
                        className={`w-full pl-10 pr-4 py-3 rounded-xl text-sm border-2 transition-all duration-200 ${
                          isSearchFocused
                            ? isDark
                              ? "bg-white/5 border-white/30 text-white placeholder-white/50"
                              : "bg-black/5 border-black/30 text-black placeholder-black/50"
                            : isDark
                              ? "bg-white/5 border-transparent text-white placeholder-white/40 hover:bg-white/10"
                              : "bg-black/5 border-transparent text-black placeholder-black/40 hover:bg-black/10"
                        }`}
                      />
                    </motion.div>

                    {/* Filter */}
                    <motion.div
                      className="flex items-center space-x-2"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                    >
                      <Filter className={`h-4 w-4 ${isDark ? "text-white/50" : "text-black/50"}`} />
                      <select
                        value={filterBy}
                        onChange={(e) => setFilterBy(e.target.value)}
                        className={`flex-1 text-sm rounded-lg px-3 py-2 border transition-all duration-200 appearance-none cursor-pointer ${
                          isDark
                            ? "bg-white/5 border-white/20 text-white hover:bg-white/10"
                            : "bg-black/5 border-black/20 text-black hover:bg-black/10"
                        }`}
                      >
                        <option value="all">All conversations</option>
                        <option value="today">Today</option>
                        <option value="week">This week</option>
                        <option value="month">This month</option>
                      </select>
                    </motion.div>

                    {/* Bulk Actions */}
                    <AnimatePresence>
                      {selectedChats.size > 0 && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.9, y: -10 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.9, y: -10 }}
                          className={`flex items-center justify-between p-3 rounded-xl border ${
                            isDark ? "bg-white/5 border-white/20" : "bg-black/5 border-black/20"
                          }`}
                        >
                          <span className={`text-sm font-medium ${isDark ? "text-white" : "text-black"}`}>
                            {selectedChats.size} selected
                          </span>
                          <button
                            onClick={handleDeleteSelected}
                            className="text-red-500 hover:text-red-600 text-sm font-medium transition-colors duration-200"
                          >
                            Delete
                          </button>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Chat History List - Now scrollable */}
                  <div className="flex-1 overflow-y-auto px-4 pb-4">
                    <motion.div className="space-y-2">
                      <AnimatePresence>
                        {filteredChatHistory.map((chat, index) => (
                          <motion.div
                            key={chat.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ delay: index * 0.05 }}
                            onMouseEnter={() => setHoveredChat(chat.id)}
                            onMouseLeave={() => setHoveredChat(null)}
                            className={`group relative p-4 rounded-2xl border cursor-pointer transition-all duration-300 ${
                              currentChatId === chat.id
                                ? isDark
                                  ? "bg-white/10 border-white/30 shadow-lg"
                                  : "bg-black/10 border-black/30 shadow-lg"
                                : isDark
                                  ? "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
                                  : "bg-black/5 border-black/10 hover:bg-black/10 hover:border-black/20"
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0" onClick={() => handleChatSelect(chat.id)}>
                                <div className="flex items-start space-x-3">
                                  <div
                                    className={`flex-shrink-0 w-3 h-3 rounded-full mt-2 ${
                                      currentChatId === chat.id
                                        ? isDark
                                          ? "bg-white"
                                          : "bg-black"
                                        : isDark
                                          ? "bg-white/30"
                                          : "bg-black/30"
                                    }`}
                                  ></div>

                                  <div className="flex-1 min-w-0">
                                    <h4
                                      className={`text-sm font-semibold truncate mb-1 ${
                                        isDark ? "text-white" : "text-black"
                                      }`}
                                    >
                                      {chat.title}
                                    </h4>

                                    {chat.lastMessage && (
                                      <p
                                        className={`text-xs truncate mb-2 ${
                                          isDark ? "text-white/60" : "text-black/60"
                                        }`}
                                      >
                                        {chat.lastMessage}
                                      </p>
                                    )}

                                    <div className="flex items-center space-x-3">
                                      <div className="flex items-center space-x-1">
                                        <Clock className={`h-3 w-3 ${isDark ? "text-white/40" : "text-black/40"}`} />
                                        <span className={`text-xs ${isDark ? "text-white/40" : "text-black/40"}`}>
                                          {formatDate(chat.createdAt)}
                                        </span>
                                      </div>

                                      {chat.attachedFiles && chat.attachedFiles.length > 0 && (
                                        <div className="flex items-center space-x-1">
                                          <FileText
                                            className={`h-3 w-3 ${isDark ? "text-white/40" : "text-black/40"}`}
                                          />
                                          <span className={`text-xs ${isDark ? "text-white/40" : "text-black/40"}`}>
                                            {chat.attachedFiles.length}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Actions */}
                              <div className="flex items-center space-x-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                <motion.button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleChatSelection(chat.id)
                                  }}
                                  className={`p-1.5 rounded-lg transition-all duration-200 ${
                                    selectedChats.has(chat.id)
                                      ? isDark
                                        ? "bg-white text-black"
                                        : "bg-black text-white"
                                      : isDark
                                        ? "hover:bg-white/10 text-white/60 hover:text-white"
                                        : "hover:bg-black/10 text-black/60 hover:text-black"
                                  }`}
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                >
                                  <div className="w-3 h-3 border border-current rounded-sm flex items-center justify-center">
                                    {selectedChats.has(chat.id) && (
                                      <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="w-1.5 h-1.5 bg-current rounded-sm"
                                      />
                                    )}
                                  </div>
                                </motion.button>

                                <motion.button
                                  className={`p-1.5 rounded-lg transition-colors duration-200 ${
                                    isDark
                                      ? "hover:bg-white/10 text-white/60 hover:text-white"
                                      : "hover:bg-black/10 text-black/60 hover:text-black"
                                  }`}
                                  whileHover={{ scale: 1.1 }}
                                  whileTap={{ scale: 0.9 }}
                                >
                                  <MoreHorizontal className="h-3 w-3" />
                                </motion.button>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>

                      {filteredChatHistory.length === 0 && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
                          <div
                            className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center ${
                              isDark ? "bg-white/5" : "bg-black/5"
                            }`}
                          >
                            <History className={`h-8 w-8 ${isDark ? "text-white/40" : "text-black/40"}`} />
                          </div>
                          <h3 className={`text-lg font-semibold mb-2 ${isDark ? "text-white/80" : "text-black/80"}`}>
                            {searchQuery || filterBy !== "all" ? "No matches found" : "No conversations yet"}
                          </h3>
                          <p className={`text-sm ${isDark ? "text-white/50" : "text-black/50"}`}>
                            {searchQuery || filterBy !== "all"
                              ? "Try adjusting your search or filters"
                              : "Start a new chat to begin your analysis"}
                          </p>
                        </motion.div>
                      )}
                    </motion.div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>

        {/* Bottom Section - User Auth & Theme Controls */}
        <div className={`border-t backdrop-blur-sm ${isDark ? "border-white/10" : "border-black/10"}`}>
          <AnimatePresence>
            {!isCollapsed && (
              <motion.div
                variants={contentVariants}
                initial="collapsed"
                animate="expanded"
                exit="collapsed"
                className="p-4 space-y-4"
              >
                {isAuthenticated ? (
                  <motion.div
                    className="space-y-3"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    {/* User Profile */}
                    <div
                      className={`relative p-4 rounded-2xl border overflow-hidden ${
                        isDark ? "bg-white/5 border-white/10" : "bg-black/5 border-black/10"
                      }`}
                    >
                      <div className="relative z-10 flex items-center space-x-3">
                        <div className="relative">
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                              isDark ? "bg-white text-black" : "bg-black text-white"
                            } shadow-lg`}
                          >
                            <User className="h-5 w-5" />
                          </div>
                          <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white dark:border-black flex items-center justify-center">
                            <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className={`text-sm font-semibold truncate ${isDark ? "text-white" : "text-black"}`}>
                            {user?.name || "User"}
                          </h4>
                          {user?.email && (
                            <p className={`text-xs truncate ${isDark ? "text-white/60" : "text-black/60"}`}>
                              {user.email}
                            </p>
                          )}
                          <div className="flex items-center space-x-2 mt-1">
                            <div
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                isDark
                                  ? "bg-green-500/20 text-green-300 border border-green-500/30"
                                  : "bg-green-500/20 text-green-700 border border-green-500/30"
                              }`}
                            >
                              Pro
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Control Buttons */}
                    <div className="grid grid-cols-3 gap-2">
                      <motion.button
                        onClick={toggleTheme}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 ${
                          isDark
                            ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
                            : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
                        }`}
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <motion.div
                          animate={{ rotate: isDark ? 0 : 180 }}
                          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
                          className="mb-1"
                        >
                          {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                        </motion.div>
                        <span>Theme</span>
                      </motion.button>

                      <motion.button
                        className={`flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 ${
                          isDark
                            ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
                            : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
                        }`}
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Settings className="h-4 w-4 mb-1" />
                        <span>Settings</span>
                      </motion.button>

                      <motion.button
                        onClick={handleLogout}
                        className="flex flex-col items-center justify-center p-3 rounded-xl text-xs font-medium transition-all duration-300 text-red-500 hover:text-red-600 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/30"
                        whileHover={{ scale: 1.02, y: -1 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <LogOut className="h-4 w-4 mb-1" />
                        <span>Logout</span>
                      </motion.button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    className="space-y-3"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    {/* Sign In Button */}
                    <motion.button
                      onClick={() => openAuthModal("login")}
                      className={`w-full relative p-4 rounded-2xl font-semibold transition-all duration-300 overflow-hidden group ${
                        isDark
                          ? "bg-white text-black hover:bg-white/90 shadow-lg hover:shadow-xl"
                          : "bg-black text-white hover:bg-black/90 shadow-lg hover:shadow-xl"
                      }`}
                      whileHover={{ scale: 1.02, y: -1 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="relative flex items-center justify-center space-x-2">
                        <User className="h-5 w-5" />
                        <span>Sign In</span>
                      </div>
                    </motion.button>

                    {/* Theme Toggle */}
                    <motion.button
                      onClick={toggleTheme}
                      className={`w-full flex items-center justify-center space-x-2 p-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                        isDark
                          ? "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 hover:border-white/20"
                          : "bg-black/5 hover:bg-black/10 text-black/70 hover:text-black border border-black/10 hover:border-black/20"
                      }`}
                      whileHover={{ scale: 1.02, y: -1 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <motion.div
                        animate={{ rotate: isDark ? 0 : 180 }}
                        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
                      >
                        {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                      </motion.div>
                      <span>Toggle Theme</span>
                    </motion.button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Collapsed view controls */}
          {isCollapsed && (
            <motion.div className="p-3 space-y-3" variants={contentVariants} animate="expanded">
              {/* Theme Toggle */}
              <motion.button
                onClick={() => {
                  toggleTheme()
                  // Don't expand sidebar for theme toggle, just toggle theme
                }}
                className={`w-full p-3 rounded-2xl transition-all duration-300 group relative ${
                  isDark
                    ? "hover:bg-white/10 text-white/70 hover:text-white"
                    : "hover:bg-black/10 text-black/70 hover:text-black"
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="Toggle Theme"
              >
                <motion.div
                  animate={{ rotate: isDark ? 0 : 180 }}
                  transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
                >
                  {isDark ? <Sun className="h-5 w-5 mx-auto" /> : <Moon className="h-5 w-5 mx-auto" />}
                </motion.div>

                {/* Enhanced Tooltip */}
                <div
                  className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
                    isDark ? "bg-white text-black border border-white/20 shadow-lg" : "bg-black text-white border border-black/20 shadow-lg"
                  }`}
                >
                  Toggle Theme
                  <div
                    className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
                      isDark ? "border-r-white" : "border-r-black"
                    }`}
                  ></div>
                </div>
              </motion.button>

              {/* User Avatar/Sign In */}
              {isAuthenticated ? (
                <motion.button 
                  className="relative group w-full" 
                  whileHover={{ scale: 1.05 }} 
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    // Expand sidebar to show user controls
                    handleToggleCollapse()
                  }}
                >
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-2xl shadow-lg mx-auto ${
                      isDark ? "bg-white text-black" : "bg-black text-white"
                    }`}
                  >
                    <User className="h-5 w-5" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white dark:border-black"></div>

                  {/* Enhanced Tooltip */}
                  <div
                    className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
                      isDark
                        ? "bg-white text-black border border-white/20 shadow-lg"
                        : "bg-black text-white border border-black/20 shadow-lg"
                    }`}
                  >
                    {user?.name || "User"}
                    <span className="block text-xs opacity-70 mt-1">Click to expand</span>
                    <div
                      className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
                        isDark ? "border-r-white" : "border-r-black"
                      }`}
                    ></div>
                  </div>
                </motion.button>
              ) : (
                <motion.button
                  onClick={() => {
                    // Expand sidebar to show sign in options
                    handleToggleCollapse()
                  }}
                  className={`w-full p-3 rounded-2xl transition-all duration-300 group shadow-lg hover:shadow-xl ${
                    isDark ? "bg-white text-black hover:bg-white/90" : "bg-black text-white hover:bg-black/90"
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title="Sign In"
                >
                  <User className="h-5 w-5 mx-auto" />

                  {/* Enhanced Tooltip */}
                  <div
                    className={`absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 rounded-lg text-sm font-medium opacity-0 pointer-events-none group-hover:opacity-100 transition-all duration-200 whitespace-nowrap z-50 ${
                      isDark
                        ? "bg-white text-black border border-white/20 shadow-lg"
                        : "bg-black text-white border border-black/20 shadow-lg"
                    }`}
                  >
                    Sign In
                    <span className="block text-xs opacity-70 mt-1">Click to expand</span>
                    <div
                      className={`absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent ${
                        isDark ? "border-r-white" : "border-r-black"
                      }`}
                    ></div>
                  </div>
                </motion.button>
              )}
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {!isCollapsed && typeof window !== "undefined" && window.innerWidth < 1024 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[9998] lg:hidden"
            onClick={() => setIsCollapsed(true)}
          />
        )}
      </AnimatePresence>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModal.isOpen}
        mode={authModal.mode}
        onClose={closeAuthModal}
        onSwitchMode={(mode) => setAuthModal({ ...authModal, mode })}
      />
    </>
  )
}

export default Sidebar