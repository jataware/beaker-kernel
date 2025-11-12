<template>
    <div v-if="output.parsed && output.parsed.research_goal_analysis" class="supervisor-agent">
        <p class="summary">{{ output.parsed.research_goal_analysis.goal_summary }}</p>

        <div class="expand-toggle" @click="expanded = !expanded">
            <span>{{ expanded ? 'Hide' : 'Show' }} Details</span>
            <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
        </div>

        <div v-if="expanded" class="expanded-content">
            <div v-if="output.parsed.research_goal_analysis.key_areas" class="key-areas">
                <strong>Key Areas:</strong>
                <ul>
                    <li v-for="(area, i) in output.parsed.research_goal_analysis.key_areas" :key="i">{{ area }}</li>
                </ul>
            </div>

            <div v-if="output.parsed.workflow_plan?.generation_phase" class="workflow-plan">
                <strong>Workflow Plan:</strong>
                <div class="plan-details">
                    <div class="plan-item">
                        <span class="label">Target:</span>
                        <span>{{ output.parsed.workflow_plan.generation_phase.quantity_target }} hypotheses</span>
                    </div>
                    <div class="plan-item">
                        <span class="label">Diversity:</span>
                        <span>{{ output.parsed.workflow_plan.generation_phase.diversity_targets }}</span>
                    </div>
                    <div v-if="output.parsed.workflow_plan.generation_phase.strategies" class="plan-item">
                        <span class="label">Strategies:</span>
                        <ul>
                            <li v-for="(strategy, i) in output.parsed.workflow_plan.generation_phase.strategies" :key="i">
                                {{ strategy }}
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <div v-if="output.parsed.workflow_plan?.review_phase" class="review-plan">
                <strong>Review Phase Plan:</strong>
                <div class="plan-details">
                    <div class="plan-item">
                        <span class="label">Reviews per hypothesis:</span>
                        <span>{{ output.parsed.workflow_plan.review_phase.reviews_per_hypothesis }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface AgentOutput {
    name: string;
    content: string;
    parsed: any;
    timestamp: number;
}

defineProps<{
    output: AgentOutput;
}>();

const expanded = ref(false);
</script>

<style lang="scss" scoped>
.supervisor-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;

    .summary {
        margin: 0;
        line-height: 1.5;
        color: var(--p-text-color);
    }

    .expand-toggle {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--p-primary-color);
        font-weight: 500;
        align-self: flex-start;
        transition: background 0.2s;

        &:hover {
            background: var(--p-surface-200);
        }

        i {
            font-size: 0.7rem;
        }
    }

    .expanded-content {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--p-surface-border);
    }

    .key-areas, .workflow-plan, .review-plan {
        display: flex;
        flex-direction: column;
        gap: 0.375rem;

        strong {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--p-text-color-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        ul {
            margin: 0;
            padding-left: 1.25rem;
            font-size: 0.8rem;
            line-height: 1.4;
            color: var(--p-text-color-secondary);

            li {
                margin: 0.25rem 0;
            }
        }
    }

    .plan-details {
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
        padding-left: 0.5rem;
        font-size: 0.8rem;

        .plan-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;

            .label {
                font-weight: 600;
                color: var(--p-text-color-secondary);
            }

            span {
                color: var(--p-text-color);
            }

            ul {
                margin: 0;
                padding-left: 1rem;
            }
        }
    }
}
</style>
