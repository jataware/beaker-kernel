<template>
    <div class="beaker-notebook">
        <main style="display: flex;">
            <div
                class="ide-cells"
                style="flex: 100;"
                @keydown="handleKeyboardShortcut"
            >
                <NotebookControls
                        @run-cell="runCell()"
                        @remove-cell="removeCell"
                        @add-code-cell="addCodeCell"
                        @add-markdown-cell="addMarkdownCell"
                        @reset-nb="resetNB"
                    />
                <div style="flex: 1; display: flex; position: relative;">
                    <!-- Added drag-sort-enable to BeakerCell parent to
                            allow BeakerCell grab/drag to sort.-->
                    <div
                        class="cell-container drag-sort-enable"
                        ref="cellsContainerRef"
                    >
                        <BeakerCell
                            v-for="(cell, index) in session.notebook.cells"
                            :key="cell.id"
                            :class="{
                                selected: (index.toString() === selectedCellIndex),
                                'drag-source': (index == dragSourceIndex),
                                'drag-above': (index === dragOverIndex && index < dragSourceIndex),
                                'drag-below': (index === dragOverIndex && index > dragSourceIndex),
                                'drag-itself': (index === dragOverIndex && index === dragSourceIndex ),
                                'drag-active': isDragActive,
                            }"
                            ref="notebookCellsRef"
                            :selectedCellIndex="selectedCellIndex"
                            :index="String(index)"
                            :drag-enabled="isDragEnabled"
                            @move-cell="handleMoveCell"
                            @click="selectCell(index)"
                            :childOnClickCallback="selectCell"
                            :cell="cell"
                            :getCell="_getCell"
                            @keyboard-nav="handleNavAction"
                            @dragstart="handleDragStart($event, cell, index)"
                            @drop="handleDrop($event, index)"
                            @dragover="handleDragOver($event, cell, index)"
                            @dragend="handleDragEnd"
                        />
                        <BeakerAgentQuery
                            class="agent-query-container"
                            @select-cell="selectCell"
                            @run-cell="runCell"
                            :run-cell-callback="scrollBottomCellContainer"
                        />
                    </div>
                </div>
            </div>
        </main>

    </div>

    <BeakerContextSelection
        :isOpen="contextSelectionOpen"
        :toggleOpen="toggleContextSelection"
        @update-context-info="setContext"
        :contextProcessing="contextProcessing"
    />

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, defineExpose } from "vue";
import { BeakerBaseCell, BeakerSession } from 'beaker-kernel';
import { type IBeakerCell } from "beaker-kernel";
// import { IBeakerCell } from "beaker-kernel/dist/notebook";

import Card from 'primevue/card';
import Button from 'primevue/button';
import Toolbar from 'primevue/toolbar';
import BeakerCell from './BeakerCell.vue';
import NotebookControls from './NotebookControls.vue';
import BeakerAgentQuery from './BeakerAgentQuery.vue';
import BeakerContextSelection from "./BeakerContextSelection.vue";
import BeakerExecuteAction from "./BeakerExecuteAction.vue";
import FooterDrawer from './FooterDrawer.vue';
import LoggingPane from './LoggingPane.vue';
import BeakerFilePane from "./BeakerFilePane.vue";
import ContextTree from "./ContextTree.vue";
import PreviewPane from "./PreviewPane.vue";
import SvgPlaceholder from './SvgPlaceholder.vue';
import SideMenu from "./SideMenu.vue";
import SideMenuPanel from "./SideMenuPanel.vue";
import { arrayMove, capitalize } from '../util';


const props = defineProps([
    "connectionStatus",
    "debugLogs",
    "rawMessages",
    "previewData",
]);

const emit = defineEmits([
    'clear-preview',
]);

// TODO export/import from ts-lib utils.ts
enum KernelState {
	unknown = 'unknown',
	starting = 'starting',
	idle = 'idle',
	busy = 'busy',
	terminating = 'terminating',
	restarting = 'restarting',
	autorestarting = 'autorestarting',
	dead = 'dead',
  // This extends kernel status for now.
  connected = 'connected',
  connecting = 'connecting'
}

const connectionStatusColorMap = {
    [KernelState.connected]: 'green-400',
    // [KernelState.idle]: 'green-400',
    [KernelState.connecting]: 'green-200',
    [KernelState.busy]: 'orange-400',
};

const connectionColor = computed(() => {
    return connectionStatusColorMap[props.connectionStatus];
});

