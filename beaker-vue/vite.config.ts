import { fileURLToPath, URL } from 'node:url';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import vueDevTools from 'vite-plugin-vue-devtools';
import topLevelAwait from 'vite-plugin-top-level-await';

let chunkNum: number = 0;
const ProxyHost = `${process.env.PROXY || 'http://localhost:8888'}`;

// https://vite.dev/config/
export default defineConfig({

  server: {
    host: '0.0.0.0',
    port: 8080,
    proxy: {
      '/api': {
        target: `${ProxyHost}/`,
        ws: true,
        rewriteWsOrigin: true,
      },
      '/appconfig.js': `${ProxyHost}/`,
      '/files': `${ProxyHost}/`,
      '/config': `${ProxyHost}/`,
      '/contexts': `${ProxyHost}/`,
    },
    fs: {
      allow: [".."]
    },
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
      'node-fetch': fileURLToPath(new URL('./node_modules/isomorphic-fetch', import.meta.url)),
      'path': fileURLToPath(new URL('./node_modules/path-browserify', import.meta.url)),
      // Allows automatic updating when beaker-ts is updated, but will use the dist version of beaker-ts/beaker-kernel
      // when building or running in production mode.
      'beaker-kernel': (
        process.env.NODE_ENV === "development"
        ? fileURLToPath(new URL('../beaker-ts/src', import.meta.url))
        : 'beaker-kernel'
      ),
    },
    dedupe: [
      'vue',
      'primevue',
      '@primevue/themes',
      '@primevue/icons',
      '@primeuix/styled',
      '@primeuix/themes',
      '@primeuix/utils',
      '@lumino',
      '@lumino/widgets',
      '@lumino/algorithm',
      '@lumino/coreutils',
      '@lumino/polling',
      '@lumino/signaling',
      '@jupyterlab',
      '@jupyterlab/ui-components',
      '@jupyterlab/services',
      '@jupyterlab/apputils',
      '@jupyterlab/translation',
      '@jupyterlab/statedb',
      'react-dom',
      'xlsx',
      '@jupyterlab/coreutils',
      '@jupyterlab/mathjax-extension',
      '@jupyterlab/rendermime',
    ],
  },
  build: {
    target: 'esnext',
    assetsDir: 'static/',
    outDir: 'dist/html/',
    rollupOptions: {
      output: {
        manualChunks: {
          primevue: [
            'primevue',
            'vue',
            '@primevue/themes',
            '@primevue/icons',
            '@primeuix/styled',
            '@primeuix/themes',
            '@primeuix/utils',
          ],
          xlsx: ['xlsx'],
          codemirror: ['codemirror'],
          jupyterlab: [
            '@jupyterlab/coreutils',
            '@jupyterlab/mathjax-extension',
            '@jupyterlab/rendermime',
          ],
          pdfjs: ['pdfjs-dist'],
        },
        // chunkFileNames: (chunkInfo) => {
        //   if (/\.vue_vue/.test(chunkInfo.name)) {
        //     const name = `lib-${chunkNum}-[hash].js`;
        //     chunkNum++;
        //     return name;
        //   }
        //   else {
        //     return "[name]-[hash].js";
        //   }
        // },
      }
    }
  },
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext',
    },
  }
})
