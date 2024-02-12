<template>
    <div
        class="code-cell"
        :class="{busy: isBusy}"
    >
        <Codemirror
            v-model="cell.source"
            placeholder="Your code..."
            :extensions="codeExtensions"
            :disabled="isBusy"
            @keydown.ctrl.enter.self.stop.prevent="execute"
            @keydown.alt.enter="console.log('alt-enter')"
            @keydown.shift.enter.prevent="execute"
            @keydown.meta.enter="console.log('meta-enter')"
        />

        <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" />
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';

const props = defineProps([
    "cell",
    "session",
    "contextData",
    "theme"
]);

const cell = ref(props.cell);
const isBusy = ref(false);

const codeExtensions = computed(() => {
    const ext = [];

    const subkernel = props?.contextData?.language?.subkernel || '';
    const isPython = subkernel.includes('python');
    if (isPython) {
        ext.push(python());
    }
    if (props.theme === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});


const execute = (evt: any) => {
    isBusy.value = true;

    const handleDone = async (message: any) => {

        // Timeout added to busy indicators from jumping in/out too quickly
        setTimeout(() => {
            isBusy.value = false;
        }, 1000);
    };

    evt.preventDefault();
    evt.stopPropagation();
    // const sourceCode = cell.value.source;
    const future = props.cell.execute(props.session);
    future.done.then(handleDone);
}
</script>


<style lang="scss">
.code-cell {
    padding: 1rem;
}

.busy {
}

</style>
