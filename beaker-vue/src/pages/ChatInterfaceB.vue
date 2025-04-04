<template>
    <BaseInterface
        :title="$tmpl._('short_title', 'Beaker B')"
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
                            <div v-html="$tmpl._('chat_welcome_html', `
                                <p>Hi! I'm Beaker.</p>
                                <p>Ask me about whatever...</p>
                            `)"
                            />
                        </template>
                        <template #notebook-background>
                            <div class="welcome-placeholder">
                            </div>
                        </template>
                    </ChatPanel>
                    <AgentQuery
                        class="agent-query-container agent-query-container-chat"
                        :placeholder="$tmpl._('agent_query_prompt', 'Message to the agent')"
                        v-show="!isLastCellAwaitingInput"
                    />
            </div>
            <div class="chat-cell-details"
                v-if="selectedCellId"
            >
                <!-- {{ selectedCellId }} -->
                <div class="details-header">
                    <p style="color: #666; font-size: 1rem;">TBD AI-generated summary of query-task-steps here</p>
                    <button class="close-button" @click="unselectCell" title="Close details">
                        <i class="pi pi-times"></i>
                    </button>
                </div>

                <div class="filter-controls">
                    <div class="filter-button-group">
                        <ToggleButton 
                            v-model="showFailedCells" 
                            outlined
                            on-label="Hide Failed" 
                            off-label="Show Failed"
                            on-icon="pi pi-eye-slash"
                            off-icon="pi pi-eye"
                            class="p-button-sm filter-button" />
                        
                        <ToggleButton 
                            v-model="showCodeCells" 
                            outlined
                            on-label="Hide Code" 
                            off-label="Show Code"
                            on-icon="pi pi-eye-slash"
                            off-icon="pi pi-eye"
                            class="p-button-sm filter-button" />
                        
                        <ToggleButton 
                            v-model="showThoughtCells" 
                            outlined
                            on-label="Hide Thoughts" 
                            off-label="Show Thoughts"
                            on-icon="pi pi-eye-slash"
                            off-icon="pi pi-eye"
                            class="p-button-sm filter-button" />
                        
                        <ToggleButton 
                            v-model="showOutputCells" 
                            outlined
                            on-label="Hide Output" 
                            off-label="Show Output"
                            on-icon="pi pi-eye-slash"
                            off-icon="pi pi-eye"
                            class="p-button-sm filter-button" />
                    </div>
                </div>

                <div class="events-scroll-container">
                    <BeakerQueryCellEvent
                        v-for="(event, eventIndex) in filteredCellEvents"
                        :key="eventIndex"
                        :hide-output="!showOutputCells"
                        :event="event"
                    />

                    <ProgressBar 
                        v-if="isSelectedCellInProgress" 
                        mode="indeterminate" 
                        style="height: 6px; width: 40%; margin: 1rem auto;">
                    </ProgressBar>
                </div>
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
                            rightSideMenuRef.selectPanel('Contents');
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
                ref="rightSideMenuRef"
            >
                <SideMenuPanel label="Preview" icon="pi pi-eye" no-overflow>
                    <PreviewPanel :previewData="contextPreviewData"/>
                </SideMenuPanel>
                <SideMenuPanel id="file-contents" label="Contents" icon="pi pi-file" no-overflow>
                    <FileContentsPanel
                        :url="previewedFile?.url"
                        :mimetype="previewedFile?.mimetype"
                        v-model="previewVisible"
                    />
                </SideMenuPanel>
                <SideMenuPanel id="media" label="Media" icon="pi pi-chart-bar" no-overflow>
                    <MediaPanel></MediaPanel>
                </SideMenuPanel>
            </SideMenu>
        </template>
    </BaseInterface>
</template>

<script setup lang="ts">
import BaseInterface from './BaseInterface.vue';
import AgentQuery from '../components/chat-interface/AgentQuery.vue';
import ChatPanel from '../components/chat-interface/ChatPanel.vue';
import SideMenu from '../components/sidemenu/SideMenu.vue';
import SideMenuPanel from '../components/sidemenu/SideMenuPanel.vue';
import ContextPanel from '../components/panels/ContextPanel.vue';
import ProgressBar from 'primevue/progressbar';
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
// import { _ } from '../util/whitelabel';
import { NavOption } from '../components/misc/BeakerHeader.vue';

import { defineProps, inject, ref, computed, ComponentInstance, Component, StyleHTMLAttributes, ComputedRef, } from 'vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';
import ToggleButton from 'primevue/togglebutton';

import { IBeakerTheme } from '../plugins/theme';
import { vKeybindings } from '../directives/keybindings';
import FileContentsPanel from '../components/panels/FileContentsPanel.vue';
import PreviewPanel from '../components/panels/PreviewPanel.vue';
import MediaPanel from '../components/panels/MediaPanel.vue';
import BeakerQueryCellEvent from '../components/cell/BeakerQueryCellEvent.vue';

import { toRaw } from 'vue';

const beakerInterfaceRef = ref();
const isMaximized = ref(false);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const beakerApp = inject<any>("beakerAppConfig");
beakerApp.setPage("chatb");

const rightSideMenuRef = ref();
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

const headerNav = computed((): NavOption[] => {
    const nav: NavOption[] = [
        {
            type: 'button',
            command: () => {
                if (window.confirm(`This will reset your entire session, clearing the notebook and removing any updates to the environment. Proceed?`))
                    beakerSession.value.session.reset();
            },
            icon: 'refresh',
            label: 'Reset Session',
        }

    ];
    if (!(beakerApp?.config?.pages) || (Object.hasOwn(beakerApp.config.pages, "notebook"))) {
        const href = "/" + (beakerApp?.config?.pages?.notebook?.default ? '' : 'notebook') + window.location.search;
        nav.push(
            {
                type: 'link',
                href: href,
                component: NotebookSvg,
                componentStyle: {
                    fill: 'currentColor',
                    stroke: 'currentColor',
                    height: '1rem',
                    width: '1rem',
                },
                label: 'Navigate to notebook view',
            }
        );
    }
    nav.push(...([
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
    ] as NavOption[]));
    return nav;
});

const beakerSession = computed(() => {
    return beakerInterfaceRef?.value?.beakerSession;
});

const selectedCellId = computed(() => {
    return beakerSession.value?.session?.notebook?.selectedCell?.id || null;
});

// Find the selected cell and get its events
const selectedCellEvents = computed(() => {
    if (!selectedCellId.value) {
        // console.log("No cell selected to show selectedCellEvents for");
        return null;
    }

    // console.log("computing selectedCellEvents for", selectedCellId.value);
    
    const cells = beakerSession.value?.session?.notebook?.cells ?? [];
    const selectedCell = cells.find(cell => cell.id === selectedCellId.value);
    const events = selectedCell?.events || [];

    return events;
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

const unselectCell = () => {
    beakerSession.value.session.notebook.selectedCell = undefined;
}

// Add state for toggle buttons
const showFailedCells = ref(true);
const showCodeCells = ref(true);
const showThoughtCells = ref(true);
const showOutputCells = ref(true);

// Filter events based on toggle states
const filteredCellEvents = computed(() => {
    if (!selectedCellEvents.value) return [];
    
    return selectedCellEvents.value.filter(event => {

        // console.log("filtered cell events; event:", event.type);
        // console.log("event.status:", event.status);

        // Filter on failed cells; TODO this doesn't work this way- we'll check events renderer
        if (!showFailedCells.value && event.type === 'code_cell' && event.status === 'error') {
            return false;
        }
        
        // Filter based on code cells
        if (!showCodeCells.value && event.type === 'code_cell') {
            return false;
        }
        
        // Filter based on thought cells
        if (!showThoughtCells.value && event.type === 'thought') {
            return false;
        }
        
        // Filter based on output- TODO this doesnt work this way- we'll check events renderer
        // if (!showOutputCells.value && event.type === 'output') {
        //     return false;
        // }

        // Hardcode remove conclusion so that it isn't rendered twice (one in the chat; one in the thoughts panel)
        if (event.type === 'response') { 
            return false;
        }
        
        return true;
    });
});

const isSelectedCellInProgress = computed(() => {
    if (selectedCellId.value === null) return false;

    const cells = beakerSession.value?.session?.notebook?.cells ?? [];
    const selectedCell = cells.find(cell => cell.id === selectedCellId.value);

    const isBusy = selectedCell.status === 'busy';
    return isBusy;
})
</script>

<style lang="scss">

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
    flex: 3;
    // padding-right: 1rem;
    // padding-left: 1rem;
    display: flex;
    flex-direction: column;
    max-width: 1250px;
    
    @media (max-width: 1000px) {
        // flex: 1;
        &:has(+ .chat-cell-details) {
            display: none;
        }
    }
}

.chat-cell-details {
    flex: 4;
    // overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--surface-d) transparent;
    
    border: 1px solid var(--surface-d);
    border-radius: 0.75rem;
    background-color: var(--surface-card);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    margin: 0.75rem 1rem 1rem 0;
    padding: 0.25rem 1rem 1rem 1.2rem;
    max-width: 1250px;

    height: 100%;

    display: flex;
    flex-direction: column;
    
    // @media (max-width: 1000px) {
    //     flex: 1;
    // }
}

.chat-layout {
    display:flex;
    flex-direction: row;
    height: 100%;
    gap: 1rem;
    margin-left: 1rem;
    margin-right: 0.5rem;
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

.details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 0.5rem 0.5rem 0.5rem;
    // border-bottom: 1px solid var(--surface-border);
    // margin-bottom: 0.5rem;

    button {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: var(--text-color-secondary);
        cursor: pointer;
        transition: color 0.2s;
        
        &:hover {
            color: var(--text-color);
        }
    }
}

.filter-controls {
    display: flex;
    flex-direction: column;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    background-color: var(--surface-ground);
    border-radius: 6px;
}

.filter-label {
    font-size: 0.85rem;
    color: var(--text-color-secondary);
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.filter-button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.filter-button {
    background-color: var(--surface-card) !important;
    border-color: var(--surface-border) !important;
    color: var(--text-color-secondary) !important;
}

.filter-button .p-button-icon {
    color: var(--text-color-secondary) !important;
}

.filter-button.p-highlight {
    background-color: var(--surface-hover) !important;
    border-color: var(--surface-border) !important;
    color: var(--text-color) !important;
}

.filter-button.p-highlight .p-button-icon {
    color: var(--text-color) !important;
}

.filter-button:hover {
    background-color: var(--surface-hover) !important;
    border-color: var(--primary-color) !important;
}

.events-scroll-container {
    overflow-y: auto;
}
</style>
