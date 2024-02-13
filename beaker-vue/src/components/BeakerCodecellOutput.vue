<template>
    <div class="code-cell-output">
        <i
            v-if="busy"
            class="pi pi-spin pi-spinner busy-icon"
        />
        <div v-for="output of props.outputs" :key="output">
            <div v-if="output.output_type == 'stream'" :class="output.name">{{ output.text }}</div>
            <div v-else-if="output.output_type == 'display_data'" :class="output.name" v-html="renderResult(output)"></div>
            <div v-else-if="output.output_type == 'execute_result'" :class="output.name" v-html="renderResult(output)"></div>
            <div v-else-if="output.output_type == 'error'" :class="output.name" v-html="renderError(output)"></div>
            <div v-else>{{ output }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps } from "vue";
import { RenderMimeRegistry} from '@jupyterlab/rendermime';
import { standardRendererFactories } from '@jupyterlab/rendermime';

const renderMimeRegistry = new RenderMimeRegistry({
    initialFactories: standardRendererFactories
});

const props = defineProps([
    "outputs",
    "busy"
]);

const renderResult = (resultOutput) => {
    const preferredMimeType = renderMimeRegistry.preferredMimeType(resultOutput.data);
    const renderer = renderMimeRegistry.createRenderer(preferredMimeType);
    const model = renderMimeRegistry.createModel({
        trusted: true,
        data: resultOutput.data,
        metadata: resultOutput.metadata,
    });
    renderer.render(model);
    return renderer.node.innerHTML;
}

const renderError = (errorOutput) => {
    const bundle = {};
    bundle['application/vnd.jupyter.error'] = errorOutput.content;
    const traceback = errorOutput.content.traceback?.join('\n');
    bundle['application/vnd.jupyter.stderr'] = traceback || `${errorOutput.content.ename}: ${errorOutput.content.evalue}`;
    return renderResult({data: bundle});
};
</script>


<style lang="scss">
@import url('@jupyterlab/notebook/style/index.css');
// @import url('@jupyterlab/theme-light-extension/style/theme.css');

.code-cell-output {
    padding: 1em;
    background-color: var(--surface-b);
    position: relative;
    overflow-x: auto;
}

.stdout {
    color: #448;
    white-space: pre;
}

.stderr {
    color: #a44;
    white-space: pre;
}

.busy-icon {
    color: var(--blue-500);
    font-weight: bold;
    font-size: 1.2rem;
    position: absolute;
    top: 0.4rem;
    right: 1.2rem;
}

</style>
