<template>
    <div
        class="cell-container drag-sort-enable"
    >
        <span v-if="session.notebook.cells.length == 0" class="chat-help-text-display">
            <slot name="help-text"></slot>
        </span>
        <component
            v-for="(cell, index) in session.notebook.cells"
            ref="cellsContainerRef"
            :cell="cell"
            :key="index"
            :is="cellMap[cell.cell_type]"
            class="beaker-chat-cell"
        />
        <div class="drop-overflow-catcher">
            <slot name="notebook-background" />
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, inject, defineProps, defineExpose } from 'vue';
import { BeakerSession } from 'beaker-kernel';

const session = inject<BeakerSession>('session');
const cellMap = inject("cell-component-mapping");
const cellsContainerRef = ref(null);

defineExpose({
    cellsContainerRef
});

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

.drop-overflow-catcher {
    flex: 1;
}

.chat-help-text-display {
    background-color: var(--surface-c);
    padding: 0 1rem 0 1rem;
    margin: 0 1rem 1rem 1rem;
    border-radius: var(--border-radius);
}
</style>