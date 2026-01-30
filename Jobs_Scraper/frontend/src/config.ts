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
  const stack = new Error().stack;
  console.log('[redirectToLogin] Called');
  console.log('[redirectToLogin] Stack trace:', stack);
  
  // Prevent multiple redirects
  if (redirecting) {
    console.log('[redirectToLogin] Already redirecting, skipping...');
    return;
  }
  
  // Check if already on login page or if we're authenticated
  const currentUrl = window.location.href;
  const pathname = window.location.pathname;
  
  console.log('[redirectToLogin] Current URL:', currentUrl, 'Pathname:', pathname);
  
  // Don't redirect if already on login page
  if (currentUrl.includes('/login') || pathname === '/login' || currentUrl.includes('localhost:5000/login')) {
    console.log('[redirectToLogin] Already on login page or Flask backend, skipping redirect');
    redirecting = false; // Reset flag if already on login
    return;
  }
  
  console.log('[redirectToLogin] Will redirect to login');
  redirecting = true;
  
  // Reset redirecting flag after a delay in case redirect fails
  setTimeout(() => {
    redirecting = false;
  }, 3000);
  
  // Use replace to avoid adding to history
  // Use proxy path if we're on the frontend
  const targetUrl = (window.location.port === '3000' || window.location.port === '3001') 
    ? '/login' 
    : LOGIN_URL;
  
  console.log('[redirectToLogin] Redirecting to:', targetUrl);
  
  // Force redirect immediately
  window.location.replace(targetUrl);
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
