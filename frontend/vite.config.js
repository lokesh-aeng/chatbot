import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/chat": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,         // if you ever run HTTPS locally, you might set this to true
        // rewrite: (path) => path.replace(/^\/chat/, "/chat") // not needed here
      },
    },
    port: 3000, // Change this to any port you want
  },
})
