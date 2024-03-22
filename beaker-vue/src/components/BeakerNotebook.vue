<template>
    <div class="beaker-notebook">
        <header>
            <Toolbar class="toolbar">
                <template #start>
                    <div class="status-bar">
                        <i class="pi pi-circle-fill" :style="`font-size: inherit; color: var(--${connectionColor});`" />
                        {{capitalize(props.connectionStatus)}}
                    </div>
                    <Button
                        outlined
                        size="small"
                        icon="pi pi-angle-down"
                        iconPos="right"
                        class="connection-button"
                        @click="toggleContextSelection"
                        :label="selectedKernel"
                        :loading="!activeContext?.slug"
                    />
                </template>

                <template #center>
                    <div class="logo">
                        <h4>
                            Beaker <span class="longer-title">Development Interface</span>
                        </h4>
                    </div>
                </template>

                <template #end>
                    <nav>
                        <Button
                            text
                            @click="toggleDarkMode"
                            style="margin: 0; color: var(--gray-500);"
                            :icon="themeIcon"
                        />
                        <a
                            href="https://jataware.github.io/beaker-kernel"
                            rel="noopener"
                            target="_blank"
                        >
                            <Button
                                text
                                style="margin: 0; color: var(--gray-500);"
                                aria-label="Beaker Documentation"
                                icon="pi pi-book"
                            />
                        </a>
                        <a
                            href="https://github.com/jataware/beaker-kernel"
                            rel="noopener"
                            target="_blank"
                        >
                            <Button
                                text
                                style="margin: 0; color: var(--gray-500);"
                                aria-label="Github Repository Link Icon"
                                icon="pi pi-github"
                            />
                        </a>
                    </nav>
                </template>
            </Toolbar>

        </header>

        <main style="display: flex;">

            <ContextTree :context="activeContext?.info" @action-selected="selectAction"/>

            <Splitter @resizeend="handleSplitterResized" class="splitter">

                <SplitterPanel
                    :size="70"
                    :minSize="30"
                    class="main-panel"
                    @keydown="handleKeyboardShortcut"
                >

                    <NotebookControls
                        @run-cell="runCell()"
                        @remove-cell="removeCell"
                        @add-cell="addCell"
                        @set-context="reapplyContext"
                    />

                    <div class="ide-cells">
                        <div style="flex: 1; position: relative;">
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
                                        selected: (index === selectedCellIndex),
                                        'drag-source': (index == dragSourceIndex),
                                        'drag-above': (index === dragOverIndex && index < dragSourceIndex),
                                        'drag-below': (index === dragOverIndex && index > dragSourceIndex),
                                        'drag-itself': (index === dragOverIndex && index === dragSourceIndex ),
                                        'drag-active': isDragActive,
                                    }"
                                    ref="notebookCellsRef"
                                    :index="index"
                                    :drag-enabled="isDragEnabled"
                                    @move-cell="handleMoveCell"
                                    @click="selectCell(index)"
                                    :cell="cell"
                                    @keyboard-nav="handleNavAction"
                                    @dragstart="handleDragStart($event, cell, index)"
                                    @drop="handleDrop($event, index)"
                                    @dragover="handleDragOver($event, cell, index)"
                                    @dragend="handleDragEnd"
                                />
                                <div
                                    class="drop-overflow-catcher"
                                    @dragover="dragOverIndex = session.notebook.cells.length-1; $event.preventDefault();"
                                    @drop="handleDrop($event, session.notebook.cells.length-1)"
                                >
                                    <transition name="fade">
                                        <div class="welcome-placeholder" v-if="cellCount < 3">
                                            <SvgPlaceholder />
                                        </div>
                                    </transition>
                                </div>
                            </div>
                        </div>

                        <BeakerAgentQuery
                            class="agent-query-container"
                            @select-cell="selectCell"
                            @run-cell="runCell"
                            :run-cell-callback="scrollBottomCellContainer"
                        />
                    </div>
                </SplitterPanel>

                <SplitterPanel
                    v-if="showDebugPane"
                    :minSize="5"
                    :size="30"
                    class="right-splitter"
                >
                    <TabView v-model:activeIndex="rightPaneTabIndex" ref="debugTabView">
                        <TabPanel tabId="preview">
                            <template #header>
                                <Button tabindex="-1" label="Preview" text icon="pi pi-eye" />
                            </template>
                            <div class="scroller-area">
                                <PreviewPane :previewData="previewData"/>
                            </div>
                        </TabPanel>

                        <TabPanel tabId="action">
                            <template #header>
                                <Button tabindex="-1" label="Action" text icon="pi pi-send" />
                            </template>
                            <div class="scroller-area">
                                <Card class="debug-card">
                                    <template #title>Execute an Action</template>
                                    <template #content>
                                        <BeakerExecuteAction
                                            :selectedAction="selectedAction"
                                            :actions="activeContext?.info?.actions"
                                            :rawMessages="props.rawMessages"
                                            @clear-selection="selectedAction = undefined"
                                        />
                                    </template>
                                </Card>
                            </div>
                        </TabPanel>

                        <TabPanel tabId="logging">
                            <template #header>
                                <Button tabindex="-1" label="Logging" text icon="pi pi-list" />
                            </template>
                            <LoggingPane :entries="props.debugLogs" />
                        </TabPanel>

                        <TabPanel>
                            <template #header>
                                <Button tabindex="-1" label="Messages" text icon="pi pi-comments" />
                            </template>
                            <LoggingPane :entries="props.rawMessages" />
                        </TabPanel>

                        <TabPanel>
                            <template #header>
                                <Button tabindex="-1" label="Files" text icon="pi pi-file-export" />
                            </template>
                            <BeakerFilePane />
                        </TabPanel>

                    </TabView>
                </SplitterPanel>

            </Splitter>

            <div
                v-if="!showDebugPane"
                class="debug-pane-toggler"
            >
                <Button text
                    icon="pi pi-eye"
                    size="small"
                    v-tooltip.left="'Preview'"
                    @click="handleRightPaneIconClick(0)"
                />
                <Button text
                    icon="pi pi-send"
                    size="small"
                    v-tooltip.left="'Debug'"
                    @click="handleRightPaneIconClick(1)"
                />
                <Button text
                    icon="pi pi-list"
                    size="small"
                    v-tooltip.left="'Logs'"
                    @click="handleRightPaneIconClick(2)"
                />
                <Button text
                    icon="pi pi-comments"
                    size="small"
                    v-tooltip.left="'Messages'"
                    @click="handleRightPaneIconClick(3)"
                />
                <Button text
                    icon="pi pi-file-export"
                    size="small"
                    v-tooltip.left="'Files'"
                    @click="handleRightPaneIconClick(4)"
                />
            </div>

        </main>

        <!-- TODO may use HTML comments to hide footer -->
        <footer>
            <FooterDrawer />
         </footer>
    </div>

    <BeakerContextSelection
        :isOpen="contextSelectionOpen"
        :toggleOpen="toggleContextSelection"
        @update-context-info="setContext"
        :contextProcessing="contextProcessing"
    />

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits } from "vue";
import { IBeakerCell, BeakerBaseCell, BeakerSession } from 'beaker-kernel';

