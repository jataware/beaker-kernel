<template>
    <Button
        text
        @click="props.toggleDarkMode"
        style="margin: 0; color: var(--gray-500);"
        :icon="themeIcon"
        v-tooltip.right="{value: 'Swap Theme', showDelay: 300}"
    />
</template>

<script setup>

import { defineProps, computed, inject } from "vue";
import Button from 'primevue/button';
const props = defineProps([
    "toggleDarkMode",
]);
const theme = inject('theme');
const themeIcon = computed(() => {
    return `pi pi-${theme === 'dark' ? 'sun' : 'moon'}`;
});

</script>