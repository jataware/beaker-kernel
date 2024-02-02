<template>
    <div class="llm-query-cell">
        <div style="display: flex; justify-content: space-between">
            <div class="query">{{ cell.source }}</div>
            <div v-if="busy">
                <i
                    class="pi pi-spin pi-spinner"
                    style="color: var(--blue-500); font-weight: bold;"
                />
            </div>
            <div v-else>
                <i
                    class="pi pi-check-circle"
                    style="color: var(--green-500); font-weight: bold;"
                />
            </div>
        </div>
        <div class="thought" v-for="thought of cell.thoughts" :key="thought">Thought: {{ thought }}</div>
        <div class="response">{{ cell.response }}</div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, ref, computed } from "vue";

const props = defineProps([
    "cell",
    "session",
]);

const cell = ref(props.cell);
const timeout = ref(false);

setTimeout(() => {
    timeout.value = true;
}, 8000);

const busy = computed(() => {
    return props.cell.source &&
     !props.cell.response &&
     !timeout.value
});

</script>


<style lang="scss">
.llm-query-cell {
    padding: 1em;
}

.query {
    font-weight: bold;
    margin-bottom: 0.5em;
}

.thought {
    color: var(--orange-400);
}

.response {
    margin-top: 1em;
    white-space: pre-line;
}

</style>
