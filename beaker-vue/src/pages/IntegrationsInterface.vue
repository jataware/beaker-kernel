<template>
    <BaseInterface
        :title="$tmpl._('short_title', 'Beaker Notebook')"
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
    >
        <div class="datasource-container">
            <div class="beaker-notebook">
                <DatasourceEditor
                    :datasources="datasources"
                    :selected-on-load="selectedOnLoad"
                    :folderRoot="datasourcesFolderRoot"
                />
            </div>
        </div>

        <template #left-panel>
            <SideMenu
                ref="sideMenuRef"
                position="left"
                highlight="line"
                :expanded="true"
                initialWidth="25vi"
                :maximized="isMaximized"
            >
                <SideMenuPanel id="files" label="Files" icon="pi pi-folder" no-overflow :lazy="true">
                    <FilePanel
                        ref="filePanelRef"
                        @preview-file="(file, mimetype) => {
                            previewedFile = {url: file, mimetype: mimetype};
                            previewVisible = true;
                            rightSideMenuRef.selectPanel('file-contents');
                        }"
                    />
                </SideMenuPanel>
                <SideMenuPanel
                    id="integrations" label="Integrations" icon="pi pi-database"
                    v-if="datasources.length > 0"
                >
                    <DatasourcePanel :datasources="datasources">
                    </DatasourcePanel>
                </SideMenuPanel>
                <SideMenuPanel
                    v-if="props.config.config_type !== 'server'"
                    id="config"
                    :label="`${$tmpl._('short_title', 'Beaker')} Config`"
                    icon="pi pi-cog"
                    :lazy="true"
                    position="bottom"
                >
                    <ConfigPanel
                        ref="configPanelRef"
                        @restart-session="restartSession"
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
                <SideMenuPanel
                    id="file-contents"
                    label="File Contents"
                    icon="pi pi-file beaker-zoom"
                    no-overflow
                >
                    <FileContentsPanel
                        :url="previewedFile?.url"
                        :mimetype="previewedFile?.mimetype"
                    />
                </SideMenuPanel>
                <SideMenuPanel id="kernel-logs" label="Logs" icon="pi pi-list" position="bottom">
                    <DebugPanel :entries="debugLogs" @clear-logs="debugLogs.splice(0, debugLogs.length)" v-autoscroll />
                </SideMenuPanel>
            </SideMenu>
        </template>
    </BaseInterface>
</template>

<script setup lang="ts">
import { defineProps, ref, defineEmits, watch, provide, computed, nextTick, onMounted, inject, toRaw, isReactive, reactive } from 'vue';
import { JupyterMimeRenderer, IBeakerCell, IMimeRenderer, BeakerSession } from 'beaker-kernel/src';
import { BeakerNotebookComponentType } from '../components/notebook/BeakerNotebook.vue';
import { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, MarkdownRenderer, wrapJupyterRenderer, BeakerRenderOutput, TableRenderer } from '../renderers';
import { NavOption } from '../components/misc/BeakerHeader.vue';
import { standardRendererFactories } from '@jupyterlab/rendermime';

import BaseInterface from './BaseInterface.vue';
import FilePanel from '../components/panels/FilePanel.vue';
import ConfigPanel from '../components/panels/ConfigPanel.vue';
import SideMenu from "../components/sidemenu/SideMenu.vue";
import SideMenuPanel from "../components/sidemenu/SideMenuPanel.vue";
import FileContentsPanel from '../components/panels/FileContentsPanel.vue';
import NotebookSvg from '../assets/icon-components/NotebookSvg.vue';

import { IBeakerTheme } from '../plugins/theme';
import DebugPanel from '../components/panels/DebugPanel.vue'

import DatasourceEditor from '../components/misc/DatasourceEditor.vue';
import DatasourcePanel from '../components/panels/DatasourcePanel.vue';

const beakerNotebookRef = ref<BeakerNotebookComponentType>();
const beakerInterfaceRef = ref();
const filePanelRef = ref();
const configPanelRef = ref();
const sideMenuRef = ref();
const rightSideMenuRef = ref();

const previewVisible = ref<boolean>(false);

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.has("session") ? urlParams.get("session") : "notebook_dev_session";
const selectedOnLoad = urlParams.has("selected") ? urlParams.get("selected") : undefined;

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

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const saveAsFilename = ref<string>(null);

