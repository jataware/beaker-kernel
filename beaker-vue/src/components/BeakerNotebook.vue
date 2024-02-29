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

            <ContextTree :context="activeContext?.info" />

            <Splitter @resizeend="handleSplitterResized" class="splitter">

                <SplitterPanel
                    :size="70"
                    :minSize="30"
                    class="main-panel"
                    @keydown="handleKeyboardShortcut"
                >

                    <div class="notebook-controls">
                        <InputGroup>
                            <Button
                                @click="addCell()"
                                v-tooltip.bottom="{value: 'Add New Cell', showDelay: 300}"
                                icon="pi pi-plus"
                                size="small"
                                severity="info"
                                text
                            />
                            <Button
                                @click="removeCell"
                                v-tooltip.bottom="{value: 'Remove Selected Cell', showDelay: 300}"
                                icon="pi pi-minus"
                                size="small"
                                severity="info"
                                text
                            />
                            <Button
                                @click="runCell()"
                                v-tooltip.bottom="{value: 'Run Selected Cell', showDelay: 300}"
                                icon="pi pi-play"
                                size="small"
                                severity="info"
                                text
                            />
                            <!-- TODO implement Stop-->
                            <Button
                                @click="identity"
                                v-tooltip.bottom="{value: 'Stop Execution', showDelay: 300}"
                                icon="pi pi-stop"
                                size="small"
                                severity="info"
                                text
                            />
                        </InputGroup>
                        <InputGroup style="margin-right: 1rem;">
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
                        </InputGroup>
                    </div>

                    <div class="ide-cells">
                        <div style="flex: 1; position: relative;">
                            <!-- Added drag-sort-enable to BeakerCell parent to 
                                 allow BeakerCell grab/drag to sort.-->
                            <div 
                                class="cell-container drag-sort-enable"
                                ref="cellsContainerRef"
                            >
                                <BeakerCell
                                    v-for="(cell, index) in props.session?.notebook?.cells"
                                    :key="cell.id"
                                    :class="{selected: (index === selectedCellIndex)}"
                                    :index="index"
                                    :cellID="cell.id"
                                    :cellCount="cellCount"
                                    @move-cell="handleMoveCell"
                                    @click="selectCell(index)"
                                >
                                    <Component
                                        :is="componentMap[cell.cell_type]"
                                        :cell="cell"
                                        :session="props.session"
                                        :context-data="activeContext"
                                        @keyboard-nav="handleKeyboardAction"
                                    />
                                </BeakerCell>
                                <transition name="fade">
                                    <div class="welcome-placeholder" v-if="cellCount < 3">
                                        <SvgPlaceholder />
                                    </div>
                                </transition>
                            </div>
                        </div>

                        <BeakerAgentQuery
                            class="agent-query-container"
                            :session="session"
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
                    <TabView v-model:activeIndex="rightPaneTabIndex">
                        <TabPanel>
                            <template #header>
                                <Button tabindex="-1" label="Preview" text icon="pi pi-eye" />
                            </template>
                            <div class="scroller-area">
                                <PreviewPane />
                            </div>
                        </TabPanel>

                        <TabPanel>
                            <template #header>
                                <Button tabindex="-1" label="Debug" text icon="pi pi-send" />
                            </template>
                            <div class="scroller-area">
                                <Card class="debug-card">
                                    <template #title>Custom Message</template>
                                    <template #content>
                                        <BeakerCustomMessage
                                            :intercepts="activeContext?.info?.intercepts"
                                            :session="session"
                                            :rawMessages="props.rawMessages"
                                        />
                                    </template>
                                </Card>
                                <!-- <Card class="debug-card">
                                    <template #title>State</template>
                                    <template #content>
                                        <vue-json-pretty
                                            :data="debugData()"
                                            :deep="3"
                                            showLength
                                            showIcon
                                        />
                                        <br />
                                        <Button label="Copy" />
                                    </template>
                                </Card> -->
                            </div>
                        </TabPanel>

                        <TabPanel>
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
                            <BeakerFilePane :session="props.session"/>
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
        :session="props.session"
        :activeContext="activeContext"
        :isOpen="contextSelectionOpen"
        :toggleOpen="toggleContextSelection"
        @update-context-info="setContext"
        :contextProcessing="contextProcessing"
    />

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, Component, nextTick, provide, inject } from "vue";
import { IBeakerCell, BeakerBaseCell } from 'beaker-kernel';

import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';

import Card from 'primevue/card';
import Button from 'primevue/button';
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Toolbar from 'primevue/toolbar';
import InputGroup from 'primevue/inputgroup';

import BeakerCell from './BeakerCell.vue';
import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import BeakerAgentQuery from './BeakerAgentQuery.vue';
import BeakerContextSelection from "./BeakerContextSelection.vue";
import BeakerCustomMessage from "./BeakerCustomMessage.vue";
import FooterDrawer from './FooterDrawer.vue';
import LoggingPane from './LoggingPane.vue';
import BeakerFilePane from "./BeakerFilePane.vue";
import ContextTree from "./ContextTree.vue";
import PreviewPane from "./PreviewPane.vue";
import SvgPlaceholder from './SvgPlaceholder.vue';
import OpenNotebookButton from './OpenNotebookButton.vue';


function capitalize(s: string) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

const props = defineProps([
    "session",
    "connectionStatus",
    "debugLogs",
    "rawMessages",
]);

const showToast = inject('show_toast');

