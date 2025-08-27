import { computed } from 'vue';
import type { ComputedRef } from 'vue';
import type { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';

export interface WorkflowStep {
    prompt: string;
    metadata?: { [key: string]: any };
}

export interface WorkflowStage {
    name: string;
    steps: WorkflowStep[];
    metadata?: { [key: string]: any };
    description?: string[] | null;
}

export interface Workflow {
    title: string;
    agent_description: string;
    human_description: string;
    example_prompt: string;
    stages: WorkflowStage[];
    hidden?: boolean;
    is_context_default?: boolean;
    category?: string | null;
    metadata?: { [key: string]: any };
    output_prompt?: string | null;
}

interface UseWorkflowsReturn {
    workflows: ComputedRef<{[key: string]: Workflow} | undefined>;
    attachedWorkflowId: ComputedRef<string | undefined>;
    attachedWorkflow: ComputedRef<Workflow | undefined>;
    attachedWorkflowProgress: ComputedRef<{[key: string]: {
        code_cell_id: string,
        state: 'in_progress' | 'finished',
        results_markdown: string
    }} | undefined>;
}

export function useWorkflows(beakerSession: BeakerSessionComponentType): UseWorkflowsReturn {
    const workflows = computed(() => {
        return beakerSession?.activeContext?.info?.workflows?.workflows;
    });

    const attachedWorkflowId = computed(() => {
        return beakerSession?.activeContext?.info?.workflows?.attached?.workflow_id;
    });

    const attachedWorkflow = computed(() => {
        return workflows.value?.[attachedWorkflowId.value];
    });

    const attachedWorkflowProgress = computed(() => {
        return beakerSession?.activeContext?.info?.workflows?.attached?.progress;
    });

    return {
        workflows,
        attachedWorkflowId,
        attachedWorkflow,
        attachedWorkflowProgress,
    };
}
