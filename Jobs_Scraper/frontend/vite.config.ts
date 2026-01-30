import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // Default port (Vite will use next available if taken)
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        ws: true, // Enable websocket proxying
        cookieDomainRewrite: '',
        cookiePathRewrite: '/',
      },
      // Also proxy the login route for consistency
      '/login': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Set header to identify frontend requests
            proxyReq.setHeader('X-Forwarded-Host', 'localhost:3000');
            proxyReq.setHeader('X-Forwarded-Proto', 'http');
            // Preserve the original referer if it exists
            if (req.headers.referer) {
              proxyReq.setHeader('Referer', req.headers.referer);
            }
          });
        },
      },
      '/register': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/logout': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      '/profile': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
