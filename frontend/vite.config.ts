import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv, type ProxyOptions } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // The API key is read from an unprefixed variable. Vite only exposes
  // `VITE_*` keys to client code, so anything read here stays server-side and
  // never reaches the bundle.
  const env = loadEnv(mode, process.cwd(), '')
  const apiKey = env.API_KEY ?? ''
  const target = env.BACKEND_URL ?? 'http://localhost:8000'

  if (!apiKey) {
    console.warn(
      '[curated-space] API_KEY is not set. Copy .env.example to .env and set API_KEY, ' +
        'or item and usage requests will return 401.',
    )
  }

  // Every /api request is same-origin from the browser. The proxy attaches the
  // key so no key ever lives in client code.
  const proxy: Record<string, ProxyOptions> = {
    '/api': {
      target,
      changeOrigin: true,
      configure(proxyServer) {
        proxyServer.on('proxyReq', (proxyReq) => {
          if (apiKey) proxyReq.setHeader('X-API-Key', apiKey)
        })
      },
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