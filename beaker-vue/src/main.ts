import { createApp } from 'vue'
import { createPinia } from 'pinia'

import PrimeVue from 'primevue/config';
import Tooltip from 'primevue/tooltip';
import ConfirmationService from 'primevue/confirmationservice';
import DialogService from 'primevue/dialogservice';
import ToastService from 'primevue/toastservice';
import FocusTrap from 'primevue/focustrap';
import { vKeybindings } from './directives/keybindings';
import { vAutoScroll } from './directives/autoscroll';
import BeakerThemePlugin from './plugins/theme';
import BeakerAppConfigPlugin from './plugins/appconfig';

import App from './App.vue'
import router from './router'
import { DefaultTheme } from './themes';

import 'primeicons/primeicons.css';
import './index.scss';

const theme = {
    preset: DefaultTheme,
    options: {
        prefix: '',
        darkModeSelector: '.beaker-dark',
        cssLayer: {
            name: 'primevue',
            order: 'primevue, beaker'
        }
    }
};

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(PrimeVue, {theme});
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
