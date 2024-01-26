import { createApp } from 'vue'
import App from './App.vue'

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
(window as any).__webpack_public_path__ = URLExt.join(
  PageConfig.getBaseUrl(),
  'example/'
);

createApp(App).mount('#app')
