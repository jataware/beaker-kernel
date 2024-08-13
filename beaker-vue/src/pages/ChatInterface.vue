<template>
    <div id="app">
        <BeakerSession
            ref="beakerSessionRef"
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
                <header style="justify-content: center;">
                    <VerticalToolbar style="align-self: flex-start;">
                        <template #start>
                            <Button
                                outlined
                                size="small"
                                icon="pi pi-angle-down"
                                iconPos="right"
                                class="connection-button"
                                @click="() => {contextSelectionOpen = !contextSelectionOpen}"
                                v-tooltip.right="{
                                    value: `${statusLabel}: ${beakerSessionRef?.activeContext?.slug || ''}`, 
                                    showDelay: 300
                                }"
                                :label="beakerSessionRef?.activeContext?.slug"
                                :loading="!(beakerSessionRef?.activeContext?.slug)"
                            >
                                <i class="pi pi-circle-fill" :style="`font-size: inherit; color: var(--${connectionColor});`" />
                            </Button>
                            <ResetButton :on-reset-callback="() => setContext({})"/>
                            <Button
                                @click="toggleFileMenu"
                                v-tooltip.right="{value: 'Show file menu', showDelay: 300}"
                                icon="pi pi-file-export"
                                size="small"
                                severity="info"
                                text
                            />
                            <OverlayPanel ref="isFileMenuOpen" style="overflow-y: auto; height:40em;">
                                <BeakerFilePane/>
                            </OverlayPanel>
                            <DarkModeButton :toggle-dark-mode="toggleDarkMode"/>
                        </template>
                        <template #end>

                        </template>
                    </VerticalToolbar>
                </header>
                <main style="display: flex; overflow: auto;">
                    <div class="central-panel">
                        <BeakerNotebook
                            ref="beakerNotebookRef"
                            :cell-map="cellComponentMapping"
                            v-keybindings="notebookKeyBindings"
                        >
                            <ChatPanel
                                ref="chatPanelRef"
                                :selected-cell="beakerNotebookRef?.selectedCellId"
                            >
                                <template #notebook-background>
                                    <div class="welcome-placeholder">
                                    </div>
                                </template>
                            </ChatPanel>
                            <AgentQuery
                                class="agent-query-container"
                            />
                        </BeakerNotebook>
                    </div>
                    <HelpSidebar></HelpSidebar>
                </main>
            </div>
            <BeakerContextSelection
                :isOpen="contextSelectionOpen"
                :contextProcessing="contextProcessing"
                @context-changed="(contextData) => {beakerSessionRef.setContext(contextData)}"
                @close-context-selection="contextSelectionOpen = false"
            />
        </BeakerSession>
        <!-- Modals, popups and globals -->
        <Toast position="bottom-right" />
    </div>
</template>

<script setup lang="ts">
import AgentQuery from '@/components/chat-interface/AgentQuery.vue';
import ChatPanel from '@/components/chat-interface/ChatPanel.vue';
import ResetButton from '@/components/chat-interface/ResetButton.vue';
import DarkModeButton from '@/components/chat-interface/DarkModeButton.vue';
import HelpSidebar from '@/components/chat-interface/HelpSidebar.vue';
import VerticalToolbar from '@/components/chat-interface/VerticalToolbar.vue';

import BeakerCodeCell from '@/components/cell/BeakerCodeCell.vue';
import BeakerLLMQueryCell from '@/components/cell/BeakerLLMQueryCell.vue';
import BeakerMarkdownCell from '@/components/cell/BeakerMarkdownCell.vue';
import BeakerRawCell from '@/components/cell/BeakerRawCell.vue';

import BeakerFilePane from '@/components/dev-interface/BeakerFilePane.vue';

import BeakerNotebook from '@/components/notebook/BeakerNotebook.vue';
import { BeakerNotebookComponentType } from '@/components/notebook/BeakerNotebook.vue';

import BeakerSession from '@/components/session/BeakerSession.vue';

import { standardRendererFactories } from '@jupyterlab/rendermime';

import { JupyterMimeRenderer } from 'beaker-kernel';

import Button from "primevue/button";
import OverlayPanel from 'primevue/overlaypanel';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

import { defineProps, inject, nextTick, onBeforeMount, onUnmounted, provide, ref, defineEmits, computed } from 'vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';

const { theme, toggleDarkMode } = inject('theme');
const toast = useToast();
const chatPanelRef = ref();
const notebook = inject<BeakerNotebookComponentType>("notebook");
const contextSelectionOpen = ref(false);
const contextProcessing = ref(false);
import BeakerContextSelection from '@/components/session/BeakerContextSelection.vue';



// NOTE: Right now, we don't want the context changing
const activeContext = ref();
const beakerNotebookRef = ref();
const setContext = (contextInfo) => {
    if (contextInfo?.slug !== 'default') {
        beakerSessionRef.value.setContext(activeContext);
    }
}

// TODO -- WARNING: showToast is only defined locally, but provided/used everywhere. Move to session?
// Let's only use severity=success|warning|danger(=error) for now
const showToast = ({title, detail, life=3000, severity='success', position='bottom-right'}) => {
    toast.add({
        summary: title,
        detail,
        life,
        // for options, seee https://primevue.org/toast/
        severity,
        position
    });
};

provide('show_toast', showToast);

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

