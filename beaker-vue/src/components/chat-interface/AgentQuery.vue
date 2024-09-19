<template>
    <Card class="agent-input-card">
        <template #content>
            <div class="query-input-container">
                <ContainedTextArea
                    @submit="handleQuery"
                    v-model="query"
                    style="flex: 1; margin-right: 0.75rem"
                    placeholder="How can the agent help?"
                />

                <Button
                    @click="handleQuery"
                    class="agent-submit-button"
                    icon="pi pi-reply"
                />
            </div>
        </template>
    </Card>
</template>


<script setup lang="ts">
import { defineEmits, ref, nextTick, inject } from "vue";
import Card from 'primevue/card';
import Button from 'primevue/button';
import ContainedTextArea from '../misc/ContainedTextArea.vue';
import { BeakerSession } from 'beaker-kernel/src';
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
]);

const session: BeakerSession = inject("session");
const handleQuery = (e: any) => {
    const notebook = session.notebook;
    if (!query.value.trim()) {
        return; // TODO notify user that they're missing the agent query?
    }
    // Remove the top cell if it is blank/not used.
    if (notebook.cells.length === 1) {
        const existingCell = notebook.cells[0];
        if (
            existingCell.cell_type === "code" 
            && existingCell.source === ""
            && existingCell.execution_count === null 
            && (existingCell.outputs as object[]).length === 0
        ) {
            notebook.removeCell(0);
        }
    }
    const cell = session.addQueryCell(query.value);
    query.value = "";
    nextTick(() => {
        beakerSession.findNotebookCellById(cell.id).execute();
    });
}
</script>


<style lang="scss">
.agent-input-card {
    .p-card-body .p-card-content {
        padding: 0;
    }
}
.agent-query-container {
    background-color: var(--surface-b);
}
.agent-query-container div {
    padding: 0rem;
}
.query-input-container {
    display: flex;
    align-items: flex-start;
    align-self: flex-end;
    margin-bottom: 0;
    padding: 0;
}
.query-input-container textarea {
    margin-bottom: 0;
}
.agent-submit-button {
    flex: 0 1 3rem;
    align-self: flex-end;
    height: 3rem;
}
</style>