import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import topLevelAwait from 'vite-plugin-top-level-await';

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 8080,
    proxy: {
      '/api': 'http://localhost:8888',
      '/appconfig.js': 'http://localhost:8888/',
      '/files': 'http://localhost:8888/',
      '/config': 'http://localhost:8888/',
    },
    fs: {
      allow: [".."]
    }
  },
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
    topLevelAwait(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // 'path': fileURLToPath(new URL('./node_modules/path-browserify', import.meta.url)),
    },
  },
  define: {
    // global: 'window',
  },
  build: {
    target: 'esnext',
  },
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext',
    }
  }
})
