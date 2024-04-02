<template>
  <div class="notebook-controls">
      <InputGroup>
          <Button
              @click="emit('add-cell')"
              v-tooltip.bottom="{value: 'Add New Cell', showDelay: 300}"
              icon="pi pi-plus"
              size="small"
              severity="primary"
              text
          />
          <Button
              @click="emit('remove-cell')"
              v-tooltip.bottom="{value: 'Remove Selected Cell', showDelay: 300}"
              icon="pi pi-minus"
              size="small"
              severity="primary"
              text
          />
          <Button
              @click="emit('run-cell')"
              v-tooltip.bottom="{value: 'Run Selected Cell', showDelay: 300}"
              icon="pi pi-play"
              size="small"
              severity="primary"
              text
          />
          <!-- TODO implement Stop-->
          <Button
              @click="identity"
              v-tooltip.bottom="{value: 'Stop Execution', showDelay: 300}"
              icon="pi pi-stop"
              size="small"
              severity="primary"
              text
          />
      </InputGroup>
      <InputGroup style="margin-right: 1rem;">
          <Button
              @click="resetNotebook"
              v-tooltip.bottom="{value: 'Reset notebook', showDelay: 300}"
              icon="pi pi-refresh"
              size="small"
              severity="primary"
              text
          />
          <Button
              @click="downloadNotebook"
              v-tooltip.bottom="{value: 'Download as .ipynb', showDelay: 300}"
              icon="pi pi-download"
              size="small"
              severity="primary"
              text
          />
          <OpenNotebookButton @open-file="loadNotebook"/>
      </InputGroup>
  </div>
</template>

<script setup>
import { defineEmits, inject } from 'vue';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import OpenNotebookButton from './OpenNotebookButton.vue';
import { downloadFileDOM, getDateTime } from '../util';

const emit = defineEmits([
  "run-cell",
  "remove-cell",
  "add-cell",
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
    margin-top: 0.25rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--surface-c);

    .p-inputgroup {
        width: unset;
    }
}

</style>