// TODO info object map type
const notebookCellsRef = ref<typeof BeakerCell|null>(null);
const activeContext = ref<{slug: string, class: string, context: any, info: any} | undefined>(undefined);
const selectedCellIndex = ref("");
const selectedKernel = ref();
const contextSelectionOpen = ref(false);
const showDebugPane = ref (true);
const cellsContainerRef = ref(null);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightPaneTabIndex = ref(0);
const isDeleteprefixActive = ref(false);
const rightMenu = ref<typeof SideMenu>()
const selectedTheme = ref(localStorage.getItem('theme') || 'light');
const debugTabView = ref<{tabs: any[]}|null>(null);
const selectedAction = ref<string|undefined>(undefined);
const isDragEnabled = computed(() => session.notebook?.cells.length > 1);
const isDragActive = ref(false);
const dragSourceIndex = ref(-1);
const dragOverIndex = ref(-1);

const themeIcon = computed(() => {
    return `pi pi-${selectedTheme.value == 'dark' ? 'sun' : 'moon'}`;
});

const session: BeakerSession = inject('session');
const showToast = inject('show_toast');

provide('theme', selectedTheme);
provide('active_context', activeContext);

const cellCount = computed(() => session.notebook?.cells?.length || 0);

const setTheme = () => {
    const themeLink = document.querySelector('#primevue-theme');
    themeLink.href = `/themes/soho-${selectedTheme.value}/theme.css`;
}

const toggleDarkMode = () => {
    selectedTheme.value = selectedTheme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', selectedTheme.value);
    setTheme();
};

function handleRightPaneIconClick(index) {
    rightPaneTabIndex.value = index;
    showDebugPane.value = true;
}

