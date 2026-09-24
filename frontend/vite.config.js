import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// export default defineConfig({
//   plugins: [react()],
//   server: {
//     port: 5173,
//     proxy: {
//       '/auth':    'http://localhost:8000',
//       '/users':   'http://localhost:8000',
//       '/posts':   'http://localhost:8000',
//       '/groups':  'http://localhost:8000',
//       '/profile': 'http://localhost:8000',
//       '/follow':  'http://localhost:8000',
//     },
//   },
// })

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,          // чтобы слушал 0.0.0.0 внутри контейнера
    port: 5173,
    proxy: {
      // все запросы на /auth, /users, /posts и т.п. идут на бэкенд
      '/auth': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/posts': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/groups': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/profile': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/follow': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      // или общий префикс, если у тебя все ручки под /api
      // '/api': { target: 'http://backend:8000', changeOrigin: true }
    },
  },
})