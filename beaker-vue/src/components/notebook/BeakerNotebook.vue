<template>
    <div class="beaker-notebook">
        <div class="controls" style="position: relative;">
            <InputGroup>
                <slot name="notebook_buttons_left">
                <Button
                    @click="addCell()"
                    icon="pi pi-plus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="removeCell()"
                    icon="pi pi-minus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="runCell()"
                    icon="pi pi-play"
                    size="small"
                    severity="info"
                    text
                />
                </slot>
            </InputGroup>
            <InputGroup style="margin-right: 1rem; position: absolute; right: 0;">
                <slot name="notebook_buttons_right">
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
                </slot>
            </InputGroup>
        </div>

        <div class="ide-cells">
            <NotebookPanel
                :selectCell="selectCell"
                :selectedCellIndex="selectedCellIndex"
                ref="beakerNotebookRef"
            >
                <template #notebook-background>
                    <transition name="fade">
                        <div class="welcome-placeholder" v-if="cellCount < 3">
                            <SvgPlaceholder />
                        </div>
                    </transition>
                </template>
            </NotebookPanel>
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, defineExpose } from "vue";
import { IBeakerCell, BeakerBaseCell, BeakerSession } from 'beaker-kernel';
import { BeakerCodeCell } from "beaker-kernel";

import Button from "primevue/button";

import NotebookPanel from '@/components/notebook/NotebookPanel.vue';
import NotebookControls from '@/components/notebook/NotebookControls.vue';
import BeakerAgentQuery from '@/components/agent/BeakerAgentQuery.vue';
import SvgPlaceholder from '@/components/misc/SvgPlaceholder.vue';
import BeakerCell from '@/components/cell/BeakerCell.vue';
import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";


// double check this import
// import { arrayMove, capitalize } from '../util';
// import { arrayMove } from "beaker-kernel/src/util"


const props = defineProps([
    "connectionStatus",
    "debugLogs",
    "rawMessages",
    "previewData",
]);

const emit = defineEmits([
    'clear-preview',
]);

// TODO info object map type
const notebookCellsRef = ref<typeof BeakerCell|null>(null);
const activeContext = ref<{slug: string, class: string, context: any, info: any} | undefined>(undefined);
const selectedCellIndex = ref("");
const selectedKernel = ref();
const contextSelectionOpen = ref(false);
const showDebugPane = ref (true);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightPaneTabIndex = ref(0);
const isDeleteprefixActive = ref(false);
const selectedTheme = ref(localStorage.getItem('theme') || 'light');
const debugTabView = ref<{tabs: any[]}|null>(null);
const selectedAction = ref<string|undefined>(undefined);
const beakerNotebookRef = ref<typeof NotebookPanel>();


const session: BeakerSession = inject('session');
const showToast = inject('show_toast');

provide('theme', selectedTheme);
provide('active_context', activeContext);

const cellCount = computed(() => session.notebook?.cells?.length || 0);

/**
 * Parses emits by other child components to follow commands that the notebook
 * controls.
 **/
function handleNavAction(action) {
    // TODO types
    if (action === 'focus-cell') {
        focusSelectedCell();
    } else if (action === 'select-next-cell') {
        if (selectedCellIndex.value === String(cellCount.value - 1)) {
            addCodeCell();
        } else {
            selectNextCell();
        }
    }
}

/**
 * Splits a combined cell index into component parts.
 * Cell indices are in the form of `"1:2"` (representing notebook cell 1, third child)
 *
 * usage: `const [parent, child] = splitCellIndex("1:2")`
 *
 * note: child will be `undefined` in the case of `const [parent, child] = splitCellIndex("1")`
 * due to assignment destructuring rules
 */
const splitCellIndex = (index: string): number[] => index.split(":").map((part) => Number(part));

const mergeCellIndex = (parent: number, child: number | undefined): string => {
    if (typeof(child) !== "undefined") {
        return `${parent}:${child}`;
    }
    return `${parent}`;
}

const getChildCount = (index: string): number => {
    const [parent, child] = splitCellIndex(index);
    return session.notebook.cells[parent]?.children?.length || 0
}

function handleMoveCell(fromIndex: number, toIndex: number) {
    //arrayMove(session.notebook.cells, fromIndex, toIndex)
    selectCell(toIndex);
}

