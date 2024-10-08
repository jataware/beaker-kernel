<template>
    <BaseInterface
        title="Beaker Chat Interface"
        ref="beakerInterfaceRef"
        :header-nav="headerNav"
        :connectionSettings="props.config"
        sessionName="chat_interface"
        :sessionId="sessionId"
        defaultKernel="beaker_kernel"
        :renderers="renderers"
        @session-status-changed="statusChanged"
        @iopub-msg="iopubMessage"
        @open-file="loadNotebook"
    >
        <div class="chat-layout">
            <div class="chat-container">
                    <ChatPanel
                        :cell-map="cellComponentMapping"
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
            <div v-if="!isMaximized" class="spacer right"></div>
        </div>

        <template #left-panel>
            <SideMenu
                position="left"
                :show-label="true"
                highlight="line"
                :expanded="false"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel label="Info" icon="pi pi-home">
                    <ContextPanel />
                </SideMenuPanel>
                <SideMenuPanel label="Files" icon="pi pi-file-export" no-overflow>
                    <FilePanel @open-file="loadNotebook" />
                </SideMenuPanel>
            </SideMenu>
        </template>
                <!-- <HelpSidebar></HelpSidebar> -->
                 <!-- <SideMenu
                    position="right"
                    :expanded="false"
                    :style="{gridArea: 'r-sidebar'}"
                    :show-label="false"
                    :static-size="true"
                 >
                    <SideMenuPanel
                        icon="pi pi-question"
                    >
                        <HelpSidebar/>
                    </SideMenuPanel>
                 </SideMenu> -->
            <!-- </div> -->
    <!-- </div> -->
    </BaseInterface>
</template>

<script setup lang="ts">
import BaseInterface from './BaseInterface.vue';
import AgentQuery from '../components/chat-interface/AgentQuery.vue';
import ChatPanel from '../components/chat-interface/ChatPanel.vue';
import DarkModeButton from '../components/chat-interface/DarkModeButton.vue';
import HelpSidebar from '../components/chat-interface/HelpSidebar.vue';
import VerticalToolbar from '../components/chat-interface/VerticalToolbar.vue';
import SideMenu from '../components/sidemenu/SideMenu.vue';
import SideMenuPanel from '../components/sidemenu/SideMenuPanel.vue';
import ContextPanel from '../components/panels/ContextPanel.vue';

import NotebookSvg from '../assets/icon-components/NotebookSvg.vue';
import BeakerCodeCell from '../components/cell/BeakerCodeCell.vue';
import BeakerQueryCell from '../components/cell/BeakerQueryCell.vue';
import BeakerMarkdownCell from '../components/cell/BeakerMarkdownCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';

import BeakerFilePane from '../components/dev-interface/BeakerFilePane.vue';
import FilePanel from '../components/panels/FilePanel.vue';

import BeakerSession from '../components/session/BeakerSession.vue';

import { standardRendererFactories } from '@jupyterlab/rendermime';

import { JupyterMimeRenderer } from 'beaker-kernel/src';

import Button from "primevue/button";
import OverlayPanel from 'primevue/overlaypanel';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

import { defineProps, inject, nextTick, onBeforeMount, onUnmounted, provide, ref, defineEmits, computed, shallowRef } from 'vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';

import { IBeakerTheme } from '../plugins/theme';
import { vKeybindings } from '../directives/keybindings';

const beakerInterfaceRef = ref();
const isMaximized = ref(false);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
// const toast = useToast();

// const contextSelectionOpen = ref(false);
// const contextProcessing = ref(false);
// import BeakerContextSelection from '../components/session/BeakerContextSelection.vue';


const headerNav = computed(() => [
    {
        type: 'link',
        href: `/${window.location.search}`,
        component: NotebookSvg,
        componentStyle: {
            fill: 'currentColor',
            stroke: 'currentColor',
            height: '1rem',
            width: '1rem',
        },
        label: 'Navigate to notebook view',
    },
    {
        type: 'button',
        icon: (theme.mode === 'dark' ? 'sun' : 'moon'),
        command: toggleDarkMode,
        label: `Switch to ${theme.mode === 'dark' ? 'light' : 'dark'} mode.`,
    },
    {
        type: 'link',
        href: `https://jataware.github.io/beaker-kernel`,
        label: 'Beaker Documentation',
        icon: "book",
        rel: "noopener",
        target: "_blank",
    },
    {
        type: 'link',
        href: `https://github.com/jataware/beaker-kernel`,
        label: 'Check us out on Github',
        icon: "github",
        rel: "noopener",
        target: "_blank",
    },
]);

const beakerSession = computed(() => {
    return beakerInterfaceRef?.value?.beakerSession;
});

const loadNotebook = (notebookJSON: any) => {
    beakerSession.value?.session.loadNotebook(notebookJSON);
}
const urlParams = new URLSearchParams(window.location.search);

const sessionId = urlParams.has("session") ? urlParams.get("session") : "chat_dev_session";

const props = defineProps([
    "config",
    "connectionSettings",
    "sessionName",
    "sessionId",
    "defaultKernel",
    "renderers",
]);

