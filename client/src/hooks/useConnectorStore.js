// hooks/useConnectorStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useConnectorStore = create(
  persist(
    (set, get) => ({
      connectors: {
        postgres: [],
        mongodb: [],
        mysql: [],
        elasticsearch: [],
        googleDrive: [],
        github: []
      },

      // Add a new connector
      addConnector: (type, connectionData) => {
        const currentConnectors = get().connectors
        const newConnector = {
          ...connectionData,
          id: `${type}-${Date.now()}`,
          type,
          createdAt: new Date().toISOString(),
          lastUsed: new Date().toISOString()
        }

        set({
          connectors: {
            ...currentConnectors,
            [type]: [...(currentConnectors[type] || []), newConnector]
          }
        })

        return newConnector
      },

      // Get connectors by type
      getConnectorsByType: (type) => {
        const connectors = get().connectors
        return connectors[type] || []
      },

      // Get all connectors
      getAllConnectors: () => {
        const connectors = get().connectors
        const allConnectors = []
        
        Object.keys(connectors).forEach(type => {
          connectors[type].forEach(connector => {
            allConnectors.push({ ...connector, type })
          })
        })
        
        return allConnectors
      },

      // Get a specific connector
      getConnector: (type, id) => {
        const connectors = get().connectors
        return connectors[type]?.find(c => c.id === id)
      },

      // Update a connector
      updateConnector: (type, id, updates) => {
        const currentConnectors = get().connectors
        
        set({
          connectors: {
            ...currentConnectors,
            [type]: currentConnectors[type].map(connector =>
              connector.id === id
                ? { ...connector, ...updates, lastUsed: new Date().toISOString() }
                : connector
            )
          }
        })
      },

      // Remove a connector
      removeConnector: (type, id) => {
        const currentConnectors = get().connectors
        
        set({
          connectors: {
            ...currentConnectors,
            [type]: currentConnectors[type].filter(c => c.id !== id)
          }
        })
      },

      // Check if a connection already exists
      connectionExists: (type, connectionName) => {
        const connectors = get().connectors
        return connectors[type]?.some(c => c.connectionName === connectionName) || false
      },

      // Update last used timestamp
      updateLastUsed: (type, id) => {
        get().updateConnector(type, id, { lastUsed: new Date().toISOString() })
      },

      // Clear all connectors of a type
      clearConnectorType: (type) => {
        const currentConnectors = get().connectors
        
        set({
          connectors: {
            ...currentConnectors,
            [type]: []
          }
        })
      },

      // Clear all connectors
      clearAllConnectors: () => {
        set({
          connectors: {
            postgres: [],
            mongodb: [],
            mysql: [],
            elasticsearch: [],
            googleDrive: [],
            github: []
          }
        })
      }
    }),
    {
      name: 'data-connectors',
      partialize: (state) => ({
        connectors: state.connectors
      }),
      // Optional: Add encryption for sensitive data
      storage: {
        getItem: (name) => {
          const str = localStorage.getItem(name)
          if (!str) return null
          
          try {
            const data = JSON.parse(str)
            // You could decrypt here if implementing encryption
            return data
          } catch {
            return null
          }
        },
        setItem: (name, value) => {
          // You could encrypt here if implementing encryption
          localStorage.setItem(name, JSON.stringify(value))
        },
        removeItem: (name) => {
          localStorage.removeItem(name)
        }
      }
    }
  )
)