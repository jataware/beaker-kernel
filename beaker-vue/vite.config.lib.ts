import { fileURLToPath, URL } from 'node:url';
import path from 'path';

import { defineConfig } from 'vite';
import dts from 'vite-plugin-dts';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";
import topLevelAwait from 'vite-plugin-top-level-await';
import { globSync } from 'glob';

// Vite configuration for library build
const entryPoints = Object.fromEntries(
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
    cssInjectedByJsPlugin(),
    topLevelAwait(),
    dts({
      tsconfigPath: "tsconfig.lib.json",
      insertTypesEntry: true,
      declarationOnly: false,
      outDir: "./dist/lib",
      logLevel: "error",
    }),
    {
      name: "sanitize-eval",
      transform(src, id) {
        // Custom inline plugin to replace 'eval()' calls with 'console.debug()'.
        if (id.includes("@jupyterlab/coreutils/lib/pageconfig")) {
          return src.replaceAll(/\beval\b/g, 'console.debug');
        }
      }
    },
    {
      name: "export-exports",
      buildStart(options) {
        const prefix = './dist/lib/';
        const exportObject = Object.fromEntries(
          Object.entries(entryPoints).flatMap(([key, srcPath]) => {
            const importPath = ('./' + key.replace(/(^|\/)index/, '')).replace(/\/$/, '');
            const result = [
              [
                importPath, {
                  import: `${prefix}${key}.js`,
                  types: `${prefix}${key}.d.ts`
                }
              ]
            ];
            if (/\.vue\b/.test(srcPath)) {
              const vuePath = `${importPath}.vue`;
              result.push(
                [
                  vuePath, {
                      import: prefix + path.normalize(`${vuePath}.js`),
                      types: prefix + path.normalize(`${vuePath}.d.ts`)
                  }
                ]
              )
            }
            return result;
          })
        );
        this.emitFile({
          type: "asset",
          fileName: "exports.json",
          source: JSON.stringify(exportObject, null, 2),
        });
      }
    }
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'node-fetch': path.resolve(require.resolve('isomorphic-fetch'), '..'),
      'path': path.resolve(require.resolve('path-browserify'), '..'),
    },
  },
  build: {
    target: 'esnext',
    minify: false,
    outDir: 'dist/lib',
    cssCodeSplit: false,
    rollupOptions: {
      onwarn(warning, warn) {
        // Custom warning suppression for known issues that are not a concern
        if (
          (warning.code === "MISSING_EXPORT" && warning.message.includes('json5') && warning.message.includes('@jupyterlab/settingregistry'))
        ) {
          return;
        }
        warn(warning);
      },
      external: [
        /^@?codemirror/,
        /^@?jupyterlab/,
        /^@?plutojl/,
        /^@?primevue/,
        /^@?primeuix/,
        "ansi-html-community",
        "beaker-kernel",
        "buffer",
        "content-disposition",
        "cookie",
        "cytoscape",
        "escape-html",
        "filesize",
        "hash-sum",
        "isomorphic-fetch",
        "json5",
        "katex",
        "marked",
        "panel",
        "path-browserify",
        "pinia",
        "primeicons",
        "scroll-into-view-if-needed",
        "uuid",
        /^vue/,
      ],
      preserveEntrySignatures: "exports-only",
      input: entryPoints,
      output: {
        format: "es",
        preserveModules: true,
        preserveModulesRoot: "src/",
        entryFileNames: (chunk) => {
          return `${chunk.name}.js`;
        }
      }
    },
  }
});
