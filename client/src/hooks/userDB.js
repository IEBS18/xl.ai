// hooks/userDB.js
import { openDB } from 'idb'

const DB_NAME = 'InsiPredictDB'
const DB_VERSION = 1
const STORE_NAME = 'userStore'

const getDB = () => {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'key' })
      }
    }
  })
}

export const saveUser = async (user) => {
  try {
    const db = await getDB()
    await db.put(STORE_NAME, { key: 'currentUser', ...user })
    console.log('User saved to IndexedDB:', user)
  } catch (error) {
    console.error('Error saving user to IndexedDB:', error)
    throw error
  }
}

export const getUser = async () => {
  try {
    const db = await getDB()
    const result = await db.get(STORE_NAME, 'currentUser')
    if (result) {
      // Remove the 'key' property and return just the user data
      const { key, ...userData } = result
      console.log('User retrieved from IndexedDB:', userData)
      return userData
    }
    return null
  } catch (error) {
    console.error('Error getting user from IndexedDB:', error)
    return null
  }
}

export const clearUser = async () => {
  try {
    const db = await getDB()
    await db.delete(STORE_NAME, 'currentUser')
    console.log('User cleared from IndexedDB')
  } catch (error) {
    console.error('Error clearing user from IndexedDB:', error)
    throw error
  }
}