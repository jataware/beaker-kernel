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
                            :onClick="toggleDarkMode"
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

            <Splitter class="splitter">

                <SplitterPanel
                    :size="70"
                    :minSize="30"
                    class="main-panel"
                >

                    <div class="notebook-controls">
                        <InputGroup>
                            <CellActionButton
                                @click="addCell"
                                v-tooltip.bottom="{value: 'Add New Cell', showDelay: 300}"
                                primeIcon="plus"
                            />
                            <CellActionButton
                                @click="removeCell"
                                v-tooltip.bottom="{value: 'Remove Selected Cell', showDelay: 300}"
                                primeIcon="minus"
                            />
                            <CellActionButton
                                @click="runCell()"
                                v-tooltip.bottom="{value: 'Run Selected Cell', showDelay: 300}"
                                primeIcon="play"
                            />
                            <CellActionButton
                                @click="identity"
                                v-tooltip.bottom="{value: 'Stop Execution', showDelay: 300}"
                                primeIcon="stop"
                            />
                            <CellActionButton @click="identity" primeIcon="refresh" />
                            <CellActionButton @click="identity" primeIcon="upload" />
                        </InputGroup>
                    </div>

                    <div class="ide-cells">
                        <div style="flex: 1; position: relative;">
                            <div class="cell-container">
                                <Component
                                    v-for="(cell, index) in props.session?.notebook?.cells" :key="cell.id" :cell="cell"
                                    :is="componentMap[cell.cell_type]"
                                    :session="props.session" class="beaker-cell" :class="{selected: (index == selectedCellIndex)}"
                                    :context-data="activeContext"
                                    :theme="selectedTheme"
                                    @click="selectCell(index)"
                                />
                            </div>
                        </div>

                        <BeakerAgentQuery
                            class="agent-query-container"
                            :session="session"
                            @select-cell="selectCell"
                            @run-cell="runCell"
                        />
                    </div>
                </SplitterPanel>

                <SplitterPanel
                    :minSize="27"
                    :size="30"
                    class="right-splitter"
                >
                    <TabView :activeIndex="0">
                        <TabPanel header="Preview">
                            <div class="scroller-area">
                                <PreviewPane />
                            </div>
                        </TabPanel>

                        <TabPanel header="Debug">
                            <div class="scroller-area">
                                <Card class="debug-card">
                                    <template #title>Custom Message</template>
                                    <template #content>
                                        <BeakerCustomMessage
                                            :theme="selectedTheme"
                                            :session="session"
                                            :expanded="true"
                                        />
                                    </template>
                                </Card>
                                <Card class="debug-card">
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
                                </Card>
                            </div>
                        </TabPanel>

                        <TabPanel header="Logging">
                            <LoggingPane />
                        </TabPanel>

                    </TabView>
                </SplitterPanel>

            </Splitter>

        </main>

        <!-- TODO may use HTML comments to hide footer -->
        <footer>
            <LoggingDrawer />
         </footer>
    </div>

    <BeakerContextSelection
        :session="props.session"
        :activeContext="activeContext"
        :isOpen="contextSelectionOpen"
        :toggleOpen="toggleContextSelection"
        @update-context-info="updateContextInfo"
        :theme="selectedTheme"
    />

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, Component } from "vue";
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

import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import BeakerAgentQuery from './BeakerAgentQuery.vue';
import BeakerContextSelection from "./BeakerContextSelection.vue";
import BeakerCustomMessage from "./BeakerCustomMessage.vue";
import LoggingDrawer from './LoggingDrawer.vue';
import LoggingPane from './LoggingPane.vue';
import ContextTree from "./ContextTree.vue";
import PreviewPane from "./PreviewPane.vue";


function capitalize(s: string) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

const props = defineProps([
    "session",
    "connectionStatus"
]);

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

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const identity = (args: any) => {console.log('identity func called'); return args;};

const CellActionButton = ({primeIcon, onClick}) => (
    <Button
        onClick={onClick}
        icon={`pi pi-${primeIcon}`}
        size="small"
        severity="info"
        text
    />
);

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
    return `pi pi-${selectedTheme.value == 'light' ? 'sun' : 'moon'}`;
})

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

const addCell = () => {
    props.session.addCodeCell("");
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
    if (props.session.notebook.cells.length == 0) {
        props.session.addCodeCell("");
    }
    // Fixup the selection if we remove the last item.
    if (selectedCellIndex.value <= props.session.notebook.cells.length) {
        selectedCellIndex.value = props.session.notebook.cells.length - 1;
    }
};

const resetNB = async () => {
    // TODO hook to notebook-control button
    await props.session.reset();
    if (props.session.notebook.cells.length == 0) {
        props.session.addCodeCell("");
    }
};

const loadNB = () => {
    console.log('load notebook');
};

const exportNB = () => {
    console.log('export notebook')
}


function toggleContextSelection() {
    contextSelectionOpen.value = !contextSelectionOpen.value;
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
    background: var(--surface-b);
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
}

.ide-cells {
    display: flex;
    flex-direction: column;
    height: 100%;
    z-index: 3;
    background: var(--surface-a);
}

.splitter {
    height: 100%;
    flex: 1;
}

.beaker-cell {
    border-bottom: 2px solid var(--surface-b);
    background-color: var(--surface-c);
    border-right: 5px solid transparent;
}

.beaker-cell.selected {
    border-right: 5px solid var(--purple-400);
    border-top: unset;
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
    justify-content: left;
    align-items: center;

    .p-inputgroup {
        width: unset;
    }
}

.right-splitter {
    display: flex;
    flex-direction: column;

    .p-tabview {
        height: 100%;
        display: flex;
        flex-direction: column;
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
            margin: 0;
            padding: 0;
            font-weight: 300;
            color: var(--gray-500);

            @media(max-width: 885px) {
                .longer-title {
                    display: none;
                }
            }
        }
    }
   
}

</style>
