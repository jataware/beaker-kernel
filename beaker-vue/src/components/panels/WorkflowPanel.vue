<template>
    <div class="workflow-container">
        <div class="header" v-if="attachedWorkflow">
            <h4> {{ attachedWorkflow.title }}</h4>
            <p>
                {{ attachedWorkflow.human_description }}
            </p>
            <p>Example: <i>{{ attachedWorkflow.example_prompt }}</i></p>
        </div>

        <p v-else>
            No workflow selected. Select one above or ask the agent about which workflow could work for your task.
        </p>
        <Stepper :value="activeStage" v-if="attachedWorkflow">
            <StepItem v-for="stage, index of attachedWorkflow?.stages" :value="index + 1">
                <Step> {{ createHeader(stage.name) }} </Step>
                <StepPanel>
                    <div class="stage-contents">
                        <ul>
                            <li v-for="step in parsedSteps[index]" v-html="step" style="white-space: pre-line;">
                            </li>
                        </ul>
                        <div class="results-container" v-if="parsedResults?.[stage.name]?.results_markdown">
                            <div class="results-inner" v-html="parsedResults?.[stage.name].results_markdown"></div>
                        </div>
                    </div>
                </StepPanel>
            </StepItem>
        </Stepper>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, watch } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { Stepper, StepItem, Step, StepPanel } from "primevue";

import { marked } from "marked";

const activeStage = ref<number>(1);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const workflows = computed(() => {
    return beakerSession?.activeContext?.info?.workflows?.workflows;
})

const attachedWorkflowId = computed(() => {
    return beakerSession?.activeContext?.info?.workflows?.attached?.workflow_id;
})

const attachedWorkflowProgress = computed<{[key in string]: {
    code_cell_id: string,
    state: 'in_progress' | 'finished',
    results_markdown: string}
}>(() => {
    return beakerSession?.activeContext?.info?.workflows?.attached?.progress;
})

const attachedWorkflow = computed(() => {
    return workflows.value?.[attachedWorkflowId.value]
})

const parsedResults = computed(() => Object.fromEntries(
    Object.entries(attachedWorkflowProgress?.value ?? {}).map(([name, details]) => {
        return [name, {...details, results_markdown: marked.parse(details?.results_markdown ?? "") as string}];
})))

const parsedSteps = computed(() =>
    (attachedWorkflow?.value?.stages ?? []).map(stage =>
        stage.steps.map(step =>
            marked.parse(step?.prompt ?? "") as string)));

const createHeader = (name) => {
    const stateMappings = {
        'in_progress': '(In Progress)',
        'finished': '(Finished)',
        undefined: ''
    }
    return `${name} ${stateMappings[attachedWorkflowProgress.value?.[name]?.state]}`
}

// autoselector
watch(attachedWorkflowProgress, (newValue) => {
    for (const [stageName, progress] of Object.entries(newValue)) {
        if (progress?.state === 'in_progress') {
            const newestStep = attachedWorkflow.value.stages.findIndex((stage) => stage?.name === stageName)
            if (newestStep !== undefined) {
                // one-indexed
                activeStage.value = newestStep + 1;
            }
        }
    }
})

</script>


<style lang="scss">

.workflow-container {
    .header {
        h4 {
            margin-top: 0.5rem;
        }
        margin-left: 1rem;
    }
}

.stage-contents {
    display: flex;
    flex-direction: column;
    ul {
        padding-left: 1rem;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        p {
            margin: 0;
        }
    }

}

.results-container {
    background-color: var(--p-surface-b);
    border-radius: var(--p-surface-border-radius);
    padding: 0.5rem;
    :nth-child(1) {
        margin-top: 0;
    }
    :nth-last-child(1) {
        margin-bottom: 0;
    }
    white-space: pre-line;
    .results-inner {
        display: flex;
        flex-direction: column;
    }

    h1 { font-size: 1.3rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1.10rem; }
    h4 { font-size: 1.05rem; }
    br,hr { width: 100%; }
}

</style>
