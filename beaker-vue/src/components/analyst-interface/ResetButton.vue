<template>
    <Button
        @click="resetNotebook"
        v-tooltip.right="{value: 'Reset notebook', showDelay: 300}"
        icon="pi pi-refresh"
        size="small"
        severity="info"
        text
    />
</template>

<script setup lang="tsx">

import { inject, defineProps } from "vue";
import { BeakerSession } from 'beaker-kernel';
import Button from "primevue/button";

const session = inject<BeakerSession>('session');
const props = defineProps([
    "onResetCallback",
]);

const resetNotebook = async () => {
    session.reset();
    props.onResetCallback?.();
};

</script>