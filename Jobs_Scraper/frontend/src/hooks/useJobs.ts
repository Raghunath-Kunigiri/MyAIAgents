import { useState, useEffect } from 'react';
import { Job } from '../types';
import { redirectToLogin } from '../config';

interface UseJobsReturn {
  jobs: Job[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useJobs(): UseJobsReturn {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/jobs', {
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
        setJobs(data.jobs || []);
      } else {
        if (data.error === 'Authentication required' || data.redirect) {
          redirectToLogin();
          return; // Stop execution
        }
        throw new Error(data.error || 'Failed to load jobs');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  return {
    jobs,
    loading,
    error,
    refetch: fetchJobs,
  };
}
