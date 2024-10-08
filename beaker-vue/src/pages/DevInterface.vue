<template>
    <div id="app">
        <BeakerSession
            ref="beakerSession"
            :connectionSettings="props.config"
            sessionName="dev_interface"
            :sessionId="sessionId"
            defaultKernel="beaker_kernel"
            :renderers="renderers"
            @iopub-msg="iopubMessage"
            @unhandled-msg="unhandledMessage"
            @any-msg="anyMessage"
            @session-status-changed="statusChanged"
            v-keybindings="sessionKeybindings"
        >
            <div class="beaker-dev-interface">
            <header>
                <BeakerHeader
                    :connectionStatus="connectionStatus"
                    :loading="!activeContext?.slug"
                    @select-kernel="toggleContextSelection"
                />
            </header>
            <main style="display: flex; overflow: auto;">
                <SideMenu
                    position="left"
                    :show-label="true"
                    highlight="line"
                >
                    <SideMenuPanel label="Context" icon="pi pi-home">
                        <ContextTree :context="activeContext?.info" @action-selected="selectAction"/>
                    </SideMenuPanel>
                </SideMenu>

                    <div class="central-panel"
                    >
                        <BeakerNotebook
                            ref="beakerNotebookRef"
                            :cell-map="cellComponentMapping"
                            v-keybindings.top="notebookKeyBindings"
                        >
                            <BeakerNotebookToolbar/>
                            <BeakerNotebookPanel
                                :selected-cell="beakerNotebookRef?.selectedCellId"
                                v-autoscroll
                            >
                                <template #notebook-background>
                                    <div class="welcome-placeholder">
                                        <SvgPlaceholder />
                                    </div>
                                </template>
                            </BeakerNotebookPanel>
                            <BeakerAgentQuery
                                class="agent-query-container"
                            />
                        </BeakerNotebook>
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
                                            :rawMessages="rawMessages"
                                        />
                                    </template>
                                </Card>
                            </SideMenuPanel>

                            <SideMenuPanel tabId="logging" label="Logging" icon="pi pi-list" >
                                <LoggingPane :entries="debugLogs" @clear-logs="debugLogs.splice(0, debugLogs.length)" v-autoscroll />
                            </SideMenuPanel>

                            <SideMenuPanel label="Messages" icon="pi pi-comments">
                                <LoggingPane :entries="rawMessages" @clear-logs="rawMessages.splice(0, rawMessages.length)" v-autoscroll />
                            </SideMenuPanel>

                            <SideMenuPanel label="Files" icon="pi pi-file-export">
                                <BeakerFilePane />
                            </SideMenuPanel>

                        </SideMenu>
            </main>
            <footer>
                <FooterDrawer />
            </footer>
            </div>
            <slot name="context-selection-popup">
                <BeakerContextSelection
                    :isOpen="contextSelectionOpen"
                    :toggleOpen="toggleContextSelection"
                    :contextProcessing="contextProcessing"
                    @context-changed="(contextData) => {beakerSession.setContext(contextData)}"
                    @close-context-selection="contextSelectionOpen = false"
                />
            </slot>
        </BeakerSession>

        <!-- Modals, popups and globals -->
        <Toast position="bottom-right" />
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, onBeforeMount, provide, nextTick, onUnmounted } from 'vue';
import { JupyterMimeRenderer, IBeakerCell, IMimeRenderer } from 'beaker-kernel';
import BeakerNotebook from '../components/notebook/BeakerNotebook.vue';
import BeakerNotebookToolbar from '../components/notebook/BeakerNotebookToolbar.vue';
import BeakerNotebookPanel from '../components/notebook/BeakerNotebookPanel.vue';
import BeakerSession from '../components/session/BeakerSession.vue';
import BeakerHeader from '../components/dev-interface/BeakerHeader.vue';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer, BeakerRenderOutput } from '../renderers';
import { standardRendererFactories } from '@jupyterlab/rendermime';
import scrollIntoView from 'scroll-into-view-if-needed';

