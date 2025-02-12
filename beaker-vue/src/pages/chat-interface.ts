import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import Tooltip from 'primevue/tooltip';
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';
import DialogService from 'primevue/dialogservice';
import FocusTrap from 'primevue/focustrap';

import BeakerThemePlugin from '../plugins/theme';
import BeakerAppConfigPlugin from '../plugins/appconfig';
import ChatInterface from './ChatInterface.vue';
import { vAutoScroll } from '../directives/autoscroll';
import { vKeybindings } from '../directives/keybindings';

import 'primeicons/primeicons.css';
import '../index.scss';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

const baseUrl = PageConfig.getBaseUrl();

(async () => {

  const confUrl = URLExt.join(baseUrl, '/config')
  const configResponse = await fetch(confUrl);
  const config = await configResponse.json();

  const app = createApp(ChatInterface, {config});

  app.use(PrimeVue);
  app.use(ToastService);
  app.use(ConfirmationService);
  app.use(DialogService);
  app.use(BeakerThemePlugin);
  app.use(BeakerAppConfigPlugin);
  app.directive('tooltip', Tooltip);
  app.directive('focustrap', FocusTrap);
  app.directive('keybindings', vKeybindings);
  app.directive('autoscroll', vAutoScroll);
  app.mount('#app');
})();
