<template>
    <BaseInterface
        title="Beaker Notebook"
        :title-extra="saveAsFilename"
        :header-nav="headerNav"
        ref="beakerInterfaceRef"
        :connectionSettings="props.config"
        sessionName="notebook_interface"
        defaultKernel="beaker_kernel"
        :sessionId="sessionId"
        :renderers="renderers"
        :savefile="saveAsFilename"
        @iopub-msg="iopubMessage"
        @unhandled-msg="unhandledMessage"
        @any-msg="anyMessage"
        @session-status-changed="statusChanged"
        @open-file="loadNotebook"
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
                    @open-file="loadNotebook"
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
                <BeakerAgentQuery
                    ref="agentQueryRef"
                    class="agent-query-container"
                />
            </BeakerNotebook>
        </div>

        <template #left-panel>
            <SideMenu
                ref="sideMenuRef"
                position="left"
                :show-label="true"
                highlight="line"
                :expanded="true"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel label="Info" icon="pi pi-home">
                    <InfoPanel/>
                </SideMenuPanel>
                <SideMenuPanel id="files" label="Files" icon="pi pi-file-export" no-overflow :lazy="true">
                    <FilePanel
                        ref="filePanelRef"
                        @open-file="loadNotebook"
                        @preview-file="(file, mimetype) => {
                            previewedFile = {url: file, mimetype: mimetype};
                            previewVisible = true;
                        }"
                    />
                </SideMenuPanel>
                <SideMenuPanel v-if="props.config.config_type !== 'server'" id="config" label="Config" icon="pi pi-cog" :lazy="true">
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
                :expanded="true"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel label="Preview" icon="pi pi-eye" no-overflow>
                    <PreviewPane :previewData="contextPreviewData"/>
                </SideMenuPanel>
                <SideMenuPanel id="file-contents" label="Contents" icon="pi pi-file" no-overflow>
                    <PreviewPanel
                        :url="previewedFile?.url"
                        :mimetype="previewedFile?.mimetype"
                        v-model="previewVisible"
                    />
                </SideMenuPanel>
                <SideMenuPanel id="media" label="Media" icon="pi pi-chart-bar" no-overflow>
                    <MediaPanel />
                </SideMenuPanel>
                <SideMenuPanel id="kernel-state" label="State" icon="pi pi-code" no-overflow>
                    <KernelStatePanel :data="kernelStateInfo"/>
                </SideMenuPanel>
            </SideMenu>
        </template>
    </BaseInterface>
</template>

<script setup lang="ts">
import { defineProps, ref, defineEmits, watch, provide, computed, nextTick, onUnmounted, inject, toRaw } from 'vue';
import { JupyterMimeRenderer, IBeakerCell, IMimeRenderer, BeakerSession } from 'beaker-kernel/src';
import { BeakerNotebookComponentType } from '../components/notebook/BeakerNotebook.vue';
import { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';
import BeakerNotebook from '../components/notebook/BeakerNotebook.vue';
import BeakerNotebookToolbar from '../components/notebook/BeakerNotebookToolbar.vue';
import BeakerNotebookPanel from '../components/notebook/BeakerNotebookPanel.vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, MarkdownRenderer, wrapJupyterRenderer, BeakerRenderOutput, TableRenderer } from '../renderers';
import { atStartOfInput, atEndOfInput } from '../util'
import { standardRendererFactories } from '@jupyterlab/rendermime';

import Button from "primevue/button";
import BaseInterface from './BaseInterface.vue';
import BeakerAgentQuery from '../components/agent/BeakerAgentQuery.vue';
import InfoPanel from '../components/panels/InfoPanel.vue';
import FilePanel from '../components/panels/FilePanel.vue';
import ConfigPanel from '../components/panels/ConfigPanel.vue';
import SvgPlaceholder from '../components/misc/SvgPlaceholder.vue';
import SideMenu from "../components/sidemenu/SideMenu.vue";
import SideMenuPanel from "../components/sidemenu/SideMenuPanel.vue";
import PreviewPanel from '../components/panels/PreviewPanel.vue';

// context preview
import PreviewPane from '../components/misc/PreviewPane.vue';

import BeakerCodeCell from '../components/cell/BeakerCodeCell.vue';
import BeakerMarkdownCell from '../components/cell/BeakerMarkdownCell.vue';
import BeakerQueryCell from '../components/cell/BeakerQueryCell.vue';
import BeakerRawCell from '../components/cell/BeakerRawCell.vue';
import { IBeakerTheme } from '../plugins/theme';
import MediaPanel from '../components/panels/MediaPanel.vue';
import KernelStatePanel from '../components/panels/KernelStatePanel.vue';


const beakerNotebookRef = ref<BeakerNotebookComponentType>();
const beakerInterfaceRef = ref();
const filePanelRef = ref();
const configPanelRef = ref();
const sideMenuRef = ref();
const agentQueryRef = ref();
const previewVisible = ref<boolean>(false);

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.has("session") ? urlParams.get("session") : "notebook_dev_session";

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
    MarkdownRenderer,
    DecapodeRenderer,
    TableRenderer
];

