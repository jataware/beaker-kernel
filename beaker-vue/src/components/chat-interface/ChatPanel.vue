<template>
    <div
        class="cell-container drag-sort-enable"
        ref="cellsContainerRef"
    >
        <component
            v-for="(cell, index) in session.notebook.cells"
            :cell="cell"
            :selected="cell.id === notebook.selectedCellId"
            :key="index"
            :is="cellMap[cell.cell_type]"
            :class="{
                selected: (cell.id === notebook.selectedCellId),
            }"
            @click="(evt)=>clicked(cell)"
            class="beaker-chat-cell"
        />
        <div class="drop-overflow-catcher">
            <slot name="notebook-background" />
        </div>
    </div>
</template>

<script setup lang="tsx">

import { ref, inject, computed } from 'vue';
import { BeakerSession } from 'beaker-kernel';
import { BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';

const session = inject<BeakerSession>('session');
const cellMap = inject("cell-component-mapping");
const notebook = inject<BeakerNotebookComponentType>("notebook");
const cellsContainerRef = ref(null);

const clicked = (cell) => (evt) => {
    notebook.selectCell(cell.value as {id: string}, );
};

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
}
.drop-overflow-catcher {
    flex: 1;
}
</style>