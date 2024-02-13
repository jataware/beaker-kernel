<template>
  <div class="data-container">
    <div class="scroller-area">

      <div style="padding: 0.5rem;">

        <!-- Some dev options to format json body display
        <div style="padding-bottom: 0.5rem; display: none;">
          <Checkbox 
            v-model="options"
            id="quotes"
            name="quotes"
            value="quotes"
          />
          <label for="quotes" class="ml-2">quotes</label>

          <Checkbox 
            class="ml-2"
            v-model="options"
            id="linenum"
            name="linenum"
            value="linenum"
          />
          <label for="linenum" class="ml-2">linenum</label>
        </div>
        -->

        <div class="flex-container">
          <div 
            class="p-input-icon-left"
            style="padding: 0; margin: 0;"
          >
            <i class="pi pi-search" />
            <InputText 
              v-model="filterValue"
              size="small"
              placeholder="Filter"
            />
          </div>

          <div class="sort-actions p-buttonset">
            <Button @click="sortDirection = 'asc'" v-tooltip.bottom="'Sort Asc'" outlined size="small" icon="pi pi-sort-numeric-down" aria-label="Sort Time Asc" />
            <Button @click="sortDirection = 'desc'" v-tooltip.bottom="'Sort Desc'" outlined size="small" icon="pi pi-sort-numeric-up-alt" aria-label="Sort Time Desc" />
          </div>

        </div>

        <Panel 
          class="log-panel"
          :class="{odd: index % 2 !== 0}"
          :data-index="index"
          v-for="(logEntry,index) in filteredLogs" :key="index"
          :header="logEntry.event"
        >
          <vue-json-pretty 
            :data="logEntry.body" 
            :deep="2"
            showLength
            showIcon
            :showDoubleQuotes="isQuotes"
            :showLineNumber="linenum"
          />
        </Panel>

        <div 
          class="bottom-actions"
        >
          <Button
            v-if="filteredLogs.length"
            label="Clear Logs"
            severity="warning"
            size="small"
          />
          <p v-else>
            No logs. Ensure loaded context has debug enabled.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>

import { ref, computed, inject } from "vue";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
// import Checkbox from 'primevue/checkbox'; // Commented dev opts in template
import Panel from 'primevue/panel';


const filterValue = ref("");
const sortDirection = ref("asc");

const options = ref([]);

const isQuotes = computed(() => {
  return options.value.includes('quotes');
});

const linenum = computed(() => {
  return options.value.includes('linenum');
})

const upstreamLogs: [{event: string, body: object}] = inject('debug_logs');

// TODO debounce for quick typing
const filteredLogs = computed(() => {
  const filtered = upstreamLogs.filter(logObj => logObj.event.includes(filterValue.value));
  // Default sort as downloaded- return
  if (sortDirection.value === 'asc') {
     return filtered;
  }
  // else we'll sort by index, reverse
  const mapped = filtered.map((item, idx) => ({
      event: item.event,
      body: item.body,
      idx
    })
  );
  return mapped.sort((a,b) => b.idx - a.idx);
});

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
