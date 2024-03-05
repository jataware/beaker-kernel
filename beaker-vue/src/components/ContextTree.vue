<template>
    <div class="context-sidebar">
        <h4
            class="context-heading"
            :class="{hidden: !contextPanelOpen}"
        >
            Context
        </h4>

        <Button
            class="context-toggle-button"
            icon="pi pi-angle-right"
            size="small"
            outlined
            aria-label="Toggle Context Pane"
            :class="{ 'button-rotate': contextPanelOpen }"
            @click="toggleContextPanel"
        />

        <div
            v-if="contextPanelOpen"
            class="context-tree"
        >
            <Tree
                :value="contextNodes"
                :loading="!props.context"
                v-model:expandedKeys="contextExpandedKeys"
            >
                <template v-slot:loadingicon>
                    <div class="loading-area">
                        No Context Loaded.
                    </div>
                </template>
                <template #tool="slotProps">
                    <span
                        style="cursor: help; border-bottom: 1px dotted var(--text-color-secondary);"
                        v-tooltip="{
                            value: `${slotProps.node.data}`,
                            pt: {
                                text: {
                                    style: {
                                        width: '20rem'
                                    }
                                },
                                root: {
                                    style: {
                                        marginLeft: '1rem'
                                    }
                                }
                            }
                            }"
                        >
                        {{ slotProps.node.label }}
                    </span>
                </template>
            </Tree>
        </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, computed } from "vue";
import Button from 'primevue/button';
import Tree from 'primevue/tree';

const contextPanelOpen = ref(true);
const toggleContextPanel = () => {
    contextPanelOpen.value = !contextPanelOpen.value;
};

// This should mostly be uncontrolled, but it was
// "hard" to open by default without controlling
// TODO easier way for tree to auto-open by default
const contextExpandedKeys = ref({0: true, 1: true, 2: true, 3: true});

const props = defineProps([
    "context"
]);

const contextNodes = computed(() => {

    const { context } = props;

    if (!context) {
        return [];
    }

    const displayableNodes = [{
        key: 0,
        label: 'Kernel',
        icon: 'pi pi-fw pi-cog',
        expanded: true,
        children: [{
            key: '0-1',
            label: `${context.subkernel} (${context.language})`,
        }]
    }, {
        key: 1,
        label: 'Actions',
        icon: 'pi pi-fw pi-send',
        expanded: true,
        children: Object.keys(context.actions).map((action, idx) => {
            return ({
            key: `1-${idx}`,
            label: action,
            data: context.actions[action].docs + "\n\nExample payload:\n" + context.actions[action].default_payload,
            type: 'tool',
        })
    })
    }];

    if (context.procedures.length) {
        displayableNodes.push({
            key: 2,
            label: 'Procedures',
            icon: 'pi pi-fw pi-tablet',
            expanded: true,
            children: context.procedures.map((proc, idx) => ({
                key: `2-${idx}`,
                label: proc,
            }))
        });
    }

    displayableNodes.push({
        key: 3,
        label: 'Tools',
        icon: 'pi pi-fw pi-wrench',
        expanded: true,
        children: Object.keys(context?.agent?.tools || {})
            .map((toolname, idx) => ({
                key: `3-${idx}`,
                label: toolname.replace('PyPackageAgent.', ''),
                data: context.agent.tools[toolname],
                type: 'tool'
            }))
    });

    if (Object.keys(context.custom_messages).length) {
        displayableNodes.push({
            key: 4,
            label: 'Custom Messages',
            icon: 'pi pi-fw pi-comment',
            expanded: false,
            children: Object.keys(context.custom_messages).map((msg, idx) => ({
                key: `4-${idx}`,
                label: msg,
                data: context.custom_messages[msg].docs + "\n\nExample payload:\n" + context.custom_messages[msg].default_payload,
                type: 'tool'
            }))
        });
    }

    return displayableNodes;

});

</script>


<style lang="scss">
.context-sidebar {
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--surface-a);
  @media(max-width: 750px) {
    display: none;
  }
}

.context-heading {
  color: var(--text-color-secondary);
  margin: 1rem 1.25rem 0.25rem 1.25rem;
}

.context-tree {
  margin-top: 0.5rem;
  flex: 1;

  border: none;
  width: 21rem;
  position: relative;

  .p-tree {
    border: none;
  }

  .p-tree-wrapper {
    position: absolute;
    left: 1rem;
    top: 0;
    bottom: 0;
    right: 0;

    .p-treenode .p-treenode-content {
      padding: 0;
    }

  }

}

.context-toggle-button {
  position: absolute;
  right: -0.5rem;
  top: 40%;
  background: var(--surface-a);
  border-color: var(--surface-300);
  color: var(--primary-300);
  z-index: 2;
}

.button-rotate {
  transform: rotate(180deg);
}

.loading-area {
    background: var(--surface-a);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
}

.hidden {
    visibility: hidden;
}


</style>
