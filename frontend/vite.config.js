import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.VITE_BACKEND_URL || 'http://backend:8000'

  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_PORT) || 5173,
      proxy: Object.fromEntries(
        ['/auth', '/users', '/posts', '/groups', '/profile',
         '/follow', '/media', '/uploads'].map((p) => [p, backend]),
      ),
    },
  }
})