function handleSplitterResized({sizes}) {
    const [_, rightPaneSize] = sizes;
    if (rightPaneSize < 15) {
        showDebugPane.value = false
    }
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
        if (selectedCellIndex.value === String(cellCount.value - 1)) {
           return;
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
    arrayMove(session.notebook.cells, fromIndex, toIndex)
    selectCell(toIndex);
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
    if (!cellsContainerRef.value){
        return;
    }
    const elem = cellsContainerRef.value.querySelector('.beaker-cell.selected');
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


function handleKeyboardShortcut(event) {

    const { target } = event;

    // TODO is there a better way to encapsulate cancelling events
    // when writing on textarea/input/code elements ?
    const isEditingCode = target.className.includes('cm-content'); // codemirror
    const isTextArea = target.className.includes('resizeable-textarea');

    if (isEditingCode || isTextArea) {
        return;
    }

    if ('Enter' === event.key && !event.shiftKey && !event.ctrlKey) {
        const cell = selectedCell.value;
        if (cell.enter !== undefined) {
            cell.enter(event);
        }
        else {
            focusSelectedCell();
        }
        return;
    }

    if (['ArrowDown', 'j', 'J'].includes(event.key)) {
        selectNextCell();
    } else if (['ArrowUp', 'k', 'K'].includes(event.key)) {
        selectPreviousCell();
    }

    const [parent, child] = splitCellIndex(selectedCellIndex.value);
    if (['b', 'B'].includes(event.key)){
        addCodeCell(parent + 1);
    } else if (['a', 'A'].includes(event.key)){
        addCodeCell(parent);
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

const addCodeCell = (toIndex?: number) => {
    const newCell = session.addCodeCell("");

    if (typeof toIndex !== 'number') {
        const [parent, child] = splitCellIndex(selectedCellIndex.value);
        toIndex = parent + 1;
    }
    arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

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
    arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    selectCell(newCell);

    nextTick(() => {
        notebookCellsRef.value[notebookCellsRef.value.length - 1].enter();
        focusSelectedCell();
    });
}

const runCell = (cell?: string | IBeakerCell) => {
    if (cell === undefined) {
        cell = selectedCell.value;
    }
    else {
        cell = _getCell(cell);
    }
    if (cell !== undefined) {
        cell.execute(session);
    }
}

const removeCell = () => {
    const [parent, child] = splitCellIndex(selectedCellIndex.value);
    if (typeof(child) !== "undefined"
        && typeof(session.notebook.cells?.[parent]?.children) !== "undefined") {
        session.notebook.cells[parent].children.splice(child, 1);
    } else {
        session.notebook.removeCell(parent);
    }

    // Fixup the selection if we remove the last item.
    if (parent >= cellCount.value) {
        selectedCellIndex.value = mergeCellIndex(cellCount.value - 1, 0);
    }
};

const resetNB = async () => {
    await session.reset();
    reapplyContext();
    if (cellCount.value === 0) {
        session.addCodeCell("");
    }
};

function toggleContextSelection() {
    contextSelectionOpen.value = !contextSelectionOpen.value;
}

const setContext = (contextPayload: any) => {

    contextProcessing.value = true;

    // Clear preview data upon changing contexts.
    emit("clear-preview");

    const future = session.sendBeakerMessage(
        "context_setup_request",
        contextPayload
    );
    future.done.then((result: any) => {

        contextProcessing.value = false;
        activeContextPayload.value = contextPayload;

        if (result?.content?.status === 'error') {
            let formatted = result?.content?.evalue;
            if (formatted) {
                const endsWithPeriod = /\.$/.test(formatted);
                if (!endsWithPeriod) {
                    formatted += '.';
                }
            }
            showToast({
                title: 'Context Setup Failed',
                severity: 'error',
                detail: `${formatted} Please try again or contact us.`,
                life: 0
            });
            return;
        }

        if (result?.content?.status === 'abort') {
            showToast({
                title: 'Context Setup Aborted',
                severity: 'warning',
                detail: result?.content?.evalue,
                life: 6000
            });
        }

        // Close the context dialog
        contextSelectionOpen.value = false;
        // Update the context info in the sidebar
        // TODO: Is this even needed? Could maybe be fed/triggered by existing events?
        updateContextInfo();
    });
}

function reapplyContext() {
    setContext(activeContextPayload.value);
}

const updateContextInfo = async () => {
    const activeContextInfo = await session.activeContext();
    activeContext.value = activeContextInfo;
    selectedKernel.value = activeContextInfo.slug;
    activeContextPayload.value = activeContextInfo.config;
}

const selectAction = (actionName: string) => {
    rightMenu.value?.selectPanel("action");
    nextTick(() => { selectedAction.value = actionName; });
};

/**
 * Handles reordering of cells if dropped within the sort-enabled cells area.
 **/
function handleDrop(event: DragEvent, index: number) {

    const target = (event.target as HTMLElement);
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

/**
 * Sets call to item being moved
 * As well as dataTransfer so that drop target knows which one was dropped
 **/
function handleDragStart(event: DragEvent, beakerCell: IBeakerCell, index: number)  {
    if (event.dataTransfer !== null) {

        var paintTarget: HTMLElement|null = (event.target as HTMLElement).closest('.beaker-cell');

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
function handleDragOver(event: DragEvent, beakerCell: IBeakerCell, index: number) {

    const cellId = event.dataTransfer?.getData("cellID");
    const sourceIndex =  Number.parseInt(event.dataTransfer?.getData("cellIndex") || "-1");

    dragOverIndex.value = index;

    event.preventDefault(); // Allow dropping
}

function handleDragEnd() {
    isDragActive.value = false;
    dragOverIndex.value = -1;
    dragSourceIndex.value = -1;
}


onBeforeMount(() => {
    // if (cellCount.value <= 0) {
    //     session.addCodeCell("");
    // }
    setTheme();
});

onMounted(() => {
    updateContextInfo();
});

defineExpose({
    updateContextInfo,
})

</script>


<style lang="scss">
.beaker-notebook {
    height: 100vh;
    width: 100vw;
    display: grid;
    grid-gap: 1px;

    grid-template-areas:
        "header header header header"
        "main main main main"
        "footer footer footer footer";

    grid-template-columns: 1fr 1fr 1fr 1fr;
    grid-template-rows: auto 1fr auto;
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
    display: flex;
    flex-direction: column;
    z-index: 3;
    background-color: var(--surface-a);
}


.agent-query-container {
    flex: 0 1 8rem;
}

.status-bar {
    display: flex;
    line-height: inherit;
    align-items: center;
    color: var(--text-color);
    width: 8rem;
    & > i {
        margin-right: 0.5rem;
    }
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

.connection-button {
    color: var(--surface-500);
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

.toolbar {
    width: 100%;
    padding: 0.5rem 1rem;

    &.p-toolbar {
        flex-wrap: nowrap;
    }
    .p-toolbar-group-end {
        margin-left: -0.5rem;
    }

    .logo {
        font-size: 1.5rem;
        padding: 0 0.5rem;
        h4 {
            font-size: 1.8rem;
            margin: 0;
            padding: 0;
            font-weight: 500;
            color: var(--gray-500);

            @media(max-width: 885px) {
                .longer-title {
                    display: none;
                }
            }
        }
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
  opacity: 90%;
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

.drop-overflow-catcher {
    flex: 1;
}

</style>
