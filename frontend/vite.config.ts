import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // The backend URL is read from an unprefixed variable. Vite only exposes
  // `VITE_*` keys to client code, so anything read here stays server-side.
  //
  // There is deliberately no API key here any more: sign-in happens in the app
  // and the session lives in an httpOnly cookie the backend sets. A key injected
  // by the proxy would answer every request as the same owner and quietly
  // bypass per-account isolation.
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.BACKEND_URL ?? 'http://localhost:8000'

  // Every /api request is same-origin from the browser, so the session cookie
  // rides along and nothing about the credential is visible to page scripts.
  const proxy = {
    '/api': {
      target,
      changeOrigin: true,
    },
  }

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: { proxy },
    preview: { proxy },
  }
})