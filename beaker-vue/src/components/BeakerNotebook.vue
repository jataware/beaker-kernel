<template>
    <div class="beaker-notebook">
        <header>
            <Toolbar style="width: 100%; padding: 0.5rem 1rem;">
                <template #start>
                    <div class="status-bar">
                        <i class="pi pi-circle-fill" style="font-size: inherit; color: #81ea81;" />
                        Connected
                    </div>
                    &nbsp;
                    &nbsp;
                    <Dropdown 
                        v-model="selectedKernel"
                        :options="kernels" 
                        optionLabel="slug"
                        dataKey="slug"
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

            <div
                class="context-sidebar"
            >
                <h4 style="color: var(--text-color-secondary); margin: 1rem 1.25rem 0.25rem 1.25rem;">Context</h4>
                
                <Button 
                    class="context-toggle-button"
                    icon="pi pi-angle-right"
                    size="small"
                    outlined
                    aria-label="Toggle"
                    :class="{ 'button-rotate': contextPanelOpen }"
                    :onClick="toggleContextPanel"
                />

                <Tree
                    v-if="contextPanelOpen"
                    class="context-tree"
                    :value="contextNodes"
                    v-model:expandedKeys="contextExpandedKeys"
                 ></Tree>

            </div>

            <Splitter class="splitter">

                <SplitterPanel 
                    :size="70"
                    :minSize="30"
                    class="justify-content-center main-panel"
                >

                    <div class="notebook-controls">
                        <InputGroup>
                            <CellActionButton :onClick="addCell" primeIcon="plus" />
                            <CellActionButton :onClick="removeCell" primeIcon="minus" />
                            <CellActionButton :onClick="runCell" primeIcon="play" />
                            <CellActionButton :onClick="runCell" primeIcon="stop" />
                            <CellActionButton :onClick="runCell" primeIcon="refresh" />
                            <CellActionButton :onClick="identity" primeIcon="upload" />
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
                    class="justify-content-center right-splitter"
                >
                    <TabView :activeIndex="0">
                        <TabPanel header="Preview">
                            <div style="position: absolute; top:0; bottom: 0; right: 0; left: 0; overflow-y: auto;">
                                <Accordion multiple :activeIndex="[0]" style="height: 100%;">
                                    <AccordionTab header="Petri Net">
                                        <div style="width: 100%; display: flex; justify-content: flex-end; margin-bottom: 1rem">
                                            <SelectButton
                                                :allowEmpty="false"
                                                v-model="previewOneMockValue"
                                                :options="previewOneMimeTypes"
                                            />
                                        </div>
                                        <img class="preview-image" src="https://assets-global.website-files.com/6308b9e1771b56be92fe7491/636416a672f13fa441c4e7e6_petri-nets-preview.jpg">
                                    </AccordionTab>
                            
                                    <AccordionTab header="df_2">
                                        <DataTable :value="products">
                                            <Column field="price" header="x"></Column>
                                            <Column field="quantity" header="y"></Column>
                                        </DataTable>                        
                                    </AccordionTab>
                                </Accordion>
                            </div>
                        </TabPanel>

                        <TabPanel header="Execute">
                            <BeakerCustomMessage :session="session" :expanded="true"/>
                        </TabPanel>

                        <TabPanel header="Debug">
                            <div style="position: absolute; top:0; bottom: 0; right: 0; left: 0; overflow-y: auto;">
                                <div class="card flex align-items-center">
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
        :expanded="true"
        :context-data="activeContext"
        @update-context-info="updateContextInfo"
    />

</template>

<script setup lang="tsx">

import { ref, onBeforeMount, onMounted, defineProps, computed, Component } from "vue";
import { BeakerSession, IBeakerCell, BeakerBaseCell } from 'beaker-kernel';

import Card from 'primevue/card';
import Button from 'primevue/button';
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Toolbar from 'primevue/toolbar';
import Tree from 'primevue/tree';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import SelectButton from 'primevue/selectbutton';

// import Sidebar from 'primevue/sidebar';

import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
// import ColumnGroup from 'primevue/columngroup';   // optional
// import Row from 'primevue/row';                   // optional
// import DataView from 'primevue/dataview';
// import DataViewLayoutOptions from 'primevue/dataviewlayoutoptions'   // optional
import Dropdown from 'primevue/dropdown';
import InputGroup from 'primevue/inputgroup';

