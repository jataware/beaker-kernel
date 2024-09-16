<template>
    <div class="code-cell-output jp-RenderedText">
        <div class="code-cell-output-box" :class="{'collapsed-output': output.metadata?.collapsed}" v-for="output of props.outputs" :key="output">
            <div class="output-collapse-box" @click.capture.stop.prevent="collapseOutput(output)"></div>
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
import { ref, defineProps, inject } from "vue";
import BeakerMimeBundle from "../render/BeakerMimeBundle.vue";

const props = defineProps([
    "outputs",
    "busy"
]);

const collapseOutput = (output) => {
    const metadata = ref(output?.metadata || (output.metadata = {}))
    metadata.value.collapsed = !metadata.value.collapsed;
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
// @import url('@jupyterlab/outputarea/style/base.css');
// @import url('@jupyterlab/rendermime/style/base.css');
// @import url('@jupyterlab/notebook/style/base.css');

.code-cell-output {
    --collapse-height: 3em;

    padding: 0 0.5em 0.5em 0;
    background-color: var(--surface-c);
    position: relative;
    .execute_result {
        pre {
            white-space: break-spaces;
            overflow-wrap: break-word;
        }
    }
}

.collapsed-output {
    max-height: var(--collapse-height);
    overflow-y: auto;

    .output-collapse-box {
        background-color: var(--surface-border);
    }
}

.code-cell-output-box {
    margin-top: 0.5em;
    display: flex;
    flex-direction: row;
    height: 100%;
}

.output-collapse-box {
    min-width: 10px;
    width: 10px;
    border: 1px inset var(--surface-border);
    cursor: pointer;

    &:hover {
        background-color: color(from var(--surface-border) srgb r g b / 0.5);
    }
    margin-right: 0.5em;

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
