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
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // fix182 (speed): React and the router change rarely, so they get their own long-cached file; a site update
        // then only re-downloads the pages that changed.
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          if (/node_modules\/(react|react-dom|scheduler|react-router|react-router-dom)\//.test(id)) return 'react';
          if (id.includes('node_modules/axios')) return 'net';
          return undefined;
        },
      },
    },
  },
  };
})
