<template>
  <div class="thoughts-pane">
    <div v-if="!selectedCell">
      <em>Select <i class="pi pi-search" style="margin: 0 0.25rem; color: var(--text-color-secondary);"></i> agent activity from the conversation to view details.</em>
    </div>
    <div v-else class="thoughts-pane-content">
      <div class="pane-actions">
        <Button
          icon="pi pi-arrow-circle-right"
          text
          @click="scrollToMessage"
          v-tooltip.bottom="'Scroll to related user message.'"
        />
      </div>
      <div class="events-scroll-container" v-autoscroll>
        <div v-if="shouldShowNoThoughtsPlaceholder" class="no-thoughts-message">
          <em>No details available for this agent query.</em>
        </div>
        <ChatQueryCellEvent 
          v-else
          v-for="(event, eventIndex) in filteredCellEvents"
          :key="eventIndex+props.selectedCell.id"
          :event="event" 
          :parent-query-cell="props.selectedCell"
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
    return !["user_answer", "response"].includes(event.type);
  })
  .map((event, index, all_events) => {
    const isLastEvent = index === all_events.length - 1;
    // if user_question event is last, add marker for unanswered question
    const unansweredQuestion = event.type === 'user_question' && isLastEvent;
    if (unansweredQuestion) {
      return {
        ...event,
        waitForUserInput: true
      }
    }
    return event;
  })
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
  gap: 0.5rem;
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

.pane-actions {
  position: fixed;
  top: 2.5rem;
  right: 5rem;
  z-index: 100;
  & > .p-button {
    color: var(--text-color-secondary);
  }
}
</style>
