<template>
    <div class="info-panel-container">
    <!-- <Accordion :multiple="true">
        <AccordionTab header="Kernel/System">
            <h3>Kernel</h3> -->
            <!-- <div><label>Display name</label>{{ activeContext.kernelInfo.display_name }}</div> -->
            <!-- <div><label>Language</label>{{ kernelInfo.language }}</div>
            <div><label>Metadata</label>{{ kernelInfo.metadata }}</div>
            <div><label>Extra</label>{{ kernelInfo.extra }}</div> -->



            <!-- <div>{{activeContext}}</div>

        </AccordionTab>
        <AccordionTab header="Context">

        </AccordionTab>
        <AccordionTab header="Agent">

        </AccordionTab>
    </Accordion> -->
    <Tree
        :value="contextNodes"
        :loading="!contextNodes"
        v-model:expandedKeys="contextExpandedKeys"
    >
        <template v-slot:loadingicon>
            <div class="loading-area">
                No Context Loaded.
            </div>
        </template>
        <template #action="slotProps">
            <div
                @mousedown="($event.detail > 1) && $event.preventDefault();"
                style="cursor: pointer; border-bottom: 1px dotted var(--text-color-secondary);"
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
</template>

<script setup lang="ts">
import { ref, defineEmits, onBeforeMount, computed, inject } from "vue";
import Tree from 'primevue/tree';
import { TreeNode } from 'primevue/treenode';
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import DataView from "primevue/dataview";
import { emitError } from "vue-json-pretty/types/utils";
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';

const contextPanelOpen = ref(true);
const toggleContextPanel = () => {
    contextPanelOpen.value = !contextPanelOpen.value;
};

// This should mostly be uncontrolled, but it was
// "hard" to open by default without controlling
// TODO easier way for tree to auto-open by default
const contextExpandedKeys = ref({0: true, 1: true, 2: true, 3: true});

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const activeContext = computed(() => {
    const contextInfo = beakerSession?.activeContext;
    const kernelInfo = beakerSession?.session.kernelInfo;
    return {
        ...contextInfo,
        kernelInfo,
    };
});

const contextNodes = computed<TreeNode[]>(() => {

    const context = activeContext.value;

    if (!context) {
        return [];
    }

    const displayableNodes: TreeNode[] = [{
        key: "0",
        label: 'Kernel',
        icon: 'pi pi-fw pi-cog',
        expanded: true,
        children: [
            {
                key: '0-1',
                label: `${context?.info?.subkernel} (${context?.info?.language})`,
            },
            // ...Object.entries(context?.kernelInfo || {}).map(
            //     ([key, value]) => {
            //         return {
            //             key: `0-${key}`,
            //             label: `${key}: ${value}`,
            //         }
            //     }
            // ),
    ]
    }];

    displayableNodes.push({
        key: "3",
        label: 'Tools',
        icon: 'pi pi-fw pi-wrench',
        expanded: true,
        children: Object.keys(context?.info?.agent?.tools || {})
            .map((toolname, idx) => ({
                key: `3-${idx}`,
                label: toolname.replace('PyPackageAgent.', ''),
                data: context.info.agent.tools[toolname],
                type: 'tool'
            }))
    });

    return displayableNodes;

});

</script>


<style lang="scss">

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
