<template>
    <Card role="panel" class="sidemenu-panel">
        <!-- <h2>{{ props.label }}</h2> -->
        <!-- <slot></slot> -->
        <template #title>{{ props.label }}</template>
        <template #content>
            <slot></slot>
        </template>
    </Card>
</template>

<script setup lang="tsx">
import { defineProps, defineEmits } from "vue";

import Card from "primevue/card";

const props = defineProps([
    "icon",
    "label",
]);

const emit = defineEmits([
]);
</script>


<style lang="scss">
.sidemenu-panel {
    display: flex;
    flex: 1;
    height: 100%;
    border-radius: 0;
}

.sidemenu-panel > .p-card {
    border-radius: 0;
}

.sidemenu-panel .p-card-body {
    display: flex;
    flex: 1;
    flex-direction: column;
    padding: 0.5em;
}

.sidemenu-panel .p-card-content {
    flex: 1;
    position: relative;
}
</style>
