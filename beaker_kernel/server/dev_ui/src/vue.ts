// @ts-nocheck

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
(window as any).__webpack_public_path__ = URLExt.join(
  PageConfig.getBaseUrl(),
  'example/'
);

import { createApp, ref } from 'vue/dist/vue.esm-bundler.js';
import { BeakerSession } from 'beaker-kernel';


// const baseUrl = PageConfig.getBaseUrl();
var beakerSession: BeakerSession = new BeakerSession(
  {
    settings: {},
    name: "MyKernel",
    kernelName: "beaker"
  }
);


function main(): void {

    const app = createApp({
        setup() {
            const message = ref('Hello vue');
            const beaker = ref(null);

            beakerSession.services.ready.then(() => {
                beaker.value = beakerSession;
            });

            return {
                message,
                beaker,
            }
        },
        template: `
    <div style="color: red">{{message}}</div>
    <div>{{beaker?.toJSON()}}</div>
    <div>{{beaker}}</div>
    <div>Cell count: {{beaker?.cells.length}}</div>
    <div id="cells" v-if="beaker?.cells">
        <div v-for="cell in beaker.cells">
          {{cell}}
        </div>
    </div>

`
    });
    app.mount("#app");
}

window.addEventListener('load', main);
