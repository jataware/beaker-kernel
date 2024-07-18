<template>
  <Button
      @click="openFileSelection"
      v-tooltip.bottom="{value: 'Open ipynb file', showDelay: 300}"
      icon="pi pi-folder-open"
      size="small"
      severity="info"
      text
  />
  <form id="open-file-form" ref="fileForm">
    <input
      @change="onSelectFile"
      ref="fileInput"
      type="file"
      style="display:none;"
    />
  </form>


</template>

<script setup>
import { ref, defineEmits, inject } from "vue";
import Button from 'primevue/button';

const emit = defineEmits([
  'open-file'
]);

const showToast = inject('show_toast');

const fileInput = ref(null);
const fileForm = ref(null);

const openFileSelection = () => {
   fileInput.value.click();
}

const onSelectFile = (event) => {
  const file = event.target.files[0]; // ensure there's always one...

  if (!file.size ) {
    showToast({title: 'Error', detail: 'File looks empty. Check file.', severity: 'error', life: 10000});
    return;
  } else if (!/\.ipynb$/.test(file.name)) {
    showToast({title: 'File not ipynb.', detail: 'Beaker will try to load as json.', severity: 'warn', life: 4000});
  }

  const reader = new FileReader();

  reader.readAsText(file);

  // handle file content when read op completes
  reader.onload = function (event) {
    const fileContent = event.target.result;
    try {
      const json = JSON.parse(fileContent);

      emit('open-file', json);
      // showToast({title: 'Well Done!', detail: 'Replacing Beaker session with ipynb file data.', life: 4000});

    // emit('open-file', json); // pass either as string or json...
    } catch(e) {
      console.error(e);
      showToast({
        title: 'Invalid File',
        detail: 'Unable to load. Please check file contains valid ipynb json data.',
        severity: 'error',
        life: 10000
      });
    }

  };

  // Reset the file selection so that selecting a file later on
  // processes the onChange event properly
  fileForm.value.reset();
};


</script>

<style lang="scss">
  #open-file-form {
    display: none;
  }

</style>
