<template>
    <div
        class="cell-container drag-sort-enable"
        ref="cellsContainerRef"
    >
        <BeakerCell
            v-for="(cell) in codeCells"
            :cell="cell"
            :selected="cell.id === notebook.selectedCellId"
            :index="session.notebook.cells.indexOf(cell)"
            :key="`outercell-${cell.id}`"
            class="beaker-cell"
            :class="{
                selected: (cell.id === notebook.selectedCellId),
                'drag-source': (session.notebook.cells.indexOf(cell) == dragSourceIndex),
                'drag-above': (session.notebook.cells.indexOf(cell) === dragOverIndex && session.notebook.cells.indexOf(cell) < dragSourceIndex),
                'drag-below': (session.notebook.cells.indexOf(cell) === dragOverIndex && session.notebook.cells.indexOf(cell) > dragSourceIndex),
                // TODO below was auto activating because queries/thoughts are apart from their
                // corresponding event code cells.
                // 'drag-itself': (session.notebook.cells.indexOf(cell) === dragOverIndex && session.notebook.cells.indexOf(cell) === dragSourceIndex ),
                'drag-active': isDragActive,
            }"
            :drag-enabled="isDragEnabled"
            @move-cell="handleMoveCell"
            @dragstart="handleDragStart($event, cell, session.notebook.cells.indexOf(cell))"
            @drop="handleDrop($event, session.notebook.cells.indexOf(cell))"
            @dragover="handleDragOver($event, cell, session.notebook.cells.indexOf(cell))"
            @dragend="handleDragEnd"
        >
            <component
                :is="cellMap[cell.cell_type]"
                :cell="cell"
            />
        </BeakerCell>
        <div
            class="drop-overflow-catcher"
            @dragover="dragOverIndex = session.notebook.cells.length-1; $event.preventDefault();"
            @drop="handleDrop($event, session.notebook.cells.length-1)"
        >
            <slot name="notebook-background" />
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, inject, computed, defineExpose, defineEmits, toRaw } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';
import BeakerCell from '../cell/BeakerCell.vue';
import { type BeakerNotebookComponentType } from './BeakerNotebook.vue';

const session = inject<BeakerSession>('session');
const cellMap = inject("cell-component-mapping");
const notebook = inject<BeakerNotebookComponentType>("notebook");

const cellsContainerRef = ref(null);
const isDragActive = ref(false);
const dragSourceIndex = ref(-1);
const dragOverIndex = ref(-1);
const isDragEnabled = computed(() => session.notebook?.cells.length > 1);

// New computed property that filters cells to only show code cells
const codeCells = computed(() => {
    console.log("session.notebook.cells", session.notebook.cells.map(cell => toRaw(cell)));
    
    // First get all top-level code cells
    const topLevelCodeCells = session.notebook.cells.filter(cell => cell.cell_type === "code");
    
    // Then get all code cells that are children of query cells
    const queryChildrenCodeCells = session.notebook.cells
        .filter(cell => cell.cell_type === "query" && Array.isArray(cell.children))
        .flatMap(queryCell => queryCell.children.filter(childCell => childCell.cell_type === "code")
            // .map(childCell => { childCell.parent = ""; return childCell;})
        );

    let res = [...topLevelCodeCells, ...queryChildrenCodeCells];
    console.log("code cells", res);
    
    // Combine both arrays
    return res;
});

const emit = defineEmits([]);


/**
 * Modifies array in place to move a cell to a new location (or any other elem)
 **/
function arrayMove(arr, old_index, new_index) {
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}

function handleMoveCell(fromIndex, toIndex) {
    arrayMove(session.notebook.cells, fromIndex, toIndex)
}

/**
 * Sets call to item being moved
 * As well as dataTransfer so that drop target knows which one was dropped
 **/
function handleDragStart(event: DragEvent, beakerCell, index)  {
    if (event.target instanceof HTMLElement && event.dataTransfer !== null && event.target.matches(".drag-handle *")) {
        var paintTarget = event.target.closest('.beaker-cell');

        event.dataTransfer.dropEffect = 'move';
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('x-beaker/cell', JSON.stringify({
            id: beakerCell.id,
            index: index,
        }));
        if (paintTarget !== null) {
            event.dataTransfer.setDragImage(paintTarget, 0, 0);
        }
        isDragActive.value = true;
        dragSourceIndex.value = index;
    }
}

/**
 * Handles when dragging over a valid drop target
 * Both appends class to cell to mark placement of dragged cell if dropped there.,
 * as well as preventing the animation where the dragged cell animates back to
 * its place when dropped into a proper target.
 **/
function handleDragOver(event: DragEvent, beakerCell, index) {
    if (event?.dataTransfer?.types.includes("x-beaker/cell")) {
        dragOverIndex.value = index;
        event.preventDefault(); // Allow dropping
    }
}

/**
 * Handles reordering of cells if dropped within the sort-enabled cells area.
 **/
function handleDrop(event: DragEvent, index) {

    const target = event.target as HTMLElement;
    const allowedDropArea = target.closest('.drag-sort-enable');

    // console.log("handleDrop", event, index, allowedDropArea);

    let useIndex = index < 0 ? 0 : index;

    if (!allowedDropArea) {
        return;
    }

    const cellData = JSON.parse(event.dataTransfer?.getData('x-beaker/cell') || 'null');
    const sourceId = cellData.id;
    const sourceIndex = cellData.index;
    const targetId = session.notebook.cells[useIndex].id

    if (sourceId !== targetId){
        arrayMove(session.notebook.cells, sourceIndex, useIndex);
    }
}

function handleDragEnd() {
    isDragActive.value = false;
    dragOverIndex.value = -1;
    dragSourceIndex.value = -1;
}


function scrollBottomCellContainer(event) {
    if (cellsContainerRef.value) {
        cellsContainerRef.value.scrollTop = cellsContainerRef.value.scrollHeight;
    }
}


defineExpose({
    scrollBottomCellContainer,
});

</script>

<style lang="scss">
.cell-container {
    position: relative;
    flex: 1;
    background-color: var(--surface-a);
    z-index: 3;
    overflow: auto;
    width: 100%;
    height: 100%;

    // Separators between cells
    > .beaker-cell {
        padding-top: 2px;
        border-collapse: separate;

    }
}

.drop-overflow-catcher {
    flex: 1;
}

</style>
