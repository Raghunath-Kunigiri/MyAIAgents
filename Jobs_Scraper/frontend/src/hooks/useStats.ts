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
          redirectToLogin();
          return; // Stop execution
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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
        setStats(data.stats);
      } else {
        if (data.error === 'Authentication required' || data.redirect) {
          redirectToLogin();
          return; // Stop execution
        }
        throw new Error(data.error || 'Failed to load stats');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setStats(null);
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
