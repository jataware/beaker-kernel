<template>
  <ConfirmDialog></ConfirmDialog>
  <div id="app">
    <div>
      <h1 style="text-align: center;">Beaker admin</h1>
      <div style="margin-right: 3rem; display: flex; justify-content: right; justify-items: center;">
        <span style="margin-top: auto; margin-bottom: auto; font-weight: bolder; font-size: larger;">Last updated: {{ lastUpdated  }}</span>
        <Button icon="pi pi-refresh" style="margin-left: 1rem;" raised @click="updateStats()" /> </div>
    </div>

    <div class="stats">
      <h2>Stats</h2>
      <div style="display: flex; flex-direction: row;">
        <DataTable :value="[adminStats.file_handles]">
          <template #header>
            <div class="header">
                <span class="header-title">File Handles</span>
            </div>
          </template>
          <Column field="open" header="Open"></Column>
          <Column field="total" header="Total"></Column>
          <Column field="usage" header="Usage"></Column>
        </DataTable>

        <DataTable :value="[adminStats.load]">
          <template #header>
            <div class="header">
                <span class="header-title">Load</span>
            </div>
          </template>
          <Column field="1_min" header="1 Min"></Column>
          <Column field="5_min" header="5 Min"></Column>
          <Column field="15_min" header="15 Min"></Column>
        </DataTable>

        <DataTable :value="[adminStats.memory]">
          <template #header>
            <div class="header">
                <span class="header-title">Memory</span>
            </div>
          </template>
          <Column field="total" header="Total"></Column>
          <Column field="used" header="Used"></Column>
          <Column field="free" header="Free"></Column>
          <Column field="usage" header="Usage"></Column>
        </DataTable>

        <DataTable :value="[adminStats.disk]">
          <template #header>
            <div class="header">
                <span class="header-title">Disk</span>
            </div>
          </template>
          <Column field="total" header="Total"></Column>
          <Column field="used" header="Used"></Column>
          <Column field="free" header="Free"></Column>
          <Column field="usage" header="Usage"></Column>
        </DataTable>

      </div>
    </div>
    <div>
      <h2>Stats</h2>
      <DataTable :value="sessionData">
        <template #header>
          <div class="header">
              <span class="header-title">Sessions</span>
          </div>
        </template>
        <Column field="beaker_id" header="Beaker ID"></Column>
        <Column field="raw_id" header="Raw ID"></Column>
        <Column field="beaker_kernel" header="Beaker Kernel"></Column>
        <Column field="last_active" header="Last Active"></Column>
        <Column field="idle" header="Idle Duration (minutes)"></Column>
        <Column field="connected" header="User connected"></Column>
        <Column header="Destroy">
          <template #body="{ data }">
            <Button icon="pi pi-times" severity="danger" raised @click="terminateSession(data.raw_id)"/>
          </template>
        </Column>
      </DataTable>
    </div>

  </div>
  <Toast position="bottom-right" />
</template>

<script setup lang="ts">
import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { defineProps, reactive, ref, onBeforeMount, provide, onBeforeUnmount, computed } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import ConfirmDialog from 'primevue/confirmdialog';
import Toast from 'primevue/toast';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';

const props = defineProps([
  "config"
]);
const confirm = useConfirm();
const toast = useToast();

const baseUrl = PageConfig.getBaseUrl();

const adminStats = ref({});
const intervalRef = ref();
const lastUpdated = ref("never");

const sessionData = computed(() => {
  const result = adminStats.value.sessions?.map((session) => {
    return {
      "beaker_id": session.path,
      "raw_id": session.id,
      "beaker_kernel": session.kernel.id,
      "last_active": session.kernel.last_activity,
      "idle": ((Date.now() - Date.parse(session.kernel.last_activity)) / 60000).toFixed(2),
      "connected": session.kernel.connections > 0,
    }
  });
  return result;
});

const updateStats = async () => {
  const statsUrl = URLExt.join(baseUrl, '/stats');
  const statsResponse = await fetch(statsUrl);
  adminStats.value = await statsResponse.json();
  lastUpdated.value = new Date().toUTCString();
}

const terminateSession = (sessionId) => {
  confirm.require({
        message: 'Are you sure you want to proceed?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        rejectClass: 'p-button-secondary p-button-outlined',
        rejectLabel: 'Cancel',
        acceptLabel: 'Confirm',
        accept: async () => {
          const sessionUrl =URLExt.join(baseUrl, '/api/sessions/', sessionId);
          const result = await fetch(sessionUrl, {method: "DELETE", headers: {"Authorization": `token ${adminStats.value.token}`}});
          if (!result.ok) {
            const responseText = await result.text();
            toast.add({ severity: 'error', summary: 'Error removing session', detail: `${result.status} ${result.statusText} - ${responseText}`, life: 3000 });
          }
          await updateStats();
        },
        reject: () => {
          // Do nothing
        }
    });
}

onBeforeMount(() => {
  updateStats();
  intervalRef.value = window.setInterval(updateStats, 60000);
});

onBeforeUnmount(() => {
  clearInterval(intervalRef.value);
});

</script>

<style lang="scss">
#app {
  margin: 0.5rem;
}

.header {
  display: flex;
}

.header-title {
  font-size: xx-large;
  font-weight: bolder;
}

.stats {
  margin-bottom: 3rem;
  * {
    margin-right: 0.5rem;
  }
}
</style>
