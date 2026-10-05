import { defineConfig, loadEnv } from 'vite'
import process from 'node:process'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// fix181 (15.2j): a production build must name its server; without it the app would silently use the wrong one.
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  if (command === 'build' && mode === 'production' && !(env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL)) {
    throw new Error('VITE_API_BASE_URL is not set. Set it (for example in render.yaml or .env.production) before building.');
  }
  return {
  plugins: [react()],
  build: {
    // The bundle is >500kB (it's a large ERP). This only silences the
    // "chunk larger than 500 kB" WARNING; it does not affect behaviour.
    chunkSizeWarningLimit: 1500,
  },
  };
})
