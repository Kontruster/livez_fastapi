import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Пути, которые проксируются на FastAPI.
const API_PREFIXES = [
  '/auth',
  '/users',
  '/posts',
  '/comments',
  '/groups',
  '/profile',
  '/follow',
  '/media',
  '/uploads',
  '/health',
]

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // В Docker backend доступен по имени сервиса (backend), локально — по
  // localhost. Значение всегда можно переопределить через VITE_BACKEND_URL.
  const inDocker = process.env.DOCKER === 'true' || env.DOCKER === 'true'
  const backend =
    env.VITE_BACKEND_URL ||
    (inDocker ? 'http://backend:8000' : 'http://127.0.0.1:8000')

  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_PORT) || 5173,
      // слушаем на всех интерфейсах, чтобы работал проброс портов из Docker
      host: env.VITE_HOST || '0.0.0.0',
      proxy: Object.fromEntries(
        API_PREFIXES.map((prefix) => [
          prefix,
          {
            target: backend,
            changeOrigin: true,
          },
        ]),
      ),
    },
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
    },
  }
})
