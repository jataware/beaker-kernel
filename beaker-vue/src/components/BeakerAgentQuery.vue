<template>
    <Card>
        <template #title>
            How can the agent help?
        </template>

        <template #content>
            <div class="query-input-container">
                <InputText 
                    type="text"
                    id="llm-query-input"
                    @keydown.enter="handleQuery"
                    v-model="query"
                    placeholder="Your wish is my command..."
                />

                <Button @click="handleQuery" icon="pi pi-reply" label="enter" />
            </div>
        </template>
    </Card>
</template>


<script setup lang="ts">

import { defineProps, defineEmits, ref, nextTick } from "vue";

import Card from 'primevue/card';
// import Panel from 'primevue/panel';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';

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
    margin-right: 0.75rem;
    width: 15rem;
}

.query-input-container {
/*
    padding: 0.5em;
*/
}
</style>
