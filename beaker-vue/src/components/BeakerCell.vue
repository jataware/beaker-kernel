<template>
  <div
    class="beaker-cell"
    :draggable="dragEnabled"
    :class="{
        'drag-target': isCurrentTarget
    }"
    :onDragstart="handleDragStart"
    :onDrop="handleDrop"
    :onDragover="handleDragOver"
    :onDragleave="handleDragLeave"
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
        <DraggableMarker />
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
import DraggableMarker from './DraggableMarker';
import BeakerCodeCell from './BeakerCodecell.vue';
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

const isCurrentTarget = ref(false);
const beakerCellRef = ref(null);
const typedCellRef = ref(null);
const dragEnabled = computed(() => props.cellCount > 1);

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

function focusEditor() {
    if (beakerCellRef.value) {
        const editor = beakerCellRef.value.querySelector('.cm-content');
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
function handleDrop(item) {

    isCurrentTarget.value = false;
    const allowedDropArea = event.target.closest('.drag-sort-enable');

    if (!allowedDropArea) {
        return;
    }

    const movedIndex = event.dataTransfer.getData('cellIndex');
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
 **/
function handleDragStart(event, item) {
    event.dataTransfer.dropEffect = 'move';
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('cellID', props.cell.id);
    event.dataTransfer.setData('cellIndex', props.index);
}

/**
 * Handles when dragging over a valid drop target
 * Both appends class to cell to mark placement of dragged cell if dropped there.,
 * as well as preventing the animation where the dragged cell animates back to
 * its place when dropped into a proper target.
 **/
function handleDragOver(event) {
    isCurrentTarget.value = true;
    event.preventDefault(); // necessary
}

/* Ensure to remove class to cell being dragged over */
function handleDragLeave(event) {
    isCurrentTarget.value = false;
}

</script>

<style lang="scss">

.beaker-cell {
    padding: 1rem 0 1rem 0.3rem;
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

    grid-template-columns: 1.5rem auto;
}

.cell-contents {
  grid-area: cell-contents;
}

.drag-handle {
  grid-area: drag-handle;
  width: 1.5rem;

  .draggable-wrapper {
    height: 4rem;

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
