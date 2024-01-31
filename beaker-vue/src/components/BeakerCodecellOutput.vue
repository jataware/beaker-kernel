<template>
    <div class="code-cell-output">
        <div v-for="output of props.outputs" :key="output">
            <div v-if="output.output_type == 'stream'" :class="output.name">{{ output.text }}</div>
            <div v-else-if="output.output_type == 'display_data'" :class="output.name" v-html="renderResult(output)"></div>
            <div v-else-if="output.output_type == 'execute_result'" :class="output.name" v-html="renderResult(output)"></div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed } from "vue";
import { RenderMimeRegistry} from '@jupyterlab/rendermime';
import { standardRendererFactories } from '@jupyterlab/rendermime';

const renderMimeRegistry = new RenderMimeRegistry({
    initialFactories: standardRendererFactories
});


// renderMimeRegistry.

const props = defineProps([
    "outputs"
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
</script>


<style lang="scss">
@import url('@jupyterlab/notebook/style/index.css');
// @import url('@jupyterlab/theme-light-extension/style/theme.css');

.code-cell-output {
    padding: 1em;
    background-color: var(--surface-b);
}

.stdout {
    color: #448;
    white-space: pre;
}

.stderr {
    color: #a44;
    white-space: pre;
}

</style>
