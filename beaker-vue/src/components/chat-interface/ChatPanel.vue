<template>
    <div
        class="cell-container"
    >
        <div class="flex-background">
            <slot name="notebook-background" />
        </div>
        <span class="chat-help-text-display">
            <slot name="help-text"></slot>
        </span>
        <component
            v-for="(cell, index) in session.notebook.cells"
            :cell="cell"
            :key="index"
            :is="props.cellMap[cell.cell_type]"
            class="beaker-chat-cell"
        />
    </div>
</template>

<script setup lang="tsx">
import { ref, inject, defineProps, defineExpose } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';

const session = inject<BeakerSession>('session');

const props = defineProps([
    "cellMap"
])

</script>

<style lang="scss">
.cell-container {
    position: relative;
    display: flex;
    flex: 1;
    flex-direction: column;
    background-color: var(--surface-a);
    z-index: 3;
    overflow: auto;
    margin-top: 1rem;
}

.flex-background {
    flex: 1;
}

.chat-help-text-display {
    background-color: var(--surface-c);
    padding: 0 1rem 0 1rem;
    margin: 0 0rem 1rem 0rem;
    border-radius: var(--border-radius);
}
</style>
