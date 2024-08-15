const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
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
