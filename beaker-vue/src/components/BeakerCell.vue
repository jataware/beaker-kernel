<template>
  <div
    class="beaker-cell"
    :class="{
        'drag-target': isCurrentTarget
    }"
    @dragstart="handleDragStart"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    tabindex="0"
    @keyup.enter.exact="focusEditor"
    @keydown.ctrl.enter.prevent="execute"
    @keydown.shift.enter.prevent="executeAndMove"
    @keyup.esc="unfocusEditor"
    ref="beakerCellRef"
  >
    <div class="cell-grid">
      <div
        class="drag-handle"
        :class="{
            'drag-disabled': !dragEnabled,
        }"
      >
        <DraggableMarker
            :draggable="dragEnabled"
        />
      </div>

      <div class="cell-contents">
        <Component
            :is="componentMap[props.cell.cell_type || 'raw']"
            :cell="props.cell"
            ref="typedCellRef"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed, defineEmits, Component } from "vue";
import DraggableMarker from './DraggableMarker.vue';
import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerMarkdownCell from './BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';

const props = defineProps([
    'index',
    'cell',
    'cellCount',
]);

const emit = defineEmits([
    'move-cell',
    'keyboard-nav'
]);

type BeakerCellType = typeof BeakerCodeCell | typeof BeakerLLMQueryCell | typeof BeakerMarkdownCell;

const isCurrentTarget = ref(false);
const beakerCellRef = ref<HTMLDivElement|null>(null);
const typedCellRef = ref<BeakerCellType|null>(null);
const dragEnabled = computed(() => props.cellCount > 1);

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
    'markdown': BeakerMarkdownCell
}

function focusEditor() {
    if (beakerCellRef.value) {
        const editor: HTMLElement|null = beakerCellRef.value.querySelector('.cm-content');
        if (editor) {
            editor.focus();
        }
    }
}

const unfocusEditor = () => {
    if (beakerCellRef.value?.focus) {
        beakerCellRef.value.focus();
    }
};

function execute() {
    if (typedCellRef?.value?.execute) {
        typedCellRef.value.execute();
        // For code/markdown cells
        unfocusEditor();
        return true;
    }
    return false;
}

const executeAndMove = () => {
    if (execute()) {
        emit('keyboard-nav', 'select-next-cell');
    }
};

/**
 * Handles reordering of cells if dropped within the sort-enabled cells area.
 **/
function handleDrop(event: DragEvent) {

    isCurrentTarget.value = false;
    const target = (event.target as HTMLElement);
    const allowedDropArea = target.closest('.drag-sort-enable');

    if (!allowedDropArea) {
        return;
    }

    const movedIndex = event.dataTransfer?.getData('cellIndex');
    const droppedIndex = props.index;

    if (movedIndex !== droppedIndex) {
        // Modify array in place so that refs can track changes (change by reference)
        // (Don't reassign cells in notebook!)
        emit('move-cell', movedIndex, droppedIndex);
    }
}

/**
 * Sets call to item being moved
 * As well as dataTransfer so that drop target knows which one was dropped
 * TODO This handler is aware of some special Beaker app classes, since
     * it needs to disable dragging when using the cursor to select text.
     * Could accept props of disallowed classes if we want to make it generic.
 **/
function handleDragStart(event: DragEvent) {

    // const paintTarget = (event.target as HTMLElement).parentElement;
    var paintTarget: HTMLElement|null = (event.target as HTMLElement);
    while (paintTarget !== null && !paintTarget.classList.contains("beaker-cell")) {
        paintTarget = paintTarget?.parentElement;
    }

    if (event.dataTransfer !== null) {
        event.dataTransfer.dropEffect = 'move';
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('cellID', props.cell.id);
        event.dataTransfer.setData('cellIndex', props.index);
        if (paintTarget !== null) {
            event.dataTransfer.setDragImage(paintTarget, 0, 0);
        }
    }
}

/**
 * Handles when dragging over a valid drop target
 * Both appends class to cell to mark placement of dragged cell if dropped there.,
 * as well as preventing the animation where the dragged cell animates back to
 * its place when dropped into a proper target.
 **/
function handleDragOver(event: DragEvent) {
    isCurrentTarget.value = true;
    event.preventDefault(); // necessary
}

/* Ensure to remove class to cell being dragged over */
function handleDragLeave(event: DragEvent) {
    isCurrentTarget.value = false;
}

</script>

<style lang="scss">

.beaker-cell {
    padding: 1rem 0 1rem 0.2rem;
    border-right: 5px solid transparent;
    background-color: var(--surface-a);
    border-bottom: 4px solid var(--surface-c);

    &.selected {
      border-right: 5px solid var(--purple-400);
      border-top: unset;
      background-color: var(--surface-ground);
    }

    &:focus {
        outline: none;
    }
}

.cell-grid {
    display: grid;

    grid-template-areas:
        "drag-handle cell-contents";

    grid-template-columns: 1.4rem auto;
}

.cell-contents {
  grid-area: cell-contents;
}

.drag-handle {
  grid-area: drag-handle;
  margin-left: auto;
  margin-right: auto;

  .draggable-wrapper {
    height: 3rem;
    width: 1rem;
    background-position: 0.5rem 0.5rem;
    background-size: 0.5rem 0.5rem;

    &:hover {
        opacity: 0.9;
    }
  }
}

.drag-disabled {
    pointer-events: none;
    opacity: 0.2;
}

.drag-target {
    outline: 1px solid var(--purple-200);
    outline-offset: -1px;
    * {
        visibility: hidden;
    }
}
</style>
