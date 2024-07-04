<template>
    <div class="code-cell-output jp-RenderedText" v-if="stripInvisibleOutputs(props.outputs).length > 0">
        <div v-for="output of stripInvisibleOutputs(props.outputs)" :key="output">
            <div v-if="output.output_type == 'stream'" :class="output.output_type">{{ output.text }}</div>
            <BeakerMimeBundle
                v-else-if="['display_data', 'execute_result'].includes(output.output_type)"
                :mime-bundle="output.data"
                collapse="true"
            />
            <div v-else-if="output.output_type == 'error'" :class="output.output_type">
                <BeakerMimeBundle :mime-bundle="rebundleError(output)" collapse="true" />
            </div>
            <div v-else>{{ output }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, inject } from "vue";
import BeakerMimeBundle from "./BeakerMimeBundle.vue";
import { IMimeBundle } from 'beaker-kernel/render';

const session = inject('session');


const props = defineProps([
    "outputs",
    "busy",
    "isVisible"
]);

const stripInvisibleOutputs = (outputs) => {
    return outputs.filter((output) => {
        const displayAnyway = ['display_data', 'execute_result'].includes(output.output_type);
        return props.isVisible || displayAnyway;
    });
}

const rebundleError = (errorOutput) => {
    const traceback = (Array.isArray(errorOutput.traceback) ? errorOutput.traceback?.join('\n') : errorOutput.traceback?.toString());
    const bundle = {
        'application/vnd.jupyter.error':  errorOutput,
        'application/vnd.jupyter.stderr': traceback || `${errorOutput.ename}: ${errorOutput.evalue}`,
    }
    return bundle;
}
</script>


<style lang="scss">
@import url('@jupyterlab/notebook/style/index.css');
@import url('@jupyterlab/outputarea/style/index.css');
@import url('@jupyterlab/rendermime/style/index.css');

.code-cell-output {
    padding: 1rem;
    background-color: var(--surface-c);
    position: relative;
    overflow-x: auto;
    .execute_result {
        pre {
            white-space: break-spaces;
            overflow-wrap: break-word;
        }
    }
}

.stdout {
    // was dark purple and hard to see- replaced with theme colors
    color: var(--text-color-secondary);
    white-space: pre;
    font-style: italic;
}

.stream {
    white-space: pre-wrap;
}

.stderr {
    color: #a44; // seems unused
    white-space: pre;
}


</style>
