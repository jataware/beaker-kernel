<template>
    <div class="beaker-dev-interface">
        <!-- <header>
            <BeakerHeader
                :connectionStatus="props.connectionStatus"
                :toggleDarkMode="toggleDarkMode"
                :loading="!activeContext?.slug"
                :kernel="selectedKernel"
                @select-kernel="toggleContextSelection"
            />
        </header> -->

        <main style="display: flex;">
            <SideMenu
                position="left"
                :show-label="true"
                highlight="line"
            >
                <SideMenuPanel label="Context" icon="pi pi-home">
                    <ContextTree :context="activeContext?.info" @action-selected="selectAction"/>
                </SideMenuPanel>
            </SideMenu>

                <div
                    class="main-panel"
                    style="flex: 100"
                    @keydown="handleKeyboardShortcut"
                >
                    <BeakerNotebook
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
                    </BeakerNotebook>
                    <BeakerAgentQuery
                        class="agent-query-container"
                        @select-cell="selectCell"
                        @run-cell="runCell"
                        :run-cell-callback="scrollBottomCellContainer"
                    />
                </div>
                    <SideMenu
                        position="right"
                        ref="rightMenu"
                        highlight="line"
                        :show-label="true"
                    >
                        <SideMenuPanel tabId="preview" label="Preview" icon="pi pi-eye">
                            <PreviewPane :previewData="previewData"/>
                        </SideMenuPanel>

                        <SideMenuPanel tabId="action" label="Actions" icon="pi pi-send">
                            <Card class="debug-card">
                                <template #title>Execute an Action</template>
                                <template #content>
                                    <BeakerExecuteAction
                                        ref="executeActionRef"
                                        :selectedAction="selectedAction"
                                        :actions="activeContext?.info?.actions"
                                        :rawMessages="props.rawMessages"
                                        @clear-selection="selectedAction = undefined"
                                    />
                                </template>
                            </Card>
                        </SideMenuPanel>

                        <SideMenuPanel tabId="logging" label="Logging" icon="pi pi-list" >
                            <LoggingPane :entries="props.debugLogs" />
                        </SideMenuPanel>

                        <SideMenuPanel label="Messages" icon="pi pi-comments">
                            <LoggingPane :entries="props.rawMessages" />
                        </SideMenuPanel>

                        <SideMenuPanel label="Files" icon="pi pi-file-export">
                            <BeakerFilePane />
                        </SideMenuPanel>

                    </SideMenu>
        </main>

        <!-- TODO may use HTML comments to hide footer -->
        <!-- <footer>
            <FooterDrawer />
         </footer> -->
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
// import Notebook from '../lib/UINotebook.vue';

import BeakerHeader from '@/components/dev-interface/BeakerHeader.vue';
// import NotebookControls from '@/components/notebook/NotebookControls.vue';
// import Notebook from '@/components/notebook/NotebookPanel.vue';
import BeakerNotebook from "@/components/notebook/BeakerNotebook.vue";
import BeakerAgentQuery from '@/components/agent/BeakerAgentQuery.vue';
import BeakerContextSelection from "@/components/session/BeakerContextSelection.vue";
import BeakerExecuteAction from "@/components/dev-interface/BeakerExecuteAction.vue";
import LoggingPane from '@/components/dev-interface/LoggingPane.vue';
import BeakerFilePane from '@/components/dev-interface/BeakerFilePane.vue';
import ContextTree from '@/components/dev-interface/ContextTree.vue';
import PreviewPane from '@/components/dev-interface/PreviewPane.vue';
import SvgPlaceholder from '@/components/misc/SvgPlaceholder.vue';
import SideMenu from "@/components/sidemenu/SideMenu.vue";
import SideMenuPanel from "@/components/sidemenu/SideMenuPanel.vue";


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
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightMenu = ref<typeof SideMenuPanel>();
const executeActionRef = ref<typeof BeakerExecuteAction>();
const selectedTheme = ref(localStorage.getItem('theme') || 'light');
// const debugTabView = ref<{tabs: any[]}|null>(null);

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
    rightMenu.value?.selectPanel("action");
    nextTick(() => { selectedAction.value = actionName; });
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

// onMounted(() => {
//     updateContextInfo();
// });

</script>


<style lang="scss">
.beaker-dev-interface {
    padding-bottom: 1rem;
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
    // position: absolute;
    // top:0;
    // bottom: 0;
    // right: 0;
    // left: 0;
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
