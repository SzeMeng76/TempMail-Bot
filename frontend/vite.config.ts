import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api/mailtm': {
        target: 'https://api.mail.tm',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mailtm/, ''),
      },
    },
  },
})
