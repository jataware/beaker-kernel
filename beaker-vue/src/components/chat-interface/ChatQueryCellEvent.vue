<template>
    <BeakerQueryCellEvent
        :event="props.event"
        :parent-query-cell="props.parentQueryCell"
        :custom-class="isExpanded ? '' : 'code-cell-collapsed'"
    >
        <template #code-cell-controls>
            <Button 
                :icon="!isExpanded ? 'pi pi-window-minimize' : 'pi pi-window-maximize'" 
                size="small"
                class="code-cell-toggle-button" 
                @click.stop="toggleExpansion"
                :title="!isExpanded ? 'Shrink code cell' : 'Expand code cell'"
            />
        </template>
    </BeakerQueryCellEvent>

</template>

<script setup lang="ts">
import { defineProps, ref } from "vue";
import Button from "primevue/button";
import BeakerQueryCellEvent from "../cell/BeakerQueryCellEvent.vue";


const isExpanded = ref(false);

const props = defineProps([
    'event',
    'parentQueryCell',
]);

const toggleExpansion = (event) => {
  event.stopPropagation();
  isExpanded.value = !isExpanded.value;
};

</script>


<style lang="scss">
.code-cell-collapsed {
  max-height: 200px;
  overflow-y: hidden;
}
.code-cell-toggle-button {
  position: absolute;
  top: 4rem;
  right: 0;
  margin: 0;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: var(--surface-500);
  border-color: var(--surface-border);
  &>.p-button-icon {
    font-weight: bold;
  }
}
</style>