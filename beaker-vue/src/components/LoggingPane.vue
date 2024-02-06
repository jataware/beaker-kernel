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

            <vue-json-pretty 
              :data="upstream_logs" 
              :deep="3"
              showLength
              showIcon
              :showDoubleQuotes="isQuotes"
              :showLineNumber="linenum"
            />
          </div>
          </div>
        </div>

</template>

<script lang="ts" setup>

import { ref, computed, defineProps, inject } from "vue";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import Checkbox from 'primevue/checkbox';

// import { Codemirror } from "vue-codemirror";
// import { oneDark } from '@codemirror/theme-one-dark';


// const props = defineProps([
//   'theme'
// ]);

const options = ref([]);

const isQuotes = computed(() => {
  return options.value.includes('quotes');
});

const linenum = computed(() => {
  return options.value.includes('linenum');
})

const upstream_logs = inject('debug_logs');


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
</style>
