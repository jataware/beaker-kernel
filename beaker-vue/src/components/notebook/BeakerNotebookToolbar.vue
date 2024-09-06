<template>
    <Toolbar class="notebook-toolbar">
        <template #start>
            <slot name="start">
                <Button
                    @click="notebook.insertCellAfter()"
                    icon="pi pi-plus"
                    size="small"
                    :severity="props.defaultSeverity"
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
import { defineProps, inject, withDefaults } from "vue";
import { BeakerSession } from 'beaker-kernel';
import { type BeakerNotebookComponentType } from './BeakerNotebook.vue';

import Button from "primevue/button";
import { ButtonProps } from "primevue/button";
import Toolbar from "primevue/toolbar";

import OpenNotebookButton from "../dev-interface/OpenNotebookButton.vue";
import { downloadFileDOM, getDateTime } from '../../util';

const session = inject<BeakerSession>('session');
const notebook = inject<BeakerNotebookComponentType>('notebook');

const addCodeCell = () => {
    // const newCell = session.addCodeCell("");
    // notebook.selectCell(newCell);
}

const addMarkdownCell = () => {
    // const newCell = session.addMarkdownCell("");
    // notebook.selectCell(newCell);
}

export interface Props {
    defaultSeverity?: ButtonProps["badgeSeverity"];
}

const props = withDefaults(defineProps<Props>(), {
    defaultSeverity: "info",
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
}
</style>
