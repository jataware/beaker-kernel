<template>
    <div class="llm-query-cell">
        <div class="query">{{ cell.source }}</div>
        <div class="thought" v-for="thought of cell.thoughts" :key="thought">Thought: {{ thought }}</div>
        <div class="response">{{ cell.response }}</div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, ref, onMounted } from "vue";

const props = defineProps([
    "cell",
    "session",
]);

const cell = ref(props.cell);

</script>


<style>
.llm-query-cell {
    padding: 1em;
}

.query {
    font-weight: bold;
    margin-bottom: 0.5em;
}

.thought {
    color: orange;
}

.response {
    margin-top: 1em;
    white-space: pre-line;
    /* color: black; */
}

</style>
