const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        "beaker-kernel": path.resolve(__dirname, "../../../beaker-ts/src/")
      }
    }
  },
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:8888',
        ws: true,
        changeOrigin: true,
      },
    },
  }
})
