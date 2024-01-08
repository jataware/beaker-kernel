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
import { defineProps, ref } from "vue";

const props = defineProps([
    "session",
]);

const query = ref("");

const handleQuery = (e: any) => {
    props.session.addQueryCell(query.value);
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