import Card from 'primevue/card';
import Button from 'primevue/button';
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
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
const selectedCellIndex = ref(0);
const selectedKernel = ref();
const contextSelectionOpen = ref(false);
const showDebugPane = ref (true);
const cellsContainerRef = ref(null);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightPaneTabIndex = ref(0);
const isDeleteprefixActive = ref(false);
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
        if (selectedCellIndex.value === cellCount.value - 1) {
            addCell();
        } else {
            selectNextCell();
        }
    }
}

function handleMoveCell(fromIndex, toIndex) {
    arrayMove(session.notebook.cells, fromIndex, toIndex)
    selectCell(toIndex);
}

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const _cellIndex = (cell: IBeakerCell): number => {
    let index = -1;
    if (typeof(cell) === "number") {
        index = cell
    }
    else if (cell instanceof BeakerBaseCell) {
        index = session.notebook.cells.indexOf(cell);
    }
    return index;
}


const _getCell = (cell: number | IBeakerCell) => {
    const index = _cellIndex(cell);
    return notebookCellsRef.value[index];
}

const selectCell = (cell: number | IBeakerCell) => {
    let index = -1;
    if (Number.isInteger(cell) ) {
        index = cell;
    }
    else if (cell instanceof BeakerBaseCell) {
        index = _cellIndex(cell);
    }
    selectedCellIndex.value = index;
}

const commonSelectAction = (event) => {
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
    elem.focus();
}

const selectNextCell = (event) => {
    if (event && !commonSelectAction(event)) {
        return;
    }

    const currentIndex = selectedCellIndex.value;
    // TODO should we wrap around? Should we auto-add a new cell?
    if (currentIndex === cellCount.value - 1) {
        return;
    }
    selectCell(currentIndex + 1);

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

    const currentIndex = selectedCellIndex.value;
    if (currentIndex === 0) {
        return;
    }
    selectCell(currentIndex - 1);

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

    if (['b', 'B'].includes(event.key)){
        addCell(selectedCellIndex.value + 1);
    } else if (['a', 'A'].includes(event.key)){
        let prevIndex = selectedCellIndex.value;
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

const addCell = (toIndex) => {
    const newCell = session.addCodeCell("");

    if (typeof toIndex === 'number') {
        // Move cell to indicated index
        arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)
    }

    selectCell(newCell);

    nextTick(() => {
        focusSelectedCell();
    });
}

const runCell = (cell?: number | IBeakerCell) => {
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
    session.notebook.removeCell(selectedCellIndex.value);

    // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    if (cellCount.value === 0) {
        session.addCodeCell("");
    }
    // Fixup the selection if we remove the last item.
    if (selectedCellIndex.value >= cellCount.value) {
        selectedCellIndex.value = cellCount.value - 1;
    }
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
}

const selectAction = (actionName: string) => {
    if (debugTabView.value === null) {
        return;
    }
    const index = debugTabView.value.tabs.findIndex((tab) => (tab.props?.tabId === "action"));
    rightPaneTabIndex.value = index;
    showDebugPane.value = true;
    selectedAction.value = actionName;
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
    if (cellCount.value <= 0) {
        session.addCodeCell("");
    }
    setTheme();
});

onMounted(() => {
    updateContextInfo();
});

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
    height: 100%;
    z-index: 3;
    background-color: var(--surface-a);
}

.splitter {
    height: 100%;
    flex: 1;
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
