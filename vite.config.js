import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    // Proxy API calls to the backend so the browser talks to a single origin
    // (no CORS), and a downed backend surfaces as a clear 502 rather than an
    // opaque "Network Error".
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
