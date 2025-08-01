// hooks/useUserStore.js
import { BACKEND_URL } from '@/utils/constants'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API_BASE_URL = BACKEND_URL

export const useUserStore = create(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      authChecked: false,

      // Set user and mark as authenticated
      setUser: (userData) => {
        set({
          user: userData,
          isAuthenticated: true,
          authChecked: true
        })
      },

      // Clear user and mark as unauthenticated
      clearUser: async () => {
        try {
          // Call logout endpoint
          await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
          })
        } catch (error) {
          console.error('Logout request failed:', error)
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            authChecked: true
          })
        }
      },

      // Check authentication status with backend
      checkAuthStatus: async () => {
        const { authChecked } = get()
        if (authChecked) return // Don't check again if already checked

        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
          })

          if (response.ok) {
            const data = await response.json()
            if (data.logged_in && data.user) {
              set({
                user: {
                  id: data.user.user_insipredict_id,
                  name: data.user.first_name,
                  email: data.user.email || ''
                },
                isAuthenticated: true,
                authChecked: true,
                isLoading: false
              })
            } else {
              set({
                user: null,
                isAuthenticated: false,
                authChecked: true,
                isLoading: false
              })
            }
          } else {
            set({
              user: null,
              isAuthenticated: false,
              authChecked: true,
              isLoading: false
            })
          }
        } catch (error) {
          console.error('Auth check failed:', error)
          set({
            user: null,
            isAuthenticated: false,
            authChecked: true,
            isLoading: false
          })
        }
      },

      // Login user
      login: async (email, password) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            mode: 'cors',
            body: JSON.stringify({ email, password })
          })

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Network error' }))
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
          }

          const data = await response.json()

          set({
            user: {
              id: data.user_insipredict_id,
              name: data.first_name,
              email: email
            },
            isAuthenticated: true,
            authChecked: true,
            isLoading: false
          })

          return { success: true, data }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      // Register user
      register: async (firstName, lastName, email, password) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            mode: 'cors',
            body: JSON.stringify({
              firstName,
              lastName,
              email,
              password
            })
          })

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Network error' }))
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
          }

          const data = await response.json()

          set({
            user: {
              id: data.user_insipredict_id,
              name: data.first_name,
              email: email
            },
            isAuthenticated: true,
            authChecked: true,
            isLoading: false
          })

          return { success: true, data }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      }
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        authChecked: state.authChecked
      })
    }
  )
)