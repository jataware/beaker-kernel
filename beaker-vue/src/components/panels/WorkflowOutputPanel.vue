<template>
    <div class="workflow-container">
        <p v-if="!attachedWorkflow">
            No workflow selected. Select one above or ask the agent about which workflow could work for your task.
        </p>
        <div class="final-response p-steppanel" v-html="finalResponse">

        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { useWorkflows } from '../../composables/useWorkflows';
import { marked } from "marked";

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const { attachedWorkflow, attachedWorkflowFinalResponse } = useWorkflows(beakerSession);

const finalResponse = computed(() => {
    const workflow_response = attachedWorkflowFinalResponse.value;
    // clone the response before filtering empty rows on markdown tables
    let response = `${workflow_response}`;
    if (response === "") {
        response = "### No workflow output yet\nThis panel will be populated as the workflow stages complete."
    }
    response = response.split('\n').filter(line => !line.match(/^[|\s]+$/)).join('\n');
    return marked.parse(response)
})

</script>

<style lang="scss">

.final-response {
    h1 { font-size: 1.3rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1.10rem; }
    h4 { font-size: 1.05rem; }
    br,hr { width: 100%; }
    padding: 0.5rem;

    table {
        table-layout: fixed;
        margin: 0 auto;
        border-collapse: collapse;
        border: 1px solid var(--p-datatable-body-cell-border-color);
        tbody tr:nth-child(odd) {
            background-color: var(--p-datatable-row-background);
        }
        tbody tr:nth-child(odd) {
            background-color: var(--p-datatable-row-striped-background);
        }
    }

    th,
    td {
        padding: 0.2rem;
        border: 1px solid var(--p-datatable-body-cell-border-color);
    }
}

</style>
