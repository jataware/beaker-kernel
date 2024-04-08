<template>
  <ConfirmDialog></ConfirmDialog>
  <div id="admin">
    <div>
      <h1 style="text-align: center;">Beaker admin</h1>
      <div style="margin-right: 3rem; display: flex; justify-content: right; justify-items: center;">
        <span style="margin-top: auto; margin-bottom: auto; font-weight: bolder; font-size: larger;">Last updated: {{ lastUpdated  }}</span>
        <Button icon="pi pi-refresh" style="margin-left: 1rem;" raised @click="updateStats()" /> </div>
    </div>

    <div class="stats">
      <h2>Stats</h2>
      <div class="stats-tables">
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
      <h2>Sessions</h2>
      <DataTable :value="sessionData" v-model:selection="selectedSessions" v-model:expanded-rows="expandedRows" :striped-rows="true" removableSort>
        <template #header>
          <div class="header">
              <span class="header-title">Sessions</span>
              <span style="flex: 100"></span>
              <span style="font-size: large;">Session count: {{ adminStats.sessions?.length || 0 }}</span>
              <span style="padding: 0 1rem"> | </span>
              <Dropdown :options="['---', 'destroy']" v-model="sessionAction"></Dropdown>
              <Button severity="success" raised @click="groupSessionAction">Go</Button>
          </div>
        </template>
        <Column selection-mode="multiple"></Column>
        <Column expander style="width: 5rem" />
        <Column field="beaker_id" header="Beaker ID" sortable></Column>
        <Column field="raw_id" header="Raw ID" sortable></Column>
        <Column field="beaker_kernel" header="Beaker Kernel" sortable></Column>
        <Column field="last_active" header="Last Active" sortable></Column>
        <Column field="idle" header="Idle Duration (minutes)" sortable></Column>
        <Column field="connected" header="User connected" sortable></Column>
        <Column header="Destroy">
          <template #body="{ data }">
            <Button icon="pi pi-times" severity="danger" raised @click="terminateSessions([{beaker_id: data.beaker_id, raw_id: data.raw_id}])"/>
          </template>
        </Column>

        <template #expansion="{ data }">
          <div>
            <h4>Process details <span style="font-size: smaller; margin-left: 3rem;">(Note: CPU and Memory usage may be reflected mulitple times due to parent/child relational reporting)</span></h4>
            <DataTable :value="data.process_info" :striped-rows="true" removableSort>
                <Column field="pid" header="PID" sortable></Column>
                <Column field="ppid" header="Parent PID" sortable></Column>
                <Column field="cpu_pct" header="CPU Usage %" sortable></Column>
                <Column field="cputime" header="Cumulative CPU Time" sortable></Column>
                <Column field="mem_pct" header="Mem Usage (%)" sortable></Column>
                <Column field="mem_bytes" header="Mem Usage (bytes)" sortable></Column>
                <Column field="threads" header="Thread count" sortable></Column>
                <Column field="open_files" header="File handles" sortable></Column>
                <Column field="cmd" header="Full command" sortable></Column>
            </DataTable>
          </div>
        </template>
      </DataTable>
    </div>

  </div>
  <Toast position="bottom-right" />
</template>

<script setup lang="ts">
import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { defineProps, reactive, ref, onBeforeMount, provide, onBeforeUnmount, computed } from 'vue';
import DataTable from 'primevue/datatable';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import Column from 'primevue/column';
import ConfirmDialog from 'primevue/confirmdialog';
import Dropdown from 'primevue/dropdown';
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
const sessionAction = ref<string>("---");
const selectedSessions = ref<{beaker_id: string, raw_id: string}[]>([]);
const expandedRows = ref([])

const sessionData = computed(() => {
  const result = adminStats.value.sessions?.map((session) => {
    return {
      "beaker_id": session.path,
      "raw_id": session.id,
      "beaker_kernel": session.kernel.id,
      "last_active": session.kernel.last_activity,
      "idle": ((Date.now() - Date.parse(session.kernel.last_activity)) / 60000).toFixed(2),
      "connected": session.kernel.connections > 0,
      "process_info": session.process_info,
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

const _terminateSessions = async (sessionIds: string[]) => {
  for (const sessionId of sessionIds) {
    const sessionUrl =URLExt.join(baseUrl, '/api/sessions/', sessionId);
    const result = await fetch(sessionUrl, {method: "DELETE", headers: {"Authorization": `token ${adminStats.value.token}`}});
    if (!result.ok) {
      const responseText = await result.text();
      toast.add({ severity: 'error', summary: 'Error removing session', detail: `${result.status} ${result.statusText} - ${responseText}`, life: 3000 });
    }
  }
  await updateStats();

};

const groupSessionAction = () => {
  if (selectedSessions.value.length === 0 || sessionAction.value === '---') {
    return;
  }
  if (sessionAction.value === "destroy") {
    terminateSessions(selectedSessions.value);
  }
};

const terminateSessions = (sessions: {beaker_id: string, raw_id: string}[]) => {
  confirm.require({
        message: `Are you sure you want to proceed? This will destroy session(s): ${sessions.map((e) => e.beaker_id).join(", ")}`,
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        rejectClass: 'p-button-secondary p-button-outlined',
        rejectLabel: 'Cancel',
        acceptLabel: 'Confirm',
        accept: async () => {
          await _terminateSessions(sessions.map((e) => e.raw_id));
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
  align-items: center;
  padding-right: 0.4rem;
  gap: 0.2rem;
}

.header-title {
  font-size: xx-large;
  font-weight: bolder;
}

.stats {
  margin-bottom: 3rem;
  gap: 4rem;
}

.p-datatable {
  border: 1px solid var(--surface-border);
}

.stats-tables {
  display: flex;
  flex-direction: row;
  gap: 2rem;

}

.session-select {
  width: 1.2rem;
  height: 1.2rem;
}

tr.p-highlight {
    color: black;
}

tr.p-row-odd {
  background-color: #F0F0F0;

  &.p-highlight {
    background-color: #D0D0F0;
  }
}

tr.p-datatable-row-expansion {
  background-color: #DDDDDD;
}
</style>
