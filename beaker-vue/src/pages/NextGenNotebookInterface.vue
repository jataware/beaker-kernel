<template>
    <BaseInterface
        :title="$tmpl._('short_title', 'Beaker NextGen')"
        :title-extra="saveAsFilename"
        :header-nav="headerNav"
        ref="beakerInterfaceRef"
        :connectionSettings="props.config"
        defaultKernel="beaker_kernel"
        :sessionId="sessionIdFromProps || sessionIdFromUrl"
        :renderers="renderersFromProps || defaultRenderers"
        :savefile="saveAsFilename"
        @iopub-msg="iopubMessageHandler"
        @unhandled-msg="unhandledMessageHandler"
        @any-msg="anyMessageHandler"
        @session-status-changed="statusChangedHandler"
        @open-file="handleLoadNotebook"
    >
        <div class="notebook-container">
            <BeakerNotebook
                ref="beakerNotebookRef"
                :cell-map="cellComponentMapping"
                v-keybindings.top="notebookKeyBindings"
            >
                <BeakerNotebookToolbar
                    default-severity=""
                    :saveAvailable="true"
                    :save-as-filename="saveAsFilename"
                    @notebook-saved="handleNotebookSaved"
                    @open-file="handleLoadNotebook"
                >
                    <template #end-extra>
                        <Button
                            @click="isMaximized = !isMaximized; beakerInterfaceRef.setMaximized(isMaximized);"
                            :icon="`pi ${isMaximized ? 'pi-window-minimize' : 'pi-window-maximize'}`"
                            size="small"
                            text
                        />
                    </template>
                </BeakerNotebookToolbar>
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
                
                <div class="agent-input-section">
                    <AgentThinkingIndicator 
                        :active-query-cells="activeQueryCells"
                        @scroll-to-query="scrollToCell"
                    />
                    
                    <BeakerAgentQuery
                        ref="agentQueryRef"
                        class="agent-query-container"
                    />
                </div>
            </BeakerNotebook>
        </div>

        <!-- TODO add all left/right panels as like in NotebookInterface.vue -->
        <template #left-panel>
            <SideMenu
                ref="sideMenuRef"
                position="left"
                highlight="line"
                :expanded="true"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel label="Context Info" icon="pi pi-home">
                    <InfoPanel/>
                </SideMenuPanel>
                <SideMenuPanel id="files" label="Files" icon="pi pi-folder" no-overflow :lazy="true">
                    <FilePanel
                        ref="filePanelRef"
                        @open-file="handleLoadNotebook"
                    />
                </SideMenuPanel>
            </SideMenu>
        </template>

        <template #right-panel>
            <SideMenu
                ref="rightSideMenuRef"
                position="right"
                highlight="line"
                :expanded="true"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel label="Preview" icon="pi pi-eye" no-overflow>
                    <PreviewPanel :previewData="contextPreviewData"/>
                </SideMenuPanel>
                <SideMenuPanel id="kernel-logs" label="Logs" icon="pi pi-list" position="bottom">
                    <DebugPanel :entries="debugLogs" @clear-logs="debugLogs.splice(0, debugLogs.length)" v-autoscroll />
                </SideMenuPanel>
            </SideMenu>
        </template>
    </BaseInterface>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Button from "primevue/button";
import BaseInterface from './BaseInterface.vue';
import BeakerAgentQuery from '../components/agent/BeakerAgentQuery.vue';
import InfoPanel from '../components/panels/InfoPanel.vue';
import FilePanel from '../components/panels/FilePanel.vue';
import SvgPlaceholder from '../components/misc/SvgPlaceholder.vue';
import SideMenu from "../components/sidemenu/SideMenu.vue";
import SideMenuPanel from "../components/sidemenu/SideMenuPanel.vue";
import PreviewPanel from '../components/panels/PreviewPanel.vue';
import BeakerNotebook from '../components/notebook/BeakerNotebook.vue';
import BeakerNotebookToolbar from '../components/notebook/BeakerNotebookToolbar.vue';
import BeakerNotebookPanel from '../components/notebook/BeakerNotebookPanel.vue';
import DebugPanel from '../components/panels/DebugPanel.vue';
import AgentThinkingIndicator from '../components/misc/AgentThinkingIndicator.vue';

import BeakerCodeCellComponent from '../components/cell/BeakerCodeCell.vue';
import BeakerMarkdownCellComponent from '../components/cell/BeakerMarkdownCell.vue';
import NextGenBeakerQueryCell from '../components/cell/NextGenBeakerQueryCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';

import { useNotebookInterface } from '../composables/useNotebookInterface';
import { useQueryCellFlattening } from '../composables/useQueryCellFlattening';

const props = defineProps([
    "config",
    "connectionSettings", 
    "sessionName",
    "sessionId",
    "defaultKernel",
    "renderers",
]);

const {
    beakerNotebookRef,
    beakerInterfaceRef,
    filePanelRef,
    sideMenuRef,
    rightSideMenuRef,
    agentQueryRef,
    saveAsFilename,
    isMaximized,
    debugLogs,
    contextPreviewData,
    beakerSession,
    defaultRenderers,
    activeQueryCells,
    createHeaderNav,
    createNotebookKeyBindings,
    createIopubMessageHandler,
    anyMessageHandler,
    unhandledMessageHandler,
    statusChangedHandler,
    loadNotebook,
    handleNotebookSaved,
    scrollToCell,
    beakerApp,
} = useNotebookInterface();

beakerApp.setPage("nextgen-notebook");

const urlParams = new URLSearchParams(window.location.search);
const sessionIdFromUrl = urlParams.has("session") ? urlParams.get("session") : "nextgen_notebook_dev_session";
const sessionIdFromProps = computed(() => props.sessionId);
const renderersFromProps = computed(() => props.renderers);

const cellComponentMapping = {
    'code': BeakerCodeCellComponent,
    'markdown': BeakerMarkdownCellComponent,
    'query': NextGenBeakerQueryCell,
    'raw': BeakerRawCell,
};

const headerNav = computed(() => createHeaderNav('nextgen-notebook'));

const notebookKeyBindings = createNotebookKeyBindings();

const iopubMessageHandler = createIopubMessageHandler();

const { setupQueryCellFlattening, resetProcessedEvents } = useQueryCellFlattening(() => beakerSession.value);

setupQueryCellFlattening(() => beakerSession.value?.session?.notebook?.cells);

const handleLoadNotebook = (notebookJSON: any, filename: string) => {
    resetProcessedEvents();
    loadNotebook(notebookJSON, filename);
};

</script>

<style lang="scss">
.notebook-container {
    display: flex;
    height: 100%;
    max-width: 100%;
}

.beaker-notebook {
    flex: 2 0 calc(50vw - 2px);
    border: 2px solid var(--p-surface-border);
    border-radius: 0;
    border-top: 0;
    max-width: 100%;
}

.agent-input-section {
    background-color: var(--p-surface-b);
}

.spacer {
    &.left {
        flex: 1 1000 25vw;
    }
    &.right {
        flex: 1 1 25vw;
    }
}

.notebook-toolbar {
    border-style: inset;
    border-radius: 0;
    border-top: unset;
    border-left: unset;
    border-right: unset;
}

.title-extra {
    vertical-align: baseline;
    display: inline-block;
    height: 100%;
    font-family: 'Ubuntu Mono', 'Courier New', Courier, monospace;
}
</style>
