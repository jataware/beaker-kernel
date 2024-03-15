<template>
  <div
    class="cell-container drag-sort-enable"
    ref="cellsContainerRef"
  >
    <Cell
      v-for="(cell, index) in session.notebook.cells"
      :key="cell.id"
      class="beaker-cell"
      :class="{
        'drag-source': (index == dragSourceIndex),
        'drag-above': (index === dragOverIndex && index < dragSourceIndex),
        'drag-below': (index === dragOverIndex && index > dragSourceIndex),
        'drag-itself': (index === dragOverIndex && index === dragSourceIndex ),
        'drag-active': isDragActive,
        'selected': index === props.selectedCellIndex
      }"
      :cell="cell"
      @click="props.selectCell(index)"
      @move-cell="handleMoveCell"
      @keyboard-nav="handleNavAction"
      :drag-enabled="isDragEnabled"
      @dragstart="handleDragStart($event, cell, index)"
      @dragover="handleDragOver($event, cell, index)"
      @drop="handleDrop($event, index)"
      @dragend="handleDragEnd"
      :ref="(el) => {setSelectedRef(el, index === props.selectedCellIndex)}"
    />
    <div
      class="drop-overflow-catcher"
      @dragover="dragOverIndex = session.notebook.cells.length - 1; $event.preventDefault();"
      @drop="handleDrop($event, session.notebook.cells.length - 1)"
    >
      <slot name="notebook-background" />
    </div>
  </div>
</template>

<script setup>
import { ref, inject, computed, nextTick, defineProps, defineExpose } from 'vue';
import Cell from './UICell.vue';
import { focusSelectedCell } from './common.ts';

const session = inject('session');

const props = defineProps([
    'selectCell',
    'selectedCellIndex'
]);

const cellsContainerRef = ref(null);
const selectedCellRef = ref(null);
const isDragActive = ref(false);
const dragSourceIndex = ref(-1);
const dragOverIndex = ref(-1);
const isDeleteprefixActive = ref(false);

const isDragEnabled = computed(() => session.notebook?.cells.length > 1);
const cellCount = computed(() => session.notebook?.cells?.length || 0);

function setSelectedRef(el, selected) {
    if (selected) {
        selectedCellRef.value = el;
    }
}

function executeSelectedCell() {
    selectedCellRef.value.execute();
}

/**
 * Modifies array in place to move a cell to a new location (or any other elem)
 **/
function arrayMove(arr, old_index, new_index) {
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}

// TODO move selectCellByObj, addCell, removeCell to common fns file
//      this is repeated in NotebookControls
//      Alternatively, expose these actions from lib/BeakerSession
function selectCellByObj(cellObj) {
  const index = session.notebook.cells.indexOf(cellObj);
  props.selectCell(index);
}

const addCell = (toIndex) => {
    const newCell = session.addCodeCell("");

    if (typeof toIndex === 'number') {
        // Move cell to indicated index
        arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)
    }

    selectCellByObj(newCell);

    // Ensure cell is focused, not the editor or contents within
    nextTick(() => {
        focusSelectedCell();
    });
}

const removeCell = () => {
    session.notebook.removeCell(props.selectedCellIndex);

    // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    if (cellCount.value === 0) {
        session.addCodeCell("");
    }

    // Fixup the selection if we remove the last item.
    if (props.selectedCellIndex >= cellCount.value) {
      props.selectCell(cellCount.value - 1);
    }
};

const commonSelectAction = (event) => {
    const { target } = event;

    const isEditingCode = target.className === 'cm-content'; // codemirror
    const isTextArea = target.className.includes('resizeable-textarea');

    if (isEditingCode || isTextArea) {
        return false;
    }

    return true;
};


const selectNextCell = (event) => {
    if (event && !commonSelectAction(event)) {
        return;
    }

    const currentIndex = props.selectedCellIndex;
    if (currentIndex === cellCount.value - 1) {
        return;
    }
    props.selectCell(currentIndex + 1);

    nextTick(() => {
        focusSelectedCell();
    });

    if (event) {
        event.preventDefault();
    }
};

const selectPreviousCell = (event) => {

    if (event && !commonSelectAction(event)) {
        return;
    }

    const currentIndex = props.selectedCellIndex;
    if (currentIndex === 0) {
        return;
    }
    props.selectCell(currentIndex - 1);

    nextTick(() => {
        focusSelectedCell();
    });

    if (event) {
        event.preventDefault();
    }
};

function handleMoveCell(fromIndex, toIndex) {
    arrayMove(session.notebook.cells, fromIndex, toIndex)
    props.selectCell(toIndex);
}

/**
 * Sets call to item being moved
 * As well as dataTransfer so that drop target knows which one was dropped
 **/
function handleDragStart(event, beakerCell, index)  {
    if (event.dataTransfer !== null) {

        var paintTarget = event.target.closest('.beaker-cell');

        event.dataTransfer.dropEffect = 'move';
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('cellID', beakerCell.id);
        event.dataTransfer.setData('cellIndex', index.toString());
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
function handleDragOver(event, beakerCell, index) {
    dragOverIndex.value = index;
    event.preventDefault(); // Allow dropping
}

/**
 * Handles reordering of cells if dropped within the sort-enabled cells area.
 **/
function handleDrop(event, index) {

    const target = event.target;
    const allowedDropArea = target.closest('.drag-sort-enable');

    if (!allowedDropArea) {
        return;
    }

    const sourceId = event.dataTransfer?.getData("cellID");
    const sourceIndex =  Number.parseInt(event.dataTransfer?.getData("cellIndex") || "-1");
    const targetId = session.notebook.cells[index].id

    if (sourceId !== targetId){
        arrayMove(session.notebook.cells, sourceIndex, index);
    }
}

function handleDragEnd() {
    isDragActive.value = false;
    dragOverIndex.value = -1;
    dragSourceIndex.value = -1;
}


/**
 * Parses emits by other child components to follow commands that the notebook
 * controls.
 **/
function handleNavAction(action) {
    // TODO types
    if (action === 'focus-cell') {
        focusSelectedCell();
    } else if (action === 'select-next-cell') {
        if (props.selectedCellIndex === cellCount.value - 1) {
            addCell();
        } else {
            selectNextCell();
        }
    }
}

function handleKeyboardShortcut(event) {

    if ('Enter' === event.key && !event.shiftKey && !event.ctrlKey) {
        focusSelectedCell();
        return;
    }

    if (['ArrowDown', 'j', 'J'].includes(event.key)) {
        selectNextCell();
    } else if (['ArrowUp', 'k', 'K'].includes(event.key)) {
        selectPreviousCell();
    }

    if (['b', 'B'].includes(event.key)) {
        addCell(props.selectedCellIndex + 1);
    } else if (['a', 'A'].includes(event.key)) {
        let prevIndex = props.selectedCellIndex;
        addCell(prevIndex);
    }

    if (['d', 'D'].includes(event.key)) {
        if (isDeleteprefixActive.value) {
            isDeleteprefixActive.value = false;
            removeCell();
            nextTick(() => {
                focusSelectedCell();
            })
        } else {
            isDeleteprefixActive.value = true;
         }
    } else {
        isDeleteprefixActive.value = false;
    }
}

function scrollBottomCellContainer(event) {
    if (cellsContainerRef.value) {
        cellsContainerRef.value.scrollTop = cellsContainerRef.value.scrollHeight;
    }
}


defineExpose({handleKeyboardShortcut, scrollBottomCellContainer, executeSelectedCell});

</script>

<style lang="scss">
.cell-container {
    display: flex;
    // flex: 1;
    flex-direction: column;
    background-color: var(--surface-a);
}

</style>
