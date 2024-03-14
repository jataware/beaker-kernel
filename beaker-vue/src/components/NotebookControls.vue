<template>
    <NotebookControls
        :selectCell="selectCell"
        :selectedCellIndex="selectedCellIndex"
    >
        <template #additional-controls>
            <InputGroup style="margin-right: 1rem;">
                <Button
                    @click="resetNotebook"
                    v-tooltip.bottom="{value: 'Reset notebook', showDelay: 300}"
                    icon="pi pi-refresh"
                    size="small"
                    severity="info"
                    text
                />
                <Button
                    @click="downloadNotebook"
                    v-tooltip.bottom="{value: 'Download as .ipynb', showDelay: 300}"
                    icon="pi pi-download"
                    size="small"
                    severity="info"
                    text
                />
              <OpenNotebookButton @open-file="loadNotebook"/>
          </InputGroup>
        </template>
    </NotebookControls>
</template>

<script setup>
import { defineEmits, inject } from 'vue';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import OpenNotebookButton from './OpenNotebookButton.vue';
import NotebookControls from '../lib/UINotebookControls.vue';
import { downloadFileDOM, getDateTime } from '../util';

const emit = defineEmits([
  "selectCell",
  "selectedCellindex",
  "set-context"
]);

const session = inject("session");

const identity = () => {console.log('identity func called');};

function loadNotebook(notebookJSON) {
    session.loadNotebook(notebookJSON);
}

const resetNotebook = () => {
    session.reset();
    emit('set-context');
};


function downloadNotebook() {
    const data = JSON.stringify(session.notebook.toIPynb(), null, 2);
    const filename = `Beaker-Notebook_${getDateTime()}.ipynb`;
    const mimeType = 'application/x-ipynb+json';
    downloadFileDOM(data, filename, mimeType);
}
</script>

<style lang="scss">

.notebook-controls {
    margin: 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .p-inputgroup {
        width: unset;
    }
}

</style>
