<template>
    <Toolbar class="notebook-toolbar">
        <template #start>
            <slot name="start">
                <SplitButton
                    @click="notebook.insertCellAfter()"
                    class="toolbar-splitbutton add-cell-button"
                    icon="pi pi-plus"
                    size="small"
                    :severity="props.defaultSeverity"
                    :model="addCellMenuItems"
                    text
                />
                <Button
                    @click="notebook.removeCell()"
                    icon="pi pi-minus"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <Button
                    @click="notebook.selectedCell().execute()"
                    icon="pi pi-play"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <Button
                    @click="session.interrupt()"
                    icon="pi pi-stop"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <slot name="start-extra"></slot>
            </slot>
        </template>
        <template #end>
            <slot name="end">
                <AnnotationButton
                    :action="analyzeCells"
                    v-tooltip.bottom="{value: 'Analyze Codecells', showDelay: 300}"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <Button
                    @click="resetNotebook"
                    v-tooltip.bottom="{value: 'Reset notebook', showDelay: 300}"
                    icon="pi pi-refresh"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <div v-if="props.saveAvailable" class="p-splitbutton toolbar-splitbutton">
                    <Button
                        class="p-splitbutton-defaultbutton"
                        @click="saveNotebook"
                        v-tooltip.bottom="{
                            value: 'Save locally as ' + (saveAsFilename ? saveAsFilename : 'a .ipynb file') ,
                            showDelay: 300
                        }"
                        icon="pi pi-save"
                        size="small"
                        :severity="props.defaultSeverity"
                        text
                    />
                    <Button
                        class="p-splitbutton-menubutton"
                        size="small"
                        :severity="props.defaultSeverity"
                        text
                        @click="saveAsHoverMenuRef.toggle($event);"
                    >
                         <ChevronDownIcon/>
                    </Button>
                    <Popover
                        class="saveas-overlay"
                        ref="saveAsHoverMenuRef"
                        :popup="true"
                        @show="if (!saveAsFilename) {resetSaveAsFilename()};"
                    >
                        <div>Save as:</div>
                        <InputGroup>
                            <InputText
                                class="saveas-input"
                                ref="saveAsInputRef"
                                v-model="saveAsFilename"
                                @keydown.enter="saveAs()"
                                autofocus
                            />
                            <Button label="Save" @click="saveAs()"/>
                        </InputGroup>
                    </Popover>
                </div>
                <SplitButton
                    @click="downloadNotebook"
                    class="toolbar-splitbutton"
                    v-tooltip.bottom="{value: 'Export (download) as .ipynb', showDelay: 300}"
                    icon="pi pi-download"
                    size="small"
                    :model="exportAsTypes"
                    :severity="props.defaultSeverity"
                    text
                />
                <OpenNotebookButton :severity="$props.defaultSeverity" @open-file="loadNotebook"/>
                <slot name="end-extra"></slot>
            </slot>
        </template>
    </Toolbar>
</template>

<script setup lang="ts">
import { computed, inject, ref, capitalize, watch, onBeforeMount, toRaw } from "vue";
import { PageConfig } from '@jupyterlab/coreutils';
import { URLExt } from '@jupyterlab/coreutils';
import type { BeakerSession, BeakerBaseCell } from 'beaker-kernel';
import type { BeakerNotebookComponentType } from './BeakerNotebook.vue';
import contentDisposition from "content-disposition";

import Button from "primevue/button";
import ChevronDownIcon from '@primevue/icons/chevrondown'
import type { ButtonProps } from "primevue/button";
import SplitButton from 'primevue/splitbutton';
import InputGroup from "primevue/inputgroup";
import InputText from "primevue/inputtext";
import Popover from "primevue/popover";
import Toolbar from "primevue/toolbar";
import type { MenuItem } from "primevue/menuitem";

import AnnotationButton from "../misc/buttons/AnnotationButton.vue"
import OpenNotebookButton from "../misc/OpenNotebookButton.vue";
import { downloadFileDOM, getDateTimeString } from '../../util';

const session = inject<BeakerSession>('session');
const notebook = inject<BeakerNotebookComponentType>('notebook');
const cellMapping = inject<{[key: string]: {icon: string, modelClass: typeof BeakerBaseCell}}>('cell-component-mapping');
const showOverlay = inject<(contents: string, header?: string) => void>('show_overlay');

const addCellMenuItems = computed(() => {
    return Object.entries(cellMapping).map(([name, obj]) => {
        return {
            label: `${capitalize(name)} Cell`,
            icon: obj.icon,
            command: () => {
                const cell = new obj.modelClass({
                    source: "",
                });
                notebook.insertCellAfter(notebook.selectedCell(), cell, true);
            },
        }
    })
});

const emit = defineEmits([
    "notebook-saved",
    "open-file",
])

interface BeakerNotebookToolbarProps {
    defaultSeverity?: ButtonProps["badgeSeverity"];
    saveAvailable?: boolean;
    saveAsFilename?: string;
}

