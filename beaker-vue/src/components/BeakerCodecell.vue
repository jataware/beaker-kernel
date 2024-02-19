<template>
    <div
        class="code-cell"
        :class="{busy: isBusy}"
    >
        <div class="code-cell-grid">
            <div
                class="draggable"
                :class="{'drag-disabled': props.session.notebook.cells.length <= 1}"
                draggable="true"
                :onDrag="handleDrag"
                :onDragEnd="handleDrop"
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
import { defineProps, ref, computed } from "vue";
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
    console.log('handling drag for', event);
  // const selectedItem = item.target,
  //       list = selectedItem.parentNode,
    const x = event.clientX;
    const y = event.clientY;
  
  // selectedItem.classList.add('drag-sort-active');
  // let swapItem = document.elementFromPoint(x, y) === null ? selectedItem : document.elementFromPoint(x, y);
  
  // if (list === swapItem.parentNode) {
  //   swapItem = swapItem !== selectedItem.nextSibling ? swapItem : swapItem.nextSibling;
  //   list.insertBefore(selectedItem, swapItem);
  // }
}

function handleDrop(item) {
    console.log('handle drop for', item);
  // item.target.classList.remove('drag-sort-active');
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

</style>
