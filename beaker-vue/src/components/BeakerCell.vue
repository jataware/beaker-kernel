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
    @keyup.enter="focusEditor"
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
        <slot /> <!-- children go here -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed, defineEmits } from "vue";
import DraggableMarker from './DraggableMarker';

const props = defineProps([
    "session",
    "index",
    "cellID",
    "cellCount",
]);

const emit = defineEmits([
    "move-cell"
]);

const isCurrentTarget = ref(false);
const beakerCellRef = ref(null);
const dragEnabled = computed(() => props.cellCount > 1);

function focusEditor() {
    if (beakerCellRef.value) {
        const editor = beakerCellRef.value.querySelector('.cm-content');
        if (editor) {
            editor.focus();
        }
    }
}

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
    event.dataTransfer.setData('cellID', props.cellID);
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

    grid-template-columns: 1.4rem auto;
}

.cell-contents {
  grid-area: cell-contents;
}

.drag-handle {
  grid-area: drag-handle;
  width: 20px;

  *.draggable-wrapper {
    height: 60px;

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
