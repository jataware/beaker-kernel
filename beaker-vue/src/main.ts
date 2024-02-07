import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import App from './App.vue';
import Tooltip from 'primevue/tooltip';

import 'primeicons/primeicons.css'
import './index.scss';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
(window as any).__webpack_public_path__ = URLExt.join(
  PageConfig.getBaseUrl(),
  'example/'
);

const app = createApp(App);
app.use(PrimeVue);
app.directive('tooltip', Tooltip);
app.mount('#app');
