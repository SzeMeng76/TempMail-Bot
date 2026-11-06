import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// 本地开发/preview 用的代理。生产环境由 nginx.conf 转发同样的路径。
// vnproxy 默认跑在 8091，可以用 VNPROXY_TARGET 覆盖。
const VNPROXY_TARGET = process.env.VNPROXY_TARGET || 'http://127.0.0.1:8091'

const proxy = {
  '/api/mailtm': {
    target: 'https://api.mail.tm',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api\/mailtm/, ''),
  },
  '/api/vn': {
    target: VNPROXY_TARGET,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api\/vn/, ''),
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy },
  preview: { proxy },
})
