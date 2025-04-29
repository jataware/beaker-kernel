import { fileURLToPath, URL } from 'node:url';
import { dirname, resolve } from 'node:path';
import * as fs from 'node:fs';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import vueDevTools from 'vite-plugin-vue-devtools';
import topLevelAwait from 'vite-plugin-top-level-await';
import { ExportRoutesPlugin } from './exportRoutes';

const __dirname = dirname(fileURLToPath(import.meta.url));

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
    ExportRoutesPlugin(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'node-fetch': fileURLToPath(new URL('./node_modules/isomorphic-fetch', import.meta.url)),
      'path': fileURLToPath(new URL('./node_modules/path-browserify', import.meta.url)),
    },
  },
  build: {
    target: 'esnext',
    assetsDir: 'static/',
    outDir: 'dist/html/',
  },
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext',
    }
  }
})
