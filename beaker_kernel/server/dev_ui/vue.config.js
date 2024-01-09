const { defineConfig } = require('@vue/cli-service')
const path = require('path');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        "beaker-kernel": "/beaker-ts/src/"
      }
    }
  },
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://jupyter:8888',
        ws: true,
        changeOrigin: true,
      },
    },
  }
})
