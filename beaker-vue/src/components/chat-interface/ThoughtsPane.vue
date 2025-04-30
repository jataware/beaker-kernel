<template>
  <div class="thoughts-pane">
    <div v-if="!selectedCell">
      <em>No cell selected.</em>
    </div>
    <div v-else>
      <div class="filter-controls">
        <div class="filter-button-group">

          <Button label="Scroll to Message" outlined @click="scrollToMessage" class="p-button-sm" />
          <!-- <Button label="Unselect Cell" outlined @click="unselectCell" class="p-button-sm" /> -->

          <ToggleButton v-model="showCodeCells" outlined on-label="Hide Code" off-label="Show Code"
            on-icon="pi pi-eye-slash" off-icon="pi pi-eye" class="p-button-sm filter-button" />

          <ToggleButton v-model="showThoughtCells" outlined on-label="Hide Thoughts" off-label="Show Thoughts"
            on-icon="pi pi-eye-slash" off-icon="pi pi-eye" class="p-button-sm filter-button" />
        </div>
      </div>
      <div class="events-scroll-container">
        <BeakerQueryCellEvent 
          v-for="(event, eventIndex) in filteredCellEvents"
          :key="eventIndex" 
          :event="event" 
        />

        <ProgressBar v-if="isSelectedCellInProgress" mode="indeterminate"
          style="height: 6px; width: 40%; margin: 1rem auto;" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, computed, ref, defineEmits } from 'vue';
import ProgressBar from 'primevue/progressbar';
import ToggleButton from 'primevue/togglebutton';
import Button from 'primevue/button';
import BeakerQueryCellEvent from '../cell/BeakerQueryCellEvent.vue';

const props = defineProps<{
  selectedCell: any | null
}>();

const emit = defineEmits<{
  (e: 'scrollToMessage'): void
  (e: 'unselectCell'): void
}>();

const showCodeCells = ref(true);
const showThoughtCells = ref(true);

const isSelectedCellInProgress = computed(() => {
  return props.selectedCell.status === 'busy';
});

const selectedCellEvents = computed(() => {
  if (!props.selectedCell) {
    return null;
  }

  return props.selectedCell?.events || [];
});

const scrollToMessage = () => {
  console.log("scrollToMessage");
  emit('scrollToMessage');
}

const unselectCell = () => {
  emit('unselectCell');
}

// Filter events based on toggle states
const filteredCellEvents = computed(() => {
  if (!selectedCellEvents.value) return [];

  return selectedCellEvents.value.filter(event => {

    if (!showCodeCells.value && event.type === 'code_cell') {
      return false;
    }

    if (!showThoughtCells.value && event.type === 'thought') {
      return false;
    }

    // Hardcode remove response so it isn't displayed twice
    // (once in main chat; once in the thoughts pane)
    if (event.type === 'response') {
      return false;
    }

    return true;
  });
});

</script>

<style scoped lang="scss">
.thoughts-pane {
  padding: 1rem;
  margin-right: 1rem;
  overflow-y: auto;
  max-height: 100%;
  scrollbar-width: thin;
  scrollbar-color: var(--surface-d) var(--surface-a);
}

.events-scroll-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  color: #043d75;
}


.filter-controls {
    display: flex;
    flex-direction: column;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    background-color: var(--surface-ground);
    border-radius: 6px;
}
.filter-label {
    font-size: 0.85rem;
    color: var(--text-color-secondary);
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.filter-button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}
.filter-button {
    background-color: var(--surface-card) !important;
    border-color: var(--surface-border) !important;
    color: var(--text-color-secondary) !important;
}

.filter-button.p-togglebutton.p-button.p-highlight :deep(.p-button-icon.p-button-icon-left),
.filter-button.p-togglebutton.p-button.p-highlight :deep(.p-button-icon.p-button-icon-right) {
    color: var(--text-color-secondary) !important;
}

.filter-button.p-highlight {
    background-color: var(--surface-hover) !important;
    border-color: var(--surface-border) !important;
    color: var(--text-color) !important;
}
.filter-button.p-highlight .p-button-icon {
    color: var(--text-color) !important;
}
.filter-button:hover {
    background-color: var(--surface-hover) !important;
    border-color: var(--primary-color) !important;
}
</style>