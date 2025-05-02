<template>
  <div class="thoughts-pane">
    <div v-if="!selectedCell">
      <em>Select <i class="pi pi-search" style="margin: 0 0.25rem; color: var(--text-color-secondary);"></i> agent actions from the conversation to view details.</em>
    </div>
    <div v-else class="thoughts-pane-content">
      <div class="filter-controls">
        <div class="filter-button-group">

          <Button label="Scroll To Query" outlined @click="scrollToMessage" class="p-button-sm" />

          <ToggleButton v-model="showCodeCells" outlined on-label="Hide Code" off-label="Show Code"
            on-icon="pi pi-eye-slash" off-icon="pi pi-eye" class="p-button-sm filter-button" 
            :disabled="shouldShowNoThoughtsPlaceholder"
            @click="handleCodeToggle" />

          <ToggleButton v-model="showThoughtCells" outlined on-label="Hide Thoughts" off-label="Show Thoughts"
            on-icon="pi pi-eye-slash" off-icon="pi pi-eye" class="p-button-sm filter-button" 
            :disabled="shouldShowNoThoughtsPlaceholder"
            @click="handleThoughtToggle" />
        </div>
      </div>
      <div class="events-scroll-container">
        <div v-if="shouldShowNoThoughtsPlaceholder" class="no-thoughts-message">
          <em>No Thought details available for this agent query.</em>
        </div>
        <ChatQueryCellEvent 
          v-else
          v-for="(event, eventIndex) in filteredCellEvents"
          :key="eventIndex" 
          :event="event" 
          :is-chat="true"
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
import ChatQueryCellEvent from './ChatQueryCellEvent.vue';

const props = defineProps<{
  selectedCell: any | null
}>();

const emit = defineEmits<{
  (e: 'scrollToMessage'): void
}>();

const showCodeCells = ref(true);
const showThoughtCells = ref(true);

const handleCodeToggle = () => {
  if (!showCodeCells.value) {
    showThoughtCells.value = true;
  }
};
const handleThoughtToggle = () => {
  if (!showThoughtCells.value) {
    showCodeCells.value = true;
  }
};

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
  emit('scrollToMessage');
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

const shouldShowNoThoughtsPlaceholder = computed(() => {
  if (!selectedCellEvents.value || isSelectedCellInProgress.value) {
    return false;
  }

  // Check if query is complete (idle) and has only a response event
  const hasOnlyResponse = selectedCellEvents.value.length === 1 && 
    selectedCellEvents.value[0].type === 'response';

  return props.selectedCell.status === 'idle' && hasOnlyResponse;
});

</script>

<style scoped lang="scss">
.thoughts-pane {
  padding: 1rem;
  // margin-right: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.thoughts-pane-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  position: relative;
  overflow: hidden;
}

.events-scroll-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  color: var(--text-color);

  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--surface-d) var(--surface-a);
  padding-right: 0.5rem;
  margin-right: 0.5rem;
  padding-top: 0.5rem;
}

.no-thoughts-message {
  text-align: center;
  padding: 1rem;
  color: var(--text-color-secondary);
}

.filter-controls {
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