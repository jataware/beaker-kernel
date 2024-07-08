<template>
    <Toolbar class="toolbar beaker-toolbar">
        <template #start>
            <slot name="start">
                <Button
                    @click="addCell()"
                    icon="pi pi-plus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="removeCell()"
                    icon="pi pi-minus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="runCell()"
                    icon="pi pi-play"
                    size="small"
                    severity="info"
                    text
                />
                <slot name="start-extra"></slot>
            </slot>
        </template>
        <template #end>
            <slot name="end">
                <Button
                    @click="resetNotebook"
                    v-tooltip.bottom="{value: 'Reset notebook', showDelay: 300}"
                    icon="pi pi-refresh"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="downloadNotebook"
                    v-tooltip.bottom="{value: 'Download as .ipynb', showDelay: 300}"
                    icon="pi pi-download"
                    size="small"
                    severity="info"
                    text
                />
                <OpenNotebookButton @open-file="loadNotebook"/>
                <slot name="end-extra"></slot>
            </slot>
        </template>
    </Toolbar>
</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, defineExpose } from "vue";
import { IBeakerCell, BeakerBaseCell, BeakerSession } from 'beaker-kernel';

import Button from "primevue/button";
import Toolbar from "primevue/toolbar";

import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";

const session: BeakerSession = inject('session');


const addCell = (toIndex) => {
    console.log("add cell");
    session.addCodeCell("");
}

const addCodeCell = (toIndex?: number) => {
    const newCell = session.addCodeCell("");

    // if (typeof toIndex !== 'number') {
    //     const [parent, child] = splitCellIndex(selectedCellIndex.value);
    //     toIndex = parent + 1;
    // }
    // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    // selectCell(newCell);

    // nextTick(() => {
    //     focusSelectedCell();
    // });
}

const addMarkdownCell = (toIndex?: number) => {
    const newCell = session.addMarkdownCell("");

    // if (typeof toIndex !== 'number') {
    //     const [parent, child] = splitCellIndex(selectedCellIndex.value);
    //     toIndex = parent + 1;
    // }
    // // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    // selectCell(newCell);

    // nextTick(() => {
    //     notebookCellsRef.value[notebookCellsRef.value.length - 1].enter();
    //     focusSelectedCell();
    // });
}

const runCell = (cell?: string | IBeakerCell) => {
    // beakerNotebookRef.value.runCell(cell);
    session
}

const removeCell = () => {
    // beakerNotebookRef.value.removeCell();
    session
    // session.notebook.removeCell(selectedCellIndex.value);

    // // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    // if (cellCount.value === 0) {
    //     session.addCodeCell("");
    // }
    // // Fixup the selection if we remove the last item.
    // if (selectedCellIndex.value >= cellCount.value) {
    //     selectedCellIndex.value = cellCount.value - 1;
    // }
};

const resetNB = async () => {
    await session.reset();
};

</script>


<style lang="scss">
.beaker-toolbar {
    padding: 0.25rem 0.5rem;
}
</style>