const renderers = [
    ...standardRendererFactories.map((factory: any) => new JupyterMimeRenderer(factory)).map(wrapJupyterRenderer),
    JSONRenderer,
    LatexRenderer,
    DecapodeRenderer,
];

const cellComponentMapping = {
    'code': BeakerCodeCell,
    'markdown': BeakerMarkdownCell,
    'query': BeakerQueryCell,
    'raw': BeakerRawCell,
}

const connectionStatus = ref('connecting');
const beakerSessionRef = ref<typeof BeakerSession>();


const iopubMessage = (msg) => {
    if (msg.header.msg_type === "job_response") {
        beakerSessionRef.value.session.addMarkdownCell(msg.content.response);
    }
};

const statusChanged = (newStatus) => {
    connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
};

// onBeforeMount(() => {
//     var notebookData: {[key: string]: any};
//     try {
//         notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
//     }
//     catch (e) {
//         console.error(e);
//         notebookData = {};
//     }
//     if (notebookData[sessionId]?.data) {
//         nextTick(() => {
//             const notebook = beakerSessionRef?.value?.session?.notebook;
//             if (notebook) {
//                 notebook.loadFromIPynb(notebookData[sessionId].data);
//             }
//         });
//     }
//     saveInterval.value = setInterval(snapshot, 30000);
//     window.addEventListener("beforeunload", snapshot);
// });

// onUnmounted(() => {
//     clearInterval(saveInterval.value);
//     saveInterval.value = null;
//     window.removeEventListener("beforeunload", snapshot);
// });

// const snapshot = () => {
//     var notebookData: {[key: string]: any};
//     try {
//         notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
//     }
//     catch (e) {
//         console.error(e);
//         notebookData = {};
//     }
//     // Only save state if there is state to save
//     const notebook = beakerSessionRef.value.session?.notebook;
//     if (notebook) {
//         notebookData[sessionId] = {
//             data: notebook.toIPynb(),
//         };
//         localStorage.setItem("notebookData", JSON.stringify(notebookData));
//     }
// };

</script>

<style lang="scss">
// #app {
//     margin: 0;
//     padding: 0.5em;
//     overflow: hidden;
//     background-color: var(--surface-b);
//     height: 100vh;
//     width: 100vw;
// }
// header {
//     display: flex;
//     justify-content: space-between;
//     align-items: start;
//     flex: 25;
// }
// main {
//     flex: 50;
// }
// footer {
//     // grid-area: r-sidebar;
//     flex: 25;
// }
// .main-panel {
//     display: flex;
//     flex-direction: column;
//     &:focus {
//         outline: none;
//     }
// }
// div.beaker-notebook {
//     padding-top: 1rem;
// }

// .central-panel {
//     flex: 50;
//     display: flex;
//     flex-direction: column;
//     max-width: 820px;
//     margin: auto;
// }

// .beaker-dev-interface {
//     padding-bottom: 1rem;
//     display: flex;
//     grid-gap: 1px;
//     flex-direction: row;
//     flex: 1;
//     height: 100%;
//     // grid-template-areas:
//     //     "l-sidebar main r-sidebar"
//     //     "l-sidebar main r-sidebar"
//     //     "l-sidebar main r-sidebar";
//     // grid-template-columns: auto 1fr auto;
//     // grid-template-rows: auto 1fr auto;
// }

// .beaker-session-container {
//     height: 100%;
// }

// div.cell-container {
//     position: relative;
//     display: flex;
//     flex: 1;
//     background-color: var(--surface-b);
//     flex-direction: column;
//     z-index: 3;
//     overflow: auto;
// }

// div.llm-query-cell.beaker-chat-cell {
//     padding: 0;
// }

// div.llm-prompt-container {
//     margin-right: 0;
// }

// div.llm-prompt-container h2.llm-prompt-text {
//     font-size: 1.25rem;
//     max-width: 70%;
//     margin-left: auto;
//     background-color: var(--surface-a);
//     padding: 1rem;
//     border-radius: 16px;
// }

// div.llm-prompt-container {
//     text-align: right;
//     max-width: 60%;
//     align-self: end;
// }

// div.query {
//     display: flex;
//     flex-direction: column;
// }

// div.query-steps {
//     display: none;
// }

// div.events div.query-answer {
//     background-color: var(--surface-b);
// }

// div.beaker-toolbar {
//     flex-direction: column;
// }

// div.beaker-toolbar div {
//     flex-direction: column;
// }

// div.central-panel, div.beaker-notebook {
//     height: 100%;
// }

// button.connection-button {
//     border: none;
// }

// div.code-cell {
//     margin-bottom: 2rem;
// }

// div.code-cell.query-event-code-cell {
//     margin-bottom: 0.25rem;
// }

.spacer {
    &.left {
        flex: 1 1000 25vw;
    }
    &.right {
        flex: 1 1 25vw;
    }
}

.chat-container {
    flex: 2 0 calc(50vw - 2px);
    border: 1px solid var(--surface-border);
    display: flex;
    flex-direction: column;
}

.chat-layout {
    display:flex;
    flex-direction: row;
    height: 100%;
}

.cell-container {
    // flex: 1;
}

</style>
