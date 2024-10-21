<template>
  <Button
      @click="openFileSelection"
      v-tooltip.bottom="{value: 'Open ipynb file', showDelay: 300}"
      icon="pi pi-folder-open"
      size="small"
      :severity="props.severity"
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

<script setup lang="tsx">
import { ref, defineEmits, inject, defineProps, withDefaults } from "vue";
import Button from 'primevue/button';
import { ButtonProps } from "primevue/button";

export interface Props {
    severity?: ButtonProps["badgeSeverity"];
}

const props = withDefaults(defineProps<Props>(), {
    severity: "info",
});

const emit = defineEmits([
  'open-file'
]);

const showToast = inject<(options: object) => void>('show_toast');

const fileInput = ref(null);
const fileForm = ref(null);

const openFileSelection = () => {
   fileInput.value.click();
}

const onSelectFile = async (event) => {
  const file: File = event.target.files[0]; // ensure there's always one...

  if (!file.size ) {
    showToast({title: 'Error', detail: 'File looks empty. Check file.', severity: 'error', life: 10000});
    return;
  } else if (!/\.ipynb$/.test(file.name)) {
    showToast({title: 'File not ipynb.', detail: 'Beaker will try to load as json.', severity: 'warn', life: 4000});
  }

  const arrayBuffer = await file.arrayBuffer();
  const text = new TextDecoder().decode(arrayBuffer);

  try {
    const json = JSON.parse(text);
    emit('open-file', json, file.name);
  } catch(e) {
    console.error(e);
    showToast({
      title: 'Invalid File',
      detail: 'Unable to load. Please check file contains valid ipynb json data.',
      severity: 'error',
      life: 10000
    });
  }

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
