<template>

<!--
    @row-dragstart="onRowDragStart($event)"
    @row-dragover="onRowDragOver($event)"
    @row-dragleave="onRowDragLeave($event)"
    @row-dragend="onRowDragEnd($event)"
    @row-drop="onRowDrop($event)"
-->

    <div
        class="code-cell"
        draggable="true"
        :class="{
            busy: isBusy,
            'drag-active': isDragActive,
            'drag-over-bottom': isDragActiveBottom,
            'drag-over-top': isDragActiveTop
        }"
        :onDrag="handleDrag"
        :onDragstart="handleDragStart"
        :onDragover="handleDragOver"
        :onDragenter="handleDragEnter"
        :onDragleave="handleDragLeave"
        :onDragend="handleDragEnd"
        :onDrop="handleDrop"
    >
        <div class="code-cell-grid">
            <div
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
import { defineProps, ref, computed, provide, inject } from "vue";
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
    "selected"
]);

const cell = ref(props.cell);
const isBusy = ref(false);
const isDragActive = ref(false);
const isDragActiveTop = ref(false);
const isDragActiveBottom = ref(false);

const cellDragId = inject('cell_drag_id');

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

function handleDrag(event) {

    // console.log('handling drag for', event);

    // const selectedItem = event.target;
    //                     // event.currentTarget

    // const parentList = document.querySelector('.drag-sort-enable');
    // const x = event.clientX;
    // const y = event.clientY;
    // // let rowY = DomHandler.getOffset(rowElement).top + DomHandler.getWindowScrollTop();

    // // isDragActive.value = true;
  
    // // selectedItem.classList.add('drag-sort-active');
    // let swapItem = document.elementFromPoint(x, y) === null ? selectedItem : document.elementFromPoint(x, y);

    // // console.log('swapItem', swapItem);

    // // if (parentList === swapItem.parentNode) {
    // swapItem = swapItem !== selectedItem.nextSibling ? swapItem : swapItem.nextSibling;

    // console.log('swapItem')
    //   list.insertBefore(selectedItem, swapItem);
    // }
}

function handleDrop(item) {

    // closest target when we dropped
    const selectedCellElement = event.target.closest('.code-cell');
    // id for item we dropped on
    // const selectedCellID =  selectedCellElement.dataset.cellid;

    const parentContainer = selectedCellElement.closest('.drag-sort-enable');

    console.log('droppable parent container', parentContainer);

    if (!parentContainer) {
        console.log('dropped outside list boundaries. not re-ordering');
        return;
    }

    // console.log('selectedCellElement (drop target)', selectedCellElement);

    // event.currentTarget
    // const x = event.clientX;
    // const y = event.clientY;
    // let swapItemID = document.elementFromPoint(x, y) === null ? selectedCellID : document.elementFromPoint(x, y).closest('.code-cell').dataset.cellid;

    // console.log('dropped cell id', selectedCellID);
    // console.log('swap item', swapItemID); // id

    const selfID = cell.value.id;

    console.log('dropped dragged cell id', selfID);

    console.log('cellDragId', cellDragId);

    const currentCells = props.session.notebook.cells;
    const draggedIndex = currentCells.findIndex((candidateCell) => candidateCell.id === cellDragId);
    const droppedIndex = currentCells.findIndex((cellItem) => cellItem.id === selfID);

    // console.log('currentIndex', draggedIndex);
    console.log('dropped index', droppedIndex);
    console.log('dragging index', draggedIndex);


    // currentCells.insertBefore(selectedItem, swapItem);

    // currentCells.sort((cellA, cellB) => {
    //     const nameA = cellA.id.toUpperCase(); // ignore upper and lowercase
    //     const nameB = cellB.id.toUpperCase(); // ignore upper and lowercase

    //     if (nameA < nameB) {
    //         return -1;
    //     }
    //     if (nameA > nameB) {
    //     return 1;
    //     }      
    //     return 0;
    // });

}

function handleDragStart(event) {
    // console.log('handleDragStart', event);

    isDragActive.value = true;
    provide('cell_drag_id', cell.value.id);
}

function handleDragOver(event) {
    // console.log('handleDragOver', event);
    event.preventDefault();
}

function handleDragEnter(event) {
    console.log('handleDragEnter', event);

    isDragActiveTop.value = true;
}

function handleDragLeave(event) {
    // console.log('handleDragLeave', event);

    isDragActiveBottom.value = true;
}

function handleDragEnd(event) {
    console.log('handleDragEnd', event);
    isDragActive.value = false;
    event.preventDefault();
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

.draggable {
    grid-area: draghandle;
}

.busy {
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

.draggable.drag-sort-active {
    background: transparent;
    color: transparent;
    border: 2px solid var(--primary-color);
    // TODO possibly decrease height
}
.sorter-span.drag-sort-active {
    background: transparent;
    color: transparent;
}

.drag-active {
    outline: 1px solid red;
    // &::after {
    //     content: "";
    //     width: 100%;
    //     border: 1px solid blue;
    //     height: 2px;
    // }
}

.drag-over-bottom {
    border-bottom: 1px solid red;
}

.drag-over-top {
    border-top: 1px solid cyan;
}

</style>
