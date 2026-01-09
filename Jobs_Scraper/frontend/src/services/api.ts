import { Job, JobStatus } from '../types';
import { redirectToLogin } from '../config';

export async function updateJobStatus(jobId: string, status: JobStatus): Promise<boolean> {
  try {
    const response = await fetch(`/api/update_app_status/${jobId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include cookies for authentication
      body: JSON.stringify({ status }),
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 302) {
        redirectToLogin();
        return false;
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error updating job status:', error);
    return false;
  }
}

export async function updateJobNotes(jobId: string, notes: string): Promise<boolean> {
  try {
    const response = await fetch(`/api/update_app_notes/${jobId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Include cookies for authentication
      body: JSON.stringify({ notes }),
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 302) {
        redirectToLogin();
        return false;
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error updating job notes:', error);
    return false;
  }
}

export async function generateResume(jobId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(`/api/generate_resume/${jobId}`, {
      method: 'POST',
      credentials: 'include', // Include cookies for authentication
    });
    
    // Try to parse response as JSON first (even for error responses)
    let data;
    try {
      data = await response.json();
    } catch (jsonError) {
      // If JSON parsing fails, use the response text
      const text = await response.text();
      data = { success: false, error: text || `HTTP ${response.status}` };
    }
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 302) {
        redirectToLogin();
        return { success: false, error: 'Authentication required' };
      }
      // Return the error message from the backend
      return {
        success: false,
        error: data.error || data.message || `HTTP ${response.status}: ${response.statusText}`,
      };
    }
    
    return data;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

export function downloadResume(fileId: string): void {
  window.open(`/api/download_resume/${fileId}`, '_blank');
}

export async function exportJobs(): Promise<void> {
  window.open('/api/export_jobs', '_blank');
}
