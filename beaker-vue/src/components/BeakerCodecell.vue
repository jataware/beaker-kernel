<template>
    <div class="code-cell">
        <Codemirror
            v-model="cell.source"
            placeholder="Your code..."
            :extensions="extensions"
            @keydown.ctrl.enter.self.stop.prevent="execute"
            @keydown.alt.enter="console.log('alt-enter')"
            @keydown.shift.enter.prevent="execute"
            @keydown.meta.enter="console.log('meta-enter')"
        />

        <CodeCellOutput :outputs="cell.outputs"/>
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
    "selectedTheme"
]);

const cell = ref(props.cell);

const extensions = computed(() => {
    const ext = [];

    const subkernel = props?.contextData?.language?.subkernel || '';
    const isPython = subkernel.includes('python');
    if (isPython) {
        ext.push(python());
    }
    if (props.selectedTheme === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});


const execute = (evt: any) => {
    const handleDone = (message: any) => {
        console.log("I'm done executing!: ", message);
        console.log(props.cell)
    };

    evt.preventDefault();
    evt.stopPropagation();
    // const sourceCode = cell.value.source;
    const future = props.cell.execute(props.session);
    future.done.then(handleDone);
}
</script>


<style>
.code-cell {
    padding: 1em;
}

</style>
