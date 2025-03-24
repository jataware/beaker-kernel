<template>
    <div class="kernel-state-panel">
        <div v-for="tree, header in treeData" :key="header">
            <h4>{{header}}</h4>
            <Tree :value="tree" class="kernel-state-tree" @nodeSelect="() => {}">

            </Tree>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { defineProps, computed } from "vue";

import Tree from "primevue/tree"
import { TreeNode } from "primevue/treenode";


type BeakerKernelStateNode = {
    label: string,
    children?: BeakerKernelStateNode[]
    key?: string
}
type BeakerKernelStateVariable = {[key in string]: BeakerKernelStateNode}
type BeakerKernelState = {
    'x-application/beaker-subkernel-state': {
        'application/json': {
            [key in string]: BeakerKernelStateVariable
        }
    }
}

const props = defineProps<{
    'data': BeakerKernelState
}>();

const data = computed(() => props?.data?.["x-application/beaker-subkernel-state"]?.["application/json"])

const treeData = computed<{[header in string]: TreeNode[]}>(() => {
    const source: {[key in string]: BeakerKernelStateVariable} = {...data.value};
    // primevue reactivity requires a unique key on each dropdown - we can use the label text.
    const attachKeysToNodes = (node: BeakerKernelStateNode): BeakerKernelStateNode => {
        node.children = node?.children?.map((child) => attachKeysToNodes(child))
        node.key = node.label;
        return node;
    }
    let keyedNodes: {[header in string]: TreeNode[]} = {}
    for (const [header, symbols] of Object.entries(source)) {
        keyedNodes[header] = []
        for (const [_variableName, value] of Object.entries(symbols)) {
            keyedNodes[header].push(attachKeysToNodes(value))
        }
    }
    return keyedNodes;
})

</script>

<style lang="scss">

.kernel-state-panel {
    margin-left: 0.5rem;
}

.kernel-state-tree {
    padding: 0;
    border: none;
    background-color: unset;
    span.p-treenode-label {
        font-family: monospace;
        font-size: 0.9rem;
    }
    /* only if child and also leaf */
    ul.p-treenode-children li.p-treenode-leaf {
        button.p-tree-toggler {
            display: none;
        }
        margin-left: 1rem;
        margin-bottom: 0;
    }
    li.p-treenode {
        margin-bottom: 1rem;
        .p-treenode-content {
            .p-tree-toggler {
                margin-right: 0;
                width: 1rem;
                height: 1rem;
            }
            padding: 0;
        }
    }
}

</style>
