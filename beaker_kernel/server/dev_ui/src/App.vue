<template>
  <div>
    <h1>Beaker dev notebook</h1>
    <BeakerNotebook :session="beakerSession" />
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { BeakerSession } from 'beaker-kernel';
import BeakerNotebook from './components/BeakerNotebook.vue';

// TODO: Move the config outside this file. Fetch from environment?
const settings = {
    baseUrl: "http://localhost:8888/",
    appUrl: "http://localhost:8888/",
    wsUrl: "http://localhost:8888/",
    token: "89f73481102c46c0bc13b2998f9a4fce",
};

const beakerSession = reactive(new BeakerSession(
  {
    settings: settings,
    name: "MyKernel",
    kernelName: "beaker"
  }
));
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
