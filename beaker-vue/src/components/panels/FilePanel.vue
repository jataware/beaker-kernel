<template>
  <div class="file-container">
    <div class="button-header">
      <Button
          @click="openFileSelection"
          v-tooltip.bottom="{value: 'Files to upload', showDelay: 300}"
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
      <Button
          @click="refreshFiles"
          v-tooltip.bottom="{value: 'Refresh files ', showDelay: 300}"
          icon="pi pi-refresh"
          size="small"
          severity="info"
          label="Refresh"
      />
    </div>

    <div v-if="files !== undefined">
      <DataTable :value="files" size="small" stripedRows scrollable class="file-table">
        <Column header="" class="download-column">
          <template #body="slotProps">
            <Button
              icon="pi pi-cloud-download"
              class="download-button"
              @click="downloadFile(slotProps.data)"
            ></Button>
          </template>
        </Column>
        <Column field="name" header="Name" class="filename-column" sortable>
          <template #body="slotProps">
            {{ slotProps.data.name }}
          </template>
        </Column>
        <Column field="last_modified" header="Last Modified" sortable>
          <template #body="slotProps">
            <span v-tooltip="slotProps.data.last_modified">
              {{ formatDate(slotProps.data.last_modified) }}
            </span>
          </template>
        </Column>
        <Column field="size" header="Size (bytes)" sortable>
          <template #body="slotProps">
            <span v-tooltip="`${slotProps.data.size} bytes`">
              {{ formatSize(slotProps.data.size) }}
            </span>
          </template>
        </Column>
      </DataTable>
    </div>
    <div v-else>
      Fetching files...
    </div>
  </div>
</template>

<script lang="ts" setup>

import { ref, inject, defineProps, onMounted } from "vue";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import 'vue-json-pretty/lib/styles.css';
import Panel from 'primevue/panel';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import cookie from 'cookie';
import {filesize} from 'filesize';
import {Time} from '@jupyterlab/coreutils/src/time';

import { ContentsManager } from '@jupyterlab/services';


const props = defineProps([
  "entries",
  "sortby",
]);

const contentManager = new ContentsManager({});

const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;

const showToast = inject<any>('show_toast');

const fileInput = ref<HTMLInputElement|undefined>(undefined);
const uploadForm = ref<HTMLFormElement|undefined>(undefined);
const files = ref<any[]|undefined>(undefined);

const formatDate = (dateString) => {
  return Time.formatHuman(dateString);
}

const formatSize = (size) => {
  return filesize(size, {spacer: ""});
}

const openFileSelection = () => {
   fileInput.value?.click();
}

const onSelectFile = () => {
  const url = "/upload";
  const formData = new FormData(uploadForm.value);
  const uploadFuture = fetch(url, {
    method: "post",
    body: formData,
  }).then(async (response) => {
    const text = await response.text();
    if (response.status === 200) {
      showToast({title: 'Upload complete', detail: text, severity: 'success', life: 4000});
    }
    else {
      showToast({title: 'Upload failed', detail: text, severity: 'error', life: 8000});
    }
    await refreshFiles();
  }).catch(async (error) => {
    showToast({title: 'Upload failed', detail: `There was an error trying to upload: ${error}`, severity: 'error', life: 8000});
    await refreshFiles();
  });
}

const downloadFile = async (file) => {
  const url = `/download/${file.name}`;
  window.location.href = url;
};

const refreshFiles = async () => {
  const contents = await contentManager.get(".");
  const filteredFiles = contents.content.filter((item) => item.type === "file" && !item.name.startsWith('.'));
  const sortedFiles = filteredFiles.sort((a, b) => a.name.localeCompare(b.name));
  files.value = sortedFiles;
};


onMounted(async () => {
  await refreshFiles();
});
</script>

<style lang="scss">

  // .filename-column {
  //   min-width: 15rem;
  // }

  .file-table {
    font-size: smaller;
  }

  .download-column {
    width: unset;
    padding: 1px;
    aspect-ratio: 1/1;

    > .p-column-header-content {
      justify-content: center;
    }
  }

  .download-button {
    padding: 0;
    width: unset;
    aspect-ratio: 1/1;
  }

  .button-header {
    display: flex;
    flex-direction: row;

    * {
      margin-right: 10px;
    }
  }

</style>
