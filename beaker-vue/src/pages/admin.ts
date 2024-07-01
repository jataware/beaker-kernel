import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import BeakerAdmin from './BeakerAdmin.vue';
import Tooltip from 'primevue/tooltip';
import ToastService from 'primevue/toastservice';
import FocusTrap from 'primevue/focustrap';
import ConfirmationService from 'primevue/confirmationservice';

import 'primeicons/primeicons.css'

import { PageConfig, URLExt } from '@jupyterlab/coreutils';

const baseUrl = PageConfig.getBaseUrl();

(async () => {

  let config;
  if (process.env.NODE_ENV === "development") {
    config = {
      baseUrl: baseUrl,
      appUrl: baseUrl,
      wsUrl: baseUrl.replace("http", "ws"),
      token: "89f73481102c46c0bc13b2998f9a4fce",
    }
  }
  else {
    const confUrl = URLExt.join(baseUrl, '/config')
    const configResponse = await fetch(confUrl);
    config = await configResponse.json();
  }

  const app = createApp(BeakerAdmin, {config});

  app.use(PrimeVue);
  app.use(ToastService);
  app.use(ConfirmationService);
  app.directive('tooltip', Tooltip);
  app.directive('focustrap', FocusTrap);
  app.mount('#app');
})();
