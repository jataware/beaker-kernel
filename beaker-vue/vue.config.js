const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  chainWebpack: config => {
    // config.devtool("inline-source-map");
    config.module.rule('ts').uses.delete('thread-loader');
    config.module
      .rule('ts')
      .use('ts-loader')
      .tap(options => {
        options.transpileOnly = false;
        options.happyPackMode = false;
        options.compilerOptions = {
          declaration: true,
          decalarationMap: true,
          declarationDir: "lib",
          noEmit: false,
          emitDeclarationOnly: false,
          include: [
            "src/**/*.ts",
            "src/**/*.tsx",
            "src/**/*.vue",
          ],
        };
        return options;
      });
  },
  pages: {
    index: 'src/pages/dev-interface.ts',
    admin: 'src/pages/admin.ts',
    notebook: 'src/pages/notebook.ts',
    cell: 'src/pages/cell.ts',
    playground: 'src/pages/playground.ts',
  },
  assetsDir: "static/",
  transpileDependencies: true,
  outputDir: path.resolve(__dirname, 'dist/html'),
  configureWebpack: {
    resolve: {
      extensions: ['.ts', '.tsx', '.vue'],
    },
    output: {
      library: "beaker_vue",
    },
  },
  devServer: {
    proxy: {
      '^/stats': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
      '^/api': {
        target: 'http://jupyter:8888',
        ws: true,
        changeOrigin: true,
      },
      '^/upload': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
      '^/download': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
      '^/contexts': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
      '^/config': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
      '^/summary': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      }
    },
  }
})
