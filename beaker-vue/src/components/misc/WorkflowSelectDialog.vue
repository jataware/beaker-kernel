<template>
    <div class="workflow-dialog">
        <p>
            Workflows are pre-configured approaches for the LLM agent to use for guidance
            on tackling larger problems using tried-and-true to-do lists of tasks. One workflow
            may be active at a time for framing the agent's thoughts towards a particular goal.
        </p>
        <Divider></Divider>
        <div class="attached-workflow">
            <div v-if="attachedWorkflow">
                <p class="attached-label">Selected:</p>
                <div class="attached-workflow-inner">
                    <Button
                        @click="clear"
                        label="Clear"
                        icon="pi pi-times"
                        small
                    >
                    </Button>
                    <span class="attached-label">
                        {{ attachedWorkflow.title }}
                    </span>
                </div>
            </div>
            <p v-else class="attached-label" style="margin: 0">No workflow active.</p>
            <InputGroup style="margin: auto 0 0 auto; width: 50%">
                <InputGroupAddon>
                    <i class="pi pi-search"></i>
                </InputGroupAddon>
                <InputText placeholder="Search Workflows..." v-model="searchText">
                </InputText>
                <Button
                    v-if="searchText !== undefined && searchText !== ''"
                    icon="pi pi-times"
                    severity="danger"
                    @click="() => {searchText = undefined}"
                    v-tooltip="'Clear Search'"
                />
            </InputGroup>
        </div>
        <Divider></Divider>
        <div class="card-container">
            <Card
                v-for="workflow, id in searchResults"
                style="width: 23rem"
                :pt = "{
                    root: {
                        style:
                            'transition: background-color 150ms linear;' +
                            (hoveredCard === id
                                ? 'background-color: var(--p-surface-100); cursor: pointer;'
                                : '')
                    }
                }"
                @click="setWorkflow(id)"
                @mouseleave="hoveredCard = undefined"
                @mouseenter="hoveredCard = id"
            >
                <template #title>{{
                    id === attachedWorkflowId
                    ? `${workflow.title} (Selected)`
                    : workflow.title }}
                </template>
                <template #subtitle>{{ workflow.category }}</template>
                <template #content>
                    <p style="margin: 0">
                        {{ workflow.human_description }}
                    </p>
                </template>
            </Card>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { computed, inject, ref, watch, type ComputedRef } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { Button, Divider, Card, InputGroup, InputGroupAddon, InputText} from "primevue";
import { type BeakerSession } from "beaker-kernel";
import { useWorkflows } from '../../composables/useWorkflows';

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const session = inject<BeakerSession>('session');
const dialogRef: ComputedRef = inject('dialogRef');

const hoveredCard = ref<undefined|string>(undefined);

const searchText = ref<undefined|string>(undefined);

const setWorkflow = (id?: string) => {
    // convert undefined to null as well so undefined doesn't get in json body
    session.executeAction('set_workflow', {workflow: id ? id : null});
    dialogRef.value.close();
}

const clear = () => setWorkflow(null);

const { workflows, attachedWorkflowId, attachedWorkflow } = useWorkflows(beakerSession);

const searchResults = computed<{[key in string]: any}>(() => Object.fromEntries(
    Object.entries(workflows.value).filter(([_, workflow]) =>
        searchText.value === ""
        || searchText.value === undefined
        || [
            workflow.human_description,
            workflow.title,
            workflow.category
        ].join(' ').toLocaleLowerCase().includes(searchText.value.toLocaleLowerCase()))))

</script>

<style>
.workflow-dialog {
    width: 48rem;

    p {
        margin-top: 0.2rem;
    }

    .attached-workflow {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 0rem;
        .attached-workflow-inner {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
    }
    .attached-label {
        font-weight: 600;
        flex-shrink: 0;
    }
    .card-container {
        display: flex;
        max-height: 24rem;
        overflow-y: auto;
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.5rem;
    }
}
</style>