const isMaximized = ref(false);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const beakerApp = inject<any>("beakerAppConfig");

beakerApp.setPage("integrations");

const contextPreviewData = ref<any>();
const kernelStateInfo = ref();
const datasources = ref([]);
const datasourcesFolderRoot = ref("");

const hasOpenedPanelOnce = ref(false);

type FilePreview = {
    url: string,
    mimetype?: string
}
const previewedFile = ref<FilePreview>();

onMounted(() => {
    sideMenuRef.value.hidePanel()
    rightSideMenuRef.value.hidePanel()
})

const headerNav = computed((): NavOption[] => {
    const nav = [];
    if (!(beakerApp?.config?.pages) || (Object.hasOwn(beakerApp.config.pages, "notebook"))) {
        const href = "/" + (beakerApp?.config?.pages?.notebook?.default ? '' : 'notebook') + window.location.search;
        nav.push(
            {
                type: 'link',
                href: href,
                label: 'Navigate to notebook view',
                component: NotebookSvg,
                componentStyle: {
                    fill: 'currentColor',
                    stroke: 'currentColor',
                    height: '1rem',
                    width: '1rem',
                },
            }
        );
    }
    if (!(beakerApp?.config?.pages) || (Object.hasOwn(beakerApp.config.pages, "chat"))) {
        const href = "/" + (beakerApp?.config?.pages?.chat?.default ? '' : 'chat') + window.location.search;
        nav.push(
            {
                type: 'link',
                href: href,
                icon: 'comment',
                label: 'Navigate to chat view',
            }
        );
    }
    nav.push(...[
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
    return nav;
});

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
    }
    else if (msg.header.msg_type === "kernel_state_info") {
        kernelStateInfo.value = msg.content;
    }
    else if (msg.header.msg_type === "debug_event") {
        debugLogs.value.push({
            type: msg.content.event,
            body: msg.content.body,
            timestamp: msg.header.date,
        });
    }
    else if (msg.header.msg_type === "context_setup_response" || msg.header.msg_type === "context_info_response") {
        var incomingDatasources;
        if (msg.header.msg_type === "context_setup_response") {
            incomingDatasources = msg.content.datasources;

        }
        else if (msg.header.msg_type === "context_info_response") {
            incomingDatasources = msg.content.info.datasources;
        }
        if (incomingDatasources === undefined) {
            incomingDatasources = [];
        }
        datasources.value.splice(0, datasources.value.length, ...incomingDatasources);
        datasourcesFolderRoot.value = msg.content.datasource_root;

        if (!hasOpenedPanelOnce.value) {
            nextTick(() => sideMenuRef.value.selectPanel('integrations'))
            hasOpenedPanelOnce.value = true;
        }
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



</script>

<style lang="scss">

.datasource-container {
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
    padding-top: 1rem;
    overflow: auto;

    .p-fieldset {
        input {
            max-width: 100%;
            width: 100%;
        }
        textarea {
            max-width: 100%;
            width: 100%;
        }

        max-width: 100%;
        .p-fieldset-legend {
            max-width: 100%;
            background: none;
            padding: 0.5rem;
            .p-dropdown {
                margin-right: 0.5rem;
            }
        }
        margin-bottom: 1rem;

        .p-fieldset-content {
            max-width: 100%;
            padding: 0.5rem;
            display: flex;
            flex-direction: column;
            div.p-toolbar {
                max-width: 100%;
                padding: 0.5rem;
                margin-bottom: 0.5rem;
                // &:nth-child(1) {
                //     margin-bottom: 0rem;
                // }
                .p-toolbar-group-start {
                    button {
                        margin-right: 0.5rem
                    }
                }
            }
            > .p-inputtextarea.p-inputtext {
                height: 10rem;
            }
            > p {
                margin-top: 0rem;
            }
        }
    }
}

.spacer {
    &.left {
        flex: 1 1000 25vw;
    }
    &.right {
        flex: 1 1 25vw;
    }
}

.title-extra {
    vertical-align: baseline;
    display: inline-block;
    height: 100%;
    font-family: 'Ubuntu Mono', 'Courier New', Courier, monospace;
}

</style>
