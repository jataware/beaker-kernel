<template>
    <div class="beaker-notebook">
        <header>
            <Toolbar style="width: 100%; padding: 0.5rem 1rem;">
                <template #start>
                    <div class="status-bar">
                        <i class="pi pi-circle-fill" style="font-size: inherit; color: var(--green-400);" />
                        Connected
                    </div>
                    &nbsp;
                    &nbsp;
                    <Button
                        outlined
                        size="small"
                        icon="pi pi-angle-down"
                        iconPos="right"
                        class="connection-button"
                        @click="openContextSelection"
                        :label="selectedKernel"
                        :loading="!activeContext?.slug"
                    />
                </template>

                <template #center>
                    <h4 class="logo">
                        Beaker
                    </h4>
                </template>

                <template #end>
                    <nav>
                        <a
                            href="https://jataware.github.io/beaker-kernel"
                            rel="noopener"
                            target="_blank"
                        >
                            <Button
                                text
                                style="margin: 0; color: gray;"
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
                                style="margin: 0; color: gray;"
                                aria-label="Github Repository Link Icon"
                                icon="pi pi-github"
                            />
                        </a>
                    </nav>
                </template>
            </Toolbar>

        </header>

        <main style="display: flex;">

            <ContextTree />

            <Splitter class="splitter">

                <SplitterPanel
                    :size="70"
                    :minSize="30"
                    class="main-panel"
                >

                    <div class="notebook-controls">
                        <InputGroup>
                            <CellActionButton @click="addCell" primeIcon="plus" />
                            <CellActionButton @click="removeCell" primeIcon="minus" />
                            <CellActionButton @click="runCell()" primeIcon="play" />
                            <CellActionButton @click="identity" primeIcon="stop" />
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
                    :minSize="20"
                    :size="30"
                    class="right-splitter"
                >
                    <TabView :activeIndex="0">
                        <TabPanel header="Preview">
                            <div style="scroller-area">
                                <PreviewPane />
                            </div>
                        </TabPanel>

                        <TabPanel header="Execute">
                            <BeakerCustomMessage :session="session" :expanded="true"/>
                        </TabPanel>

                        <TabPanel header="Debug">
                            <div class="scroller-area">
                                <div>
                                    <Card>
                                        <template #title>State</template>
                                        <template #content>
                                            <pre class="notebook-json">
                                                {{JSON.stringify(JSON.parse(props.session.notebook.toJSON()), undefined, 2)}}
                                            </pre>
                                            <Button label="Copy" />
                                        </template>
                                    </Card>
                                </div>
                            </div>
                        </TabPanel>

                        <TabPanel header="Settings">
                        </TabPanel>

                    </TabView>
                </SplitterPanel>

            </Splitter>

        </main>

        <footer>
            <LoggingDrawer />
         </footer>
    </div>

    <BeakerContextSelection
        :session="props.session"
        :context-data="activeContext"
        :isOpen="contextSelectionOpen"
        @update-context-info="updateContextInfo"
    />

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, Component } from "vue";
import { IBeakerCell, BeakerBaseCell } from 'beaker-kernel';

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
import ContextTree from "./ContextTree.vue";
import PreviewPane from "./PreviewPane.vue";

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

const props = defineProps([
    "session"
]);

const activeContext = ref<{slug: string, class: string, context: any} | undefined>(undefined);
const selectedCellIndex = ref(0);
const selectedKernel = ref();
const contextSelectionOpen = ref(false);


const selectedCell = computed(() => {
    console.log(3, selectedCellIndex.value);
    return _getCell(selectedCellIndex.value);
});

const identity = (args) => {console.log('identity func called'); return args;};

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
    console.log(cell);
    if (cell === undefined) {
        console.log(2);
        cell = selectedCell.value;
    }
    else {
        console.log(1);
        cell = _getCell(cell);
    }
    console.log(cell);
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


function openContextSelection() {
    contextSelectionOpen.value = true;
}

const updateContextInfo = async () => {
    const activeContextInfo = await props.session.activeContext();
    activeContext.value = activeContextInfo;
    selectedKernel.value = activeContextInfo.slug;

    const savedContext = sessionStorage.getItem('active_context');
    contextSelectionOpen.value = !savedContext;
}

onBeforeMount(() => {
    if (props.session.notebook.cells.length <= 0) {
        props.session.addCodeCell("");
    }
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
    background: #fbfbfb;
    border-radius: 0.5rem;
    border: 1px solid #eaeaea;
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

.beaker-nb-toolbar {
    vertical-align: middle;
    height: 5rem;
    padding: 1em;
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
    border-top: 1px solid lightgray;
    border-bottom: 1px solid lightgray;
    background-color: var(--surface-c);
}

.beaker-cell.selected {
    border-right: 4px solid var(--primary-color);
    background-color: var(--surface-a);
}

.agent-query-container {
    flex: 0 1 8rem;
}

.status-bar {
    display: flex;
    line-height: inherit;
    align-items: center;
    min-width: 7rem;
    justify-content: space-evenly;
    color: var(--text-color);
}

.main-ide-panel {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 100%;
}

.logo {
    font-size: 1.5rem;
    margin: 0;
    padding: 0;
    width: 15rem;
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

</style>
