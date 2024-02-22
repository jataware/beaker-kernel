<template>
  <div class="data-container">
    <div class="scroller-area">
      <div style="padding: 0.5rem;">
        <Button
            @click="openFileSelection"
            v-tooltip.bottom="{value: 'Open ipynb file', showDelay: 300}"
            icon="pi pi-folder"
            size="small"
            severity="info"
            label="Upload file(s)"
        />
        <form ref="uploadForm">
          <input
            @change="onSelectFile"
            ref="fileInput"
            type="file"
            multiple
            style="display:none;"
            name="uploadfiles"
          />
          <input
            type="hidden"
            name="_xsrf"
            :value="xsrfCookie"
          />
        </form>

      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>

import { ref, computed, inject, defineProps } from "vue";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
// import Checkbox from 'primevue/checkbox'; // Commented dev opts in template
import Panel from 'primevue/panel';
import cookie from 'cookie';

const props = defineProps([
  "entries",
  "sortby",
])

const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;

console.log(cookies);
console.log(xsrfCookie);

const showToast = inject('show_toast');

const options = ref([]);

const fileInput = ref(null);
const uploadForm = ref<HTMLFormElement|undefined>(undefined);

const openFileSelection = () => {
   fileInput.value.click();
}

const onSelectFile = (event) => {
  const url = "/upload";
  // const files = event.target.files; // ensure there's always one...
  // console.log(uploadForm);
  // uploadForm.value.submit();
  const formData = new FormData(uploadForm.value);
  console.log(formData);
  const uploadFuture = fetch(url, {
    method: "post",
    body: formData,
  }).then(async (response) => {
    console.log(response);
    const text = await response.text();
    if (response.status === 200) {
      showToast({title: 'Upload complete', detail: text, severity: 'success', life: 4000});
    }
    else {
      showToast({title: 'Upload failed', detail: text, severity: 'error', life: 4000});
    }
  }).catch((r) => {
    console.log("error!", r);

  });
}

</script>

<style lang="scss">
.data-container {
  // The internal class for the json viewer-
  // Change the hoder color for better contrast
  .vjs-tree-node:hover{
    background-color: var(--surface-b);
  }
}

.ml-2 {
  margin-left: 0.5rem;
}

.flex-container {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  justify-content: space-between;
  flex-wrap: wrap;
}

.log-panel {
  margin-top: 0.5rem;
  // margin-bottom: 0;
  position: relative;

  .p-panel-header {
    background: var(--surface-b);
    padding: 0.5rem 1rem;
  }
  .p-panel-content {
    padding: 0.5rem 0.75rem;
  }

  // If we wanted to alternate widget panel-heading bg color or so:
  // &.odd {
  //   .p-panel-header {
  //     background: var(--surface-b);
  //   }
  // }
}

.log-panel::before {
  content: attr(data-index);
  color: var(--gray-300);
  position: absolute;
  right: 1rem;
  top: 0.4rem;
}

.bottom-actions {
  width: 100%;
  display: flex;
  margin-top: 0.5rem;
  justify-content: center;
  color: var(--text-color-secondary);
}

.sort-actions {
  .p-button {
    border-color: var(--surface-d);
  }
}

</style>
