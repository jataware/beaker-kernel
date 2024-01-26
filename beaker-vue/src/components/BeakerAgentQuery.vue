<template>
    <div class="query-input-container">
        How can the agent help?
        <div>
            <input id="llm-query-input" @keydown.enter="handleQuery" v-model="query" placeholder="Type here to ask the AI a question or to do something for you..." />
            <button @click="handleQuery">Submit</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, nextTick } from "vue";

const props = defineProps([
    "session",
]);

const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
]);

const handleQuery = (e: any) => {
    const cell = props.session.addQueryCell(query.value);
    emit("select-cell", cell);
    nextTick(() => {
        // Delay running of cell by a ticket to allow selection and rendering to complete.
        emit("run-cell", cell);
    })
}
</script>


<style>
#llm-query-input {
    margin-right: 1em;
    width: 80%;
}

.query-input-container {
    border: 1px solid darkgray;
    padding: 0.5em;
}
</style>
