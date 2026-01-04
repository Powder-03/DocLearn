import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token getter function - will be set by useApi hook
let getTokenFunction: (() => Promise<string | null>) | null = null

export function setTokenGetter(getter: () => Promise<string | null>) {
  getTokenFunction = getter
}

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    // Get fresh token from Clerk
    if (getTokenFunction) {
      try {
        const token = await getTokenFunction()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
      } catch (error) {
        console.error('Failed to get auth token:', error)
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to sign in
      window.location.href = '/sign-in'
    }
    return Promise.reject(error)
  }
)

export default api