function handleKeyboardShortcut(event) {

    const { target } = event;

    // TODO is there a better way to encapsulate cancelling events
    // when writing on textarea/input/code elements ?
    const isEditingCode = target.className === 'cm-content'; // codemirror
    const isTextArea = target.className.includes('resizeable-textarea');

    if (isEditingCode || isTextArea) {
        return;
    }

    beakerNotebookRef.value.handleKeyboardShortcut(event);
}

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const _cellIndex = (cell: number | string | IBeakerCell): string => {
    let index = "-1";
    if (typeof(cell) === "string") {
        index = cell;
    }
    if (typeof(cell) === "number") {
        index = cell.toString();
    }
    else if (cell instanceof BeakerBaseCell) {
        const notebookIndex = session.notebook.cells.indexOf(cell);
        index = notebookIndex.toString();

        // cell is within a notebook cell's children
        if (notebookIndex === -1) {
            for (const [notebookIndex, notebookCell] of session.notebook.cells.entries()) {
                const innerIndex = notebookCell?.children?.indexOf(cell);
                if (innerIndex !== -1) {
                    index = `${notebookIndex}:${innerIndex}`;
                    break;
                }
            }
        }
    }
    return index;
}


const _getCell = (cell: string | IBeakerCell): IBeakerCell => {
    const index = _cellIndex(cell);
    const [parent, child] = splitCellIndex(index);
    if (typeof(child) !== "undefined") {
        return session.notebook.cells[parent]?.children[child];
    }
    return session.notebook.cells[parent];
}

const selectCell = (cell: number | string | IBeakerCell): void => {
    let index = _cellIndex(cell);
    selectedCellIndex.value = index;
}

const commonSelectAction = (event): boolean => {
    const { target } = event;

    const isEditingCode = target.className === 'cm-content'; // codemirror
    const isTextArea = target.className.includes('resizeable-textarea');

    if (isEditingCode || isTextArea) {
        return false;
    }

    return true;
};

function focusSelectedCell() {
    if (!beakerNotebookRef.value){
        return;
    }
    const elem = beakerNotebookRef.value.querySelector('.beaker-cell.selected');
    if (typeof(elem) !== "undefined" && elem !== null) {
        elem.focus();
    }
}

const selectNextCell = (event?) => {
    if (event && !commonSelectAction(event)) {
        return;
    }

    const currentIndex = selectedCellIndex.value;
    const childCount = getChildCount(currentIndex);
    const [parent, child] = splitCellIndex(currentIndex);
    // TODO should we wrap around? Should we auto-add a new cell?
    if (parent === cellCount.value - 1) {
        return;
    }

    // since children are 0-indexed, consider a parent selector as "child -1" for purpose of incrementing
    const childIndex = typeof(child) === "undefined" ? -1 : child;
    if (childCount > 0 && childIndex < childCount - 1) {
        selectCell(`${parent}:${childIndex + 1}`);
    } else {
        selectCell(`${parent + 1}`);
    }

    nextTick(() => {
        focusSelectedCell();
    });

    if (event) {
        event.preventDefault();
    }
};

const selectPreviousCell = (event?) => {

    if (event && !commonSelectAction(event)) {
        return;
    }

    const currentIndex = selectedCellIndex.value;
    const childCount = getChildCount(currentIndex);
    const [parent, child] = splitCellIndex(currentIndex);

    if (parent === 0) {
        return;
    }

    if (childCount > 0 && child > 0) {
        selectCell(`${parent}:${child - 1}`);
    } else {
        // select last child of above cell if present
        const target = `${parent - 1}`;
        const targetChildCount = getChildCount(target);
        if (targetChildCount > 0) {
            selectCell(`${target}:${targetChildCount - 1}`)
        } else {
            selectCell(target);
        }
    }

    nextTick(() => {
        focusSelectedCell();
    });

    if (event) {
        event.preventDefault();
    }
};

const addCell = (toIndex) => {
    beakerNotebookRef.value.addCell(toIndex);
    // if (typeof toIndex !== 'number') {
    //     toIndex = selectedCellIndex.value + 1;
    // }
    // const newCell = new BeakerCodeCell({
    //     cell_type: "code",
    //     source: "",
    //     metadata: {},
    //     outputs: [],
    // });
    // session.notebook.insertCell(newCell, toIndex);

    // // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    // selectCell(newCell);

    // nextTick(() => {
    //     focusSelectedCell();
    // });
}

const addCodeCell = (toIndex?: number) => {
    const newCell = session.addCodeCell("");

    if (typeof toIndex !== 'number') {
        const [parent, child] = splitCellIndex(selectedCellIndex.value);
        toIndex = parent + 1;
    }
    // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    selectCell(newCell);

    nextTick(() => {
        focusSelectedCell();
    });
}

