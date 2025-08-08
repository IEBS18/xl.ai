import { useState, useEffect, useCallback } from 'react'
import { BACKEND_URL } from '../utils/constants'

const STORAGE_KEY = 'insipredictChatHistory'
const MAX_HISTORY_ITEMS = 50

export const useChatHistory = (isAuthenticated, currentSessionId) => {
  const [chatHistory, setChatHistory] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  // Load chat history from localStorage and optionally from API
  const loadChatHistory = useCallback(async () => {
    try {
      setIsLoading(true)
      
      // First load from localStorage for immediate display
      const savedHistory = localStorage.getItem(STORAGE_KEY)
      if (savedHistory) {
        const parsed = JSON.parse(savedHistory)
        setChatHistory(parsed)
      }
      
      // If authenticated, try to sync with server
      if (isAuthenticated) {
        try {
          const response = await fetch(`${BACKEND_URL}/api/chat-history`, {
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          })
          
          if (response.ok) {
            const data = await response.json()
            if (data.success && data.history) {
              setChatHistory(data.history)
              localStorage.setItem(STORAGE_KEY, JSON.stringify(data.history))
            }
          }
        } catch (apiError) {
          console.log('Could not sync with server, using local history:', apiError.message)
          // Continue with localStorage data
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
      setChatHistory([])
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated])

  // Save chat history to localStorage and optionally to API
  const saveChatHistory = useCallback(async (newHistory) => {
    try {
      // Save to localStorage immediately
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory))
      
      // If authenticated, try to sync with server
      if (isAuthenticated) {
        try {
          await fetch(`${BACKEND_URL}/api/chat-history`, {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ history: newHistory }),
          })
        } catch (apiError) {
          console.log('Could not sync with server:', apiError.message)
          // Continue with local save
        }
      }
    } catch (error) {
      console.error('Error saving chat history:', error)
    }
  }, [isAuthenticated])

  // Update or add a chat entry
  const updateChatHistory = useCallback((sessionId, userMessage, assistantMessage, fileInfo) => {
    if (!sessionId || !userMessage) return

    const chatEntry = {
      id: sessionId,
      title: userMessage.slice(0, 50) + (userMessage.length > 50 ? '...' : ''),
      lastMessage: assistantMessage ? assistantMessage.slice(0, 100) : 'Processing...',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      attachedFiles: fileInfo ? [fileInfo.filename || fileInfo.name] : [],
      messageCount: 1, // Could be enhanced to track actual message count
    }
    
    setChatHistory(prev => {
      // Remove existing entry for this session
      const filtered = prev.filter(chat => chat.id !== sessionId)
      
      // Add new entry at the beginning
      const newHistory = [chatEntry, ...filtered].slice(0, MAX_HISTORY_ITEMS)
      
      // Save to storage
      saveChatHistory(newHistory)
      
      return newHistory
    })
  }, [saveChatHistory])

  // Delete a chat entry
  const deleteChatHistory = useCallback((sessionId) => {
    setChatHistory(prev => {
      const filtered = prev.filter(chat => chat.id !== sessionId)
      saveChatHistory(filtered)
      return filtered
    })
  }, [saveChatHistory])

  // Delete multiple chat entries
  const deleteChatHistoryBulk = useCallback((sessionIds) => {
    setChatHistory(prev => {
      const filtered = prev.filter(chat => !sessionIds.includes(chat.id))
      saveChatHistory(filtered)
      return filtered
    })
  }, [saveChatHistory])

  // Clear all chat history
  const clearChatHistory = useCallback(() => {
    setChatHistory([])
    saveChatHistory([])
  }, [saveChatHistory])

  // Get a specific chat by ID
  const getChatById = useCallback((sessionId) => {
    return chatHistory.find(chat => chat.id === sessionId)
  }, [chatHistory])

  // Search chat history
  const searchChatHistory = useCallback((query, filterBy = 'all') => {
    if (!query && filterBy === 'all') return chatHistory

    return chatHistory.filter(chat => {
      // Search filter
      const matchesSearch = !query || 
        chat.title.toLowerCase().includes(query.toLowerCase()) ||
        (chat.lastMessage && chat.lastMessage.toLowerCase().includes(query.toLowerCase()))

      // Time filter
      let matchesFilter = true
      if (filterBy !== 'all') {
        const now = new Date()
        const chatDate = new Date(chat.updatedAt || chat.createdAt)
        
        switch (filterBy) {
          case 'today':
            matchesFilter = chatDate.toDateString() === now.toDateString()
            break
          case 'week':
            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
            matchesFilter = chatDate >= weekAgo
            break
          case 'month':
            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            matchesFilter = chatDate >= monthAgo
            break
          default:
            matchesFilter = true
        }
      }

      return matchesSearch && matchesFilter
    })
  }, [chatHistory])

  // Load history on mount and when authentication changes
  useEffect(() => {
    loadChatHistory()
  }, [loadChatHistory])

  return {
    chatHistory,
    isLoading,
    updateChatHistory,
    deleteChatHistory,
    deleteChatHistoryBulk,
    clearChatHistory,
    getChatById,
    searchChatHistory,
    reloadChatHistory: loadChatHistory,
  }
}