const debugData = () => {
    return JSON.parse(props.session.notebook.toJSON());
};

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
const activeContext = ref<{slug: string, class: string, context: any, info: any} | undefined>(undefined);
const selectedCellIndex = ref(0);
const selectedKernel = ref();
const contextSelectionOpen = ref(false);
const showDebugPane = ref (true);
const cellsContainerRef = ref(null);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightPaneTabIndex = ref(1);
const isDeleteprefixActive = ref(false);

const cellCount = computed(() => props.session?.notebook?.cells?.length || 0);

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


function handleKeyboardAction(action) {
    // TODO types
    if (action === 'focus-cell') {
        focusActiveCell();
    } else if (action === 'select-next-cell') {
        if (selectedCellIndex.value === cellCount.value - 1) {
            addCell();
        } else {
            selectNextCell();
        }
    }
}

/**
 * Modifies array in place to move a cell to a new location
 **/
function arrayMove(arr, old_index, new_index) {
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}
function handleMoveCell(fromIndex, toIndex) {
    arrayMove(props.session.notebook.cells, fromIndex, toIndex)
    selectCell(toIndex);
}

function getDateTime() {
    let t = new Date();
    // convert the local time zone offset from minutes to milliseconds
    let z = t.getTimezoneOffset() * 60 * 1000;
    // subtract the offset from t
    let tLocal = t - z;
    // create shifted Date object
    tLocal = new Date(tLocal);
    // convert to ISO format string
    let iso = tLocal.toISOString();
    // drop the milliseconds and zone
    iso = iso.split(".")[0];
    // replace the T with _, and : with , (: aren't allowed on filenames)
    iso = iso.replace('T', '_').replace(/:/g,',');
    return iso;
}

function downloadNotebook() {
    const rawData = null;
    const data = JSON.stringify(props.session.notebook.toIPynb(), null, 2); // TODO error handling

    const filename = `Beaker-Notebook_${getDateTime()}.ipynb`;

    const blob = new Blob([data], {type: 'application/x-ipynb+json'});

    if (window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveBlob(blob, filename);
    }
    else {
        const elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
    }
}

function loadNotebook(notebookJSON) {
    props.session.loadNotebook(notebookJSON);
}

const resetNotebook = () => {
    props.session.reset();
    // Reapply context
    setContext(activeContextPayload.value);
};

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const identity = (args: any) => {console.log('identity func called'); return args;};

const _cellIndex = (cell: IBeakerCell): number => {
    let index = -1;
    if (typeof(cell) === "number") {
        index = cell
    }
    else if (cell instanceof BeakerBaseCell) {
        index = props.session.notebook.cells.indexOf(cell);
    }
    return index;
}

const selectedTheme = ref(localStorage.getItem('theme') || 'light');
const themeIcon = computed(() => {
    return `pi pi-${selectedTheme.value == 'dark' ? 'sun' : 'moon'}`;
})

provide('theme', selectedTheme);

const setTheme = () => {
    const themeLink = document.querySelector('#primevue-theme');
    themeLink.href = `/themes/soho-${selectedTheme.value}/theme.css`;
}

const toggleDarkMode = () => {
    selectedTheme.value = selectedTheme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', selectedTheme.value);
    setTheme();
};

const _getCell = (cell: number | IBeakerCell) => {
    const index = _cellIndex(cell);
    return props.session.notebook.cells[index];
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
    const isAgentQueryBox = target.className.includes('llm-query-input');

    if (isEditingCode || isAgentQueryBox) {
        return false;
    }

    return true;
};

function focusActiveCell() {
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
        focusActiveCell();
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
    // TODO Should we wrap around?
    if (currentIndex === 0) {
        return;
    }
    selectCell(currentIndex - 1);

    nextTick(() => {
        focusActiveCell();
    });
   
    if (event) {
        event.preventDefault();
    }
};


function handleKeyboardShortcut(event) {

    const { target } = event;

    const isEditingCode = target.className === 'cm-content'; // codemirror
    const isAgentQueryBox = target.className.includes('llm-query-input');

    if (isEditingCode || isAgentQueryBox) {
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
                focusActiveCell();
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
    const newCell = props.session.addCodeCell("");

    if (typeof toIndex === 'number') {
        // Move cell to indicated index
        arrayMove(props.session.notebook.cells, cellCount.value - 1, toIndex)
    }
    
    selectCell(newCell);

    nextTick(() => {
        focusActiveCell();
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
        cell.execute(props.session);
    }
}

const removeCell = () => {
    props.session.notebook.removeCell(selectedCellIndex.value);

    // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    if (cellCount.value == 0) {
        props.session.addCodeCell("");
    }
    // Fixup the selection if we remove the last item.
    if (selectedCellIndex.value >= cellCount.value) {
        selectedCellIndex.value = cellCount.value - 1;
    }
};

const resetNB = async () => {
    // TODO hook to notebook-control button
    await props.session.reset();
    if (cellCount.value == 0) {
        props.session.addCodeCell("");
    }
};

function toggleContextSelection() {
    contextSelectionOpen.value = !contextSelectionOpen.value;
}

const setContext = (contextPayload: any) => {

    contextProcessing.value = true;

    const future = props.session.sendBeakerMessage(
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

const updateContextInfo = async () => {
    const activeContextInfo = await props.session.activeContext();
    activeContext.value = activeContextInfo;
    selectedKernel.value = activeContextInfo.slug;
}

onBeforeMount(() => {
    if (props.session.notebook.cells.length <= 0) {
        props.session.addCodeCell("");
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
    position: absolute;
    top: 0;
    overflow-y: auto;
    bottom: 0;
    right: 0;
    left: 0;
    z-index: 2;
}

.notebook-controls {
    margin: 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .p-inputgroup {
        width: unset;
    }
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


</style>
