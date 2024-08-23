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
                            <Button
                                @click="resetNotebook"
                                v-tooltip.right="{value: 'Reset notebook', showDelay: 300}"
                                icon="pi pi-refresh"
                                size="small"
                                severity="info"
                                text
                            />
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
                        <template #center>
                            <div class="vertical-toolbar-divider" />
                        </template>
                        <template #end>
                            <a  
                                :href="`/${sessionId == 'dev_session' ? '' : '?session=' + sessionId}`" 
                                v-tooltip.right="{value: 'To Notebook View', showDelay: 300}"
                            >
                                <Button
                                    icon="pi pi-book"
                                    size="small"
                                    severity="info"
                                    text
                                />
                            </a>
                        </template>
                    </VerticalToolbar>
                </header>
                <main style="display: flex; overflow-y: auto; overflow-x: hidden;">
                    <div class="central-panel">
                        <ChatPanel
                            ref="chatPanelRef"
                            v-autoscroll
                        >
                            <template #help-text>
                                <p>Hi! I'm your Beaker Agent and I can help you do programming and software engineering tasks.</p>
                                <p>Feel free to ask me about whatever the context specializes in..</p>
                                <p>
                                    On top of answering questions, I can actually run code in a python environment, and evaluate the results. 
                                    This lets me do some pretty awesome things like: web scraping, or plotting and exploring data.
                                    Just shoot me a message when you're ready to get started.
                                </p>
                            </template>
                            <template #notebook-background>
                                <div class="welcome-placeholder">
                                </div>
                            </template>
                        </ChatPanel>
                        <AgentQuery
                            class="agent-query-container"
                        />
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
import AgentQuery from '../components/chat-interface/AgentQuery.vue';
import ChatPanel from '../components/chat-interface/ChatPanel.vue';
import DarkModeButton from '../components/chat-interface/DarkModeButton.vue';
import HelpSidebar from '../components/chat-interface/HelpSidebar.vue';
import VerticalToolbar from '../components/chat-interface/VerticalToolbar.vue';

import BeakerCodeCell from '../components/cell/BeakerCodeCell.vue';
import BeakerLLMQueryCell from '../components/cell/BeakerLLMQueryCell.vue';
import BeakerMarkdownCell from '../components/cell/BeakerMarkdownCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';

import BeakerFilePane from '../components/dev-interface/BeakerFilePane.vue';

import BeakerSession from '../components/session/BeakerSession.vue';

import { standardRendererFactories } from '@jupyterlab/rendermime';

import { JupyterMimeRenderer } from 'beaker-kernel';

import Button from "primevue/button";
import OverlayPanel from 'primevue/overlaypanel';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

import { defineProps, inject, nextTick, onBeforeMount, onUnmounted, provide, ref, defineEmits, computed, shallowRef } from 'vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';

import { IBeakerTheme } from '../plugins/theme';

const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const toast = useToast();
const chatPanelRef = shallowRef();
const contextSelectionOpen = ref(false);
const contextProcessing = ref(false);
import BeakerContextSelection from '../components/session/BeakerContextSelection.vue';

const beakerNotebookRef = ref();

// TODO -- WARNING: showToast is only defined locally, but provided/used everywhere. Move to session?
// Let's only use severity=success|warning|danger(=error) for now
const showToast = ({title, detail, life=3000, severity='success' as any}) => {
    toast.add({
        summary: title,
        detail,
        life,
        // for options, seee https://primevue.org/toast/
        severity,
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

provide('cell-component-mapping', cellComponentMapping);

const isFileMenuOpen = ref();

const toggleFileMenu = (event) => {
    isFileMenuOpen.value.toggle(event);
}

const resetNotebook = async () => {
    const session = beakerSessionRef.value.session;
    session.reset();
};

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
            const notebook = beakerSessionRef?.value?.session?.notebook;
            if (notebook) {
                notebook.loadFromIPynb(notebookData[sessionId].data);
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

// no state to track selection - find code editor divs and compare to evt
const executeActiveCell = (editorSourceElement) => {
    const panel = chatPanelRef?.value;
    const queryCellComponents = panel?.cellsContainerRef;
    queryCellComponents.forEach(cell => {
        const events = cell?.queryEventsRef;
        if (!events) {
            return;
        }
        events.forEach(eventRef => {
            const codeCellRef = eventRef?.codeCellRef;
            const codeEditor = codeCellRef?.codeEditorRef;
            if (!codeEditor) {
                return;
            }
            if (codeEditor.view._root.activeElement == editorSourceElement) {
                codeCellRef.execute();
            }
        });
    });
}

const sessionKeybindings = {
    "keydown.enter.ctrl.prevent.capture.in-editor": (evt) => {
        executeActiveCell(evt.srcElement);
        // execute
    },
    "keydown.enter.shift.prevent.capture.in-editor": (evt) => {
        // execute
        executeActiveCell(evt.srcElement);
    }
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
    const notebook = beakerSessionRef.value.session?.notebook;
    if (notebook) {
        notebookData[sessionId] = {
            data: notebook.toIPynb(),
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

div.code-cell {
    margin-bottom: 2rem;
}

div.code-cell.query-event-code-cell {
    margin-bottom: 0.25rem;
}

</style>