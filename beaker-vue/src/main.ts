import { createApp } from 'vue'
import { createPinia } from 'pinia'

import PrimeVue from 'primevue/config';
import Tooltip from 'primevue/tooltip';
import ConfirmationService from 'primevue/confirmationservice';
import DialogService from 'primevue/dialogservice';
import ToastService from 'primevue/toastservice';
import FocusTrap from 'primevue/focustrap';
import { vKeybindings } from '@/directives/keybindings';
import { vAutoScroll } from '@/directives/autoscroll';
import BeakerThemePlugin from '@/plugins/theme';
import BeakerAppConfigPlugin from '@/plugins/appconfig';

import Aura from '@primevue/themes/aura';

import App from './App.vue'
import router from './router'


import 'primeicons/primeicons.css';
import './index.scss';

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { options } from 'marked';

const baseUrl = PageConfig.getBaseUrl();

const confUrl = URLExt.join(baseUrl, '/config')
const configResponse = await fetch(confUrl);
const config = await configResponse.json();

const app = createApp(App, {config})

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            prefix: '',
            darkModeSelector: 'none',
            cssLayer: {
                name: 'primevue',
                order: 'primevue, beaker'
            }
        }

    }
});
app.use(ToastService);
app.use(ConfirmationService);
app.use(DialogService);
app.use(BeakerAppConfigPlugin);
app.use(BeakerThemePlugin);
app.directive('tooltip', Tooltip);
app.directive('focustrap', FocusTrap);
app.directive('keybindings', vKeybindings);
app.directive('autoscroll', vAutoScroll);

app.mount('#app')
