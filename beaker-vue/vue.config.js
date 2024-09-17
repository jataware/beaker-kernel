const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  pages: {
    index: {
      entry: 'src/pages/notebook-interface.ts',
      title: "Beaker Notebook",
    },
    chat: {
      entry: 'src/pages/chat-interface.ts',
      title: "Beaker Chat Interface",
    },
    admin: {
      entry: 'src/pages/admin.ts',
      title: "Beaker Admin",
    },
    dev: {
      entry: 'src/pages/dev-interface.ts',
      title: "Beaker Development Interface",
    },
  },
  css: { extract: false },
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
      },
      '^/files': {
        target: 'http://jupyter:8888',
        changeOrigin: true,
      },
    },
  }
})
