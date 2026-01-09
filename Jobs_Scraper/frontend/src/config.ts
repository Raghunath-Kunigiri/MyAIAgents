// API and backend configuration
// In production, these can be set via environment variables during build

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
// Default to localhost:5000 for local development, or use environment variable
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.DEV && (window.location.port === '3000' || window.location.port === '3001')
    ? 'http://localhost:5000' 
    : window.location.origin);

// Login URL - defaults to Flask backend login page
export const LOGIN_URL = import.meta.env.VITE_LOGIN_URL || `${BACKEND_URL}/login`;

// Prevent redirect loops
let redirecting = false;
export function redirectToLogin() {
  // Prevent multiple redirects
  if (redirecting) {
    console.log('Already redirecting, skipping...');
    return;
  }
  
  // Check if already on login page
  const currentUrl = window.location.href;
  if (currentUrl.includes('/login') || currentUrl.includes('localhost:5000')) {
    console.log('Already on login page or Flask backend, skipping redirect');
    return;
  }
  
  console.log('Redirecting to login:', LOGIN_URL);
  redirecting = true;
  
  // Use replace to avoid adding to history
  window.location.replace(LOGIN_URL);
}

// Helper function to get API URL
export function getApiUrl(path: string): string {
  if (path.startsWith('http')) {
    return path; // Already a full URL
  }
  if (API_BASE_URL) {
    return `${API_BASE_URL}${path}`;
  }
  // Use relative URL (same origin)
  return path;
}
