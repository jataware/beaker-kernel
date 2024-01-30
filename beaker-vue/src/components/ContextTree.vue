<template>
  <div class="context-sidebar">
      <h4 class="context-heading">
          Context
      </h4>
    
      <Button 
          class="context-toggle-button"
          icon="pi pi-angle-right"
          size="small"
          outlined
          aria-label="Toggle Context Pane"
          :class="{ 'button-rotate': contextPanelOpen }"
          :onClick="toggleContextPanel"
     />

      <Tree
          v-if="contextPanelOpen"
          class="context-tree"
          :value="contextNodes"
          v-model:expandedKeys="contextExpandedKeys"
      ></Tree>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps } from "vue";
import Button from 'primevue/button';
import Tree from 'primevue/tree';

const contextPanelOpen = ref(true);
const toggleContextPanel = () => {
    contextPanelOpen.value = !contextPanelOpen.value;
};

// This should mostly be uncontrolled, but it was
// "hard" to open by default without controlling
const contextExpandedKeys = ref({0: true, 1: true});

// TODO use contextData to create contextNodes below
const props = defineProps([
    "contextData"
]);
const contextNodes = [{
    key: '0',
    label: 'Kernel',
    data: 'Kernel Details',
    icon: 'pi pi-fw pi-cog',
    expanded: true,
    children: [{
        key: '0-0',
        label: 'language=python',
        data: 'Python',
        icon: 'pi pi-fw pi-align-justify'
    },
    {
        key: '0-1',
        label: 'version=3.11.2',
        data: '3.11.2',
        icon: 'pi pi-fw pi-wrench'
    }]
},
{
    key: '1',
    label: 'env',
    data: 'Environment Variables',
    icon: 'pi pi-fw pi-cloud',
    expanded: true,
    children: [{
        key: '1-0',
        label: 'deployment=dev',
            data: 'development',
        icon: 'pi pi-fw pi-cog'
    },
    {
        key: '1-1',
        label: 'agent-backend=openai',
        data: 'openai',
        icon: 'pi pi-fw pi-qrcode'
    }]
}];
</script>


<style lang="scss">
.context-sidebar {
  display: flex;
  flex-direction: column;
  position: relative;
}

.context-heading {
  color: var(--text-color-secondary);
  margin: 1rem 1.25rem 0.25rem 1.25rem;  
}

.context-tree {
  padding: 0;
  border: none;
  
  width: 19rem;
  padding: 0.75rem;
  
  .p-tree-container .p-treenode .p-treenode-content {
      padding: 0;
      border: none;
  }
}

.context-toggle-button {
  position: absolute;
  right: -0.5rem;
  top: 40%;
  background: var(--surface-a);
  border-color: var(--surface-300);
  color: var(--primary-300);
}

.button-rotate {
  transform: rotate(180deg);
}
</style>
