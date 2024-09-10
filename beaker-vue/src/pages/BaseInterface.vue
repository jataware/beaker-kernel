<template>
    <BeakerSession
        style="height: 100vh; width: 100vw; display: flex; flex-direction: column;"
        ref="beakerSession"
        :connectionSettings="props.connectionSettings"
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
        <app>
            <header>
                <slot name="header">
                    <BeakerHeader
                        :connectionStatus="connectionStatus"
                        :loading="!activeContext?.slug"
                        @select-kernel="toggleContextSelection"
                        :title="props.title"
                    />
                </slot>
            </header>

            <main>
                <slot name="main">
                    <div id="left-panel">
                        <slot name="left-panel">
                        </slot>
                    </div>

                    <div id="center-panel">
                        <slot>
                        </slot>
                    </div>

                    <div id="right-panel">
                        <slot name="right-panel">
                        </slot>
                    </div>
                </slot>
            </main>

            <footer>
            <slot name="footer">
                <FooterDrawer />
            </slot>
            </footer>

            <!-- Modals, popups and globals -->
            <slot name="context-selection-popup">
                <BeakerContextSelection
                    :isOpen="contextSelectionOpen"
                    :toggleOpen="toggleContextSelection"
                    :contextProcessing="contextProcessing"
                    @context-changed="(contextData) => {beakerSession.setContext(contextData)}"
                    @close-context-selection="contextSelectionOpen = false"
                />
            </slot>
            <slot name="toast">
                <Toast position="bottom-right" />
            </slot>
        </app>
    </BeakerSession>
</template>

<script setup lang="ts">
import { defineProps, ref, onBeforeMount, provide, nextTick, onUnmounted, defineExpose } from 'vue';
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
    "title",
    "connectionSettings",
    "sessionName",
    "sessionId",
    "defaultKernel",
    "renderers",
    "connectionSettings",
    "sessionName",
    "sessionId",
    "defaultKernel",
    "renderers",
]);
    // @iopub-msg="iopubMessage"
    // @unhandled-msg="unhandledMessage"
    // @any-msg="anyMessage"
    // @session-status-changed="statusChanged"
    // v-keybindings="sessionKeybindings"

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

defineExpose({
    beakerSession,
});

</script>

<style lang="scss">

app {
    margin: 0;
    padding: 0;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    display: grid;
    grid-template:
        "header" max-content
        "main" auto
        "footer" max-content /
        100%;
}

header {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

main {
    grid-area: main;
    position: relative;
    display: grid;
    grid-template:
        "left-panel center-panel right-panel" 100% /
        min-content auto min-content;
    background-color: var(--surface-0);
    overflow: auto;
}

footer {
    grid-area: footer;
}

#left-panel {
    grid-area: left-panel;
    width: 100%;
}

#center-panel {
    grid-area: center-panel;
    border: 1px solid;
    border-color: var(--surface-border);

}

#right-panel {
    grid-area: right-panel;
    width: 100%;
}

</style>
