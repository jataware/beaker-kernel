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
  chainWebpack: (config) => {
    config.plugin('define').tap((definitions) => {
      Object.assign(definitions[0], {
        __VUE_OPTIONS_API__: 'true',
        __VUE_PROD_DEVTOOLS__: 'false',
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false'
      });
      return definitions;
    });
  },
  devServer: {
    proxy: process.env.PROXY || 'http://localhost:8888',
    onBeforeSetupMiddleware (server) {
      // Proxy everything to the server except for `/ws`, webpacks websocket for hotloading, static files and pages.
      const origContext = server.options.proxy[0].context;
      server.options.proxy[0].context = (pathname, req) => {
        if (pathname === '/ws') {
          return false;
        }
        // Always proxy requests to /files/* for downloading
        if (/^\/files\//.test(pathname)) {
          return true;
        }
        // Never proxy pages defined in the vue config.
        const pageRegex = '^/?(' + Object.keys(module.exports.pages).join('|') + ')\\b'
        if (RegExp(pageRegex).test(pathname)) {
          return false;
        }

        const result = origContext(pathname, req);
        // Will be undefined on websocket requests, or any other request that does not provide an `accepts` header.
        // Allow all such requests other than `/ws` which is handled above.
        if (result === undefined) {
          return true;
        }
        return result;
      }
    },
  },
})
