<template>
  <main>
    <RouterView :config="config"/>
  </main>
</template>

<script setup lang="ts">
import './assets/beaker-common.css';
import { RouterLink, RouterView } from 'vue-router'

const props = defineProps([
  "config",
]);

</script>

<style scoped>
</style>
