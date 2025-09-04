<template>
    <div class="workflow-container">
        <p v-if="!attachedWorkflow">
            No workflow selected. Select one above or ask the agent about which workflow could work for your task.
        </p>
        <Stepper :value="activeStage" v-if="attachedWorkflow">
            <StepItem v-for="stage, index of attachedWorkflow?.stages" :value="index + 1">
                <Step>
                    {{ createHeader(stage.name) }}
                </Step>
                <StepPanel>
                    <!-- https://github.com/primefaces/primeng/issues/17320, also #17157 -->
                    <span class="p-stepper-separator" data-pc-section="separator" data-p="vertical"></span>
                    <div class="stage-contents">
                        <ul>
                            <li v-for="step in stageBodyHtml[index]" v-html="step" style="white-space: pre-line;">
                            </li>
                        </ul>

                        <div class="step-results" v-if="parsedResults?.[stage.name]?.results_markdown">
                            <div class='step-separator' />

                            <div
                                class="step-dropdown step-dropdown-details"
                                :onclick="() => {resultDropdowns[index] = !resultDropdowns[index]}"
                            >
                                <span class="pi" :class="{
                                    'pi-angle-right': !resultDropdowns[index],
                                    'pi-angle-down': resultDropdowns[index]
                                }"/>
                                <span class="step-dropdown-label">
                                    {{resultDropdowns[index] ? 'Hide' : 'Show'}} Stage Results
                                </span>
                            </div>
                            <div class="results-container" v-if="resultDropdowns[index]">
                                <div class="results-inner" v-html="parsedResults?.[stage.name].results_markdown"></div>
                            </div>
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
import { useWorkflows } from '../../composables/useWorkflows';
import { marked } from "marked";

const activeStage = ref<number>(1);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const resultDropdowns = ref<{[key in number]?: boolean}>({});

const { attachedWorkflow, attachedWorkflowProgress } = useWorkflows(beakerSession);

const parsedResults = computed(() => Object.fromEntries(
    Object.entries(attachedWorkflowProgress?.value ?? {}).map(([name, details]) => {
        return [name, {...details, results_markdown: marked.parse(details?.results_markdown ?? "") as string}];
})))

const parsedSteps = computed(() =>
    (attachedWorkflow?.value?.stages ?? []).map(stage =>
        stage.steps.map(step =>
            marked.parse(step?.prompt ?? "") as string)));

const parsedDescription = computed(() =>
    (attachedWorkflow?.value?.stages ?? []).map(stage =>
        (stage?.description ?? []).map(step =>
            marked.parse(step ?? "") as string)));

const stageBodyHtml = computed(() => parsedSteps.value.map(
    (step, index) => {
        const description = parsedDescription.value?.[index];
        if (description.length === 0) {
            return step;
        } else {
            return description;
        }
    })
);

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
    for (const [stageName, progress] of Object.entries(newValue ?? {})) {
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
    /* https://github.com/primefaces/primeng/issues/17320, also #17157 */
    div.p-steppanel-content {
        display: flex;
        flex-direction: column;
    }
    div.p-steppanel-content span.p-stepper-separator {
        min-height: 0;
        display: inline-block;
    }

    span.p-step-title {
        font-size: 1rem;
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
        li::marker {
            align-self: flex-start;
            width: 200px;

        }
        p {
            margin: 0;
        }
    }

}

.results-container {
    margin-top: 0.5rem;
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

.step-separator {
    background-color: var(--p-surface-d);
    height: 1px;
    width: 100%;
    margin: 0.5rem 0 0.5rem 0;
}
.step-results {
    margin-top: -1.5rem;
}

.step-dropdown {
    font-size: 0.8rem;
    display: flex;
    flex-direction: row;
    gap: 0.2rem;
    justify-content: flex-start;
    color: var(--p-surface-h);
    span.pi {
        font-size: 0.85rem;
    }
    * {
        margin: auto 0.2rem auto 0;
    }
    &:hover {
        cursor: pointer;
        .step-dropdown-label {
            text-decoration: underline;
            color: var(--p-surface-f);
        }
    }
}
</style>
