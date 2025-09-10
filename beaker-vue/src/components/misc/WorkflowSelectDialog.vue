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
                <p class="attached-label">Currently Active:</p>
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
        
        <div class="workflow-content">
            <div class="workflow-list">
                <Card
                    v-for="workflow, id in searchResults"
                    class="workflow-card"
                    :class="{ 
                        'selected-card': selectedWorkflowId === id,
                        'current-card': id === attachedWorkflowId
                    }"
                    @click="selectWorkflow(id)"
                    @mouseleave="hoveredCard = undefined"
                    @mouseenter="hoveredCard = id"
                >
                    <template #title>
                        <div class="card-title">
                            {{ workflow.title }}
                            <span v-if="id === attachedWorkflowId" class="current-badge">Current</span>
                            <span v-if="workflow.category" class="category-badge">{{ workflow.category }}</span>
                        </div>
                    </template>
                    <template #content>
                        <p class="card-description">{{ workflow.human_description }}</p>
                        <div class="card-meta">
                            <span class="stages-count">{{ workflow.stages?.length || 0 }} stages</span>
                        </div>
                    </template>
                </Card>
            </div>
            
            <div class="workflow-preview" v-if="selectedWorkflow">
                <Card class="preview-card">
                    <template #title>{{ selectedWorkflow.title }}</template>
                    <template #subtitle>
                        <div class="preview-badges">
                            <span v-if="selectedWorkflow.category" class="category-badge large">{{ selectedWorkflow.category }}</span>
                            <span class="stages-badge">{{ selectedWorkflow.stages?.length || 0 }} stages</span>
                        </div>
                    </template>
                    <template #content>
                        <div class="preview-content">
                            <div class="section">
                                <h4>Description</h4>
                                <p>{{ selectedWorkflow.human_description }}</p>
                            </div>
                            
                            <div class="section" v-if="selectedWorkflow.example_prompt">
                                <h4>Example Usage</h4>
                                <div class="example-prompt">{{ selectedWorkflow.example_prompt }}</div>
                            </div>
                            
                            <div class="section" v-if="selectedWorkflow.stages?.length">
                                <h4>Workflow Stages</h4>
                                <div class="stages-list">
                                    <div v-for="(stage, index) in selectedWorkflow.stages" :key="index" class="stage-item">
                                        <span class="stage-number">{{ index + 1 }}</span>
                                        <span class="stage-name">{{ stage.name }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                    <template #footer>
                        <div class="preview-actions">
                            <Button 
                                :label="selectedWorkflowId === attachedWorkflowId ? 'Already Active' : `Start ${selectedWorkflow.title}`"
                                :disabled="selectedWorkflowId === attachedWorkflowId"
                                @click="confirmSelection"
                                icon="pi pi-play"
                                class="select-button"
                            />
                        </div>
                    </template>
                </Card>
            </div>
            
            <div class="workflow-preview empty-preview" v-else>
                <Card class="preview-card">
                    <template #content>
                        <div class="empty-state">
                            <i class="pi pi-arrow-left" style="font-size: 2rem; color: var(--p-surface-400);"></i>
                            <p>Select a workflow to see details</p>
                        </div>
                    </template>
                </Card>
            </div>
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
const selectedWorkflowId = ref<undefined|string>(undefined);
const searchText = ref<undefined|string>(undefined);

const setWorkflow = (id?: string) => {
    // convert undefined to null as well so undefined doesn't get in json body
    session.executeAction('set_workflow', {workflow: id ? id : null});
    dialogRef.value.close();
}

const selectWorkflow = (id: string) => {
    selectedWorkflowId.value = id;
}

const confirmSelection = () => {
    if (selectedWorkflowId.value) {
        setWorkflow(selectedWorkflowId.value);
    }
}

const clear = () => setWorkflow(null);

const { workflows, attachedWorkflowId, attachedWorkflow } = useWorkflows(beakerSession);

const selectedWorkflow = computed(() => {
    if (!selectedWorkflowId.value || !workflows.value) return null;
    return workflows.value[selectedWorkflowId.value];
});

const searchResults = computed<{[key in string]: any}>(() => {
    if (!workflows.value) return {};
    return Object.fromEntries(
        Object.entries(workflows.value).filter(([_, workflow]) =>
            searchText.value === ""
            || searchText.value === undefined
            || [
                workflow.human_description,
                workflow.title,
                workflow.category
            ].join(' ').toLocaleLowerCase().includes(searchText.value.toLocaleLowerCase()))
    );
});

</script>

<style>
.workflow-dialog {
    width: 80vw;
    max-width: 1200px;
    height: 80vh;
    max-height: 800px;
    display: flex;
    flex-direction: column;

    p {
        margin-top: 0.75rem;
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
    }
    
    .workflow-content {
        display: flex;
        flex: 1;
        gap: 1.5rem;
        min-height: 0;
    }
    
    .workflow-list {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        overflow-y: auto;
        padding-right: 0.5rem;
        min-width: 0;
    }
    
    .workflow-card {
        cursor: pointer;
        transition: all 150ms ease;
        border: 2px solid transparent;
        
        &:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        &.selected-card {
            border-color: var(--p-primary-color);
            background: var(--p-primary-50);
        }
        
        &.current-card {
            border-color: var(--p-green-500);
            background: var(--p-green-50);
        }
    }
    
    .card-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .current-badge {
        background: var(--p-green-500);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .category-badge {
        background: var(--p-surface-200);
        color: var(--p-surface-700);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        
        &.large {
            font-size: 0.85rem;
            padding: 0.3rem 0.7rem;
        }
    }
    
    .card-description {
        margin: 0.5rem 0;
        line-height: 1.4;
        color: var(--p-text-color-secondary);
    }
    
    .card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
    }
    
    .stages-count {
        font-size: 0.85rem;
        color: var(--p-text-color-secondary);
        font-weight: 500;
    }
    
    .workflow-preview {
        flex: 1.2;
        min-width: 400px;
    }
    
    .preview-card {
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .preview-badges {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-top: 0.5rem;
    }
    
    .stages-badge {
        background: var(--p-primary-100);
        color: var(--p-primary-700);
        padding: 0.3rem 0.7rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .preview-content {
        flex: 1;
    }
    
    .section {
        margin-bottom: 1.5rem;
        
        h4 {
            margin: 0 0 0.5rem 0;
            color: var(--p-text-color);
            font-size: 1rem;
            font-weight: 600;
        }
        
        p {
            margin: 0;
            line-height: 1.5;
            color: var(--p-text-color-secondary);
        }
    }
    
    .example-prompt {
        background: var(--p-surface-100);
        border: 1px solid var(--p-surface-200);
        border-radius: 6px;
        padding: 0.75rem;
        font-family: var(--p-font-family-monospace, monospace);
        font-size: 0.9rem;
        line-height: 1.4;
        color: var(--p-text-color);
    }
    
    .stages-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .stage-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem;
        background: var(--p-surface-50);
        border-radius: 4px;
        border-left: 3px solid var(--p-primary-300);
    }
    
    .stage-number {
        background: var(--p-primary-color);
        color: white;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    .stage-name {
        font-weight: 500;
        color: var(--p-text-color);
    }
    
    .preview-actions {
        display: flex;
        justify-content: flex-end;
        padding-top: 1rem;
    }
    
    .select-button {
        min-width: 200px;
    }
    
    .empty-preview .preview-card {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .empty-state {
        text-align: center;
        color: var(--p-text-color-secondary);
        
        p {
            margin-top: 0.5rem;
            font-size: 1rem;
        }
    }
}

/* Responsive design */
@media (max-width: 1000px) {
    .workflow-dialog {
        width: 95vw;
        height: 90vh;
        
        .workflow-content {
            flex-direction: column;
        }
        
        .workflow-list {
            max-height: 40vh;
        }
        
        .workflow-preview {
            min-width: unset;
            flex: 1;
        }
    }
}
</style>