import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import LoggingDrawer from './LoggingDrawer.vue';
import BeakerAgentQuery from './BeakerAgentQuery.vue';
import BeakerContextSelection from "./BeakerContextSelection.vue";
import BeakerCustomMessage from "./BeakerCustomMessage.vue";

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

const props = defineProps([
    "session"
]);


const previewOneMockValue = ref('PNG');
const previewOneMimeTypes = ref(['PNG', 'LATEX']);

const products = [
{
    id: '1000',
    name: 'Bamboo Watch',
    description: 'Product Description',
    price: 65,
    category: 'Accessories',
    quantity: 24,
    inventoryStatus: 'INSTOCK',
    rating: 5
},
{
    id: '1000',
    name: 'Bamboo Watch',
    description: 'Product Description',
    price: 65,
    category: 'Accessories',
    quantity: 24,
    inventoryStatus: 'INSTOCK',
    rating: 5
}];

const contextNodes = [{
    key: '0',
    label: 'Kernel',
    data: 'Kernel Details',
    icon: 'pi pi-fw pi-cog',
    expanded: true,
    children: [{
        key: '0-0',
        label: 'language=python',
        data: 'Python',
        icon: 'pi pi-fw pi-align-justify'
    },
    {
        key: '0-1',
        label: 'version=3.11.2',
        data: '3.11.2',
        icon: 'pi pi-fw pi-wrench'
    }]
},
{
    key: '1',
    label: 'env',
    data: 'Environment Variables',
    icon: 'pi pi-fw pi-cloud',
    expanded: true,
    children: [{
        key: '1-0',
        label: 'deployment=dev',
            data: 'development',
        icon: 'pi pi-fw pi-cog'
    },
    {
        key: '1-1',
        label: 'agent-backend=openai',
        data: 'openai',
        icon: 'pi pi-fw pi-qrcode'
    }]
}];

const activeContext = ref<{slug: string, class: string, context: any} | undefined>(undefined);
// const contextSelectionExpanded = ref(false);
const selectedCellIndex = ref(0);

const contextExpandedKeys = ref({0: true, 1: true});

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const contextPanelOpen = ref(true);
const toggleContextPanel = () => {
    contextPanelOpen.value = !contextPanelOpen.value;
}

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

// activeContext?.slug

const selectedKernel = ref();
const kernels = ref([
    { slug: 'pypackage' },
    { slug: 'julia' }
]);


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
    if (cell) {
        cell = _getCell(cell);
    }
    else {
        cell = selectedCell.value;
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
    //
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

const updateContextInfo = async () => {
    const activeContextInfo = await props.session.activeContext();
    activeContext.value = activeContextInfo;
    selectedKernel.value = {slug: activeContextInfo.slug};
    // contextSelectionExpanded.value = false;
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
}

.main-ide-panel {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: 100%;
}
.btn {
    border: gray 1px lightgray;
    padding: 1ex;
    cursor: pointer;
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

.context-tree {
    padding: 0;
    border: none;
    
    width: 19rem;
    padding: 0.75rem;
    
    .p-tree-container .p-treenode .p-treenode-content {
        padding: 0;
        border: none;
    }
}

.p-accordion .p-accordion-header .p-accordion-header-link {
    background: var(--surface-a);
}

.preview-image {
    width: 100%;
}

.p-selectbutton .p-button {
    background: #f1f5f9;
    border: 1px solid #f1f5f9;
    color: #64748b;
    transition: background-color 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, outline-color 0.2s;
    height: 2rem;
}


.p-selectbutton .p-button.p-highlight {
    background: #ffffff;
    border-color: #4e34bf;
    border: 3px solid var(--gray-50);
}

.p-selectbutton .p-button.p-highlight::before {
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.02), 0px 1px 2px 0px rgba(0, 0, 0, 0.04);
}

.context-sidebar {
    display: flex;
    flex-direction: column;
    position: relative;
}

.context-toggle-button {
    position: absolute;
    right: -0.5rem;
    top: 40%;
    background: var(--surface-a);
    border-color: var(--surface-300);
    color: var(--primary-300);
}

.button-rotate {
    transform: rotate(180deg);
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

</style>

