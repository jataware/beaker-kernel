<template>
    <div class="beaker-notebook">
        <header>
            <BeakerHeader 
                :connectionStatus="props.connectionStatus"
                :toggleDarkMode="toggleDarkMode"
                :loading="!activeContext?.slug"
                :kernel="selectedKernel"
                @select-kernel="toggleContextSelection"
            />
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
                        :selectCell="selectCell"
                        :selectedCellIndex="selectedCellIndex"
                        :set-context="reapplyContext"
                        :run-cell="runCell"
                    />

                    <div class="ide-cells">
                        <div 
                            style="flex: 1; position: relative;"
                        >
                             <Notebook
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
                            </Notebook>
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
import Notebook from '../lib/UINotebook.vue';
import BeakerHeader from './BeakerHeader.vue';
import NotebookControls from './NotebookControls.vue';
import BeakerAgentQuery from './BeakerAgentQuery.vue';
import BeakerContextSelection from "./BeakerContextSelection.vue";
import BeakerExecuteAction from "./BeakerExecuteAction.vue";
import FooterDrawer from './FooterDrawer.vue';
import LoggingPane from './LoggingPane.vue';
import BeakerFilePane from './BeakerFilePane.vue';
import ContextTree from './ContextTree.vue';
import PreviewPane from './PreviewPane.vue';
import SvgPlaceholder from './SvgPlaceholder.vue';


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
const activeContext = ref<{slug: string, class: string, context: any, info: any} | undefined>(undefined);
const selectedCellIndex = ref(0);
const selectedKernel = ref();
const contextSelectionOpen = ref(false);
const showDebugPane = ref (true);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightPaneTabIndex = ref(1);
const selectedTheme = ref(localStorage.getItem('theme') || 'light');
const debugTabView = ref<{tabs: any[]}|null>(null);
const selectedAction = ref<string|undefined>(undefined);
const beakerNotebookRef = ref(null);


const session: BeakerSession = inject('session');
const showToast = inject('show_toast');

provide('theme', selectedTheme);
provide('active_context', activeContext);

const cellCount = computed(() => session.notebook?.cells?.length || 0);

const applyTheme = () => {
    const themeLink = document.querySelector('#primevue-theme');
    themeLink.href = `/themes/soho-${selectedTheme.value}/theme.css`;
}

const toggleDarkMode = () => {
    selectedTheme.value = selectedTheme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', selectedTheme.value);
    applyTheme();
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
    return session.notebook.cells[index];
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

const runCell = () => {
    beakerNotebookRef.value.executeSelectedCell();
}

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

function scrollBottomCellContainer() {
    if (beakerNotebookRef.value) {
        beakerNotebookRef.value.scrollBottomCellContainer();
    }
}

onBeforeMount(() => {
    if (cellCount.value <= 0) {
        session.addCodeCell("");
    }
    applyTheme();
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
    position: relative;
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

.drop-overflow-catcher {
    flex: 1;
}

</style>
