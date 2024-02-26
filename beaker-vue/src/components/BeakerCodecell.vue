<template>

    <div
        class="code-cell"
        draggable="true"
        :class="{
            'drag-active': isDragActive,
            'drag-target': isCurrentTarget
        }"
        :onDragstart="handleDragStart"
        :onDrop="handleDrop"
        :onDragover="handleDragOver"
        :onDragleave="handleDragLeave"
        :onDragend="handleDragEnd"
    >
        <div class="code-cell-grid">
            <div
                class="drag-handle"
                :class="{
                    'drag-disabled': props.session.notebook.cells.length <= 1,
                }"
            >
                <DraggableMarker />
            </div>
            <div class="code-data">
                <Codemirror
                    v-model="cell.source"
                    placeholder="Your code..."
                    :extensions="codeExtensions"
                    :disabled="isBusy"
                    :autofocus="true"
                    @keydown.ctrl.enter.self.stop.prevent="execute"
                    @keydown.alt.enter="console.log('alt-enter')"
                    @keydown.shift.enter.prevent="execute"
                    @keydown.meta.enter="console.log('meta-enter')"
                />
                <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" />
            </div>
            <div class="execution-count">
                <span>
                    [{{cell.execution_count || '&nbsp;'}}]
                </span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed, defineEmits } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import DraggableMarker from './DraggableMarker';

const props = defineProps([
    "cell",
    "session",
    "contextData",
    "theme",
    "selected",
    "index"
]);

const emit = defineEmits([
    "select-cell"
]);

const cell = ref(props.cell);
const isBusy = ref(false);
const isDragActive = ref(false);
const isCurrentTarget = ref(false);


const codeExtensions = computed(() => {
    const ext = [];

    const subkernel = props?.contextData?.language?.subkernel || '';
    const isPython = subkernel.includes('python');
    if (isPython) {
        ext.push(python());
    }
    if (props.theme === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const execute = (evt: any) => {
    isBusy.value = true;

    const handleDone = async (message: any) => {

        // Timeout added to busy indicators from jumping in/out too quickly
        setTimeout(() => {
            isBusy.value = false;
        }, 1000);
    };

    evt.preventDefault();
    evt.stopPropagation();
    const future = props.cell.execute(props.session);
    future.done.then(handleDone);
}

/**
 *
 **/
function arrayMove(arr, old_index, new_index) {
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}

/**
 * Handles reordering of cells if dropped within the sort-enable area
 * that is, dropped in center area and not in sidebar/other UI sections
 **/
function handleDrop(item) {
    const parentContainer = event.target.closest('.drag-sort-enable');

    if (!parentContainer) {
        return;
    }

    const movedIndex = event.dataTransfer.getData('cellIndex');
    const droppedIndex = props.index;

    isCurrentTarget.value = false;

    if (movedIndex !== droppedIndex) {
        // Modify array in place so that refs can track changes (change by reference)
        // (Don't reassign cells in notebook!)
        arrayMove(props.session.notebook.cells, movedIndex, droppedIndex);
        emit('select-cell', droppedIndex);
    }
}

/**
 * Sets call to item being moved
 * As well as dataTransfer so that drop target knows which one was dropped
 **/
function handleDragStart(event, item) {
    isDragActive.value = true;

    event.dataTransfer.dropEffect = 'move'
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('cellID', cell.value.id);
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

/* Remove class of cell being dragged/moved */
function handleDragEnd(event) {
    isDragActive.value = false;
    event.preventDefault(); // may not be necessary
}


</script>


<style lang="scss">
.code-cell {
    padding: 1rem 0 1rem 1rem;
    &.selected {
        .execution-count {
            color: var(--green-400);
        }
    }
}

.code-cell-grid {
    display: grid;

    grid-template-areas:
        "draghandle code code code exec";

    grid-template-columns: 2.7rem 1fr 1fr 1fr auto;
}

.code-data {
    grid-area: code;
}

.drag-handle {
    grid-area: draghandle;
}

.execution-count {
    grid-area: exec;
    color: var(--text-color-secondary);
    display: flex;
    justify-content: center;
    width: 0;
    font-family: monospace;
    font-size: 1rem;    
    padding: 0 1.2rem;
}

.drag-disabled {
    pointer-events: none;
    opacity: 0.2;
}

.drag-active {
    // TODO only if we wish to mark the moved item while dragging
    // not necessary
}

.drag-over-bottom {
    border-bottom: 1px solid red;
}

.drag-over-top {
    border-top: 1px solid cyan;
}

.drag-target {
    outline: 2px solid var(--primary-color);
    * {
        visibility: hidden;
    }
}



</style>