import Card from 'primevue/card';
import LoggingPane from '../components/dev-interface/LoggingPane.vue';
import BeakerAgentQuery from '../components/agent/BeakerAgentQuery.vue';
import BeakerContextSelection from "../components/session/BeakerContextSelection.vue";
import BeakerExecuteAction from "../components/dev-interface/BeakerExecuteAction.vue";
import ContextTree from '../components/dev-interface/ContextTree.vue';
import BeakerFilePane from '../components/dev-interface/BeakerFilePane.vue';
import PreviewPane from '../components/dev-interface/PreviewPane.vue';
import SvgPlaceholder from '../components/misc/SvgPlaceholder.vue';
import SideMenu from "../components/sidemenu/SideMenu.vue";
import SideMenuPanel from "../components/sidemenu/SideMenuPanel.vue";
import FooterDrawer from '../components/dev-interface/FooterDrawer.vue';

import BeakerCodeCell from '../components/cell/BeakerCodeCell.vue';
import BeakerMarkdownCell from '../components/cell/BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from '../components/cell/BeakerLLMQueryCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';


const toast = useToast();

const activeContext = ref();
const beakerNotebookRef = ref();


// TODO -- WARNING: showToast is only defined locally, but provided/used everywhere. Move to session?
// Let's only use severity=success|warning|danger(=error) for now
const showToast = ({title, detail, life=3000, severity=('success' as undefined), position='bottom-right'}) => {
    toast.add({
        summary: title,
        detail,
        life,
        // for options, seee https://primevue.org/toast/
        severity,
        // position
    });
};

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.has("session") ? urlParams.get("session") : "dev_session";

const props = defineProps([
    "config",
    "connectionSettings",
    "sessionName",
    "sessionId",
    "defaultKernel",
    "renderers",
]);

const renderers: IMimeRenderer<BeakerRenderOutput>[] = [
    ...standardRendererFactories.map((factory: any) => new JupyterMimeRenderer(factory)).map(wrapJupyterRenderer),
    JSONRenderer,
    LatexRenderer,
    DecapodeRenderer,
];

const cellComponentMapping = {
    'code': BeakerCodeCell,
    'markdown': BeakerMarkdownCell,
    'query': BeakerLLMQueryCell,
    'raw': BeakerRawCell,
}

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const previewData = ref<any>();
const saveInterval = ref();
const copiedCell = ref<IBeakerCell | null>(null);
const notebookRef = ref<typeof BeakerNotebook>();
const beakerSession = ref<typeof BeakerSession>();

const contextSelectionOpen = ref(false);
const activeContextPayload = ref<any>(null);
const contextProcessing = ref(false);
const rightMenu = ref<typeof SideMenuPanel>();
const executeActionRef = ref<typeof BeakerExecuteAction>();

const iopubMessage = (msg) => {
    if (msg.header.msg_type === "preview") {
        previewData.value = msg.content;
    } else if (msg.header.msg_type === "debug_event") {
        debugLogs.value.push({
            type: msg.content.event,
            body: msg.content.body,
            timestamp: msg.header.date,
        });
    }
};

const anyMessage = (msg, direction) => {
    rawMessages.value.push({
        type: direction,
        body: msg,
        timestamp: msg.header.date,
    });
};

const unhandledMessage = (msg) => {
    console.log("Unhandled message recieved", msg);
}

const statusChanged = (newStatus) => {
    connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
};

const toggleContextSelection = () => {
    contextSelectionOpen.value = !contextSelectionOpen.value;
};

const selectAction = (actionName: string) => {
    rightMenu.value?.selectPanel("action");
    executeActionRef.value?.selectAction(actionName);
};

onBeforeMount(() => {
    document.title = "Beaker Development Interface"
    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }

    if (notebookData[sessionId]?.data) {
        nextTick(() => {
            if (beakerNotebookRef.value?.notebook) {
                beakerNotebookRef.value?.notebook.loadFromIPynb(notebookData[sessionId].data);
                nextTick(() => {
                    beakerNotebookRef.value?.selectCell(notebookData[sessionId].selectedCell);
                });
            }
        });
    }
    saveInterval.value = setInterval(snapshot, 30000);
    window.addEventListener("beforeunload", snapshot);
});

onUnmounted(() => {
    clearInterval(saveInterval.value);
    saveInterval.value = null;
    window.removeEventListener("beforeunload", snapshot);
});

// TODO: See above. Move somewhere better.
provide('show_toast', showToast);

const prevCellKey = () => {
    beakerNotebookRef.value?.selectPrevCell();
};

const nextCellKey = () => {
    beakerNotebookRef.value?.selectNextCell();
};

