import { fileURLToPath, URL } from 'node:url';
import path from 'path';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import topLevelAwait from 'vite-plugin-top-level-await';
import { globSync } from 'glob';

export const entryPoints = Object.fromEntries(
  globSync("src/**/*.{vue,ts}").map(file => [
    path.relative(
      'src',
      file.slice(0, file.length - path.extname(file).length)
    ),
    fileURLToPath(new URL(file, import.meta.url))
  ])
);


export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    topLevelAwait(),
    {
      name: "sanitize-eval",
      transform(src, id) {
        // Custom inline plugin to replace 'eval()' calls with 'console.debug()'.
        if (id.includes("@jupyterlab/coreutils/lib/pageconfig")) {
          return src.replaceAll(/\beval\b/g, 'console.debug');
        }
      }
    }
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'node-fetch': path.resolve(require.resolve('isomorphic-fetch'), '..'),
      'path': path.resolve(require.resolve('path-browserify'), '..'),
    },
  }
});
