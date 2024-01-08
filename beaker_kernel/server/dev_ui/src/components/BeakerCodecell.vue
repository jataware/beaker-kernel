<template>
    <div class="code-cell">
        <Codemirror
            v-model="cell.source"
            placeholder="Your code..."
            @ready="handleReady"
            @keydown.ctrl.enter.self.stop.prevent="execute"
            @keydown.alt.enter="console.log('alt-enter')"
            @keydown.shift.enter.prevent="execute"
            @keydown.meta.enter="console.log('meta-enter')"
        />

        <CodeCellOutput :outputs="cell.outputs"/>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, defineModel } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";

const props = defineProps([
    "cell",
    "session",
]);

const cell = ref(props.cell);

const handleReady = (e: any) => {
    // console.log(props.content)
    console.log(e);
}

const execute = (evt: any) => {
    const handleDone = (message: any) => {
        console.log("I'm done!: ", message);
        console.log(props.cell)
    };

    evt.preventDefault();
    evt.stopPropagation();
    const sourceCode = cell.value.source;
    console.log(`about to exectute: "${sourceCode}"`);
    console.log(props.cell);
    console.log(props.session);
    const future = props.cell.execute(props.session);
    console.log(future);
    console.log(props.cell);
    future.done.then(handleDone);
}
</script>


<style>
.code-cell {
    padding: 1em;
}

</style>