const keyBindingState = {};
const notebookKeyBindings = {
    "keydown.enter.ctrl.prevent.capture.in-cell": () => {
        beakerNotebookRef.value?.selectedCell().execute();
        beakerNotebookRef.value?.selectedCell().exit();
    },
    "keydown.enter.shift.prevent.capture.in-cell": () => {
        const targetCell = beakerNotebookRef.value?.selectedCell();
        targetCell.execute();
        if (!beakerNotebookRef.value?.selectNextCell()) {
            // Create a new cell after the current cell if one doesn't exist.
            beakerNotebookRef.value?.insertCellAfter(
                targetCell,
                targetCell.cell.cell_type,
                true
            );
            // Focus the editor only if we are creating a new cell.
            nextTick(() => {
                beakerNotebookRef.value?.selectedCell().enter();
            });
        }
    },
    "keydown.enter.exact.prevent.stop.!in-editor": () => {
        beakerNotebookRef.value?.selectedCell().enter();
    },
    "keydown.esc.exact.prevent": () => {
        beakerNotebookRef.value?.selectedCell().exit();
    },
    "keydown.up.!in-editor.prevent": prevCellKey,
    "keydown.k.!in-editor": prevCellKey,
    "keydown.down.!in-editor.prevent": nextCellKey,
    "keydown.j.!in-editor": nextCellKey,
    "keydown.a.prevent.!in-editor": (evt) => {
        const notebook = beakerNotebookRef.value;
        notebook?.selectedCell().exit();
        notebook?.insertCellBefore();
    },
    "keydown.b.prevent.!in-editor": () => {
        const notebook = beakerNotebookRef.value;
        notebook?.selectedCell().exit();
        notebook?.insertCellAfter();
    },
    "keydown.d.!in-editor": () => {
        const notebook = beakerNotebookRef.value;
        const cell = notebook.selectedCell();
        const deleteCallback = () => {
            delete keyBindingState['d'];
        };
        const state = keyBindingState['d'];

        if (state === undefined) {
            const timeoutId = setTimeout(deleteCallback, 1000);
            keyBindingState['d'] = {
                cell_id: cell.id,
                timeout: timeoutId,
            }
        }
        else {
            const {cell_id, timeout} = keyBindingState['d'];
            if (cell_id === cell.id) {
                notebook?.removeCell(cell);
                copiedCell.value = cell.cell;
                delete keyBindingState['d'];
            }
            if (timeout) {
                window.clearTimeout(timeout);
            }
        }
    },
    "keydown.y.!in-editor": () => {
        const notebook = beakerNotebookRef.value;
        const cell = notebook.selectedCell();
        const copyCallback = () => {
            delete keyBindingState['y'];
        };
        const state = keyBindingState['y'];

        if (state === undefined) {
            const timeoutId = setTimeout(copyCallback, 1000);
            keyBindingState['y'] = {
                cell_id: cell.id,
                timeout: timeoutId,
            }
        }
        else {
            const {cell_id, timeout} = keyBindingState['y'];
            if (cell_id === cell.id) {
                copiedCell.value = cell.cell;
                delete keyBindingState['y'];
            }
            if (timeout) {
                window.clearTimeout(timeout);
            }
        }
    },
    "keydown.p.!in-editor": () => {
        const notebook = beakerNotebookRef.value;
        const oldCell = copiedCell.value;
        if (oldCell !== null) {
            const newCell: IBeakerCell = notebook?.insertCellAfter(notebook.selectedCell(), oldCell);
            for (const key of Object.keys(oldCell).filter((k) => k !== "id")) {
                newCell[key] = oldCell[key];
            }
            copiedCell.value = null;
        }
    },
}

const sessionKeybindings = {
}

const snapshot = () => {
    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }
    // Only save state if there is state to save
    if (beakerNotebookRef.value?.notebook) {
        notebookData[sessionId] = {
            data: beakerNotebookRef.value?.notebook.toIPynb(),
            selectedCell: beakerNotebookRef.value?.selectedCellId,
        };
        localStorage.setItem("notebookData", JSON.stringify(notebookData));
    }
};

</script>

<style lang="scss">
#app {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background-color: var(--surface-b);
}

header {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

main {
    grid-area: main;
    padding-top: 2px;
    padding-bottom: 2px;
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


.central-panel {
    flex: 1000;
    display: flex;
    flex-direction: column;
}

.beaker-dev-interface {
    padding-bottom: 2px;
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

.beaker-dev-interface .p-toolbar {
    border: none;
}

</style>
