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
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, useSlots } from "vue";

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
    position: absolute;
    top:0;
    bottom: 0;
    right: 0;
    left: 0;
    overflow-y: auto;

}

.sidemenu-panel .p-card-body {
    display: flex;
    flex: 1;
    flex-direction: column;
}

.sidemenu-panel .p-card-content {
    flex: 1;
    position: relative;
}
</style>
