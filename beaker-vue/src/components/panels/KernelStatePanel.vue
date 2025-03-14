<template>
    <div class="kernel-state-panel">
        <div v-for="tree, header in treeData" :key="header">
            <h4>{{header}}</h4>
            <Tree :value="tree" class="kernel-state-tree">

            </Tree>
        </div>

    </div>
</template>

<script lang="ts" setup>
import { ref, defineProps, defineEmits, inject, computed } from "vue";
import { BeakerQueryCell, BeakerCodeCell, BeakerSession, IBeakerCell } from 'beaker-kernel/src';

import Tree from "primevue/tree"
import { TreeNode } from "primevue/treenode";
import Toolbar from "primevue/toolbar";
import Button from "primevue/button";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import Dropdown from "primevue/dropdown";
import BeakerMimeBundle from "../render/BeakerMimeBundle.vue";

type BeakerKernelState = {
    'x-application/beaker-subkernel-state': {
        'state': {
            'application/json': {
                [key in string]: object
            }
        }
    }
}

const props = defineProps<{
    'data': BeakerKernelState
}>();

const data = computed(() => props?.data?.["x-application/beaker-subkernel-state"]?.state["application/json"])

// CustomDisplayTransforms match on variable_name -> repr(variable_name) pairs
// and transform it into tree nodes for primevue's tree component to handle interactivity.
//
// the main computed property matches on fields of BeakerKernelState to only apply
// transformations to arbitrarily defined categories to keep it as language agnostic as possible.

type CustomDisplayTransform = (key: string, payload: string) => TreeNode | object;

const pythonModuleDisplay: CustomDisplayTransform = (key, payload) => {
    if (payload.startsWith('<module') && payload.endsWith('>')) {
        const chunks = payload.split(' ').map(string => string.replaceAll(`'`, ''));
        return {
            key: `module-${chunks[1]}`,
            label: `${key}` + (key !== chunks[1] ? ` (${chunks[1]})` : ''),
            children: [
                {
                    key: `module-${chunks[1]}-inner`,
                    label: `import path: ${chunks[1]}: ${chunks[3].slice(0, -1)}`
                }
            ]
        }
    }
    return {}
}

const pythonVariableDisplay: CustomDisplayTransform = (key, payload) => {
    const { value, type, size } = JSON.parse(payload);
    const typeDisplay = type.slice("<class '".length, -"'>".length).split('.').pop();
    const specialContainerTypes = [
        'list',
        'dict',
        'DataFrame',
        'nparray',
        'ndarray',
        'Dataset'
    ]

    const node: TreeNode = {
        key: `variable-${key}`,
        label: `${key} (${typeDisplay}): ${value}`
                + (specialContainerTypes.includes(typeDisplay) ? ` (size: ${size})` : '')
    }

    // arbitrary cutoff
    if (value.length > 10) {
        node.label = `${key} (${typeDisplay}): ... (size: ${size})`
        node.children = [{
            key: `variable-${key}-expanded`,
            label: value
        }]
    }
    return node
}

const pythonFunctionDisplay: CustomDisplayTransform = (key, payload) => {
    const { docstring, signature } = JSON.parse(payload);
    const children = docstring === null ? []: [
        {
            key: `${key}-inner-docstring`,
            label: docstring
        }
    ]
    return {
        key,
        label: `${key}: ${signature}`,
        children
    }
}

// [
//   [transformerFunction, [<list of headers to fire on>]],
//   ...
// ]
const customTransforms: [(key: string, payload: string) => TreeNode, string[]][] =
    [
        [pythonModuleDisplay, ['modules']],
        [pythonVariableDisplay, ['variables']],
        [pythonFunctionDisplay, ['functions']]
    ];

const treeData = computed<{[header in string]: TreeNode[]}>(() => {
    const source: BeakerKernelState = (data.value as BeakerKernelState);
    if (source === undefined) {
        return {}
    }
    return Object.keys(source).reduce((payload, header) => {
        customTransforms.forEach(([func, match]) => {
            if (match.includes(header)) {
                console.log(source, header);
                payload[header] = Object.keys(source[header]).reduce((replacements, key) => {
                    replacements.push( func(key, source[header][key]));
                    return replacements;
                }, [])
            }
        })
        return payload;
    }, {} as {[header in string]: TreeNode[]})
})

const session = inject<BeakerSession>('session');

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
