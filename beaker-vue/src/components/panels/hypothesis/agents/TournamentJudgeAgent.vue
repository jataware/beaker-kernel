<template>
    <div v-if="output.parsed" class="tournament-agent">
        <!-- Compact view: winner and toggle on one line -->
        <div class="compact-row">
            <div v-if="output.parsed.winner" class="winner-compact">
                <i class="pi pi-trophy"></i>
                <span>Winner: {{ output.parsed.winner.toUpperCase() }}</span>
            </div>

            <div class="expand-toggle" @click="expanded = !expanded">
                <span>{{ expanded ? 'Hide' : 'Show' }} Comparison</span>
                <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
            </div>
        </div>

        <!-- Expanded view: full comparison -->
        <div v-if="expanded" class="expanded-content">
            <div class="matchup">
                <div class="hypothesis-snippet">
                    <span class="label">Hypothesis A:</span>
                    <span class="text">{{ output.parsed.hypothesis_a }}</span>
                </div>
                <div class="hypothesis-snippet">
                    <span class="label">Hypothesis B:</span>
                    <span class="text">{{ output.parsed.hypothesis_b }}</span>
                </div>
            </div>

            <div v-if="output.parsed.decision_summary" class="decision-summary">
                <strong>Decision:</strong>
                <p>{{ output.parsed.decision_summary }}</p>
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
.tournament-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.75rem;

    .compact-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .winner-compact {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 0.5rem;
        background: var(--p-highlight-bg);
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--p-primary-color);

        i {
            font-size: 0.8rem;
        }
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
        transition: background 0.2s;
        flex-shrink: 0;

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

    .matchup {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;

        .hypothesis-snippet {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            padding: 0.5rem;
            background: var(--p-surface-100);
            border-radius: 4px;

            .label {
                font-weight: 600;
                color: var(--p-text-color-secondary);
                font-size: 0.7rem;
            }

            .text {
                color: var(--p-text-color);
                font-style: italic;
                line-height: 1.3;
                font-size: 0.8rem;
            }
        }
    }

    .decision-summary {
        strong {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--p-text-color-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: block;
            margin-bottom: 0.25rem;
        }

        p {
            margin: 0;
            font-size: 0.8rem;
            color: var(--p-text-color-secondary);
            line-height: 1.4;
        }
    }
}
</style>