const cellComponentMapping = {
    'code': BeakerCodeCell,
    'markdown': BeakerMarkdownCell,
    'query': BeakerQueryCell,
    'raw': BeakerRawCell,
}

// const session = inject<BeakerSession>('session');

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const saveInterval = ref();
const copiedCell = ref<IBeakerCell | null>(null);
const saveAsFilename = ref<string>(null);

const contextSelectionOpen = ref(false);
const isMaximized = ref(false);
const rightMenu = ref<typeof SideMenuPanel>();
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

const contextPreviewData = ref<any>();
const kernelStateInfo = ref();

type FilePreview = {
    url: string,
    mimetype?: string
}
const previewedFile = ref<FilePreview>();

const notebookTitle = computed(() => {
    if (saveAsFilename.value) {
        return `Beaker Notebook`;
    }
    else {
        return 'Beaker Notebook';
    }
});

const headerNav = computed(() => [
    {
        type: 'link',
        href: `/chat${window.location.search}`,
        icon: 'comment',
        label: 'Navigate to chat view',
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

const beakerSession = computed<BeakerSessionComponentType>(() => {
    return beakerInterfaceRef?.value?.beakerSession;
});

// Ensure we always have at least one cell
watch(
    () => beakerNotebookRef?.value?.notebook.cells,
    (cells) => {
        if (cells?.length === 0) {
            beakerNotebookRef.value.insertCellBefore();
        }
    },
    {deep: true},
)

const iopubMessage = (msg) => {
    if (msg.header.msg_type === "preview") {
        contextPreviewData.value = msg.content;
    } else if (msg.header.msg_type === "kernel_state_info") {
        kernelStateInfo.value = msg.content;
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


const restartSession = async () => {
    const resetFuture = beakerSession.value.session.sendBeakerMessage(
        "reset_request",
        {}
    )
    await resetFuture;
}

const loadNotebook = (notebookJSON: any, filename: string) => {
    const notebook = beakerNotebookRef.value;
    beakerSession.value?.session.loadNotebook(notebookJSON);
    saveAsFilename.value = filename;
    const cellIds = notebook.notebook.cells.map((cell) => cell.id);
    if (!cellIds.includes(notebook.selectedCellId)) {
        nextTick(() => {
            // Force the notebook to select one of cells in the current notebook.
            notebook.selectCell(cellIds[0]);
        });
    }
}

const handleNotebookSaved = async (path: string) => {
    saveAsFilename.value = path;
    if (path) {
        sideMenuRef.value?.selectPanel("Files");
        await filePanelRef.value.refresh();
        await filePanelRef.value.flashFile(path);
    }
}


const prevCellKey = () => {
    beakerNotebookRef.value?.selectPrevCell();
};

const nextCellKey = () => {
    const lastCell = beakerNotebookRef.value.notebook.cells[beakerNotebookRef.value.notebook.cells.length-1];
    if (beakerNotebookRef.value.selectedCell().cell.id === lastCell.id) {
        agentQueryRef.value.$el.querySelector('textarea')?.focus()
    }
    else {
        beakerNotebookRef.value?.selectNextCell();
    }
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
                undefined,
                true,
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
    "keydown.up.in-editor.capture": (event: KeyboardEvent) => {
        // Note: This runs BEFORE the cursor is moved.
        const eventTarget = event.target as HTMLElement;
        const parentCellElement = eventTarget.closest('.beaker-cell');
        const targetCellId = parentCellElement?.getAttribute('cell-id');

        if (targetCellId !== undefined) {
            const curCell = beakerSession.value.findNotebookCellById(targetCellId);
            if (atStartOfInput(curCell.editor)) {
                const prevCell = beakerNotebookRef.value.prevCell();
                if (prevCell) {
                    curCell.exit();
                    beakerNotebookRef.value.selectCell(prevCell.cell.id, true, "end");
                    event.preventDefault();
                    event.stopImmediatePropagation();
                }
            }
        }
        else if (eventTarget.closest('.agent-query-container')) {
            // In the agent query box at the bottom of the notebook.
            eventTarget.blur();
            beakerNotebookRef.value.selectCell(
                beakerNotebookRef.value.notebook.cells[beakerNotebookRef.value.notebook.cells.length-1].id,
                true,
                "end",
            );
            event.preventDefault();
            event.stopImmediatePropagation();
        }
    },
    "keydown.down.in-editor.capture": (event: KeyboardEvent) => {
        // Note: This runs BEFORE the cursor is moved.
        const eventTarget = event.target as HTMLElement;
        const parentCellElement = eventTarget.closest('.beaker-cell');
        const targetCellId = parentCellElement?.getAttribute('cell-id');

        if (targetCellId !== undefined) {
            const curCell = beakerSession.value.findNotebookCellById(targetCellId);
            if (atEndOfInput(curCell.editor)) {
                const nextCell = beakerNotebookRef.value.nextCell();
                if (nextCell) {
                    curCell.exit();
                    beakerNotebookRef.value.selectCell(nextCell.cell.id, true, "start");
                    event.preventDefault();
                    event.stopImmediatePropagation();
                }
                else {
                    const lastCell = beakerNotebookRef.value.notebook.cells[beakerNotebookRef.value.notebook.cells.length-1];
                    if (beakerNotebookRef.value.selectedCell().cell.id === lastCell.id) {
                        curCell.exit();
                        agentQueryRef.value.$el.querySelector('textarea')?.focus()
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }
                }
            }
        }
    },
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
    "keydown.p.!in-editor": (evt: KeyboardEvent) => {
        const notebook = beakerNotebookRef.value;
        let copiedCellValue = toRaw(copiedCell.value);
        if (copiedCellValue !== null) {
            var newCell: IBeakerCell;


            // If a cell with the to-be-pasted cell's id already exists in the notebook, set the copied cell's id to
            // undefined so that it is regenerated when added.
            const notebookIds = notebook.notebook.cells.map((cell) => cell.id);
            if (notebookIds.includes(copiedCellValue.id)) {
                const cls = copiedCellValue.constructor as (data: IBeakerCell) => void;
                const data = {
                    ...copiedCellValue,
                    // Set non-transferable attributes to undefined.
                    id: undefined,
                    executionCount: undefined,
                    busy: undefined,
                    last_execution: undefined,
                } as IBeakerCell;
                copiedCellValue = new cls(data);
            }

            // Lowercase `p` pastes after, uppercase `P` pastes before. Checking the actual is key better than checking
            // for shift, etc as it includes caps lock, etc.
            if (evt.key === 'p') {
                 newCell = notebook?.insertCellAfter(notebook.selectedCell(), copiedCellValue);
            }
            else if (evt.key === 'P') {
                 newCell = notebook?.insertCellBefore(notebook.selectedCell(), copiedCellValue);
            }
            copiedCellValue.value = null;
        }
    },
}

</script>

<style lang="scss">

.notebook-container {
    display:flex;
    height: 100%;
    max-width: 100%;
}

.beaker-notebook {
    flex: 2 0 calc(50vw - 2px);
    border: 2px solid var(--surface-border);
    border-radius: 0;
    border-top: 0;
    max-width: 100%;
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
