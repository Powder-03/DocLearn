import { useAuth } from '@clerk/clerk-react'
import { useEffect } from 'react'

/**
 * Hook to set up API authentication with Clerk token
 */
export function useApi() {
  const { getToken, isSignedIn } = useAuth()

  useEffect(() => {
    const setupToken = async () => {
      if (isSignedIn) {
        const token = await getToken()
        if (token) {
          ;(window as unknown as { __clerk_token?: string }).__clerk_token = token
        }
      }
    }

    setupToken()

    // Refresh token periodically
    const interval = setInterval(setupToken, 1000 * 60 * 4) // Every 4 minutes

    return () => clearInterval(interval)
  }, [getToken, isSignedIn])

  return { getToken, isSignedIn }
}
