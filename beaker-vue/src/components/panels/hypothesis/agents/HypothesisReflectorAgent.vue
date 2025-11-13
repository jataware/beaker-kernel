<template>
    <div class="reflector-agent">
        <!-- Compact view: score and toggle on one line -->
        <div class="compact-row">
            <div v-if="output.parsed?.overall_score !== undefined" class="overall-score-compact">
                <span class="label">Score</span>
                <span class="value">{{ (output.parsed.overall_score * 10).toFixed(1) }}%</span>
            </div>

            <div class="expand-toggle" @click="expanded = !expanded">
                <span>{{ expanded ? 'Hide' : 'Show' }} Details</span>
                <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
            </div>
        </div>

        <!-- Expanded view: all details -->
        <div v-if="expanded" class="expanded-content">
            <div v-if="output.parsed?.hypothesis_text" class="hypothesis-being-reviewed">
                <strong>Hypothesis:</strong>
                <p>{{ output.parsed.hypothesis_text }}</p>
            </div>

            <div v-if="output.parsed?.review_summary" class="review-summary">
                <strong>Summary:</strong>
                <p>{{ output.parsed.review_summary }}</p>
            </div>

            <div v-if="output.parsed?.scores && Object.keys(output.parsed.scores).length > 0" class="score-grid">
                <strong>Detailed Scores:</strong>
                <div class="score-items">
                    <div v-for="(value, key) in output.parsed.scores" :key="String(key)" class="score-item">
                        <span class="score-name">{{ formatScoreName(String(key)) }}</span>
                        <span class="score-value">{{ value }}/10</span>
                    </div>
                </div>
            </div>

            <div v-if="output.parsed?.constructive_feedback" class="feedback">
                <strong>Feedback:</strong>
                <p>{{ output.parsed.constructive_feedback }}</p>
            </div>

            <div v-if="output.parsed?.strengths" class="strengths">
                <strong>Strengths:</strong>
                <p>{{ output.parsed.strengths }}</p>
            </div>

            <div v-if="output.parsed?.weaknesses" class="weaknesses">
                <strong>Weaknesses:</strong>
                <p>{{ output.parsed.weaknesses }}</p>
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

const formatScoreName = (key: string): string => {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};
</script>

<style lang="scss" scoped>
.reflector-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;

    .compact-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .overall-score-compact {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.375rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        flex: 1;

        .label {
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--p-text-color-secondary);
        }

        .value {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--p-primary-color);
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
            line-height: 1.5;
            color: var(--p-text-color-secondary);
        }
    }

    .hypothesis-being-reviewed {
        padding: 0.5rem;
        background: var(--p-surface-100);
        border-left: 3px solid var(--p-primary-color);
        border-radius: 4px;

        p {
            font-style: italic;
            font-size: 0.825rem;
            line-height: 1.4;
            color: var(--p-text-color);
        }
    }

    .score-grid {
        .score-items {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.375rem;
            margin-top: 0.25rem;
        }

        .score-item {
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0.5rem;
            background: var(--p-surface-100);
            border-radius: 4px;
            font-size: 0.75rem;

            .score-name {
                color: var(--p-text-color-secondary);
            }

            .score-value {
                font-weight: 600;
                color: var(--p-text-color);
            }
        }
    }

    .strengths, .weaknesses {
        p {
            font-size: 0.8rem;
        }
    }
}
</style>
