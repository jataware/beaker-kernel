<template>
    <div class="code-cell">
        <Codemirror
            v-model="cell.source"
            placeholder="Your code..."
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

const execute = (evt: any) => {
    const handleDone = (message: any) => {
        console.log("I'm done executing!: ", message);
        console.log(props.cell)
    };

    evt.preventDefault();
    evt.stopPropagation();
    const sourceCode = cell.value.source;
    const future = props.cell.execute(props.session);
    future.done.then(handleDone);
}
</script>


<style>
.code-cell {
    padding: 1em;
}

</style>
