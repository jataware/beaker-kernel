<template>
    <BaseInterface
        title="Beaker Chat"
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
        :style-overrides="['chat']"
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
                        class="agent-query-container agent-query-container-chat"
                        placeholder="Message to the agent"   
                        v-show="!isLastCellAwaitingInput"
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
                    <FilePanel 
                        @open-file="loadNotebook" 
                        @preview-file="(file, mimetype) => {
                            previewedFile = {url: file, mimetype: mimetype};
                            previewVisible = true;
                        }" 
                    />
                </SideMenuPanel>
                <SideMenuPanel id="config" label="Config" icon="pi pi-cog" :lazy="true">
                    <ConfigPanel
                        ref="configPanelRef"
                        @restart-session="restartSession"
                    />
                </SideMenuPanel>
            </SideMenu>
        </template>
        <template #right-panel>
            <SideMenu
                position="right"
                :show-label="true"
                highlight="line"
                :expanded="false"
            >
                <SideMenuPanel label="Preview" icon="pi pi-eye" no-overflow>
                    <PreviewPane :previewData="contextPreviewData"/>
                </SideMenuPanel>
                <SideMenuPanel id="file-contents" label="Contents" icon="pi pi-file" no-overflow>
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
import SideMenu from '../components/sidemenu/SideMenu.vue';
import SideMenuPanel from '../components/sidemenu/SideMenuPanel.vue';
import ContextPanel from '../components/panels/ContextPanel.vue';

import NotebookSvg from '../assets/icon-components/NotebookSvg.vue';
import BeakerCodeCell from '../components/cell/BeakerCodeCell.vue';
import BeakerQueryCell from '../components/cell/BeakerQueryCell.vue';
import BeakerMarkdownCell from '../components/cell/BeakerMarkdownCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';

import FilePanel from '../components/panels/FilePanel.vue';
import ConfigPanel from '../components/panels/ConfigPanel.vue';

import BeakerSession from '../components/session/BeakerSession.vue';

import { standardRendererFactories } from '@jupyterlab/rendermime';

import { JupyterMimeRenderer } from 'beaker-kernel/src';


import { defineProps, inject, ref, computed, } from 'vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';

import { IBeakerTheme } from '../plugins/theme';
import { vKeybindings } from '../directives/keybindings';
import PreviewPanel from '../components/panels/PreviewPanel.vue';
// context preview
import PreviewPane from '../components/misc/PreviewPane.vue';

const beakerInterfaceRef = ref();
const isMaximized = ref(false);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

const contextPreviewData = ref<any>();

type FilePreview = {
    url: string,
    mimetype?: string
}
const previewedFile = ref<FilePreview>();
const previewVisible = ref<boolean>(false);

const isLastCellAwaitingInput = computed(() => {
    const cells = beakerSession.value?.session?.notebook?.cells ?? [];
    if (cells.length == 0) {
        return false;
    }
    const last = cells[cells.length - 1];
    if (last?.cell_type === 'query' && last?.status === 'awaiting_input') {
        return true;
    }
    return false;
})

const headerNav = computed(() => [
    {
        type: 'button',
        command: () => {
            if (window.confirm(`This will reset your entire session, clearing the notebook and removing any updates to the environment. Proceed?`))
                beakerSession.value.session.reset();
        },
        icon: 'refresh',
        label: 'Reset Session',
    },
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
    }
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
    if (msg.header.msg_type === "preview") {
        contextPreviewData.value = msg.content;
    }
    if (msg.header.msg_type === "job_response") {
        beakerSessionRef.value.session.addMarkdownCell(msg.content.response);
    }
};

const statusChanged = (newStatus) => {
    connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
};

const restartSession = async () => {
    const resetFuture = beakerSession.value.session.sendBeakerMessage(
        "reset_request",
        {}
    )
    await resetFuture;
}
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
        //flex: 0 1000 25vw;
        display: none;
    }
    &.right {
        //flex: 0 1000 25vw;
        display: none;
    }
}
.left-panel .left .spacer {
    display: none;
}
.sidemenu-container.left {
    min-width: 0px !important;
}
.chat-container {
    margin-left: auto;
    margin-right: auto;
    flex: 0 0 100%;
    padding-right: 1rem;
    padding-left: 1rem;
    //border: 1px solid var(--surface-border);
    display: flex;
    flex-direction: column;
    max-width: 860px;
    width: 100%;
}

.chat-layout {
    display:flex;
    flex-direction: row;
    height: 100%;
}

div.code-cell-output-box {
    div.output-collapse-box {
        display: none;
    }
}

.jp-RenderedImage {
    img {
        width: 100%;
    }
}

div.footer-menu-bar {
    border-radius: 0px;
    padding-left: 0px;
}

.sidemenu-menu-selection.left {
    border-top: none;
    border-bottom: none;
    border-left: none;
}

.title {
    h4 {
        text-overflow: "clip";
        overflow: hidden;
        text-wrap: nowrap;
    }
}

div.status-container {
    min-width: 0px;
}

</style>
