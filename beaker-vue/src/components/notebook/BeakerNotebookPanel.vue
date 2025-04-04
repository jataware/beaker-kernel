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
            :has-error="cell.hasError"
            :code-cell-that-retries-id="cell.codeCellThatRetriesID"
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
                'deprecated': cell.codeCellThatRetriesID !== undefined
            }"
            :drag-enabled="isDragEnabled"
            @move-cell="handleMoveCell"
            @dragstart="handleDragStart($event, cell, session.notebook.cells.indexOf(cell))"
            @drop="handleDrop($event, session.notebook.cells.indexOf(cell))"
            @dragover="handleDragOver($event, cell, session.notebook.cells.indexOf(cell))"
            @dragend="handleDragEnd"
        >
            <!-- Add pagination controls if cell has children -->
            <div v-if="cell.children && cell.children.length > 0" class="cell-pagination-controls">
                <div class="cell-version-selector">
                    <span>Version: </span>
                    <select v-model="cellVersions[cell.id]" @change="handleVersionChange(cell)">
                        <option value="current">Current</option>
                        <option v-for="(childCell, index) in cell.children" :key="childCell.id" :value="index">
                            Previous {{ index + 1 }}
                        </option>
                    </select>
                </div>
                <div class="cell-navigation-buttons">
                    <button 
                        class="nav-button" 
                        @click="navigateVersion(cell, 'prev')" 
                        :disabled="false">
                        ← Previous
                    </button>
                    <button 
                        class="nav-button" 
                        @click="navigateVersion(cell, 'next')"
                        :disabled="isLatestVersion(cell)">
                        Next →
                    </button>
                </div>
                <div class="debug-info" style="font-size: 10px; color: #999;">
                    Current version: {{ cellVersions[cell.id] }}<br>
                    Current cell ID: {{ getCurrentCellVersion(cell).id }}
                </div>
            </div>
            <component
                :is="cellMap[getCurrentCellVersion(cell).cell_type]"
                :cell="getCurrentCellVersion(cell)"
                :key="`cell-component-${cell.id}-${cellVersions[cell.id]}`"
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
import { ref, inject, computed, defineExpose, defineEmits, toRaw, watch } from 'vue';
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
const cellVersions = ref({}); // Stores the currently displayed version for each cell

function failedChildOfACodeCell(cc, queryCells) {
    // correct version:
    // if (cc.outputs.length > 0 && cc.outputs.every(output => output.output_type === "error")) {
    // changing to "some", which will be less accurate, for testing:
    if (cc.outputs.length > 0 && cc.outputs.some(output => output.output_type === "error" || output.name === "stderr")) {
        //
        console.log("found a code cell with error, id:", cc.id);

        // find index of cc.id in session.notebook.cells
        const parentQueryCell = queryCells.find(qc => {
            return qc.children.find(child => child.id === cc.id)
        });
        console.log("parentQueryCell", toRaw(parentQueryCell));

        const thisCellEventIndex = parentQueryCell.events.findIndex(evt => evt.content.cell_id === cc.id);
        console.log("thisCellEventIndex", thisCellEventIndex);

        const posibilityOfRetry = thisCellEventIndex < parentQueryCell.events.length - 2;
        if (posibilityOfRetry) {
            console.log("posibilityOfRetry!");
            const nextThoughtEventIndex = thisCellEventIndex + 1;
            const nextEvent = parentQueryCell.events[nextThoughtEventIndex];
            console.log("nextEvent...", toRaw(nextEvent));
            if (nextEvent.type === "thought") {
                console.log("nextEvent is a thought event");
                const failedOps = ["retry", "failed", "error", "try again", "issue", "modify our code", "modify our approach", "modify our strategy", "modify our method", "modify our technique", "modify our approach", "modify our strategy", "modify our method", "modify our technique"];


                nextEvent.content.thought

                if (failedOps.some(op => nextEvent.content.thought.includes(op))) {
                    console.log("found a thought cell with error text:", nextEvent.content.thought);
                    // this is enough to "mark" it for debuggig purposes
                    // now, lets see if the next code cell is a retry
                    const nextCodeCellEvent = parentQueryCell.events[nextThoughtEventIndex + 1];
                    console.log("nextCodeCell...?", toRaw(nextCodeCellEvent));
                    if (nextCodeCellEvent.type === "code_cell") {
                        console.log("found a nextCodeCell, marking as retry...");
                        // cc.codeCellThatRetriesID = nextCodeCellEvent.content.cell_id;
                        return nextCodeCellEvent.content.cell_id;
                    }
                }
            }
        }
    }
    return null;
}

