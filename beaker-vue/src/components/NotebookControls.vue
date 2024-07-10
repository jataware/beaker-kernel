<template>
  <div class="notebook-controls">
        <div>
            <Button
                @click="emit('reset-nb')"
                v-tooltip.bottom="{value: 'Reset notebook', showDelay: 300}"
                icon="pi pi-refresh"
                size="small"
                severity="info"
                text
            />
            <!--
            <Button
                @click="downloadNotebook"
                v-tooltip.bottom="{value: 'Download as .ipynb', showDelay: 300}"
                icon="pi pi-download"
                size="small"
                severity="info"
                text
            />
            <OpenNotebookButton @open-file="loadNotebook"/>
            -->
            <Button
                @click="toggleFileMenu"
                v-tooltip.bottom="{value: 'Show file menu', showDelay: 300}"
                icon="pi pi-folder-open"
                size="small"
                severity="info"
                text
            />
        </div>
        <OverlayPanel ref="isFileMenuOpen"><BeakerFilePane/></OverlayPanel>
  </div>
</template>

<script setup>
import { defineEmits, inject, ref } from 'vue';
import Button from 'primevue/button';
import OverlayPanel from 'primevue/overlaypanel';
import InputGroup from 'primevue/inputgroup';
import OpenNotebookButton from './OpenNotebookButton.vue';
import { downloadFileDOM, getDateTime } from '../util';
import BeakerFilePane from './BeakerFilePane.vue';

const emit = defineEmits([
  "run-cell",
  "remove-cell",
  "add-code-cell",
  "add-markdown-cell",
  "reset-nb"
]);

const isFileMenuOpen = ref();
const toggleFileMenu = (event) => {
    isFileMenuOpen.value.toggle(event);
}

const menuModel = [
    {
        label: "Add Code Cell",
        icon: "pi pi-code",
        command: () => emit("add-code-cell"),
    },
    {
        label: "Add Markdown Cell",
        icon: "pi pi-pencil",
        command: () => emit("add-markdown-cell"),
    }
];

const session = inject("session");

const identity = () => {console.log('identity func called');};

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

.notebook-controls {
    margin-bottom: 3%;
    display: flex;
    //align-items: center;
    //padding-left: 20%;
    justify-content: center;

    .p-inputgroup {
        width: unset;
    }
}

</style>
