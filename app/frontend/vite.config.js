import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API = 'http://52.47.190.170:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth':         { target: API, changeOrigin: true },
      '/users':        { target: API, changeOrigin: true },
      '/scans':        { target: API, changeOrigin: true },
      '/incidents':    { target: API, changeOrigin: true },
      '/reports':      { target: API, changeOrigin: true },
      '/mobile-scans': { target: API, changeOrigin: true },
      '/ebios':        { target: API, changeOrigin: true },
      '/ai':           { target: API, changeOrigin: true },
      '/logs':         { target: API, changeOrigin: true },
      '/export':       { target: API, changeOrigin: true },
    }
  }
})
