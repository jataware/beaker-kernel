<template>
    <Toolbar class="toolbar beaker-toolbar">
        <template #start>
            <slot name="start">
                <Button
                    @click="notebook.insertCellAfter()"
                    icon="pi pi-plus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="notebook.removeCell()"
                    icon="pi pi-minus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="notebook.selectedCell.execute()"
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
import { IBeakerCell, BeakerBaseCell, BeakerSession, BeakerNotebook } from 'beaker-kernel';
import BeakerNotebookComponent from './BeakerNotebook.vue';

import Button from "primevue/button";
import Toolbar from "primevue/toolbar";

import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";
// import { addCellAfter, enterCell, executeCell, findCellById, removeCell as removeOp } from "@/util/operations";
import * as Operations from "@/util/operations"

const session: BeakerSession = inject('session');
const notebook: typeof BeakerNotebookComponent = inject('notebook');


const addCell = (toIndex) => {
    const newCell = session.addCodeCell("");
    notebook.selectCell(newCell);
}

const addCodeCell = (toIndex?: number) => {
    const newCell = session.addCodeCell("");
    notebook.selectCell(newCell);
}

const addMarkdownCell = (toIndex?: number) => {
    const newCell = session.addMarkdownCell("");
    notebook.selectCell(newCell);
}

const runCell = (cell?: string | IBeakerCell) => {
    // if (cell !== undefined) {
    //     if (typeof cell === "string") {
    //         // cell = Operations.findCellById(notebook.beakerSession, cell);
    //     }
    //     else if (typeof cell?.id === "string") {
    //         cell = cell.id;
    //     }
    // }
    // else {
    //     cell = notebook.selectedCellId;
    // }
    // if (!cell) {
    //     // No cell passed in or selected, so do nothing.
    //     return;
    // }

    notebook.selectedCell.execute();
}

const removeCell = () => {
    if (!notebook.selectedCell) {
        return;
    }
    // if (session.notebook.cells.includes(notebook.selectedCell))
    const cellIdx = session.notebook.cells.indexOf(notebook.selectedCell.cell);
    console.log({cellIdx});
    if (cellIdx >= 0) {
        session.notebook.cells.splice(cellIdx, 1);
    }

    if (notebook.cellCount <= 0) {
        notebook.selectCell(session.addCodeCell(""));
    }
};

const resetNotebook = async () => {
    notebook.selectNextCell();

    // await session.reset();
    // if (notebook.cellCount <= 0) {
    //     notebook.selectCell(session.addCodeCell(""));
    // }
};

</script>


<style lang="scss">
.beaker-toolbar {
    padding: 0.25rem 0.5rem;
}
</style>
