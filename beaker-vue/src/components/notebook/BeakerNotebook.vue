<template>
    <div class="beaker-notebook">
        <div class="controls">
            <InputGroup>
                <Button
                    v-if="!props.singleCell"
                    @click="addCell()"
                    icon="pi pi-plus"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    v-if="!props.singleCell"
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
const selectedCellIndex = ref(0);
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

const applyTheme = () => {
    const themeLink = document.querySelector('#primevue-theme');
    themeLink.href = `/themes/soho-${selectedTheme.value}/theme.css`;
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

const runCell = (cell?: number | IBeakerCell) => {
    beakerNotebookRef.value.runCell(cell);
    // console.log(cell);
    // if (cell === undefined) {
    //     cell = selectedCell.value;
    // }
    // else {
    //     cell = _getCell(cell);
    // }
    // if (cell !== undefined) {
    //     cell.execute(session);
    // }
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

const focusSelectedCell = (ref) => {
    let parent = document;
    if (ref && ref.value){
      parent = ref.value;
    }
    const elem: HTMLElement|null = parent.querySelector('.beaker-cell.selected');
    if (elem) {
        elem.focus();
    }
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

onBeforeMount(() => {
    if (cellCount.value <= 0) {
        session.addCodeCell("");
    }
    applyTheme();
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