const addMarkdownCell = (toIndex?: number) => {
    const newCell = session.addMarkdownCell("");

    if (typeof toIndex !== 'number') {
        const [parent, child] = splitCellIndex(selectedCellIndex.value);
        toIndex = parent + 1;
    }
    // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    selectCell(newCell);

    nextTick(() => {
        notebookCellsRef.value[notebookCellsRef.value.length - 1].enter();
        focusSelectedCell();
    });
}

const runCell = (cell?: string | IBeakerCell) => {
    beakerNotebookRef.value.runCell(cell);
}

const removeCell = () => {
    beakerNotebookRef.value.removeCell();
    // session.notebook.removeCell(selectedCellIndex.value);

    // // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    // if (cellCount.value === 0) {
    //     session.addCodeCell("");
    // }
    // // Fixup the selection if we remove the last item.
    // if (selectedCellIndex.value >= cellCount.value) {
    //     selectedCellIndex.value = cellCount.value - 1;
    // }
};

const resetNB = async () => {
    await session.reset();
    if (cellCount.value === 0) {
        session.addCodeCell("");
    }
};

function toggleContextSelection() {
    contextSelectionOpen.value = !contextSelectionOpen.value;
}


function scrollBottomCellContainer() {
    if (beakerNotebookRef.value) {
        beakerNotebookRef.value.scrollBottomCellContainer();
    }
}

onBeforeMount(() => {
    if (cellCount.value <= 0) {
        session.addCodeCell("");
    }
});

// onMounted(() => {
// });

defineExpose({

    handleKeyboardShortcut,
})

</script>


<style lang="scss">
.beaker-notebook {
    // height: 80%;
    // width: 100vw;
    display: flex;
    flex: 1;
    flex-direction: column;
    height: 100%;
    // display: grid;
    // grid-gap: 1px;

    // grid-template-areas:
    //     "header header header header"
    //     "main main main main"
    //     "footer footer footer footer";

    // grid-template-columns: 1fr 1fr 1fr 1fr;
    // grid-template-rows: auto 1fr auto;
}

.notebook-json {
    text-align: left;
    background-color: var(--surface-b);
    border-radius: 0.5rem;
    border: 1px solid var(--gray-300);
    overflow: auto;
}

header {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

main {
    grid-area: main;
}

footer {
    grid-area: footer;
}

.main-panel {
    display: flex;
    flex-direction: column;
    &:focus {
        outline: none;
    }
}

.ide-cells {
    position: relative;
    display: flex;
    flex: 1;
    flex-direction: column;
    z-index: 3;
    background-color: var(--surface-a);
}


.agent-query-container {
    flex: 0 1 8rem;
}

.main-ide-panel {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 100%;
}

.cell-container {
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 0;
    overflow-y: auto;
    bottom: 0;
    right: 0;
    left: 0;
    z-index: 2;
}


.right-splitter {
    display: flex;
    flex-direction: column;

    &:focus {
        outline: none;
    }

    .p-tabview {
        height: 100%;
        display: flex;
        flex-direction: column;
        li .p-tabview-nav-link {
            padding: 0;
            .p-button {
                pointer-events: none;
                color: var(--text-color-secondary);
            }
        }
    }

    .p-tabview-panels {
        flex: 1;
        position: relative;
    }
}

.scroller-area {
    position: absolute;
    top:0;
    bottom: 0;
    right: 0;
    left: 0;
    overflow-y: auto;
}

.debug-card {
    &.p-card {
        border-radius: 0;
    }
    .p-card-content {
        padding-top: 0.75rem;
        padding-bottom: 0.25rem;
    }

    .vjs-tree-node:hover{
        background-color: var(--surface-b);
    }

}

.welcome-placeholder  {
    position: absolute;
    top: 7rem;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: -1;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 90%;
}

.fade-enter-active {
    transition: opacity 1s ease-out;
}
.fade-leave-active {
    transition: opacity 1s ease-in;
}
.fade-leave-from {
    stop-opacity: 90%;
}
.fade-leave-to {
    opacity: 0;
}
.fade-enter-from {
    opacity: 0;
}
.fade-enter-to {
    opacity: 90%;
}

.debug-pane-toggler {
    background-color: var(--surface-a);
    display: flex;
    flex-direction: column;
}


</style>
