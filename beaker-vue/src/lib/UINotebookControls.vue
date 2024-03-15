<template>
  <div class="notebook-controls">
      <InputGroup>
          <Button
              v-if="!props.singleCell"
              @click="addCell"
              icon="pi pi-plus"
              size="small"
              severity="info"
              text
          />
          <Button
              v-if="!props.singleCell"
              @click="removeCell"
              icon="pi pi-minus"
              size="small"
              severity="info"
              text
          />
          <Button
              @click="props.runCell"
              icon="pi pi-play"
              size="small"
              severity="info"
              text
          />
      </InputGroup>
      <slot name="additional-controls" />
  </div>
</template>

<script setup>
import { inject, computed, defineProps, nextTick } from 'vue';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import { focusSelectedCell } from './common.ts';

const session = inject('session');

const props = defineProps({
  singleCell: {
    type: Boolean,
    default: false
  },
  selectCell: {
    type: Function,
    required: true
  },
  selectedCellIndex: {
    type: Number,
    required: true
  },
    runCell: {
    type: Function,
    required: true
  }
});

const selectedCell = computed(() =>  session.notebook.cells[props.selectedCellIndex])
const cellCount = computed(() => session.notebook?.cells?.length || 0);


function selectCellByObj(cellObj) {
  const index = session.notebook.cells.indexOf(cellObj);
  props.selectCell(index);
}


const addCell = (toIndex) => {
    const newCell = session.addCodeCell("");
    selectCellByObj(newCell);
    // Ensure cell is focused, not the editor or contents within
    nextTick(() => {
        focusSelectedCell();
    });
}

const removeCell = () => {
    session.notebook.removeCell(props.selectedCellIndex);
    // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    if (cellCount.value === 0) {
        session.addCodeCell("");
    }

    // Fixup the selection if we remove the last item.
    if (props.selectedCellIndex >= cellCount.value) {
        props.selectCell(cellCount.value - 1);
    }
};

</script>

<style lang="scss">

.notebook-controls {
    margin: 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .p-inputgroup {
        width: unset;
    }
}

</style>
