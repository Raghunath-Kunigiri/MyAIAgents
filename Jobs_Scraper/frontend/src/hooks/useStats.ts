import { useState, useEffect } from 'react';
import { Stats } from '../types';
import { redirectToLogin } from '../config';

interface UseStatsReturn {
  stats: Stats | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useStats(): UseStatsReturn {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/stats', {
        credentials: 'include', // Include cookies for authentication
      });
      
      if (!response.ok) {
        // If unauthorized, redirect to Flask login
        if (response.status === 401 || response.status === 302) {
          console.warn('[useStats] Unauthorized - redirecting to login');
          redirectToLogin();
          return; // Stop execution
        }
        // Try to get error message from response body
        let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.error) errorMsg = errorData.error;
        } catch {
          // response not JSON
        }
        console.error('[useStats] Request failed:', errorMsg);
        throw new Error(errorMsg);
      }
      
      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        // If not JSON, likely a redirect to login
        if (response.status === 401 || response.status === 302) {
          redirectToLogin();
          return; // Stop execution
        }
        throw new Error('Invalid response format');
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log('[useStats] Stats loaded successfully:', data.stats);
        setStats(data.stats);
      } else {
        // Only redirect if explicitly told to (401 already handled above)
        if (data.error === 'Authentication required' || data.redirect === '/login') {
          console.warn('[useStats] Server indicated auth required - redirecting');
          redirectToLogin();
          return; // Stop execution
        }
        // Other errors - just log and set error state
        console.error('[useStats] Failed to load stats:', data.error);
        throw new Error(data.error || 'Failed to load stats');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('[useStats] Error fetching stats:', errorMessage);
      setError(errorMessage);
      setStats(null);
      // Don't redirect on network errors - let the error be displayed
      // Only redirect on actual 401 responses (which are handled above)
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
}