const renderers = [
    ...standardRendererFactories.map((factory) => new JupyterMimeRenderer(factory)).map(wrapJupyterRenderer),
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

const isFileMenuOpen = ref();

const toggleFileMenu = (event) => {
    isFileMenuOpen.value.toggle(event);
}

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const previewData = ref<any>();
const saveInterval = ref();
const beakerSessionRef = ref<typeof BeakerSession>();

const statusLabels = {
    unknown: 'Unknown',
    starting: 'Starting',
    idle: 'Ready',
    busy: 'Busy',
    terminating: 'Terminating',
    restarting: 'Restarting',
    autorestarting: 'Autorestarting',
    dead: 'Dead',
    // This extends kernel status for now.
    connected: 'Connected',
    connecting: 'Connecting'
}

const statusColors = {
    connected: 'green-300',
    idle: 'green-400',
    connecting: 'green-200',
    busy: 'orange-400',
};

const statusLabel = computed(() => {
    return statusLabels[beakerSessionRef?.value?.status] || "unknown";

});

const connectionColor = computed(() => {
    // return connectionStatusColorMap[beakerSession.status];
    return statusColors[beakerSessionRef?.value?.status] || "grey-200"
});

const iopubMessage = (msg) => {
    if (msg.header.msg_type === "preview") {
        previewData.value = msg.content;
    } else if (msg.header.msg_type === "debug_event") {
        debugLogs.value.push({
            type: msg.content.event,
            body: msg.content.body,
            timestamp: msg.header.date,
        });
    } else if (msg.header.msg_type === "job_response") {
        beakerSessionRef.value.session.addMarkdownCell(msg.content.response);
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

onBeforeMount(() => {
    document.title = "Analyst UI"
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

const notebookKeyBindings = {
    "keydown.enter.ctrl.prevent.capture.in-cell": () => {
        beakerNotebookRef.value.selectedCell().execute();
        beakerNotebookRef.value.selectedCell().exit();
    },
    "keydown.enter.shift.prevent.capture.in-cell": () => {
        const targetCell = beakerNotebookRef.value.selectedCell();
        targetCell.execute();
        if (!beakerNotebookRef.value.selectNextCell()) {
            beakerNotebookRef.value.insertCellAfter(
                targetCell,
                targetCell.cell.cell_type,
                true
            );
        }
    },
    "keydown.enter.exact.prevent.in-cell.!in-editor": () => {
        beakerNotebookRef.value.selectedCell().enter();
    },
    "keydown.esc.exact.prevent.in-cell": () => {
        beakerNotebookRef.value.selectedCell().exit();
    },
    "keydown.up.in-cell.!in-editor": () => {
        beakerNotebookRef.value.selectPrevCell();
    },
    "keydown.j.in-cell.!in-editor": () => {
        beakerNotebookRef.value.selectPrevCell();
    },
    "keydown.down.in-cell.!in-editor": () => {
        beakerNotebookRef.value.selectNextCell();
    },
    "keydown.k.in-cell.!in-editor": () => {
        beakerNotebookRef.value.selectNextCell();
    },
    "keydown.a.prevent.in-cell.!in-editor": (evt) => {
        const notebook = beakerNotebookRef.value;
        notebook.selectedCell().exit();
        notebook.insertCellBefore();
    },
    "keydown.b.prevent.in-cell.!in-editor": () => {
        const notebook = beakerNotebookRef.value;
        notebook.selectedCell().exit();
        notebook.insertCellAfter();
    },
    "keydown.d.selected.!in-editor": () => {
        console.log("delete");
        //
        // TODO implement double press for action
        // const notebook = beakerNotebookRef.value;
        // notebook.removeCell();
    },
}

const sessionKeybindings = {}

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
    grid-area: l-sidebar;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
main {
    grid-area: main;
}
footer {
    grid-area: r-sidebar;
}
.main-panel {
    display: flex;
    flex-direction: column;
    &:focus {
        outline: none;
    }
}
div.beaker-notebook {
    padding-top: 1rem;
}

.central-panel {
    flex: 1000;
    display: flex;
    flex-direction: column;
    max-width: 820px;
    margin: auto;
}

.beaker-dev-interface {
    padding-bottom: 1rem;
    height: 100vh;
    width: 100vw;
    display: grid;
    grid-gap: 1px;
    grid-template-areas:
        "l-sidebar main r-sidebar"
        "l-sidebar main r-sidebar"
        "l-sidebar main r-sidebar";
    grid-template-columns: auto 1fr auto;
    grid-template-rows: auto 1fr auto;
}

div.cell-container {
    position: relative;
    display: flex;
    flex: 1;
    background-color: var(--surface-b);
    flex-direction: column;
    z-index: 3;
    overflow: auto;
}

div.llm-prompt-container h2.llm-prompt-text {
    font-size: 1.25rem;
    max-width: 70%;
    margin-left: auto;
    background-color: var(--surface-a);
    padding: 1rem;
    border-radius: 16px;
}

div.llm-prompt-container {
    text-align: right;
    max-width: 60%;
    align-self: end;
}

div.query {
    display: flex;
    flex-direction: column;
}

div.query-steps {
    display: none;
}

div.events div.query-answer {
    background-color: var(--surface-b);
}

div.beaker-toolbar {
    flex-direction: column;
}

div.beaker-toolbar div {
    flex-direction: column;
}

div.central-panel, div.beaker-notebook {
    height: 100%;
}

button.connection-button {
    border: none;
}

</style>