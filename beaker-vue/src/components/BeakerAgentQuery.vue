<template>
    <div class="agent-input-card">
        <h3>
            What Would You Like To Do?
        </h3>

            <div class="query-input-container">
                <ContainedTextArea
                    @submit="handleQuery"
                    v-model="query"
                    style="flex: 1; margin-right: 0.75rem; max-width: 40rem;"
                    placeholder="Ask the AI or request an operation."
                />

                <Button
                    @click="handleQuery"
                    class="agent-submit-button"
                    icon="pi pi-reply"
                    label="enter"
                />
            </div>
    </div>
</template>


<script setup lang="ts">
import { defineProps, defineEmits, ref, nextTick, inject } from "vue";
import Card from 'primevue/card';
import Button from 'primevue/button';
import ContainedTextArea from './ContainedTextArea.vue';


const props = defineProps([
    "runCellCallback"
]);

const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
]);

const session = inject("session");

const handleQuery = (e: any) => {
    if (!query.value.trim()) {
        return; // TODO notify user that they're missing the agent query?
    }

    const cell = session.addQueryCell(query.value);
    query.value = "";
    emit("select-cell", cell);
    nextTick(() => {
        // Delay running of cell by a ticket to allow selection and rendering to complete.
        emit("run-cell", cell);
        setTimeout(() => {
            props.runCellCallback();
        }, 1000);
    });
}

</script>


<style lang="scss">
.agent-input-card {
  padding: 0.5rem 0.75rem 0.5rem 0.75rem;
  border-bottom: 1px solid var(--surface-c);
}

.query-input-container {
    display: flex;
    align-items: flex-start;
}

.agent-submit-button {
    flex: 0 1 7rem;
}

</style>
