<template>
    <Card>
        <template #title>
            How can the agent help?
        </template>

        <template #content>
            <div class="query-input-container">
                <InputText 
                    class="llm-query-input"
                    @keydown.enter="handleQuery"
                    v-model="query"
                    placeholder="Ask the AI a question or request an operation"
                />

                <Button
                    @click="handleQuery"
                    class="agent-submit-button"
                    icon="pi pi-reply"
                    label="enter"
                />
            </div>
        </template>
    </Card>
</template>


<script setup lang="ts">
import { defineProps, defineEmits, ref, nextTick } from "vue";
import Card from 'primevue/card';
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
    query.value = "";
    emit("select-cell", cell);
    nextTick(() => {
        // Delay running of cell by a ticket to allow selection and rendering to complete.
        emit("run-cell", cell);
    })
}
</script>


<style lang="scss" scoped>
.llm-query-input {
    margin-right: 0.75rem;
    flex: 1;
    &::placeholder {
        color: var(--gray-400);
    }
}

.p-card .p-card-content, .p-card-body {
    padding-bottom: 0.5rem;
    padding-top: 1rem;
}

.query-input-container {
    display: flex;
}

.agent-submit-button {
    flex: 0 1 7rem;
}

</style>
