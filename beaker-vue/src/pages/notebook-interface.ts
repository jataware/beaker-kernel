import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import Tooltip from 'primevue/tooltip';
import ToastService from 'primevue/toastservice';
import FocusTrap from 'primevue/focustrap';
import { vKeybindings } from '../directives/keybindings';
import { vAutoScroll } from '../directives/autoscroll';
import BeakerThemePlugin from '../plugins/theme';
import NotebookInterface from './NotebookInterface.vue';


import 'primeicons/primeicons.css';
import '../index.scss';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

const baseUrl = PageConfig.getBaseUrl();

(async () => {

  const confUrl = URLExt.join(baseUrl, '/config')
  const configResponse = await fetch(confUrl);
  const config = await configResponse.json();

  const app = createApp(NotebookInterface, {config});

  app.use(PrimeVue);
  app.use(ToastService);
  app.use(BeakerThemePlugin);
  app.directive('tooltip', Tooltip);
  app.directive('focustrap', FocusTrap);
  app.directive('keybindings', vKeybindings);
  app.directive('autoscroll', vAutoScroll);
  app.mount('#app');
})();
