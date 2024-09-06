<template>
    <div class="side-panel" :class="extraClasses">
        <div class="side-panel-title">{{ props.label }}</div>
        <div class="side-panel-content">
            <slot></slot>
        </div>
    </div>
</template>

<script setup lang="tsx">
import { defineProps, defineEmits, ref } from "vue";

import Card from "primevue/card";

const extraClasses = ref<string[]>([]);

const props = defineProps([
    "icon",
    "label",
    "noOverflow",
]);

if (props.noOverflow) {
    extraClasses.value.push('no-overflow')
}

const emit = defineEmits([
]);
</script>


<style lang="scss">
.side-panel {
    height: 100%;
    display: grid;
    grid:
        "title" max-content
        "content" minmax(0%, 1fr) /
        100%;
    overflow: auto;
    &.no-overflow {
        overflow: unset;
    }
}

.side-panel-title {
    padding: 0.5rem;
    grid-area: title;
    font-weight: bold;
    font-size: 1.2rem;
}

.side-panel-content {
    grid-area: content;
    height: 100%;
    margin-right: 4px;
}

</style>
