// @ts-nocheck

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
(window as any).__webpack_public_path__ = URLExt.join(
  PageConfig.getBaseUrl(),
  'example/'
);

// import Vue from 'vue/dist/vue.esm-bundler.js';
// import { createApp, ref } from 'vue/dist/vue.esm-bundler.js';
import Vue from "vue";
import { createApp, ref } from 'vue';
import { BeakerSession } from 'beaker-kernel';
import Notebook from '../src/components/notebook.vue';


// const baseUrl = PageConfig.getBaseUrl();
var beakerSession: BeakerSession = new BeakerSession(
  {
    settings: {},
    name: "MyKernel",
    kernelName: "beaker"
  }
);


function main(): void {
  createApp(Notebook).mount("#app");
}

window.addEventListener('load', main);
