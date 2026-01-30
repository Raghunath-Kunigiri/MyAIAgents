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
          console.warn('[useJobs] Unauthorized - redirecting to login');
          redirectToLogin();
          return; // Stop execution
        }
        // Try to get error message from response
        let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMsg = errorData.error;
          }
        } catch (e) {
          // If response is not JSON, use default error message
        }
        console.error('[useJobs] Request failed:', errorMsg);
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
      console.log('[useJobs] API response:', data);
      
      if (data.success) {
        const jobsArray = data.jobs || [];
        console.log('[useJobs] Jobs loaded successfully:', jobsArray.length, 'jobs');
        if (jobsArray.length === 0) {
          console.warn('[useJobs] No jobs returned from API - database might be empty');
        }
        setJobs(jobsArray);
      } else {
        // Only redirect if explicitly told to (401 already handled above)
        if (data.error === 'Authentication required' || data.redirect === '/login') {
          console.warn('[useJobs] Server indicated auth required - redirecting');
          redirectToLogin();
          return; // Stop execution
        }
        // Other errors - just log and set error state
        console.error('[useJobs] Failed to load jobs:', data.error);
        throw new Error(data.error || 'Failed to load jobs');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('[useJobs] Error fetching jobs:', errorMessage);
      setError(errorMessage);
      setJobs([]);
      // Don't redirect on network errors - let the error be displayed
      // Only redirect on actual 401 responses (which are handled above)
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
