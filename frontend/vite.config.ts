import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
