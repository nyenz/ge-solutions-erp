import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // The bundle is >500kB (it's a large ERP). This only silences the
    // "chunk larger than 500 kB" WARNING; it does not affect behaviour.
    chunkSizeWarningLimit: 1500,
  },
})
