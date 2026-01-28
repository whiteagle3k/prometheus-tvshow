import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8011',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/tvshow': {
        target: 'http://localhost:8011',
        changeOrigin: true,
        ws: true,  // Enable WebSocket proxying for /tvshow/ws
      }
    }
  }
}) 