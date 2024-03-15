<template>
  <div class="single-cell-playground">
    <div>

      <br />
      <br />
      <br />

      <NotebookControls 
        single-cell 
        :runCell="runCell"
        :selectedCellIndex="selectedCellIndex"
      />

      <Cell 
        :cell="cell"
        ref="cellRef"
        class="selected"
        :renderOutput="false"
      />

      <h3>Output</h3>
      <CodeOutput :outputs="cell.outputs" />

      <br />

      <div style="width: 50%; margin: auto;">
      <!--
        <ContextSelection />
        -->
      </div>

      <br />

    </div>
  </div>
</template>

<script setup>

import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, VNodeRef } from "vue";

import Cell from './lib/UICell.vue';
import CodeOutput from './lib/UICodeCellOutput.vue';
import NotebookControls from './lib/UINotebookControls.vue';
// import ContextSelection from './lib/UIContextSelection.vue';

const session = inject('session');

const activeContext = ref(undefined);
const selectedCellIndex = ref(0);
const cellRef = ref(null);

provide('active_context', activeContext);
provide('theme', 'light');

const selectCell = (index) => {
    selectedCellIndex.value = index;
}

function runCell() {
    cellRef.value.execute();
}

const cell = computed(() => {
  const { cells } = session.notebook;
  return cells.length ? cells[0] : {};
});

onBeforeMount(() => {
  session.addCodeCell("");
  nextTick(() => {
    selectCell(0);
  });
});

</script>

<style lang="scss">
</style>
