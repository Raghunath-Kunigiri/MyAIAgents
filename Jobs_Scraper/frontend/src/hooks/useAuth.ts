import { useState, useEffect } from 'react';
import { redirectToLogin } from '../config';

interface UseAuthReturn {
  isAuthenticated: boolean | null; // null = checking, true = authenticated, false = not authenticated
  loading: boolean;
}

/**
 * Hook to check authentication status
 * Checks by making a lightweight API call to verify session
 */
export function useAuth(): UseAuthReturn {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: NodeJS.Timeout | null = null;
    let isChecking = false; // Prevent multiple simultaneous checks

    const checkAuth = async () => {
      // Prevent duplicate checks
      if (isChecking) {
        console.log('[useAuth] Already checking, skipping...');
        return;
      }
      isChecking = true;
      console.log('[useAuth] Starting auth check...');
      try {
        // Use a lightweight endpoint to check auth status
        // Simplified: just fetch with timeout
        const controller = new AbortController();
        let abortTimeoutId: NodeJS.Timeout | null = setTimeout(() => {
          console.warn('[useAuth] Request timeout after 3s - aborting');
          controller.abort();
        }, 3000); // 3 second timeout
        
        let response: Response;
        console.log('[useAuth] Fetching /api/stats...');
        
        try {
          response = await fetch('/api/stats', {
            method: 'GET',
            credentials: 'include',
            signal: controller.signal,
          });
          
          // Clear timeout on success
          if (abortTimeoutId) {
            clearTimeout(abortTimeoutId);
            abortTimeoutId = null;
          }
          
          console.log('[useAuth] Response received:', response.status, response.statusText);
        } catch (fetchError) {
          // Clear timeout
          if (abortTimeoutId) {
            clearTimeout(abortTimeoutId);
            abortTimeoutId = null;
          }
          
          const errorMessage = fetchError instanceof Error ? fetchError.message : String(fetchError);
          const errorName = fetchError instanceof Error ? fetchError.name : '';
          
          console.error('[useAuth] Fetch error:', errorName, errorMessage);
          
          // Check if it was an abort (timeout)
          if (errorName === 'AbortError' || errorMessage.includes('aborted')) {
            console.warn('[useAuth] Auth check timed out - redirecting to login');
            if (!cancelled) {
              setIsAuthenticated(false);
              setLoading(false);
              redirectToLogin();
            }
            return;
          }
          
          // Network error - assume not authenticated
          console.error('[useAuth] Network error - assuming not authenticated');
          if (!cancelled) {
            setIsAuthenticated(false);
            setLoading(false);
            redirectToLogin();
          }
          return;
        }

        if (cancelled) {
          console.log('[useAuth] Cancelled - returning');
          return;
        }

        // Check response status immediately
        const status = response.status;
        console.log('[useAuth] Response status:', status);
        
        if (status === 200) {
          // Authenticated - verify it's JSON response
          const contentType = response.headers.get('content-type') || '';
          console.log('[useAuth] Content-Type:', contentType);
          
          // Just check if it's JSON, don't parse it (let Dashboard hooks do that)
          if (contentType.includes('application/json')) {
            console.log('[useAuth] Authenticated successfully - setting authenticated to true');
            if (!cancelled) {
              setIsAuthenticated(true);
              setLoading(false);
              console.log('[useAuth] Auth state updated - isAuthenticated: true, loading: false');
            } else {
              console.log('[useAuth] Component cancelled, not updating state');
            }
          } else {
            // Non-JSON response - might be HTML redirect
            console.warn('[useAuth] Non-JSON response - redirecting');
            if (!cancelled) {
              setIsAuthenticated(false);
              setLoading(false);
              redirectToLogin();
            }
          }
        } else if (status === 401) {
          // Not authenticated - redirect immediately
          setIsAuthenticated(false);
          setLoading(false);
          redirectToLogin();
        } else if (status === 302 || status === 307 || status === 308) {
          // Redirect response - not authenticated
          setIsAuthenticated(false);
          setLoading(false);
          redirectToLogin();
        } else {
          // Other status codes - try to parse JSON error
          try {
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
              const data = await response.json();
              if (data.error === 'Authentication required' || data.redirect) {
                setIsAuthenticated(false);
                setLoading(false);
                redirectToLogin();
              } else {
                // Unexpected JSON response - log and treat as not authenticated
                console.warn('Unexpected API response:', data);
                setIsAuthenticated(false);
                setLoading(false);
                redirectToLogin();
              }
            } else {
              // Non-JSON response - redirect to login
              setIsAuthenticated(false);
              setLoading(false);
              redirectToLogin();
            }
          } catch (e) {
            // Failed to parse - redirect to login
            console.error('Failed to parse error response:', e);
            setIsAuthenticated(false);
            setLoading(false);
            redirectToLogin();
          }
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Auth check failed:', error);
          // On any error, assume not authenticated and redirect
          setIsAuthenticated(false);
          setLoading(false);
          redirectToLogin();
        }
      }
    };

    checkAuth();

    // Safety timeout - if we're still loading after 3 seconds, redirect to login
    timeoutId = setTimeout(() => {
      if (!cancelled && loading) {
        console.warn('[useAuth] Safety timeout reached - redirecting to login');
        setIsAuthenticated(false);
        setLoading(false);
        redirectToLogin();
      }
    }, 3000);

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []); // Empty deps - only run once on mount

  return { isAuthenticated, loading };
}
