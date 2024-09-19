<template>
    <Card class="agent-input-card">
        <template #title>
            How can the agent help?
        </template>

        <template #content>
            <div class="query-input-container">
                <ContainedTextArea
                    @submit="handleQuery"
                    v-model="query"
                    style="flex: 1; margin-right: 0.75rem"
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
import { defineProps, defineEmits, ref, nextTick, inject } from "vue";
import Card from 'primevue/card';
import Button from 'primevue/button';
import ContainedTextArea from '../misc/ContainedTextArea.vue';

import { BeakerSession } from 'beaker-kernel/src';
import { type BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { type BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';

const props = defineProps([
    "runCellCallback"
]);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const notebook = inject<BeakerNotebookComponentType>("notebook");

const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
]);

const session: BeakerSession = inject("session");

const handleQuery = (e: any) => {
    if (!query.value.trim()) {
        return; // TODO notify user that they're missing the agent query?
    }

    // Remove the top cell if it is blank/not used.
    if (notebook.notebook.cells.length === 1) {
        const existingCell = notebook.notebook.cells[0];
        if (
            existingCell.cell_type === "code" && existingCell.source === ""
            && existingCell.execution_count === null && existingCell.outputs.length === 0
        ) {
            notebook.notebook.removeCell(0);
        }
    }
    const cell = session.addQueryCell(query.value);
    query.value = "";

    nextTick(() => {
        notebook.selectCell(cell.id);
        beakerSession.findNotebookCellById(cell.id).execute();
    });
}

</script>


<style lang="scss">
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
