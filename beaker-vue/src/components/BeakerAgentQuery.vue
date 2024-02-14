<template>
    <Card class="agent-input-card">
        <template #title>
            How can the agent help?
        </template>

        <template #content>
            <div class="query-input-container">
                <!--Needed to shorten the placeholder in order to
                    Start the textarea with 1 row since it auto-grows...
                -->
                <Textarea
                    class="llm-query-input"
                    @keydown.enter.exact="handleQuery"
                    autoResize
                    rows="1"
                    v-model="query"
                    placeholder="Ask the AI or request an operation."
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
import Textarea from 'primevue/textarea';


const props = defineProps([
    "session",
]);

const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
]);

const handleQuery = (e: any) => {
    if (!query.value.trim()) {
        return; // TODO notify user that they're missing the agent query?
    }
    
    const cell = props.session.addQueryCell(query.value);
    query.value = "";
    emit("select-cell", cell);
    nextTick(() => {
        // Delay running of cell by a ticket to allow selection and rendering to complete.
        emit("run-cell", cell);
    });
}
</script>


<style lang="scss">
.llm-query-input {
    margin-right: 0.75rem;
    flex: 1;
    // We may tweak the max-height,
    // but not setting a max value and creating huge forms
    // eventually pushes all content and breaks layout.
    max-height: 12rem;

    &::placeholder {
        color: var(--gray-400);
    }
}

.agent-input-card {
    .p-card-body .p-card-content {
        padding: 0.75rem 0;
    }
}

.query-input-container {
    display: flex;
    align-items: flex-start;
}

.agent-submit-button {
    flex: 0 1 7rem;
}

</style>