// New computed property that filters cells to only show code cells
const codeCells = computed(() => {
    // console.log("session.notebook.cells", session.notebook.cells.map(cell => toRaw(cell)));
    
    // First get all top-level code cells
    const topLevelCodeCells = session.notebook.cells.filter(cell => cell.cell_type === "code");
    
    // Then get all code cells that are children of query cells
    const queryCells = session.notebook.cells
        .filter(cell => cell.cell_type === "query" && Array.isArray(cell.children))

    // mapping of parent to child
    const childCellMap = {
        // "parentID": "childID",
    };

    let queryChildrenCodeCells = queryCells
        .flatMap(queryCell => queryCell.children.filter(childCell => childCell.cell_type === "code")
        .map(cc => {
            const nextCodeId = failedChildOfACodeCell(cc, queryCells);
            if (nextCodeId) {
                cc.codeCellThatRetriesID = nextCodeId;
                childCellMap[nextCodeId] = cc.id;
                // somehow we have to find next code cell, and add a child cell to it...
            }
            return cc;
        }));

    if (Object.keys(childCellMap).length > 0) {
       queryChildrenCodeCells = queryChildrenCodeCells.map(cc => {
            if (childCellMap[cc.id]) { // if entry
                const childCell = queryChildrenCodeCells.find(ca => ca.id === childCellMap[cc.id]);
                if (childCell && !cc.children.find(c => c.id === childCell.id)) {
                    cc.children.push(childCell);
                }
            }
            return cc;
        });
    }
    
    // console.log("childCellMap", childCellMap);

    // Combine both arrays
    let res = [...topLevelCodeCells, ...queryChildrenCodeCells];

    console.log("res", res.map(cell => toRaw(cell)));
    
    return res;
});

// Initialize cell versions
function initializeCellVersions() {
  codeCells.value.forEach(cell => {
    if (cell.children && cell.children.length > 0 && !cellVersions.value[cell.id]) {
      cellVersions.value[cell.id] = 'current';
    }
  });
}

// Watch for changes in codeCells and initialize versions
// This ensures new cells with children get initialized properly
watch(codeCells, () => {
  initializeCellVersions();
}, { immediate: true });

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

// Get the current version of the cell to display (parent or one of its children)
function getCurrentCellVersion(cell) {
    console.log('getCurrentCellVersion called for cell:', cell.id);
    console.log('cellVersions for this cell:', cellVersions.value[cell.id]);
    
    if (!cell.children || 
        cell.children.length === 0 || 
        cellVersions.value[cell.id] === undefined || 
        cellVersions.value[cell.id] === null ||
        cellVersions.value[cell.id] === 'current') {
        console.log('Returning parent cell');
        return cell;
    }
    
    const childIndex = parseInt(cellVersions.value[cell.id]);
    console.log('Returning child cell at index:', childIndex);
    console.log('Child cell:', cell.children[childIndex]);
    return cell.children[childIndex] || cell;
}

// Check if the current version is the latest (current) version
function isLatestVersion(cell) {
    return cellVersions.value[cell.id] === 'current';
}

// Navigate between versions (previous/next)
function navigateVersion(cell, direction) {
    console.log('navigateVersion called:', direction, 'for cell:', cell.id);
    console.log('Current version:', cellVersions.value[cell.id]);
    
    if (!cell.children || cell.children.length === 0) return;
    
    // Initialize if not set
    if (cellVersions.value[cell.id] === undefined || cellVersions.value[cell.id] === null) {
        cellVersions.value[cell.id] = 'current';
    }
    
    if (direction === 'prev') {
        if (cellVersions.value[cell.id] === 'current') {
            // From current to last child
            cellVersions.value[cell.id] = cell.children.length - 1;
        } else {
            // Between child versions
            const currentIndex = parseInt(cellVersions.value[cell.id]);
            cellVersions.value[cell.id] = currentIndex > 0 ? (currentIndex - 1).toString() : 'current';
        }
    } else if (direction === 'next') {
        if (cellVersions.value[cell.id] === 'current') {
            // Already at current, can't go further
            return;
        } else {
            // Between child versions
            const currentIndex = parseInt(cellVersions.value[cell.id]);
            if (currentIndex < cell.children.length - 1) {
                cellVersions.value[cell.id] = (currentIndex + 1).toString();
            } else {
                cellVersions.value[cell.id] = 'current';
            }
        }
    }
    
    console.log('New version after navigation:', cellVersions.value[cell.id]);
    
    // Force component update by creating a new reference
    cellVersions.value = { ...cellVersions.value };
}

// Handle direct selection from dropdown
function handleVersionChange(cell) {
    console.log('handleVersionChange called for cell:', cell.id);
    console.log('New version selected:', cellVersions.value[cell.id]);
    
    // Force component update
    cellVersions.value = { ...cellVersions.value };
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

.deprecated {
    display: none;
    // opacity: 0.4;
}

.cell-pagination-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 8px;
    background-color: var(--surface-b);
    border-bottom: 1px solid var(--surface-d);
    margin-bottom: 8px;
}

.cell-version-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    
    select {
        padding: 2px 4px;
        border-radius: 4px;
        border: 1px solid var(--surface-d);
        background-color: var(--surface-a);
    }
}

.cell-navigation-buttons {
    display: flex;
    gap: 8px;
    
    .nav-button {
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid var(--surface-d);
        background-color: var(--surface-a);
        cursor: pointer;
        
        &:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        &:not(:disabled):hover {
            background-color: var(--surface-b);
        }
    }
}

</style>
