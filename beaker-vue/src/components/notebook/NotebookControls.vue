<template>
  <div class="notebook-controls">
      <InputGroup>
          <Button
              v-if="!props.singleCell"
              @click="addCell"
              icon="pi pi-plus"
              size="small"
              severity="info"
              text
          />
          <Button
              v-if="!props.singleCell"
              @click="removeCell"
              icon="pi pi-minus"
              size="small"
              severity="info"
              text
          />
          <Button
              @click="props.runCell"
              icon="pi pi-play"
              size="small"
              severity="info"
              text
          />
      </InputGroup>
      <slot name="additional-controls" />
  </div>

</template>

<script setup>
import { defineProps, defineEmits, inject } from 'vue';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
// import OpenNotebookButton from '../dev-interface/OpenNotebookButton.vue';
// import NotebookControls from '../lib/UINotebookControls.vue';
import { downloadFileDOM, getDateTime } from '../../util';

const props = defineProps([
  "selectCell",
  "selectedCellindex",
  "runCell"
]);

const emit = defineEmits(['set-context']);
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
