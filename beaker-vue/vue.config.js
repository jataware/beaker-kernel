const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  // publicPath: "/dev_ui/",
  pages: {
    index: 'src/pages/dev-interface.ts',
    admin: 'src/pages/admin.ts',
    notebook: 'src/pages/notebook.ts',
    cell: 'src/pages/cell.ts',
    playground: 'src/pages/playground.ts',
  },
  assetsDir: "static/",
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        // "beaker-kernel": path.resolve(__dirname, "../beaker-ts/src/")
      }
    }
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
