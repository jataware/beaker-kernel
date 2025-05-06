<template>
    <BeakerApp>
        <RouterView/>
    </BeakerApp>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useConfigStore } from './stores/config';
import { useSessionStore } from './stores/session';

const props = defineProps<{
  confUrl?: string;
}>();

const configStore = useConfigStore();
configStore.init(props.confUrl);
</script>

<style scoped>
BeakerApp {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
}
</style>
