// // hooks/useUserStore.js
// import { BACKEND_URL } from '@/utils/constants'
// import { create } from 'zustand'
// import { persist } from 'zustand/middleware'

// const API_BASE_URL = BACKEND_URL

// export const useUserStore = create(
//   persist(
//     (set, get) => ({
//       user: null,
//       isAuthenticated: false,
//       isLoading: false,
//       authChecked: false,

//       // Set user and mark as authenticated
//       setUser: (userData) => {
//         set({
//           user: userData,
//           isAuthenticated: true,
//           authChecked: true
//         })
//       },

//       // Clear user and mark as unauthenticated
//       clearUser: async () => {
//         try {
//           // Call logout endpoint
//           await fetch(`${API_BASE_URL}/auth/logout`, {
//             method: 'POST',
//             credentials: 'include',
//             headers: { 'Content-Type': 'application/json' }
//           })
//         } catch (error) {
//           console.error('Logout request failed:', error)
//         } finally {
//           set({
//             user: null,
//             isAuthenticated: false,
//             authChecked: true
//           })
//         }
//       },

//       // Check authentication status with backend
//       checkAuthStatus: async () => {
//         const { authChecked } = get()
//         if (authChecked) return // Don't check again if already checked

//         set({ isLoading: true })

//         try {
//           const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
//             method: 'GET',
//             credentials: 'include',
//             headers: { 'Content-Type': 'application/json' }
//           })

//           if (response.ok) {
//             const data = await response.json()
//             if (data.logged_in && data.user) {
//               set({
//                 user: {
//                   id: data.user.user_insipredict_id,
//                   name: data.user.first_name,
//                   email: data.user.email || ''
//                 },
//                 isAuthenticated: true,
//                 authChecked: true,
//                 isLoading: false
//               })
//             } else {
//               set({
//                 user: null,
//                 isAuthenticated: false,
//                 authChecked: true,
//                 isLoading: false
//               })
//             }
//           } else {
//             set({
//               user: null,
//               isAuthenticated: false,
//               authChecked: true,
//               isLoading: false
//             })
//           }
//         } catch (error) {
//           console.error('Auth check failed:', error)
//           set({
//             user: null,
//             isAuthenticated: false,
//             authChecked: true,
//             isLoading: false
//           })
//         }
//       },

//       // Login user
//       login: async (email, password) => {
//         set({ isLoading: true })

//         try {
//           const response = await fetch(`${API_BASE_URL}/auth/login`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             credentials: 'include',
//             mode: 'cors',
//             body: JSON.stringify({ email, password })
//           })

//           if (!response.ok) {
//             const errorData = await response.json().catch(() => ({ error: 'Network error' }))
//             throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
//           }

//           const data = await response.json()

//           set({
//             user: {
//               id: data.user_insipredict_id,
//               name: data.first_name,
//               email: email
//             },
//             isAuthenticated: true,
//             authChecked: true,
//             isLoading: false
//           })

//           return { success: true, data }
//         } catch (error) {
//           set({ isLoading: false })
//           throw error
//         }
//       },

//       // Register user
//       register: async (firstName, lastName, email, password) => {
//         set({ isLoading: true })

//         try {
//           const response = await fetch(`${API_BASE_URL}/auth/signup`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             credentials: 'include',
//             mode: 'cors',
//             body: JSON.stringify({
//               firstName,
//               lastName,
//               email,
//               password
//             })
//           })

//           if (!response.ok) {
//             const errorData = await response.json().catch(() => ({ error: 'Network error' }))
//             throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
//           }

//           const data = await response.json()

//           set({
//             user: {
//               id: data.user_insipredict_id,
//               name: data.first_name,
//               email: email
//             },
//             isAuthenticated: true,
//             authChecked: true,
//             isLoading: false
//           })

//           return { success: true, data }
//         } catch (error) {
//           set({ isLoading: false })
//           throw error
//         }
//       }
//     }),
//     {
//       name: 'user-storage',
//       partialize: (state) => ({
//         user: state.user,
//         isAuthenticated: state.isAuthenticated,
//         authChecked: state.authChecked
//       })
//     }
//   )
// )

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
            headers: {
              'Content-Type': 'application/json',
              'user_insipredict_id': get().user?.id || '',
            }
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
          const currentUser = get().user
          const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
            method: 'GET',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              'user_insipredict_id': currentUser?.id || '',
              'first_name_insipredict_user': currentUser?.name || '',
            }
          })

          if (response.ok) {
            const data = await response.json()
            if (data.logged_in) {
              if (data.user) {
                // User data from remember token or fresh login
                set({
                  user: {
                    id: data.user.id,
                    name: data.user.first_name,
                    email: data.user.email || ''
                  },
                  isAuthenticated: true,
                  authChecked: true,
                  isLoading: false
                })
              } else {
                // User authenticated via existing session
                set({
                  isAuthenticated: true,
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

      // Login user (enhanced with remember me and verification check)
      login: async (email, password, rememberMe = false) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            mode: 'cors',
            body: JSON.stringify({
              email,
              password,
              rememberMe
            })
          })

          const data = await response.json()

          if (!response.ok) {
            set({ isLoading: false })

            // Handle email verification requirement
            if (response.status === 403 && data.requires_verification) {
              return {
                requires_verification: true,
                email: data.email,
                error: data.error
              }
            }

            throw new Error(data.error || `HTTP error! status: ${response.status}`)
          }

          // Successful login
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

      // Register user (enhanced with verification requirement)
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

          const data = await response.json()

          if (!response.ok) {
            set({ isLoading: false })
            throw new Error(data.error || `HTTP error! status: ${response.status}`)
          }

          set({ isLoading: false })

          // Return registration result with verification requirement
          return {
            success: true,
            data,
            requires_verification: data.requires_verification || true,
            email: data.email || email,
            message: data.message
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      // Verify Email
      verifyEmail: async (email, code) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, code })
          })

          const data = await response.json()

          if (response.ok) {
            set({
              user: {
                id: data.user_insipredict_id,
                name: data.first_name,
                email: data.email
              },
              isAuthenticated: true,
              authChecked: true,
              isLoading: false
            })
            return { success: true, message: data.message }
          } else {
            set({ isLoading: false })
            throw new Error(data.error || 'Email verification failed')
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      // Resend Verification
      resendVerification: async (email) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
          })

          const data = await response.json()

          if (response.ok) {
            set({ isLoading: false })
            return { success: true, message: data.message }
          } else {
            set({ isLoading: false })
            throw new Error(data.error || 'Failed to resend verification')
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      // Forgot Password
      forgotPassword: async (email) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
          })

          const data = await response.json()

          if (response.ok) {
            set({ isLoading: false })
            return { success: true, message: data.message }
          } else {
            set({ isLoading: false })
            throw new Error(data.error || 'Failed to process forgot password request')
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      // Reset Password
      resetPassword: async (token, password) => {
        set({ isLoading: true })

        try {
          const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token, password })
          })

          const data = await response.json()

          if (response.ok) {
            set({ isLoading: false })
            return {
              success: true,
              message: data.message,
              email: data.email,  // Return email for auto-login
              first_name: data.first_name
            }
          } else {
            set({ isLoading: false })
            throw new Error(data.error || 'Failed to reset password')
          }
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