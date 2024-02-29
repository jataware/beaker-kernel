<template>
    <div class="code-cell-output jp-RenderedText">
        <div v-for="output of props.outputs" :key="output">
            <div v-if="output.output_type == 'stream'" :class="output.output_type">{{ output.text }}</div>
            <div v-else-if="output.output_type == 'display_data'" :class="output.output_type" v-html="renderResult(output)"></div>
            <div v-else-if="output.output_type == 'execute_result'" :class="output.output_type" v-html="renderResult(output)"></div>
            <div v-else-if="output.output_type == 'error'" :class="output.output_type" v-html="renderError(output)"></div>
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
    bundle['application/vnd.jupyter.error'] = errorOutput;
    const traceback = errorOutput.traceback?.join('\n');
    bundle['application/vnd.jupyter.stderr'] = traceback || `${errorOutput.ename}: ${errorOutput.evalue}`;
    return renderResult({data: bundle});
};
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

.stderr {
    color: #a44; // seems unused
    white-space: pre;
}


</style>