const props = withDefaults(defineProps<BeakerNotebookToolbarProps>(), {
    defaultSeverity: "info",
    saveAvailable: false,
});

const saveAsFilename = ref<string>(props.saveAsFilename);
const saveAsHoverMenuRef = ref();
const saveAsInputRef = ref();

const exportAsTypes = ref<MenuItem[]>([
    {
        label: "Loading...",
        disabled: true,
    }
]);

const exportAction = (format: string, mimetype: string) => {
    const url = URLExt.join(PageConfig.getBaseUrl(), 'export', format);
    if (!saveAsFilename.value) {
        resetSaveAsFilename();
    }
    fetch(
        url,
        {
            "method": "POST",
            "body": JSON.stringify({
                name: saveAsFilename.value,
                content: notebook.notebook.toIPynb(),
            }),
            "headers": {
                "Content-Type": "application/json;charset=UTF-8"
            },
        }
    ).then(async (result) => {
        if (result.status === 200) {
            const data = await result.text();
            const dispositionHeader = result.headers.get("content-disposition")
            const disposition = contentDisposition.parse(dispositionHeader);
            const filename = disposition.parameters.filename;
            downloadFileDOM(data, filename, mimetype)
        }
        else {
            const errorInfo = await result.json();
            showOverlay(errorInfo, "Error converting notebook");
        }
    }).catch((reason) => console.error(reason));
}

const refreshExportTypes = async () => {
    const ignoredFormats = new Set(["custom", "qtpdf", "qtpng", "webpdf"]);
    const formats = await session.services.nbconvert.getExportFormats();
    exportAsTypes.value = Object.entries(formats).filter(([format]) => {
        if (ignoredFormats.has(format)) {
            return false;
        }
        return true
    }).map(([format, formatInfo]) => {
        const mimetype = formatInfo.output_mimetype;
        return {
            label: format,
            tooltip: mimetype,
            command: () => {exportAction(format, mimetype)},
        }
    });
};

onBeforeMount(async () => {
    refreshExportTypes();
})

watch(props, (oldValue, newValue) => {
    if (saveAsFilename.value !== newValue.saveAsFilename) {
        saveAsFilename.value = newValue.saveAsFilename;
    }
});

const resetSaveAsFilename = () => {
    saveAsFilename.value = `Beaker-Notebook_${getDateTimeString()}.ipynb`;
}


const analyzeCells = async () => {
    const payload = {
        notebook_id: notebook.id,
        cells: notebook.notebook.cells.map(cell => {return {cell_id: cell.id, content: cell.source}}),
    };
    const lintAction = session.executeAction("lint_code", payload)
    await lintAction.done;
}

const resetNotebook = async () => {
    if (window.confirm(`This will reset your entire session, clearing the notebook and removing any updates to the environment. Proceed?`)) {
        toRaw(session).reset();
        saveAsFilename.value = undefined;
        emit("notebook-saved", undefined);
        if (notebook.cellCount <= 0) {
            notebook.selectCell(session.addCodeCell("") as {id: string});
        }
    }
};

function loadNotebook(notebookJSON: any, filename: string) {
    emit("open-file", notebookJSON, filename);
}

async function saveNotebook() {
    const notebookContent = session.notebook.toIPynb();
    const contentsService = session.services.contents;
    if (!saveAsFilename.value) {
        resetSaveAsFilename();
    }
    const path = `./${saveAsFilename.value}`;
    const result = await contentsService.save(path, {
        type: "notebook",
        content: notebookContent,
        format: 'text',
    });
    emit("notebook-saved", result.path);
    saveAsFilename.value = result.path;
}

async function saveAs() {
    await saveNotebook();
    saveAsHoverMenuRef.value.hide();

}

function downloadNotebook() {
    const data = JSON.stringify(session.notebook.toIPynb(), null, 2);
    const filename = `Beaker-Notebook_${getDateTimeString()}.ipynb`;
    const mimeType = 'application/x-ipynb+json';
    downloadFileDOM(data, filename, mimeType);
}

</script>


<style lang="scss">
.notebook-toolbar {
    margin: 0;
    padding: 0;
    *:focus {
        box-shadow: none !important;
    }

    .toolbar-splitbutton {
        .p-splitbutton-defaultbutton {
            padding-right: 0;
        }

        .p-splitbutton-dropdown {
            padding-left: 0;
            padding-top: 0;
            padding-bottom: 0.5rem;
            width: min-content;

            .p-icon, .p-button-icon {
                height: 0.7rem;
                font-size: 0.875rem;;
            }
        }
    }

}

.saveas-overlay {
    .p-overlaypanel-content {
        padding: 0.5rem;
    }
    .saveas-input {
        min-width: 25rem;
        padding: 0.25rem;
        font-size: small;
        font-family: 'Courier New', Courier, monospace;
    }
}
</style>
