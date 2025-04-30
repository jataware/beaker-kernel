<template>
    <div
        class="cell-container"
    >
        <div class="flex-background">
            <slot name="notebook-background" />
        </div>
        <span class="chat-help-text-display query-answer-chat-override">
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
    z-index: 3;
    overflow: auto;

    // styling the scrollbar
    scrollbar-color: var(--surface-d) var(--surface-a);
}

.flex-background {
    flex: 1;
}

.chat-help-text-display {
    margin-bottom: 1rem;
}
</style>
