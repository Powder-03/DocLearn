import { useAuth } from '@clerk/clerk-react'
import { useEffect, useState } from 'react'
import { setTokenGetter } from '@/lib/api'

/**
 * Hook to set up API authentication with Clerk token
 */
export function useApi() {
  const { getToken, isSignedIn, isLoaded } = useAuth()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      // Set the token getter function for axios interceptor
      setTokenGetter(getToken)
      setIsReady(true)
    } else if (isLoaded && !isSignedIn) {
      setIsReady(true)
    }
  }, [getToken, isSignedIn, isLoaded])

  return { getToken, isSignedIn, isReady }
}
