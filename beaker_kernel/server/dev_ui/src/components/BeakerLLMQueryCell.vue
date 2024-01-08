<template>
    <div class="llm-query-cell">
        <div class="query">{{ props.cell?.source }}</div>
        <div class="thought" v-for="thought of props.cell?.thoughts" :key="thought.id">Thought: {{ thought }}</div>
        <div class="response">{{ props.cell?.response }}</div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, ref, onMounted } from "vue";

const props = defineProps([
    "session",
    "cell",
]);

// onMounted(() => {

// });


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
}

</style>
