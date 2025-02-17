<template>
    <div class="media-focus">
        <Toolbar class="media-toolbar">
            <template #start>
                <Button 
                    icon="pi pi-arrow-left" 
                    class="media-toolbar-button" 
                    severity="primary" 
                    outlined
                    :onclick="() => {
                        currentOutputOneIndexed -= (currentOutputOneIndexed - 1) < 1 
                            ? 0 
                            : 1
                    }" 
                />
                <Button 
                    icon="pi pi-arrow-right" 
                    class="media-toolbar-button" 
                    severity="primary"
                    outlined
                    :onclick="() => {
                        currentOutputOneIndexed += (currentOutputOneIndexed + 1) > notebookOutputs.length 
                            ? 0
                            : 1
                    }" 
                />
            </template>
            <template #end>
                <InputGroup>
                    <InputGroupAddon class="media-dropdown-icon">
                        <i class="pi pi-chart-bar"></i>
                    </InputGroupAddon>
                    <Dropdown 
                        v-model="currentOutputOneIndexed"
                        :options="[...Array(notebookOutputs.length + 1).keys()].slice(1)"
                    />

                    <InputGroupAddon>/ {{ notebookOutputs.length ?? 0 }}</InputGroupAddon>
                </InputGroup>
            </template>
        </Toolbar>
        <div class="media-mime-bundle">
            <div 
                v-html="currentMimeBundle['text/html']" 
                v-if="currentMimeBundle && currentMimeBundle['text/html'] !== undefined"
                class="code-cell-output"
                
            />
            <BeakerMimeBundle 
                :mime-bundle="currentMimeBundle" 
                v-else-if="currentMimeBundle !== undefined"
            />

        </div>
    </div>
</template>
  
<script lang="ts" setup>
import { ref, defineProps, defineEmits, inject, computed } from "vue";
import { BeakerQueryCell, BeakerCodeCell, BeakerSession, IBeakerCell } from 'beaker-kernel/src';
import Toolbar from "primevue/toolbar";
import Button from "primevue/button";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import Dropdown from "primevue/dropdown";
import BeakerMimeBundle from "../render/BeakerMimeBundle.vue";

const session = inject<BeakerSession>('session');

const props = defineProps(['dropdownValue'])
const emit = defineEmits(['update:dropdownValue'])

const currentOutputOneIndexed = ref(1);

const filteredMimetypes = [
    'image/png',
    'text/html'
]

const notebookOutputs = computed(() => {
    const outputs = [];
    const cells = session.notebook.cells;
    
    const getOutputs = (cell: IBeakerCell) => {
        const outputs = [];
        if (cell.cell_type === 'query') {
            for (const child of (cell as BeakerQueryCell)?.children ?? []) {
                outputs.push(...getOutputs(child));
            }
        }
        else if (cell.cell_type === 'code') {
            for (const output of (cell as BeakerCodeCell)?.outputs ?? []) {
                const data = output?.data ?? {};
                filteredMimetypes.forEach(mimetype => {
                    if (data[mimetype]) {
                        outputs.push(output);
                    }
                });
            }
        }
        return outputs;
    }; 

    for (const cell of cells) {
        outputs.push(...getOutputs(cell));
    }

    return outputs;
})

const currentMimeBundle = computed(() => {
    if (notebookOutputs.value.length === 0 || notebookOutputs.value === undefined) {
        return undefined;
    }
    const target = notebookOutputs.value[currentOutputOneIndexed.value - 1]?.data;
    if (target === undefined) {
        return undefined;
    }
    const {'text/plain': _, ...significantBundle} = target;
    return significantBundle;
})

</script>

<style lang="scss">

div.media-toolbar {
    padding: 0.5rem;
    background: none;
    border: none;
    button {
        width: 2em;
        height: 2em;
        margin-right: 0.5em;
    }
    .p-inputgroup {
        height: 2em;
        .media-dropdown-icon {
            min-width: 2em;
        }

        .p-dropdown-label {
            padding: 0;
            margin: auto;
            padding-left: 0.5rem;
        }

        .p-dropdown-trigger {
            width: 2rem;
        }
    }
}

.media-mime-bundle > div {
    overflow: auto;
    height: 100%;
    > .mime-select-container {
        display: none;
    }
    > .mime-payload img {
        width: 100%;
    }
}
</style>
