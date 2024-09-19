<template>
    <Toolbar class="notebook-toolbar">
        <template #start>
            <slot name="start">
                <SplitButton
                    @click="notebook.insertCellAfter()"
                    class="add-cell-button"
                    icon="pi pi-plus"
                    size="small"
                    :severity="props.defaultSeverity"
                    :model="menuItems"
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
                <Button
                    v-if="saveAvailable"
                    @click="saveNotebook"
                    v-tooltip.bottom="{value: 'Save locally as .ipynb', showDelay: 300}"
                    icon="pi pi-save"
                    size="small"
                    :severity="props.defaultSeverity"
                    text
                />
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
import { defineEmits, defineProps, computed, inject, withDefaults, capitalize } from "vue";
import { BeakerSession, BeakerBaseCell } from 'beaker-kernel/src';
import { type BeakerNotebookComponentType } from './BeakerNotebook.vue';

import Button from "primevue/button";
import { ButtonProps } from "primevue/button";
import SplitButton from 'primevue/splitbutton';
import Toolbar from "primevue/toolbar";

import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";
import { downloadFileDOM, getDateTime } from '../../util';

const session = inject<BeakerSession>('session');
const notebook = inject<BeakerNotebookComponentType>('notebook');
const cellMapping = inject<{[key: string]: {icon: string, modelClass: typeof BeakerBaseCell}}>('cell-component-mapping');

const menuItems = computed(() => {
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
])

export interface Props {
    defaultSeverity?: ButtonProps["badgeSeverity"];
    saveAvailable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    defaultSeverity: "info",
    saveAvailable: false,
});

const resetNotebook = async () => {
    session.reset();
    if (notebook.cellCount <= 0) {
        notebook.selectCell(session.addCodeCell("") as {id: string});
    }
};

function loadNotebook(notebookJSON) {
    session.loadNotebook(notebookJSON);
}

async function saveNotebook() {
    const notebookContent = session.notebook.toIPynb();
    const contentsService = session.services.contents;
    const filename = `Beaker-Notebook_${getDateTime()}.ipynb`;
    const path = `${filename}`;
    const result = await contentsService.save(path, {
        type: "notebook",
        content: notebookContent,
        format: 'text',
    });
    emit("notebook-saved", result.path);

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

    .add-cell-button {
        .p-splitbutton-defaultbutton {
            padding-right: 0;
        }

        .p-splitbutton-menubutton {
            padding-left: 0;
            padding-top: 0;
            padding-bottom: 0.5rem;
            width: min-content;

            .p-icon {
                height: 0.7rem;
            }
        }
    }
}
</style>
