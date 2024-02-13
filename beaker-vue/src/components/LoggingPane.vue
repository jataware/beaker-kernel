<template>

        <div class="data-container">
          <div class="scroller-area">

            <div style="padding: 0.5rem;">
            <div style="padding-bottom: 0.5rem;">
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

              <Button
                class="ml-2"
                label="Clear"
                severity="warning"
                size="small"
              />
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
import Checkbox from 'primevue/checkbox';
import Panel from 'primevue/panel';


// import { Codemirror } from "vue-codemirror";
// import { oneDark } from '@codemirror/theme-one-dark';


// const props = defineProps([
//   'theme'
// ]);

const filterValue = ref("");

const options = ref([]);

const isQuotes = computed(() => {
  return options.value.includes('quotes');
});

const linenum = computed(() => {
  return options.value.includes('linenum');
})

const upstreamLogs = inject('debug_logs');

// TODO debounce for quick typing
const filteredLogs = computed(() => {
  return upstreamLogs.filter(logObj => {
    return logObj.event.includes(filterValue.value);
  });
});

// TODO some leftover code from before for now, since we just tried using this
// new widget.
// const debug_logs = computed(() => {
//   return JSON.stringify(upstream_logs, undefined, 2);
// });

// const codeExtensions = computed(() => {
//     const ext = [];

//     if (props.theme === 'dark') {
//         ext.push(oneDark);
//     }
//     return ext;

// });

</script>

<style lang="scss">
.data-container {
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
}

.log-panel {
  margin-top: 1rem;
  margin-bottom: 1rem;
  position: relative;

  .p-panel-header {
    background: var(--surface-b);
    padding: 0.75rem 1rem;
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
  top: 0.65rem;
}

</style>
