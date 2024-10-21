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
                <slot name="start-extra"></slot>
            </slot>
        </template>
        <template #end>
            <slot name="end">
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
                    <OverlayPanel
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
                    </OverlayPanel>
                </div>
                <Button
                    @click="downloadNotebook"
                    v-tooltip.bottom="{value: 'Download as .ipynb', showDelay: 300}"
                    icon="pi pi-download"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
                <OpenNotebookButton :severity="$props.defaultSeverity" @open-file="loadNotebook"/>
                <slot name="end-extra"></slot>
            </slot>
        </template>
    </Toolbar>
</template>

<script setup lang="tsx">
import { defineEmits, defineProps, computed, inject, ref, withDefaults, capitalize, nextTick, watch } from "vue";
import { BeakerSession, BeakerBaseCell } from 'beaker-kernel/src';
import { type BeakerNotebookComponentType } from './BeakerNotebook.vue';

import Button from "primevue/button";
import ChevronDownIcon from 'primevue/icons/chevrondown'
import { ButtonProps } from "primevue/button";
import SplitButton from 'primevue/splitbutton';
import InputGroup from "primevue/inputgroup";
import InputText from "primevue/inputtext";
import OverlayPanel from 'primevue/overlaypanel';
import Toolbar from "primevue/toolbar";

import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";
import { downloadFileDOM, getDateTime } from '../../util';

const session = inject<BeakerSession>('session');
const notebook = inject<BeakerNotebookComponentType>('notebook');
const cellMapping = inject<{[key: string]: {icon: string, modelClass: typeof BeakerBaseCell}}>('cell-component-mapping');

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

export interface Props {
    defaultSeverity?: ButtonProps["badgeSeverity"];
    saveAvailable?: boolean;
    saveAsFilename?: string;
}

const props = withDefaults(defineProps<Props>(), {
    defaultSeverity: "info",
    saveAvailable: false,
});

const saveAsFilename = ref<string>(props.saveAsFilename);
const saveAsHoverMenuRef = ref();
const saveAsInputRef = ref();

watch(props, (oldValue, newValue) => {
    if (saveAsFilename.value !== newValue.saveAsFilename) {
        saveAsFilename.value = newValue.saveAsFilename;
    }
});

const resetSaveAsFilename = () => {
    saveAsFilename.value = `Beaker-Notebook_${getDateTime()}.ipynb`;
}

const resetNotebook = async () => {
    if (window.confirm(`This will reset your entire session, clearing the notebook and removing any updates to the environment. Proceed?`)) {
        session.reset();
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
    const filename = `Beaker-Notebook_${getDateTime()}.ipynb`;
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

        .p-splitbutton-menubutton {
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
