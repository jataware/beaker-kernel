import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import Tooltip from 'primevue/tooltip';
import ToastService from 'primevue/toastservice';
import FocusTrap from 'primevue/focustrap';

import DevInterface from './DevInterface.vue';
import { vKeybindings } from '../directives/keybindings';
import { vAutoScroll } from '../directives/autoscroll';
import BeakerThemePlugin from '../plugins/theme';
// import { vTheme } from '../directives/theme';

import 'primeicons/primeicons.css';
import '../index.scss';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

const baseUrl = PageConfig.getBaseUrl();

(async () => {

  const confUrl = URLExt.join(baseUrl, '/config')
  const configResponse = await fetch(confUrl);
  const config = await configResponse.json();

  const app = createApp(DevInterface, {config});

  app.use(PrimeVue);
  app.use(ToastService);
  app.use(BeakerThemePlugin);
  app.directive('tooltip', Tooltip);
  app.directive('focustrap', FocusTrap);
  app.directive('keybindings', vKeybindings);
  app.directive('autoscroll', vAutoScroll);
  app.mount('#app');
})();
